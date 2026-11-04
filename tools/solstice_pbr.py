"""Original procedural PBR paint atlases for SOLSTICE, not copied textures.

Exports via glTF: image -> Base Color; packed ORM G/B -> roughness and
metallic; tangent-space OpenGL +Y normal map -> Principled Normal.
"""
import bpy, math, array

def install_solstice_pbr(mat,size=1024):
    base=array.array("f")
    orm=array.array("f")
    normal=array.array("f")
    pi2=math.tau
    for y in range(size):
        v=y/size
        for x in range(size):
            u=x/size
            h=((x*73856093)^(y*19349663)^((x*y+17)*83492791))&255
            grain=h/255.0-.5
            a=math.sin(pi2*(u*2.7+v*.8))
            b=math.sin(pi2*(u*1.1-v*3.9))
            tint=1+.006*a+.003*b+.003*grain
            rough=max(.25,min(.37,.305+.009*a+.005*b+.004*grain))
            metal=max(.65,min(.81,.735+.008*b))
            # A good automotive clearcoat is almost perfectly smooth:
            # shape-changing reflectance belongs in the actual body mesh.
            nx=.0020*a+.0009*grain
            ny=.0023*b+.0009*grain
            nz=math.sqrt(max(.01,1-nx*nx-ny*ny))
            base.extend((.058*tint,.245*tint,.263*tint,1))
            orm.extend((1,rough,metal,1))
            normal.extend((.5+.5*nx,.5+.5*ny,.5+.5*nz,1))
    def image(name,pixels,non_color=False):
        im=bpy.data.images.new(name,width=size,height=size,alpha=False,float_buffer=False)
        im.file_format="PNG"
        if non_color: im.colorspace_settings.name="Non-Color"
        im.pixels.foreach_set(pixels)
        im.pack()
        assert im.packed_file is not None,name
        return im
    albedo=image("SOLSTICE_Paint_BaseColor_1K",base)
    packed=image("SOLSTICE_Paint_ORM_1K",orm,True)
    bumps=image("SOLSTICE_Paint_NormalGL_1K",normal,True)
    n=mat.node_tree.nodes;links=mat.node_tree.links
    p=n.get("Principled BSDF")
    a=n.new("ShaderNodeTexImage");a.image=albedo
    links.new(a.outputs["Color"],p.inputs["Base Color"])
    m=n.new("ShaderNodeTexImage");m.image=packed
    sep=n.new("ShaderNodeSeparateColor");sep.mode="RGB"
    links.new(m.outputs["Color"],sep.inputs["Color"])
    links.new(sep.outputs["Green"],p.inputs["Roughness"])
    links.new(sep.outputs["Blue"],p.inputs["Metallic"])
    tex=n.new("ShaderNodeTexImage");tex.image=bumps
    nm=n.new("ShaderNodeNormalMap");nm.space="TANGENT"
    nm.inputs["Strength"].default_value=.20
    links.new(tex.outputs["Color"],nm.inputs["Color"])
    links.new(nm.outputs["Normal"],p.inputs["Normal"])
    p.inputs["Coat Weight"].default_value=.29
    p.inputs["Coat Roughness"].default_value=.20
    print("SCENEFORGE_SOLSTICE_ORIGINAL_PBR_TEXTURES_OK",size)
