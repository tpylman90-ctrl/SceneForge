"""Rhea v03: distinctive copper mane, red goggles, freckles, eyes and gold earrings on Rhea’s continuous MakeHuman anatomy.
All details are actual mesh data exported to GLB, not an image or billboard.
Local Blender coordinates: X across body, Y negative toward front, Z up.
Body proportions are untouched; visual feature layers remain separate meshes.
"""
import bpy
import math
import random
from mathutils import Vector

def build_rhea_identity(body, make_material):
    rand = random.Random(591521)
    items = []
    def mat(name, rgb, rough=.65, metallic=0):
        return make_material(name, rgb, rough, metallic)
    espresso = mat("Rhea_Hair_Dark_Copper", (.088,.018,.007),.50)
    deep = mat("Rhea_Hair_Auburn_Shadow", (.148,.035,.012),.48)
    aubergine = mat("Rhea_Hair_Cinnamon", (.245,.068,.022),.46)
    hotpink = mat("Rhea_Hair_Bright_Copper", (.38,.115,.032),.43)
    pinkdim = mat("Rhea_Hair_Copper_Lowlights", (.19,.041,.013),.51)
    lip = mat("Rhea_Warm_Rose_Lips", (.37,.115,.115),.48)
    eyebrow = mat("Rhea_Eyebrows_Dark_Auburn", (.075,.026,.017),.72)
    freckle = mat("Rhea_Skin_Freckles_Cinnamon", (.22,.085,.050),.82)
    softfreckle = mat("Rhea_Skin_Freckles_Soft", (.29,.13,.078),.85)
    sclera = mat("Rhea_Eyes_Warm_White", (.79,.73,.65),.22)
    iris = mat("Rhea_Eyes_Deep_Brown", (.11,.041,.020),.24)
    irislite = mat("Rhea_Eyes_Honey_Amber_Rays", (.38,.17,.052),.28)
    pupil = mat("Rhea_Eyes_Pupil", (.014,.008,.01),.12)
    glint = mat("Rhea_Eye_Catchlight", (.98,.88,.69),.12)
    charcoal = mat("Rhea_Goggles_BlackRubber", (.025,.028,.035),.66)
    rim = mat("Rhea_Goggles_Gunmetal", (.16,.18,.21),.28,.77)
    orange = mat("Rhea_Goggles_Crimson_Red_Lens", (.62,.016,.035),.13,.35)
    gold = mat("Rhea_Hoop_Jewelry_Gold", (.72,.43,.13),.23,.82)

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

    # Smooth closed-form scalp hemisphere. V05/V06 polygon-cut scalp caps
    # produced a visibly jagged hairline; the continuous loft fixes this.
    verts=[]; faces=[]
    nr=12; ns=48
    for j in range(nr+1):
        phi=.0001+(math.pi/2-.0001)*j/nr
        for i in range(ns):
            a=2*math.pi*i/ns
            u=math.sin(phi)
            x=.088*u*math.cos(a)
            y=-.008+.103*u*math.sin(a)
            z=1.706+.091*math.cos(phi)
            verts.append((x,y,z))
    for j in range(nr):
        for i in range(ns):
            i2=(i+1)%ns
            faces.append((j*ns+i,j*ns+i2,(j+1)*ns+i2,(j+1)*ns+i))
    scalpmesh=bpy.data.meshes.new("Rhea_Smooth_Scalp_Hairline")
    scalpmesh.from_pydata(verts,[],faces)
    scalpmesh.update()
    scalp=keep(bpy.data.objects.new("Rhea_Smooth_Scalp_Crown",scalpmesh))
    bpy.context.collection.objects.link(scalp)
    scalp.data.materials.append(espresso)
    for p in scalp.data.polygons:p.use_smooth=True

    # V03: volumetric strand-based hairstyle. NO enlarged ellipsoid "hair masses".
    # Each lock is a proper tapered 3D tubular spline, combined by material.
    # Hair follows a sculpted scalp cap, gathers above the crown into a
    # high ponytail, then becomes cascading spiral copper curls.
    shades={0:[],1:[],2:[],3:[],4:[]}
    def add_lock(points,shading,base_rad):
        path=[]
        for k,pt in enumerate(points):
            t=k/max(1,len(points)-1)
            envelope=max(.055,1.0-.48*t*t)
            if t>.85: envelope*=1.0-.91*(t-.85)/.15
            path.append((pt,envelope))
        shades[shading].append((path,base_rad))

    # Fine swept hair fibers closely hug the continuous head cap.
    for n in range(145):
        rx=rand.uniform(-.071,.071)
        start_y=rand.uniform(-.077,-.033)
        phase=rand.uniform(-.6,.6)
        path=[]
        for k in range(24):
            t=k/23
            x=rx*(1.-.36*t)+.006*math.sin(2.0*math.pi*t+phase)
            y=start_y+(.175-start_y)*t
            r2=(x/.094)**2+((y+.008)/.115)**2
            z=1.705+.093*math.sqrt(max(0.025,1.-r2))+.0025
            path.append((x,y,z))
        sh=3 if n%8==0 else (4 if n%9==0 else n%3)
        add_lock(path,sh,rand.uniform(.0018,.0035))

    # High ponytail: distributed tresses radiate from the tie and curl down
    # across the back. Controlled radii avoid giant disconnected blobs.
    for n in range(235):
        theta=rand.random()*math.tau
        radius=rand.uniform(.035,.113)
        rootx=rand.uniform(-.035,.035)
        rooty=rand.uniform(.071,.103)
        rootz=rand.uniform(1.777,1.819)
        endz=rand.uniform(1.355,1.485)
        phase=rand.uniform(0,math.tau)
        wave=rand.uniform(.007,.016)
        path=[]
        for k in range(35):
            t=k/34
            spread=t**.74
            x=rootx+radius*math.cos(theta)*spread + wave*math.sin(8*math.pi*t+phase)*(.18+.82*t)
            y=rooty+.055*t+radius*.64*math.sin(theta)*spread + .012*math.sin(7*math.pi*t+phase)*t
            z=rootz+(endz-rootz)*t+.004*math.cos(8*math.pi*t+phase)*t
            path.append((x,y,z))
        sh=3 if n%7==0 else (4 if n%11==0 else n%3)
        add_lock(path,sh,rand.uniform(.0043,.0094))

    # Deliberate face framing: asymmetric copper corkscrews beside the temples
    # without crossing the eyes or producing a giant sphere on the cheek.
    for sign in (-1,1):
        count=34 if sign<0 else 22
        for n in range(count):
            rootx=sign*rand.uniform(.066,.086)
            rooty=rand.uniform(-.046,-.009)
            rootz=rand.uniform(1.721,1.789)
            endz=rand.uniform(1.510,1.620)
            phase=rand.uniform(0,math.tau)
            targetx=sign*rand.uniform(.113,.159)
            path=[]
            for k in range(29):
                t=k/28
                x=(1-t)*rootx+t*targetx+sign*.012*math.sin(6*math.pi*t+phase)*t
                y=rooty-.027*t+.012*math.cos(5.8*math.pi*t+phase)*t
                z=rootz+(endz-rootz)*t
                path.append((x,y,z))
            sh=3 if n%6==0 else n%3
            add_lock(path,sh,rand.uniform(.0034,.0062))

    # Physical copper tresses are grouped into five Blender-editable GLB meshes.
    for shade,material in enumerate((espresso,deep,aubergine,hotpink,pinkdim)):
        lines=[[(pt,r*w/.0049) for pt,r in path] for path,w in shades[shade]]
        if lines:
            poly_curves("Rhea_Hair_%02d_%s"%(shade,material.name),lines,material,bevel=.0049,res=2)

    # A compact black hair tie at the gathered rear root, not a scalp proxy.
    tie=[]
    for i in range(33):
        a=math.tau*i/32
        tie.append(((-.001+.043*math.cos(a),.087,1.792+.023*math.sin(a)),1.))
    poly_curves("Rhea_Ponytail_Tie",[tie],charcoal,bevel=.0042,res=2)

    # Rhea keeps a full copper hairline; no mechanic-style shaved stripe geometry.

    # Eyes are layered spheres and irises at her anatomical eye sockets,
    # with separate translucent-looking colored features (opaque GLB PBR).
    for sign in (-1,1):
        ex=sign*.034
        ez=1.65921
        h=ray_front(ex,ez)
        if not h:
            print("RHEA_V03_EYE_SURFACE_MISSING",sign,flush=True)
            continue
        eye_pt,eye_normal=h
        # Eyes are almond-shaped surface details, not protruding eyeballs.
        ey=eye_pt.y-.0006
        print("RHEA_V03_EYE_SURFACE",sign,round(ey,4),flush=True)
        uv("Rhea_Eye_%s_Sclera"%sign,(ex,ey,ez),(.0085,.00075,.00355),sclera,20,12)
        uv("Rhea_Eye_%s_Iris"%sign,(ex,ey-.0011,ez),(.0038,.0006,.00325),iris,24,12)
        uv("Rhea_Eye_%s_AmberInner"%sign,(ex,ey-.0017,ez),(.0029,.00043,.0028),irislite,18,10)
        uv("Rhea_Eye_%s_Pupil"%sign,(ex,ey-.0022,ez),(.00145,.00032,.0022),pupil,20,10)
        uv("Rhea_Eye_%s_Glint"%sign,(ex-sign*.0012,ey-.0025,ez+.0015),(.0009,.00025,.0010),glint,12,8)

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
        surface_line("Rhea_Eyebrow_%s"%sign,sign,[
            (.018,1.67193),(.028,1.67617),(.039,1.6788),(.050,1.6789),(.063,1.67405)
        ],eyebrow,.0027)
        surface_line("Rhea_Eyeliner_%s"%sign,sign,[
            (.019,1.65815),(.028,1.66133),(.038,1.66239),(.049,1.66027),(.060,1.65392)
        ],espresso,.0011)

    # Natural facial beauty detail: procedural surface-mounted freckles.
    # Mesh dots (not fake texture maps), so both viewer and Godot show them.
    for side in (-1,1):
        for i in range(42):
            xx=side*rand.uniform(.020,.066)
            zz=rand.uniform(1.60412,1.64226)
            hit=ray_front(xx,zz)
            if not hit:continue
            point,normal=hit
            # Keep the front-most face intersection; V05 incorrectly culled it.
            rad=rand.uniform(.00037,.00115)
            # Slight offset prevents skin z-fighting in mobile renderers.
            uv("Rhea_Freckle_%s_%02d"%(side,i),tuple(point+normal*.00035),
               (rad,rad*.3,rad),freckle if i%4==0 else softfreckle,8,4)
    # Combine freckle meshes to keep Android draw calls manageable.
    freckles=[o for o in items if o.name.startswith("Rhea_Freckle_")]
    if freckles:
        bpy.ops.object.select_all(action='DESELECT')
        for o in freckles:o.select_set(True)
        bpy.context.view_layer.objects.active=freckles[0]
        bpy.ops.object.join()
        fused=bpy.context.view_layer.objects.active
        fused.name="Rhea_Freckles_SingleSurfaceDecoration"
        items[:]=[o for o in items if o not in freckles]+[fused]
    print("RHEA_V03_FRECKLE_GEOMETRY",len(freckles),flush=True)

    # Natural narrow lip material accents, close to the actual mouth surface.
    # This remains an overlay, not a replacement for anatomical lips.
    for z,w in ((1.59776,.017),(1.59035,.015)):
        pts=[]
        for i in range(13):
            x=(-1+2*i/12)*w
            zz=z+(.0015*math.sin(math.pi*i/12) if z>1.59352 else -.001*math.sin(math.pi*i/12))
            h=ray_front(x,zz)
            if h:pt,n=h;pts.append((tuple(pt+n*.0006),.68))
        if len(pts)>3:poly_curves("Rhea_Lip_Refinement_%d"%int(z*1000),[pts],lip,bevel=.0016)

    # Small star tattoo + healed scar near undercut, subtle and geometry-based.
    for i in range(5):
        ang=i*2*math.pi/5
        x=.047+.003*math.cos(ang)
        z=1.71219+.003*math.sin(ang)
        h=ray_front(x,z)
        if h: pt,n=h;uv("Rhea_Temple_Mark_%d"%i,tuple(pt+n*.0005),(.00095,.00032,.0011),softfreckle,8,4)

    # Orange-lens mechanic goggles perched on top of hair, NOT covering eyes.
    for sign in (-1,1):
        gx=sign*.037
        gy=-.085
        gz=1.80649
        uv("Rhea_Goggle_%s_RubberBedding"%sign,(gx,gy+.004,gz),(.036,.014,.023),charcoal,24,12)
        uv("Rhea_Goggle_%s_AmberLens"%sign,(gx,gy-.010,gz),(.028,.006,.016),orange,24,12)
        ringpts=[]
        for i in range(33):
            a=i*math.tau/32
            ringpts.append(((gx+.031*math.cos(a),gy-.014,gz+.018*math.sin(a)),1.))
        poly_curves("Rhea_Goggle_%s_StainlessFrame"%sign,[ringpts],rim,bevel=.00275,res=2)
    # Goggle strap goes over the crown and ties around the rear scalp.
    strap=[]
    for i in range(25):
        a=(i/24)*math.pi
        strap.append(((-.079*math.cos(a),-.010+.045*math.sin(a),1.79165+.025*math.sin(a)),1.0))
    poly_curves("Rhea_Goggle_Strap",[strap],charcoal,bevel=.0055)

    # Physical brass ear hoops; cross-section of jewellery stays round in GLB.
    for side in (-1,1):
        x=side*.085
        y=-.009
        z=1.59988
        pts=[]
        for i in range(33):
            a=i*math.tau/32
            pts.append(((x+.0098*math.cos(a),y-.0003,z-.014+.014*math.sin(a)),1.))
        poly_curves("Rhea_Hoop_Earring_%s"%side,[pts],gold,bevel=.00185)
    print("RHEA_V03_FACE_HAIR_OBJECTS",len(items),flush=True)
    return items
