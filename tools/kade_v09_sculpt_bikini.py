"""Kade V09: anatomical detail polish and separate fitted bikini geometry.

Requires the SceneForge MakeHuman V08 body mesh already in Blender.
Preserves approved body silhouette and makes independent, riggable garment parts.
All coordinates are in Blender: X=left/right, Y=front (-), Z=up.
"""
import bpy
import math
from mathutils import Vector

def refine_and_dress_kade(body, make_material, identity_parts):
    body.data.update()
    points=[p.co.copy() for p in body.data.vertices]
    normals=[v.normal.copy() for v in body.data.vertices]
    maximum=0.0
    # The V04 body silhouette is approved. Surface detailing < 5mm total.
    def detail(x, z, y, sx, sz, sy, magnitude, front=False):
        nonlocal maximum
        for i,v in enumerate(body.data.vertices):
            diff=v.co-Vector((x,y,z))
            dist=(diff.x/sx)**2+(diff.z/sz)**2+(diff.y/sy)**2
            if dist>22:continue
            w=math.exp(-.5*dist)
            if front:w*=max(0,min(1,(normals[i].y*(-1)+.22)/.75))
            delta=normals[i]*(magnitude*w)
            v.co+=delta
            maximum=max(maximum,(v.co-points[i]).length)
    for sign in (-1,1):
        detail(sign*.043,1.525,-.025,.026,.018,.026,.00175,True)
        detail(sign*.036,1.594,-.018,.027,.009,.022,.001,True)
        detail(sign*.045,1.555,-.012,.023,.009,.025,-.00055,True)
        detail(sign*.037,1.498,-.042,.021,.007,.024,.00045,True)
    for z,y,amp,sx,sz,sy in [
      (1.512,-.044,.00165,.018,.006,.025),
      (1.505,-.044,.0012,.022,.006,.024),
      (1.532,-.045,.00065,.008,.012,.024),
      (1.085,-.053,-.002,.012,.018,.030)]:
        detail(0,z,y,sx,sz,sy,amp,True)
    for sign in (-1,1):
        detail(sign*.084,1.368,.025,.042,.008,.04,.0012,True)
        detail(sign*.070,1.125,-.047,.038,.058,.028,.0007,True)
        detail(sign*.095,.555,-.050,.035,.025,.042,.00085)
        detail(sign*.118,.745,.080,.035,.055,.065,.0010)
        detail(sign*.045,.92,.194,.050,.040,.028,.00055)
        detail(sign*.043,.31,.04,.035,.055,.030,.0008)
    body.data.update()
    assert maximum<.009, maximum

    fabric=make_material("Kade_V09_Matte_Black_Fabric",(.025,.022,.030),.82,0)
    binding=make_material("Kade_V09_Black_Binding",(.018,.017,.021),.9,0)
    orange=make_material("Kade_V09_Orange_Trim",(.86,.20,.025),.46,.05)

    garments=[]
    hit_count=[0,0]
    def cast(x,z,front=True):
        start=Vector((x,-.52 if front else .52,z))
        direction=Vector((0,1 if front else -1,0))
        yes,hit,norm,index=body.ray_cast(start,direction,distance=1.1)
        if yes:
            hit_count[0]+=1
            return hit+norm*.0038
        hit_count[1]+=1
        # Boundary fallback: use closest vertex near the requested X/Z pair.
        cand=min(body.data.vertices,key=lambda v:(v.co.x-x)**2+(v.co.z-z)**2)
        return cand.co+cand.normal*.005

    def mesh(name,vertices,faces,material):
        data=bpy.data.meshes.new(name+"_Topology")
        data.from_pydata(vertices,[],faces)
        data.update()
        ob=bpy.data.objects.new(name,data)
        bpy.context.collection.objects.link(ob)
        ob.data.materials.append(material)
        for p in data.polygons:p.use_smooth=True
        garments.append(ob)
        return ob

    def fitted_triangle(name,corners,front=True,n=22):
        corner=[Vector(p) for p in corners] # XY here is horizontal x and vertical z
        verts=[];mapping={}
        for j in range(n+1):
            for i in range(n+1-j):
                t=i/n;u=j/n
                p=corner[0]*(1-t-u)+corner[1]*t+corner[2]*u
                mapping[(i,j)]=len(verts)
                verts.append(cast(p.x,p.y,front))
        faces=[]
        for j in range(n):
            for i in range(n-j):
                a=mapping[(i,j)];b=mapping[(i+1,j)];c=mapping[(i,j+1)]
                faces.append((a,b,c))
                if i+j<n-1:faces.append((b,mapping[(i+1,j+1)],c))
        nv=len(verts)
        # 1.8mm woven fabric thickness, with a closed hem and reverse face.
        inside=[p+Vector((0,.0018 if front else -.0018,0)) for p in verts]
        faces.extend([(c+nv,b+nv,a+nv) for a,b,c in list(faces)])
        outline=[]
        for i in range(n):outline.append((mapping[(i,0)],mapping[(i+1,0)]))
        for i in range(n):outline.append((mapping[(n-i,i)],mapping[(n-i-1,i+1)]))
        for j in range(n):outline.append((mapping[(0,n-j)],mapping[(0,n-j-1)]))
        for a,b in outline:faces.extend([(a,b,b+nv),(a,b+nv,a+nv)])
        return mesh(name,verts+inside,faces,fabric)

    def cord(name,coords,radius,material):
        data=bpy.data.curves.new(name+"_Path","CURVE")
        data.dimensions="3D"; data.resolution_u=8
        data.bevel_depth=radius;data.bevel_resolution=2;data.use_fill_caps=True
        path=data.splines.new("POLY")
        path.points.add(len(coords)-1)
        for i,p in enumerate(coords):path.points[i].co=(*p,1)
        ob=bpy.data.objects.new(name,data)
        bpy.context.collection.objects.link(ob)
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active=ob
        bpy.ops.object.convert(target="MESH")
        ob=bpy.context.object
        ob.name=name
        ob.data.materials.append(material)
        garments.append(ob)
        return ob

    def edge(name,corners,front=True,radius=.002):
        path=[]
        for a,b in ((corners[0],corners[1]),(corners[1],corners[2]),(corners[2],corners[0])):
            for i in range(20):
                t=i/20
                x=a[0]*(1-t)+b[0]*t
                z=a[1]*(1-t)+b[1]*t
                path.append(cast(x,z,front))
        path.append(path[0])
        return cord(name,path,radius,orange)

    for sign,name in ((-1,"L"),(1,"R")):
        corners=[(sign*.015,1.165),(sign*.148,1.166),(sign*.076,1.341)]
        fitted_triangle("Kade_V09_Cup_"+name,corners,True)
        edge("Kade_V09_Cup_OrangePiping_"+name,corners)
        neck=[(sign*.076,1.341),(sign*.067,1.368),(sign*.047,1.39),(sign*.026,1.426)]
        cord("Kade_V09_Halter_"+name,[cast(x,z) for x,z in neck],.0036,binding)
        outer=[cast(sign*.145,1.17),Vector((sign*.17,.022,1.165)),cast(sign*.118,1.17,False)]
        cord("Kade_V09_BackTie_"+name,outer,.003,binding)

    front=[(-.119,1.022),(.119,1.022),(0,.807)]
    back=[(-.027,1.020),(.027,1.020),(0,.807)]
    fitted_triangle("Kade_V09_Thong_Bottom_Front",front,True,28)
    edge("Kade_V09_Bottom_Front_Trim",front,True,.0018)
    fitted_triangle("Kade_V09_Thong_Bottom_Back",back,False,28)
    edge("Kade_V09_Bottom_Back_Trim",back,False,.0017)

    # Fit both waist cords using the anatomical waist circumference.
    # Ray starts inside the torso at z 1.02 and tracks surface around hips.
    waist=[]
    for i in range(97):
        ang=2*math.pi*i/96
        origin=Vector((0,.045,1.020))
        direction=Vector((math.cos(ang),math.sin(ang),0))
        yes,loc,norm,_=body.ray_cast(origin,direction,distance=.33)
        if yes:
            waist.append(loc+norm*.0045)
        else:
            waist.append(Vector((math.cos(ang)*.15,math.sin(ang)*.11+.04,1.020)))
    cord("Kade_V09_Waist_String",waist,.0033,binding)
    cord("Kade_V09_Waist_Orange_Accent",
         [p+Vector((0,0,.004)) for p in waist],.00135,orange)

    # Move actual existing goggle mesh elements down into hair; no floaters.
    for ob in identity_parts:
        if ob.name.startswith("Kade_Goggle_"):
            ob.location.z-=.014
            ob.location.y+=.009
        if ob.name.startswith("Kade_Lip_Refinement_1508"):
            ob.location.y-=.045
    assert len(garments)>=14
    assert hit_count[0]>hit_count[1]*10,hit_count
    print("KADE_V09_BODY_SCULPT_MM",maximum*1000,flush=True)
    print("KADE_V09_FITTED_GARMENTS",len(garments),"SURFACE_SAMPLES",hit_count,flush=True)
    return garments
