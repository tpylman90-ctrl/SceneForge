"""Second, non-destructive surface-control pass for the user-supplied Kestrel.

Takes the previous 2-surface refined standard glTF GLB. Repairs major panel
regularity and reduces detached aggressive tail feathers without altering its
primitive layout, material slots, named node, cockpit hooks or animation rig.
Uses only Python's standard library for reproducible free GitHub CI builds.
"""
from __future__ import annotations
from collections import defaultdict
import json
import math
import struct

FRONT_TIP_START=2.72
REAR_FEATHER_START=-2.05


def glb_chunks(blob):
    assert blob[:4]==b'glTF' and struct.unpack_from('<II',blob,4)==(2,len(blob))
    cursor=12
    chunks=[]
    while cursor<len(blob):
        count,kind=struct.unpack_from('<I4s',blob,cursor);cursor+=8
        chunks.append((kind,blob[cursor:cursor+count]));cursor+=count
    assert len(chunks)==2 and chunks[0][0]==b'JSON' and chunks[1][0]==b'BIN\0'
    return json.loads(chunks[0][1]),bytearray(chunks[1][1])


def values(info,data,index,fmt,width):
    acc=info['accessors'][index];view=info['bufferViews'][acc['bufferView']]
    start=view.get('byteOffset',0)+acc.get('byteOffset',0)
    step=view.get('byteStride',struct.calcsize('<'+fmt*width))
    return [list(struct.unpack_from('<'+fmt*width,data,start+j*step))
            for j in range(acc['count'])]


def put_values(info,data,index,fmt,width,records):
    acc=info['accessors'][index];view=info['bufferViews'][acc['bufferView']]
    assert acc['count']==len(records)
    start=view.get('byteOffset',0)+acc.get('byteOffset',0)
    step=view.get('byteStride',struct.calcsize('<'+fmt*width))
    for j,rec in enumerate(records):
        struct.pack_into('<'+fmt*width,data,start+j*step,*rec)


def polish(glb):
    info,binary=glb_chunks(glb)
    mesh=info['meshes'][0]
    parts=mesh['primitives']
    assert len(parts)==2, 'Expected already-separated original body/glass'
    attrs=parts[0]['attributes']
    assert attrs['POSITION']==parts[1]['attributes']['POSITION']
    assert 'NORMAL' in attrs
    positions=values(info,binary,attrs['POSITION'],'f',3)
    colors=values(info,binary,attrs['COLOR_0'],'B',4)
    original_bounds=[[min(p[i] for p in positions),max(p[i] for p in positions)]
                     for i in range(3)]
    all_faces=[]
    body_faces=[]
    glass_vertices=set()
    for k,primitive in enumerate(parts):
        idx=[r[0] for r in values(info,binary,primitive['indices'],'I',1)]
        faces=[idx[i:i+3] for i in range(0,len(idx),3)]
        all_faces.extend(faces)
        if k==0: body_faces=faces
        else:glass_vertices.update(idx)
    assert len(all_faces)==39119 and len(positions)==20955

    # Preserve user-authored panel boundaries. Only smooth interior vertices
    # with robust manifold neighbourhoods; no edge creases, canopy or tiny
    # detached trim receive unconditional smoothing.
    neighbours=defaultdict(set)
    edge_faces=defaultdict(int)
    vertex_faces=defaultdict(int)
    for a,b,c in body_faces:
        for v in (a,b,c):vertex_faces[v]+=1
        for u,v in ((a,b),(b,c),(c,a)):
            neighbours[u].add(v);neighbours[v].add(u)
            edge_faces[(u,v) if u<v else (v,u)]+=1
    boundaries=set()
    for (a,b),count in edge_faces.items():
        if count!=2:
            boundaries.add(a);boundaries.add(b)
    smoothed=0
    maximum_delta=0.
    for iteration in range(3):
        replacements={}
        for i,near in neighbours.items():
            x,y,z=positions[i]
            if i in glass_vertices or i in boundaries or len(near)<4:
                continue
            if not (-2.12<z<2.77 and .42<y<1.89):
                continue
            if vertex_faces[i]<5 or vertex_faces[i]>16:
                continue
            # Refuse to bridge large gaps: only fair genuinely close,
            # connected control vertices on existing body patches.
            distances=[math.dist(positions[i],positions[j]) for j in near]
            if not distances or max(distances)>.23:
                continue
            average=[sum(positions[j][axis] for j in near)/len(near) for axis in range(3)]
            displacement=[(average[axis]-positions[i][axis])*.16 for axis in range(3)]
            distance=math.sqrt(sum(q*q for q in displacement))
            if distance>.018:
                displacement=[q*.018/distance for q in displacement]
                distance=.018
            if distance<.00007:continue
            replacements[i]=[positions[i][axis]+displacement[axis] for axis in range(3)]
            maximum_delta=max(maximum_delta,distance)
        for i,new in replacements.items():positions[i]=new
        smoothed+=len(replacements)

    # Retain high-grade raptor silhouette but calm the oversized, overly
    # upward-pointing rear feather forms. Full-width main rear shell and
    # powertrain below y=1.45 are not affected by this localized deformation.
    feather_vertices=0
    for i,(x,y,z) in enumerate(positions):
        if z<REAR_FEATHER_START and y>1.44 and abs(x)>.68:
            fade=min(1.,(REAR_FEATHER_START-z)/.72)
            ease=fade*fade*(3.-2.*fade)
            pos=positions[i]
            pos[2]=z+.42*ease
            pos[1]=y-.26*ease
            pos[0]=x*(1.-.09*ease)
            feather_vertices+=1
        elif z>FRONT_TIP_START and y<1.36 and abs(x)<1.25:
            t=min(1.,(z-FRONT_TIP_START)/.7)
            positions[i][2]=z-.09*t*t

    # Keep accents recognizable, but use engineered copper/rust inserts
    # rather than orange spikes brighter than the rest of the vehicle.
    recolored=0
    for i,(r,g,b,a) in enumerate(colors):
        x,y,z=positions[i]
        if z<-1.8 and y>1.42 and (r>g*1.24) and (r>b*1.28):
            colors[i]=[min(255,round(.72*r+.28*92)),
                       min(255,round(.74*g+.26*96)),
                       min(255,round(.71*b+.29*103)),a]
            recolored+=1

    # Recompute area-weighted vertex normals after deformation. The glass
    # shares the original vertex register but not the opaque material surface.
    normals=[[0.,0.,0.] for _ in positions]
    for a,b,c in all_faces:
        ax,ay,az=positions[a]
        ux,uy,uz=(positions[b][0]-ax,positions[b][1]-ay,positions[b][2]-az)
        vx,vy,vz=(positions[c][0]-ax,positions[c][1]-ay,positions[c][2]-az)
        nx=uy*vz-uz*vy;ny=uz*vx-ux*vz;nz=ux*vy-uy*vx
        for i in (a,b,c):
            normal=normals[i]
            normal[0]+=nx;normal[1]+=ny;normal[2]+=nz
    for normal in normals:
        size=math.sqrt(sum(x*x for x in normal))
        if size>1e-10:normal[:]=[v/size for v in normal]
        else:normal[:]=[0.,1.,0.]
    put_values(info,binary,attrs['POSITION'],'f',3,positions)
    put_values(info,binary,attrs['NORMAL'],'f',3,normals)
    put_values(info,binary,attrs['COLOR_0'],'B',4,colors)
    extent=info['accessors'][attrs['POSITION']]
    extent['min']=[min(p[i] for p in positions) for i in range(3)]
    extent['max']=[max(p[i] for p in positions) for i in range(3)]
    # Material slots/nodes remain unchanged; importer overrides are owned
    # by SceneForge runtime. Dark canopy looks especially flat under the
    # existing GL Compatibility garage, so slightly reduce the glass alpha.
    material=info['materials'][1]['pbrMetallicRoughness']
    material['baseColorFactor']=[.40,.68,.80,.23]
    material['metallicFactor']=.04
    material['roughnessFactor']=.24
    info['asset']['generator']='SceneForge original Kestrel surface-continuity repair S02'
    info.setdefault('extras',{})['sceneforge_surface_pass']='S02'
    payload=json.dumps(info,separators=(',',':'),sort_keys=True).encode('utf-8')
    padded=payload+b' '*((-len(payload))%4)
    binary+=b'\0'*((-len(binary))%4)
    total=12+8+len(padded)+8+len(binary)
    output=(struct.pack('<4sII',b'glTF',2,total)+
            struct.pack('<I4s',len(padded),b'JSON')+padded+
            struct.pack('<I4s',len(binary),b'BIN\0')+binary)
    report={'triangles':len(all_faces),'vertices':len(positions),
            'interior_surface_iterations':smoothed,
            'max_smoothing_step_m':round(maximum_delta,6),
            'rear_feather_vertices_adjusted':feather_vertices,
            'rear_accent_vertices_toned':recolored,
            'min_z_before':original_bounds[2][0],
            'min_z_after':extent['min'][2],
            'new_model_extents':[[round(a,3),round(b,3)] for a,b in zip(extent['min'],extent['max'])],
            'two_original_material_surfaces_preserved':True}
    assert len(output)>600000
    assert report['triangles']==39119
    assert feather_vertices>50
    assert recolored>50
    return output,report

if __name__=='__main__':
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser()
    parser.add_argument('source',type=Path)
    parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    final,report=polish(args.source.read_bytes())
    args.destination.parent.mkdir(parents=True,exist_ok=True)
    args.destination.write_bytes(final)
    print('SCENEFORGE_KESTREL_S02_SURFACE_PASS_OK',report)
