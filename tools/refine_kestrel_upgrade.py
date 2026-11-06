"""Repair user Kestrel GLB for Godot without replacing its original 3D asset.
Python stdlib only. Input SHA is verified by install_kestrel_upgrade.py.
Adds shaded normals, independent canopy glass, readably tinted materials and
a shorter rear-feather overhang; drops microscopic disconnected triangle islands.
"""
from __future__ import annotations
from collections import defaultdict
import json, math, struct

MIN_FACES=12
TAIL_START=-2.08

def unpack_glb(blob):
    assert blob[:4]==b"glTF" and struct.unpack_from("<I",blob,4)[0]==2
    assert struct.unpack_from("<I",blob,8)[0]==len(blob)
    offset=12
    chunks=[]
    while offset<len(blob):
        count,kind=struct.unpack_from("<I4s",blob,offset)
        offset+=8
        chunks.append((kind,blob[offset:offset+count]))
        offset+=count
    assert len(chunks)==2 and chunks[0][0]==b"JSON" and chunks[1][0]==b"BIN\x00"
    return json.loads(chunks[0][1]),chunks[1][1]

def accessor(data,raw,index,fmt,dims):
    a=data["accessors"][index]
    view=data["bufferViews"][a["bufferView"]]
    start=view.get("byteOffset",0)+a.get("byteOffset",0)
    size=struct.calcsize("<"+fmt*dims)
    stride=view.get("byteStride",size)
    return [struct.unpack_from("<"+fmt*dims,raw,start+i*stride)
            for i in range(a["count"])]

def paint(c):
    r,g,b=c[:3]
    if (r,g,b)==(12,18,24):
        return (127,170,187,255)
    if r<38:
        return (54,70,81,255)
    if r>=92 and g<60:
        return (166,99,65,255)
    return (125+(r-52)*2,146+(g-62)*2,159+(b-70)*2,255)

def refine(blob):
    info,raw=unpack_glb(blob)
    primitive=info["meshes"][0]["primitives"][0]
    attrs=primitive["attributes"]
    positions=[list(v) for v in accessor(info,raw,attrs["POSITION"],"f",3)]
    colors=accessor(info,raw,attrs["COLOR_0"],"B",4)
    indices=[x[0] for x in accessor(info,raw,primitive["indices"],"I",1)]
    assert len(positions)==20955 and len(indices)==39464*3
    faces=[indices[i:i+3] for i in range(0,len(indices),3)]

    # Edge-connected islands. A shared vertex alone is NOT a joined panel.
    parent=list(range(len(faces)))
    rank=[0]*len(faces)
    def root(v):
        while parent[v]!=v:
            parent[v]=parent[parent[v]]
            v=parent[v]
        return v
    def join(a,b):
        a,b=root(a),root(b)
        if a==b: return
        if rank[a]<rank[b]:a,b=b,a
        parent[b]=a
        if rank[a]==rank[b]:rank[a]+=1
    edge_owner={}
    for i,(a,b,c) in enumerate(faces):
        for u,v in ((a,b),(b,c),(c,a)):
            e=(min(u,v),max(u,v))
            if e in edge_owner:join(i,edge_owner[e])
            else:edge_owner[e]=i
    populations=defaultdict(int)
    for i in range(len(faces)):
        populations[root(i)]+=1
    kept=[face for i,face in enumerate(faces) if populations[root(i)]>=MIN_FACES]
    assert 34000<len(kept)<len(faces)

    # Avoid enormous feather prongs and high rear spikes dominating cockpit.
    for p in positions:
        if p[2]<TAIL_START:
            p[2]=TAIL_START+(p[2]-TAIL_START)*.78
            if p[1]>1.8:p[1]=1.8+(p[1]-1.8)*.76
    body,glass=[],[]
    for face in kept:
        (glass if all(tuple(colors[i][:3])==(12,18,24) for i in face)
         else body).append(face)
    assert len(glass)>3500 and len(body)>28000

    # Area-weighted normal smoothing. The upload provided no NORMAL accessor.
    normals=[[0.,0.,0.] for _ in positions]
    for a,b,c in kept:
        ax,ay,az=positions[a]
        ux,uy,uz=(positions[b][0]-ax,positions[b][1]-ay,positions[b][2]-az)
        vx,vy,vz=(positions[c][0]-ax,positions[c][1]-ay,positions[c][2]-az)
        cross=(uy*vz-uz*vy,uz*vx-ux*vz,ux*vy-uy*vx)
        for i in (a,b,c):
            n=normals[i]
            n[0]+=cross[0];n[1]+=cross[1];n[2]+=cross[2]
    for n in normals:
        length=math.sqrt(sum(q*q for q in n))
        n[:]=[q/length for q in n] if length>1e-12 else [0.,1.,0.]
    packed=bytearray()
    views=[]
    accessors=[]
    def append(binary,component,kind,count,minimum=None,maximum=None):
        while len(packed)%4:packed.append(0)
        start=len(packed);packed.extend(binary)
        slot=len(views)
        views.append({"buffer":0,"byteOffset":start,"byteLength":len(binary)})
        acc={"bufferView":slot,"componentType":component,"type":kind,"count":count}
        if minimum is not None:acc.update({"min":minimum,"max":maximum})
        if component==5121:acc["normalized"]=True
        idx=len(accessors);accessors.append(acc)
        return idx
    def index_faces(fs):
        numbers=[i for face in fs for i in face]
        return append(struct.pack("<"+"I"*len(numbers),*numbers),5125,"SCALAR",len(numbers))
    bidx=index_faces(body)
    gidx=index_faces(glass)
    floats=[x for p in positions for x in p]
    minimum=[min(p[i] for p in positions) for i in range(3)]
    maximum=[max(p[i] for p in positions) for i in range(3)]
    posidx=append(struct.pack("<"+"f"*len(floats),*floats),5126,"VEC3",
                  len(positions),minimum,maximum)
    norm=[x for n in normals for x in n]
    nidx=append(struct.pack("<"+"f"*len(norm),*norm),5126,"VEC3",len(normals))
    rgba=[min(255,max(0,int(x))) for c in colors for x in paint(c)]
    cidx=append(bytes(rgba),5121,"VEC4",len(colors))
    info["buffers"]=[{"byteLength":len(packed)}]
    info["bufferViews"]=views
    info["accessors"]=accessors
    info["materials"]=[
      {"name":"Kestrel_Satin_Slate","doubleSided":True,
       "pbrMetallicRoughness":{"baseColorFactor":[1.,1.,1.,1.],
        "metallicFactor":.31,"roughnessFactor":.38}},
      {"name":"Kestrel_Separated_Glazing","doubleSided":True,
       "alphaMode":"BLEND",
       "pbrMetallicRoughness":{"baseColorFactor":[.38,.65,.76,.28],
        "metallicFactor":.05,"roughnessFactor":.19}}
    ]
    info["meshes"][0]["primitives"]=[
       {"attributes":{"POSITION":posidx,"NORMAL":nidx,"COLOR_0":cidx},
        "indices":bidx,"material":0,"mode":4},
       {"attributes":{"POSITION":posidx,"NORMAL":nidx},
        "indices":gidx,"material":1,"mode":4}]
    info["asset"]["generator"]="SceneForge Kestrel supplied-body repair v1"
    raw_json=json.dumps(info,sort_keys=True,separators=(",",":")).encode()
    jsondata=raw_json+b" "*((-len(raw_json))%4)
    bindata=bytes(packed)+b"\0"*((-len(packed))%4)
    total=12+8+len(jsondata)+8+len(bindata)
    result=(struct.pack("<4sII",b"glTF",2,total)+
            struct.pack("<I4s",len(jsondata),b"JSON")+jsondata+
            struct.pack("<I4s",len(bindata),b"BIN\0")+bindata)
    report={"original_triangles":len(faces),"triangles":len(kept),
            "body_triangles":len(body),"glass_triangles":len(glass),
            "discarded_fragments":len(faces)-len(kept),
            "source_islands":len(populations),
            "rear_tip_z":minimum[2],
            "smooth_vertex_normals":True,
            "transparent_glass_surface":True,
            "source_model_retained":True}
    return result,report
