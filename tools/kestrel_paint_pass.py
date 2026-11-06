"""Kestrel S03 material assignment, preserving uploaded original topology.

Runs after S02 body fairing. Uses the original authored vertex-color regions
to separate stormsteel body paint, matte graphite carbon trim, forged copper
highlights and smoked cyan glazing into four genuine GLB PBR surfaces. No
new geometry, placeholder images, paid model service or Blender dependency.
"""
from __future__ import annotations

from collections import Counter
import json
import struct

PALETTE={
    "paint":(74,109,148),    # Stormsteel blue-slate pearl
    "carbon":(32,45,57),     # Blue-black graphite
    "copper":(171,90,51),    # Restrained warm metallic copper
}

def unpack(blob):
    assert blob[:4]==b"glTF" and struct.unpack_from("<II",blob,4)==(2,len(blob))
    n,kind=struct.unpack_from("<I4s",blob,12)
    assert kind==b"JSON"
    data=json.loads(blob[20:20+n])
    pos=20+n
    size,kind=struct.unpack_from("<I4s",blob,pos)
    assert kind==b"BIN\0"
    binary=bytearray(blob[pos+8:pos+8+size])
    return data,binary

def values(info,data,index,fmt,component_count):
    acc=info["accessors"][index]
    view=info["bufferViews"][acc["bufferView"]]
    start=view.get("byteOffset",0)+acc.get("byteOffset",0)
    stride=view.get("byteStride",struct.calcsize("<"+fmt*component_count))
    return [list(struct.unpack_from("<"+fmt*component_count,data,
            start+i*stride)) for i in range(acc["count"])]

def write_values(info,data,index,fmt,component_count,items):
    acc=info["accessors"][index]
    view=info["bufferViews"][acc["bufferView"]]
    start=view.get("byteOffset",0)+acc.get("byteOffset",0)
    stride=view.get("byteStride",struct.calcsize("<"+fmt*component_count))
    assert acc["count"]==len(items)
    for i,item in enumerate(items):
        struct.pack_into("<"+fmt*component_count,data,start+i*stride,*item)

def region(c):
    r,g,b=c[:3]
    if r<90:
        return "carbon"
    if r>g*1.24 and r>b*1.28:
        return "copper"
    return "paint"

def paint(glb):
    info,binary=unpack(glb)
    assert len(info["meshes"])==1
    prims=info["meshes"][0]["primitives"]
    assert len(prims)==2,"Kestrel S02 body + canopy must remain intact"
    body,glass=prims
    attr=body["attributes"]
    assert "NORMAL" in attr and "COLOR_0" in attr
    colors=values(info,binary,attr["COLOR_0"],"B",4)
    indices=values(info,binary,body["indices"],"I",1)
    assert len(colors)==20955 and len(indices)==34680*3
    groups=[region(c) for c in colors]
    # Recolour the real mesh vertices, not decals. Original copper, graphite
    # and slate tags define spatial paint placement and keep existing seams.
    for i,(r,g,b,a) in enumerate(colors):
        kind=groups[i]
        base=PALETTE[kind]
        delta=(max(-5,min(5,int((r-127)*.7))) if kind=="paint" else
               max(-4,min(4,int((g-70)*.25))) if kind=="carbon" else
               max(-6,min(6,int((r-145)*.23))))
        colors[i]=[max(0,min(255,v+delta)) for v in base]+[255]
    write_values(info,binary,attr["COLOR_0"],"B",4,colors)

    regions={key:[] for key in ("paint","carbon","copper")}
    for k in range(0,len(indices),3):
        triangle=[x[0] for x in indices[k:k+3]]
        # 95% of the supplied triangles share a single original paint
        # label. Majority assignment preserves islands and triangle count.
        key=Counter(groups[i] for i in triangle).most_common(1)[0][0]
        regions[key].extend(triangle)
    assert sum(len(x) for x in regions.values())==len(indices)
    assert all(len(x)>6000 for x in regions.values())

    surfaces=[]
    for mat,name in enumerate(("paint","carbon","copper")):
        triangles=regions[name]
        while len(binary)%4:binary.append(0)
        start=len(binary)
        binary.extend(struct.pack("<"+"I"*len(triangles),*triangles))
        view=len(info["bufferViews"])
        info["bufferViews"].append({
            "buffer":0,"byteOffset":start,"byteLength":len(triangles)*4})
        index=len(info["accessors"])
        info["accessors"].append({
            "bufferView":view,"componentType":5125,
            "count":len(triangles),"type":"SCALAR"})
        surfaces.append({"attributes":attr.copy(),
                         "indices":index,"material":mat,"mode":4})
    surfaces.append({**glass,"material":3})
    info["materials"]=[
      {"name":"Kestrel_S03_Stormsteel_Pearl",
       "doubleSided":True,"pbrMetallicRoughness":{
       "baseColorFactor":[1,1,1,1],"metallicFactor":.59,
       "roughnessFactor":.255}},
      {"name":"Kestrel_S03_Graphite_Carbon",
       "doubleSided":True,"pbrMetallicRoughness":{
       "baseColorFactor":[1,1,1,1],"metallicFactor":.22,
       "roughnessFactor":.56}},
      {"name":"Kestrel_S03_Burnished_Copper",
       "doubleSided":True,"pbrMetallicRoughness":{
       "baseColorFactor":[1,1,1,1],"metallicFactor":.66,
       "roughnessFactor":.32}},
      {"name":"Kestrel_S03_Smoked_Cyan_Glass",
       "doubleSided":True,"alphaMode":"BLEND",
       "pbrMetallicRoughness":{
       "baseColorFactor":[.26,.55,.64,.25],"metallicFactor":.05,
       "roughnessFactor":.18}}
    ]
    info["meshes"][0]["primitives"]=surfaces
    info["asset"]["generator"]="SceneForge Kestrel authored-material study S03"
    info.setdefault("extras",{})["sceneforge_paint"]="Stormsteel, graphite, burnished copper"
    info["buffers"][0]["byteLength"]=len(binary)
    js=json.dumps(info,separators=(",",":"),sort_keys=True).encode("utf-8")
    js+=b" "*((-len(js))%4)
    binary+=b"\0"*((-len(binary))%4)
    length=12+8+len(js)+8+len(binary)
    output=(struct.pack("<4sII",b"glTF",2,length)
            +struct.pack("<I4s",len(js),b"JSON")+js
            +struct.pack("<I4s",len(binary),b"BIN\0")+binary)
    summary={name:len(part)//3 for name,part in regions.items()}
    summary["glass"]=info["accessors"][glass["indices"]]["count"]//3
    summary["total_triangles"]=sum(summary.values())
    summary["surfaces"]=len(surfaces)
    assert summary["total_triangles"]==39119
    assert summary["surfaces"]==4 and summary["glass"]>4000
    return output,summary
