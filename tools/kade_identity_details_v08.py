"""Kade v08: authored game-geometry face and hair detailing on her V04 anatomical body.
All details are actual mesh data exported to GLB, not an image or billboard.
Local Blender coordinates: X across body, Y negative toward front, Z up.
Body proportions are untouched; visual feature layers remain separate meshes.
"""
import bpy
import math
import random
from mathutils import Vector

def build_kade_identity(body, make_material):
    rand = random.Random(591521)
    items = []
    def mat(name, rgb, rough=.65, metallic=0):
        return make_material(name, rgb, rough, metallic)
    espresso = mat("Kade_Hair_Espresso", (.035,.015,.026),.47)
    deep = mat("Kade_Hair_BlackCherry", (.065,.018,.039),.43)
    aubergine = mat("Kade_Hair_VioletBrown", (.11,.026,.065),.41)
    hotpink = mat("Kade_Hair_Electric_Magenta", (.61,.012,.21),.40)
    pinkdim = mat("Kade_Hair_Magenta_Shadow", (.30,.012,.11),.47)
    lip = mat("Kade_Natural_Rose_Lips", (.38,.14,.12),.49)
    eyebrow = mat("Kade_Eyebrows_Espresso", (.032,.012,.020),.73)
    freckle = mat("Kade_Skin_Freckles_Cinnamon", (.31,.135,.095),.80)
    softfreckle = mat("Kade_Skin_Freckles_Soft", (.39,.20,.14),.84)
    sclera = mat("Kade_Eyes_Warm_White", (.79,.73,.65),.22)
    iris = mat("Kade_Eyes_AmberBrown", (.19,.068,.027),.27)
    irislite = mat("Kade_Eyes_Iris_Rays", (.47,.24,.080),.27)
    pupil = mat("Kade_Eyes_Pupil", (.014,.008,.01),.12)
    glint = mat("Kade_Eye_Catchlight", (.98,.88,.69),.12)
    charcoal = mat("Kade_Goggles_BlackRubber", (.025,.028,.035),.66)
    rim = mat("Kade_Goggles_Gunmetal", (.16,.18,.21),.28,.77)
    orange = mat("Kade_Goggles_Amber_Lens", (.91,.32,.025),.17,.32)
    gold = mat("Kade_Hoop_Jewelry_Brass", (.70,.38,.11),.28,.8)
    shave = mat("Kade_Undercut_Shaved_Scalp", (.025,.016,.018),.88)
    scalpstripe = mat("Kade_Undercut_Trim_Stripes", (.20,.10,.075),.78)

    def keep(o):
        items.append(o)
        return o
    def uv(name,loc,scale,material,seg=16,rings=8):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc)
        ob=bpy.context.object
        ob.name=name
        ob.scale=scale
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        ob.data.materials.append(material)
        for p in ob.data.polygons:p.use_smooth=True
        return keep(ob)
    def poly_curves(name,paths,material,bevel=.003,res=2):
        data=bpy.data.curves.new(name,"CURVE")
        data.dimensions="3D"
        data.resolution_u=12
        data.bevel_depth=bevel
        data.bevel_resolution=res
        data.use_fill_caps=True
        for path in paths:
            sp=data.splines.new("POLY")
            sp.points.add(len(path)-1)
            for po,(pt,rad) in zip(sp.points,path):
                po.co=(*pt,1.0)
                po.radius=rad
        ob=bpy.data.objects.new(name,data)
        bpy.context.collection.objects.link(ob)
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active=ob
        bpy.ops.object.convert(target="MESH")
        ob=bpy.context.object
        ob.name=name
        ob.data.materials.append(material)
        for p in ob.data.polygons:p.use_smooth=True
        return keep(ob)
    def ray_front(x,z):
        # Find anatomical surface for freckles, brows, liner and tiny scar.
        hit,loc,norm,idx=body.ray_cast(Vector((x,-.35,z)),Vector((0,1,0)),distance=.7)
        if not hit:return None
        return loc,norm
    def ray_side(y,z):
        hit,loc,norm,idx=body.ray_cast(Vector((.30,y,z)),Vector((-1,0,0)),distance=.6)
        if not hit:return None
        return loc,norm

    # V08 HAIR: scalp follows existing head topology. No artificial spherical
    # cap, tube wig, or floating hemispheres. The V04 body stays untouched.
    m=body.data
    surface_faces=[]; vertex_map={}
    for poly in m.polygons:
        c=poly.center
        if c.z<1.615 or (c.x>.052 and c.z<1.664):
            continue
        # Hairline is tapered high over the forehead and open over the
        # asymmetrical shaved right temple.
        if c.y<-.080 and c.z<1.645:
            continue
        loop=[]
        for idx in poly.vertices:
            if idx not in vertex_map:vertex_map[idx]=len(vertex_map)
            loop.append(vertex_map[idx])
        surface_faces.append(loop)
    if len(surface_faces)<50:
        raise RuntimeError("No valid topology-following scalp, check MakeHuman vertex positions")
    verts=[None]*len(vertex_map)
    for idx,newid in vertex_map.items():
        v=m.vertices[idx]
        verts[newid]=tuple(v.co+v.normal*.0010)
    scalp_mesh=bpy.data.meshes.new("Kade_HeadFollowed_Scalp")
    scalp_mesh.from_pydata(verts,[],surface_faces)
    scalp_mesh.update()
    scalp=keep(bpy.data.objects.new("Kade_Scalp_Conforming",scalp_mesh))
    bpy.context.collection.objects.link(scalp)
    scalp.data.materials.append(espresso)
    for p in scalp.data.polygons:p.use_smooth=True

    # Build sculpted, tapered ribbon-like locks with elliptical sections.
    # Curvature is engineered directly into mesh rings (real 3D geometry,
    # not a strand simulation or a noisy forest of wire curves).
    hair_palette=(espresso,deep,aubergine,hotpink,pinkdim)
    bundles=[{"verts":[],"faces":[]} for _ in hair_palette]
    def sculpt_lock(c0,c1,radius,depth,shade,turns,phase,wave):
        bundle=bundles[shade]
        nv=22; ns=8
        origin=len(bundle["verts"])
        start=Vector(c0); end=Vector(c1)
        baseline=end-start
        # lateral wave suppressed at scalp root, strengthened in free locks.
        def center(t):
            tt=t*t*(3.-2.*t)
            p=start.lerp(end,tt)
            p.x+=wave*math.sin(2*math.pi*turns*t+phase)*math.sin(math.pi*t/2)
            p.y+=wave*.70*math.cos(2*math.pi*turns*t+phase)*math.sin(math.pi*t/2)
            p.z+=.013*math.sin(math.pi*t)
            return p
        for i in range(nv):
            t=i/(nv-1)
            cp=center(t)
            tangent=(center(min(1,t+.005))-center(max(0,t-.005))).normalized()
            side=tangent.cross(Vector((0,1,0)))
            if side.length<.1:side=tangent.cross(Vector((1,0,0)))
            side.normalize()
            normal=tangent.cross(side).normalized()
            # flattened sculpted curl, thick core, slender tapered ends
            taper=(1.-t)**.47
            taper*=min(1.,(t+.055)/.14)
            wr=radius*max(.09,taper)
            dr=depth*max(.13,taper)
            for j in range(ns):
                ang=2*math.pi*j/ns
                v=cp+side*(math.cos(ang)*wr)+normal*(math.sin(ang)*dr)
                bundle["verts"].append(tuple(v))
        for i in range(nv-1):
            for j in range(ns):
                a=origin+i*ns+j; b=origin+i*ns+(j+1)%ns
                c=origin+(i+1)*ns+(j+1)%ns;d=origin+(i+1)*ns+j
                bundle["faces"].append((a,b,c,d))
        bundle["faces"].append(tuple(origin+j for j in reversed(range(ns))))
        bundle["faces"].append(tuple(origin+(nv-1)*ns+j for j in range(ns)))

    # 34 interlocking curls sweep from crown toward character's left cheek.
    # The entire right temple stays visible, per approved model sheet.
    for i in range(34):
        x=rand.uniform(-.074,-.017)
        start=(x,rand.uniform(-.046,.015),rand.uniform(1.641,1.683))
        end=(rand.uniform(-.160,-.096),
             rand.uniform(-.079,-.011),rand.uniform(1.365,1.490))
        shade=3 if i%5==0 else (4 if i%9==0 else i%3)
        sculpt_lock(start,end,rand.uniform(.009,.017),rand.uniform(.004,.008),
                    shade,rand.uniform(1.9,3.1),rand.uniform(0,6.28),rand.uniform(.007,.018))
    # 39 locks on the ponytail over rear collar. Roots anchored on back
    # crown, with broader overlaps so negative space looks intentional.
    for i in range(39):
        start=(rand.uniform(-.045,.055),rand.uniform(.045,.087),
               rand.uniform(1.632,1.678))
        end=(rand.uniform(-.108,.094),rand.uniform(.101,.155),
             rand.uniform(1.335,1.476))
        shade=3 if i%5==0 else (4 if i%11==0 else (i+1)%3)
        sculpt_lock(start,end,rand.uniform(.010,.018),rand.uniform(.0045,.0085),
                    shade,rand.uniform(1.8,2.8),rand.uniform(0,6.28),rand.uniform(.008,.017))
    # Layered swoop across the crown; shorter locks close the gaps but do
    # not form an inflated beanie or obscure Kade's asymmetric undercut.
    for i in range(24):
        start=(rand.uniform(-.065,.032),rand.uniform(-.065,.014),
               rand.uniform(1.662,1.686))
        end=(rand.uniform(-.097,.025),rand.uniform(-.067,.092),
             rand.uniform(1.601,1.667))
        sculpt_lock(start,end,rand.uniform(.010,.018),rand.uniform(.004,.008),
                    3 if i%7==0 else i%3,1.15,rand.uniform(0,6.28),.004)
    for idx,content in enumerate(bundles):
        if not content["faces"]:continue
        hairmesh=bpy.data.meshes.new("Kade_Sculpted_Curl_Mesh_%d"%idx)
        hairmesh.from_pydata(content["verts"],[],content["faces"])
        hairmesh.update()
        ob=keep(bpy.data.objects.new("Kade_Hair_Clumps_%02d"%idx,hairmesh))
        bpy.context.collection.objects.link(ob)
        ob.data.materials.append(hair_palette[idx])
        for poly in hairmesh.polygons:poly.use_smooth=True
    print("KADE_V08_HAIR_CLUMPS",97,flush=True)

    # Three distinctive shaved stripe tracks on the character's right side.
    stripepaths=[]
    for i in range(3):
        pts=[]
        for j in range(20):
            t=j/19
            yy=-.066 + .075*t
            zz=1.576 + .013*i - .011*t
            h=ray_side(yy,zz)
            if h:
                pt,n=h
                pts.append(((pt+Vector((.0030,0,0)))[:],1))
        if len(pts)>=6:stripepaths.append(pts)
    if stripepaths:poly_curves("Kade_Shaved_Geometric_Triple_Bars",stripepaths,scalpstripe,bevel=.00165,res=2)

    # Eyes are layered spheres and irises at her anatomical eye sockets,
    # with separate translucent-looking colored features (opaque GLB PBR).
    for sign in (-1,1):
        ex=sign*.034
        ez=1.566
        h=ray_front(ex,ez)
        if not h:
            print("KADE_V08_EYE_SURFACE_MISSING",sign,flush=True)
            continue
        eye_pt,eye_normal=h
        # Eyes are almond-shaped surface details, not protruding eyeballs.
        ey=eye_pt.y-.0006
        print("KADE_V08_EYE_SURFACE",sign,round(ey,4),flush=True)
        uv("Kade_Eye_%s_Sclera"%sign,(ex,ey,ez),(.0114,.0010,.0048),sclera,20,12)
        uv("Kade_Eye_%s_Iris"%sign,(ex,ey-.0011,ez),(.0043,.0007,.0042),iris,24,12)
        uv("Kade_Eye_%s_AmberInner"%sign,(ex,ey-.0017,ez),(.0033,.0005,.0034),irislite,18,10)
        uv("Kade_Eye_%s_Pupil"%sign,(ex,ey-.0022,ez),(.0017,.0004,.0025),pupil,20,10)
        uv("Kade_Eye_%s_Glint"%sign,(ex-sign*.0012,ey-.0025,ez+.0015),(.0009,.00025,.0010),glint,12,8)

    def surface_line(name,sign,raw,material,thickness):
        pts=[]
        for x,z in raw:
            h=ray_front(sign*x,z)
            if not h:continue
            loc,n=h
            pts.append((tuple(loc+n*.0015),.9))
        if len(pts)>2:
            poly_curves(name,[pts],material,bevel=thickness,res=2)
    for sign in (-1,1):
        surface_line("Kade_Eyebrow_%s"%sign,sign,[
            (.017,1.578),(.028,1.582),(.039,1.585),(.050,1.586),(.064,1.580)
        ],eyebrow,.0027)
        surface_line("Kade_Eyeliner_%s"%sign,sign,[
            (.019,1.565),(.028,1.568),(.038,1.569),(.049,1.567),(.060,1.561)
        ],espresso,.0011)

    # Natural facial beauty detail: procedural surface-mounted freckles.
    # Mesh dots (not fake texture maps), so both viewer and Godot show them.
    for side in (-1,1):
        for i in range(42):
            xx=side*rand.uniform(.020,.066)
            zz=rand.uniform(1.514,1.550)
            hit=ray_front(xx,zz)
            if not hit:continue
            point,normal=hit
            # Keep the front-most face intersection; V05 incorrectly culled it.
            rad=rand.uniform(.00037,.00115)
            # Slight offset prevents skin z-fighting in mobile renderers.
            uv("Kade_Freckle_%s_%02d"%(side,i),tuple(point+normal*.00035),
               (rad,rad*.3,rad),freckle if i%4==0 else softfreckle,8,4)
    # Combine freckle meshes to keep Android draw calls manageable.
    freckles=[o for o in items if o.name.startswith("Kade_Freckle_")]
    if freckles:
        bpy.ops.object.select_all(action='DESELECT')
        for o in freckles:o.select_set(True)
        bpy.context.view_layer.objects.active=freckles[0]
        bpy.ops.object.join()
        fused=bpy.context.view_layer.objects.active
        fused.name="Kade_Freckles_SingleSurfaceDecoration"
        items[:]=[o for o in items if o not in freckles]+[fused]
    print("KADE_V08_FRECKLE_GEOMETRY",len(freckles),flush=True)

    # Natural narrow lip material accents, close to the actual mouth surface.
    # This remains an overlay, not a replacement for anatomical lips.
    for z,w in ((1.508,.017),(1.501,.015)):
        pts=[]
        for i in range(13):
            x=(-1+2*i/12)*w
            zz=z+(.0015*math.sin(math.pi*i/12) if z>1.504 else -.001*math.sin(math.pi*i/12))
            h=ray_front(x,zz)
            if h:pt,n=h;pts.append((tuple(pt+n*.0006),.68))
        if len(pts)>3:poly_curves("Kade_Lip_Refinement_%d"%int(z*1000),[pts],lip,bevel=.0016)

    # Small star tattoo + healed scar near undercut, subtle and geometry-based.
    for i in range(5):
        ang=i*2*math.pi/5
        x=.047+.003*math.cos(ang)
        z=1.616+.003*math.sin(ang)
        h=ray_front(x,z)
        if h: pt,n=h;uv("Kade_Temple_Mark_%d"%i,tuple(pt+n*.0005),(.00095,.00032,.0011),softfreckle,8,4)

    # Orange-lens mechanic goggles perched on top of hair, NOT covering eyes.
    for sign in (-1,1):
        gx=sign*.037
        gy=-.032
        gz=1.664
        uv("Kade_Goggle_%s_RubberBedding"%sign,(gx,gy+.004,gz),(.030,.008,.018),charcoal,24,12)
        uv("Kade_Goggle_%s_AmberLens"%sign,(gx,gy-.010,gz),(.024,.004,.0135),orange,24,12)
        ringpts=[]
        for i in range(33):
            a=i*math.tau/32
            ringpts.append(((gx+.026*math.cos(a),gy-.009,gz+.0155*math.sin(a)),1.))
        poly_curves("Kade_Goggle_%s_StainlessFrame"%sign,[ringpts],rim,bevel=.00275,res=2)
    # Goggle strap goes over the crown and ties around the rear scalp.
    strap=[]
    for i in range(25):
        a=(i/24)*math.pi
        strap.append(((-.070*math.cos(a),.014+.061*math.sin(a),1.674+.007*math.sin(a)),1.0))
    poly_curves("Kade_Goggle_Strap",[strap],charcoal,bevel=.0030)

    # Physical brass ear hoops; cross-section of jewellery stays round in GLB.
    for side in (-1,1):
        x=side*.085
        y=-.009
        z=1.510
        pts=[]
        for i in range(33):
            a=i*math.tau/32
            pts.append(((x+.0098*math.cos(a),y-.0003,z-.014+.014*math.sin(a)),1.))
        poly_curves("Kade_Hoop_Earring_%s"%side,[pts],gold,bevel=.00185)
    print("KADE_V08_FACE_HAIR_OBJECTS",len(items),flush=True)
    return items
