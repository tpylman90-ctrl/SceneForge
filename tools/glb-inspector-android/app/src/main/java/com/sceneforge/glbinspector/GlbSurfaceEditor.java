package com.sceneforge.glbinspector;

import org.json.JSONArray;
import org.json.JSONObject;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.io.ByteArrayOutputStream;

/**
 * Offline, non-destructive GLB vertex deformation engine. This deliberately
 * supports only uncompressed FLOAT VEC3 POSITION, TRIANGLES and a single GLB BIN.
 * Unsupported topology is rejected, never silently corrupted.
 *
 * Coordinate convention for Shape Lab: X width, Y up, Z length. A Gaussian
 * 2D brush deforms selected vertices in side/top/front orthographic views.
 * Batching by original stroke positions prevents cumulative drift on drag.
 */
public final class GlbSurfaceEditor {
    private static final int GLB_MAGIC=0x46546c67, JSON=0x4e4f534a, BIN=0x004e4942;
    private final byte[] source;
    private final JSONObject root;
    private final JSONArray accessors, views;
    private final int binOffset, binSize;
    private final List<Part> parts = new ArrayList<>();
    private final List<Stroke> history = new ArrayList<>();

    public static final class Part {
        public final String name;
        public final int positionAccessor;
        public final int normalAccessor;
        public final int[] indices;
        public final float[][] vertices;
        public final float[][] original;
        Part(String n,int a,int normal,int[] faces,float[][] v){
            name=n;positionAccessor=a;normalAccessor=normal;indices=faces;
            vertices=v;original=copy(v);
        }
        public float[][] bounds(){
            float[] lo={Float.POSITIVE_INFINITY,Float.POSITIVE_INFINITY,Float.POSITIVE_INFINITY};
            float[] hi={Float.NEGATIVE_INFINITY,Float.NEGATIVE_INFINITY,Float.NEGATIVE_INFINITY};
            for(float[] xyz:vertices)for(int j=0;j<3;j++){lo[j]=Math.min(lo[j],xyz[j]);hi[j]=Math.max(hi[j],xyz[j]);}
            return new float[][]{lo,hi};
        }
    }
    public static final class Stroke {
        public final Part part, mirror;
        public final float[][] base, mirrorBase;
        private final float[] hit;
        private final int view;
        private final float radius;
        private final boolean symmetric;
        Stroke(Part p,Part m,float[] center,int view,float r,boolean symmetry){
            part=p;mirror=m;hit=center;this.view=view;radius=r;symmetric=symmetry;
            base=copy(p.vertices);
            mirrorBase=m==null?null:copy(m.vertices);
        }
        void apply(float du,float dv){
            restore(part.vertices,base);
            deform(part.vertices,base,hit,view,du,dv,radius);
            if(mirror!=null){
                restore(mirror.vertices,mirrorBase);
                float[] mirrorHit={-hit[0],hit[1],hit[2]};
                float mdU= view==1||view==2 ? -du:du;
                deform(mirror.vertices,mirrorBase,mirrorHit,view,mdU,dv,radius);
            }else if(symmetric&&Math.abs(hit[0])>.10f){
                float[] mh={-hit[0],hit[1],hit[2]};
                float mdU= view==1||view==2 ? -du:du;
                deform(part.vertices,base,mh,view,mdU,dv,radius);
            }
        }
    }
    private static float[][] copy(float[][] v){
        float[][] out=new float[v.length][];
        for(int i=0;i<v.length;i++)out[i]=v[i].clone();
        return out;
    }
    private static void restore(float[][] to,float[][] from) {
        for(int i=0;i<from.length;i++)System.arraycopy(from[i],0,to[i],0,3);
    }
    // view=0 side (z/y), 1 top (x/z), 2 front (x/y)
    public static int horiz(int view){return view==0?2:0;}
    public static int vert(int view){return view==1?2:1;}
    private static void deform(float[][] verts,float[][] base,float[] center,int view,float du,float dv,float radius){
        int axisA=horiz(view),axisB=vert(view);
        float inv=1f/(2f*radius*radius);
        for(int i=0;i<verts.length;i++){
            float[] v=base[i];
            float a=v[axisA]-center[axisA],b=v[axisB]-center[axisB];
            float w=(float)Math.exp(-(a*a+b*b)*inv);
            // Smooth Gaussian; editable cage preserves local continuity away from stroke.
            verts[i][axisA]+=du*w;
            verts[i][axisB]+=dv*w;
        }
    }
    public List<Part> parts(){return parts;}
    public Part find(String name){
        for(Part p:parts)if(p.name.equals(name))return p;
        return null;
    }

    public GlbSurfaceEditor(byte[] bytes) throws Exception{
        source=bytes.clone();
        ByteBuffer head=ByteBuffer.wrap(source).order(ByteOrder.LITTLE_ENDIAN);
        if(source.length<36||head.getInt(0)!=GLB_MAGIC||head.getInt(4)!=2||head.getInt(8)!=source.length)
            throw new IllegalArgumentException("Not a GLB v2 file");
        int at=12,jsonStart=-1,jsonLen=0,binStart=-1,binLen=0;
        while(at+8<=source.length){
            int len=head.getInt(at),kind=head.getInt(at+4);
            if(len<0||(long)at+8+len>source.length)throw new IllegalArgumentException("Invalid GLB chunk");
            if(kind==JSON){jsonStart=at+8;jsonLen=len;}
            else if(kind==BIN){binStart=at+8;binLen=len;}
            else throw new IllegalArgumentException("Unsupported additional GLB chunk");
            at+=len+8;
        }
        if(at!=source.length||jsonStart<0||binStart<0)
            throw new IllegalArgumentException("GLB requires JSON and BIN chunks");
        root=new JSONObject(new String(source,jsonStart,jsonLen,StandardCharsets.UTF_8).trim());
        binOffset=binStart;binSize=binLen;
        accessors=root.getJSONArray("accessors");
        views=root.getJSONArray("bufferViews");
        JSONArray buffers=root.getJSONArray("buffers");
        if(buffers.length()!=1||buffers.getJSONObject(0).has("uri"))
            throw new IllegalArgumentException("Shape Lab requires one internal GLB buffer");
        JSONArray required=root.optJSONArray("extensionsRequired");
        if(required!=null)for(int i=0;i<required.length();i++){
            String ext=required.getString(i);
            if(ext.contains("meshopt")||ext.contains("draco"))
                throw new IllegalArgumentException("Compressed meshes require pre-exporting a standard GLB");
        }
        // In a transformed/skinned hierarchy these local positions are not
        // directly in the scene's physical coordinates. Reject rather than
        // issue false side/top coordinates for a misleading geometry edit.
        JSONArray nodes=root.optJSONArray("nodes");
        if(nodes!=null)for(int i=0;i<nodes.length();i++){
            JSONObject n=nodes.getJSONObject(i);
            if(n.has("matrix")||n.has("translation")||n.has("rotation")||n.has("scale")||n.has("skin"))
                throw new IllegalArgumentException("Shape Lab needs an applied-transform GLB (use Blender: Apply All Transforms)");
        }
        JSONArray meshes=root.getJSONArray("meshes");
        for(int i=0;i<meshes.length();i++){
            JSONObject mesh=meshes.getJSONObject(i);
            if(mesh.has("weights"))throw new IllegalArgumentException("Morph-target meshes not supported");
            JSONArray prims=mesh.getJSONArray("primitives");
            for(int j=0;j<prims.length();j++){
                JSONObject prim=prims.getJSONObject(j);
                if(prim.optInt("mode",4)!=4||prim.has("targets"))
                    throw new IllegalArgumentException("Only triangle-mesh surfaces can be edited");
                JSONObject attrs=prim.getJSONObject("attributes");
                int pos=attrs.getInt("POSITION"),norm=attrs.optInt("NORMAL",-1);
                float[][] coords=readPositions(pos);
                int[] indices=readTriangleIndices(prim,coords.length);
                String name=mesh.optString("name","Mesh "+(i+1));
                if(prims.length()>1)name+=" / primitive "+(j+1);
                parts.add(new Part(name,pos,norm,indices,coords));
            }
        }
        if(parts.isEmpty())throw new IllegalArgumentException("No editable triangle meshes found");
    }
    private static int componentSize(int type){
        switch(type){case 5121:return 1;case 5123:return 2;case 5125:case 5126:return 4;}
        throw new IllegalArgumentException("Unsupported accessor component");
    }
    private int accessorOffset(int id,int strideMin) throws Exception{
        JSONObject a=accessors.getJSONObject(id);
        if(a.has("sparse"))throw new IllegalArgumentException("Sparse accessors are not editable");
        JSONObject view=views.getJSONObject(a.getInt("bufferView"));
        if(view.optInt("buffer",0)!=0)throw new IllegalArgumentException("Multiple buffers not supported");
        int byteOffset=view.optInt("byteOffset",0)+a.optInt("byteOffset",0);
        int stride=view.optInt("byteStride",strideMin);
        if(stride<strideMin||stride%componentSize(a.getInt("componentType"))!=0)
            throw new IllegalArgumentException("Invalid vertex stride");
        int count=a.getInt("count");
        if(count<1||(long)byteOffset+(long)(count-1)*stride+strideMin>binSize)
            throw new IllegalArgumentException("Vertex buffer out of bounds");
        return binOffset+byteOffset;
    }
    private int stride(int id,int minimum) throws Exception{
        JSONObject a=accessors.getJSONObject(id);
        JSONObject view=views.getJSONObject(a.getInt("bufferView"));
        return view.optInt("byteStride",minimum);
    }
    private float[][] readPositions(int id) throws Exception{
        JSONObject a=accessors.getJSONObject(id);
        if(a.getInt("componentType")!=5126||!"VEC3".equals(a.getString("type")))
            throw new IllegalArgumentException("Shape Lab needs FLOAT32 VEC3 POSITION meshes");
        int off=accessorOffset(id,12),step=stride(id,12),n=a.getInt("count");
        ByteBuffer bb=ByteBuffer.wrap(source).order(ByteOrder.LITTLE_ENDIAN);
        float[][] result=new float[n][3];
        for(int i=0;i<n;i++)for(int k=0;k<3;k++){
            float v=bb.getFloat(off+i*step+k*4);
            if(!Float.isFinite(v))throw new IllegalArgumentException("Nonfinite model position");
            result[i][k]=v;
        }
        return result;
    }
    private int[] readTriangleIndices(JSONObject prim,int vertexCount) throws Exception{
        if(!prim.has("indices")){
            if(vertexCount%3!=0)throw new IllegalArgumentException("Nonindexed triangle count invalid");
            int[] ix=new int[vertexCount];for(int i=0;i<ix.length;i++)ix[i]=i;return ix;
        }
        int id=prim.getInt("indices");
        JSONObject a=accessors.getJSONObject(id);
        int type=a.getInt("componentType"),bytes=componentSize(type);
        if(type!=5121&&type!=5123&&type!=5125)throw new IllegalArgumentException("Unsupported index type");
        if(!"SCALAR".equals(a.getString("type")))throw new IllegalArgumentException("Invalid index accessor");
        int count=a.getInt("count");
        if(count%3!=0)throw new IllegalArgumentException("Not triangles");
        int off=accessorOffset(id,bytes),step=stride(id,bytes);
        ByteBuffer bb=ByteBuffer.wrap(source).order(ByteOrder.LITTLE_ENDIAN);
        int[] result=new int[count];
        for(int i=0;i<count;i++){
            int where=off+i*step;
            long index=type==5121?(source[where]&255):type==5123?(bb.getShort(where)&65535):Integer.toUnsignedLong(bb.getInt(where));
            if(index>=vertexCount)throw new IllegalArgumentException("Bad face index");
            result[i]=(int)index;
        }
        return result;
    }
    public Stroke beginStroke(Part part,float[] at,int view,float radius,boolean mirror){
        if(part==null||radius<=0||view<0||view>2)throw new IllegalArgumentException("Invalid brush");
        Part pair=null;
        if(mirror){
            String swapped=part.name.contains("PORT")?part.name.replace("PORT","STBD"):
                    part.name.contains("STBD")?part.name.replace("STBD","PORT"):null;
            if(swapped!=null)pair=find(swapped);
        }
        return new Stroke(part,pair,at.clone(),view,radius,mirror);
    }
    public void commit(Stroke s){
        history.add(s);
        if(history.size()>20)history.remove(0);
    }
    public boolean undo(){
        if(history.isEmpty())return false;
        Stroke s=history.remove(history.size()-1);
        restore(s.part.vertices,s.base);
        if(s.mirror!=null)restore(s.mirror.vertices,s.mirrorBase);
        return true;
    }
    public void resetPart(Part p){
        if(p!=null){restore(p.vertices,p.original);history.clear();}
    }
    public float[][] sceneBounds(){
        float[] lo={Float.POSITIVE_INFINITY,Float.POSITIVE_INFINITY,Float.POSITIVE_INFINITY};
        float[] hi={Float.NEGATIVE_INFINITY,Float.NEGATIVE_INFINITY,Float.NEGATIVE_INFINITY};
        for(Part p:parts)for(float[] q:p.vertices)for(int k=0;k<3;k++){
            lo[k]=Math.min(lo[k],q[k]);hi[k]=Math.max(hi[k],q[k]);
        }
        return new float[][]{lo,hi};
    }
    private void updateNormals(Part p,byte[] out) throws Exception{
        if(p.normalAccessor<0)return; // GLB may intentionally omit normals.
        JSONObject a=accessors.getJSONObject(p.normalAccessor);
        if(a.getInt("componentType")!=5126||!"VEC3".equals(a.getString("type"))||
                a.getInt("count")!=p.vertices.length)return;
        float[][] n=new float[p.vertices.length][3];
        for(int i=0;i<p.indices.length;i+=3){
            int ai=p.indices[i],bi=p.indices[i+1],ci=p.indices[i+2];
            float[] u=p.vertices[ai],v=p.vertices[bi],w=p.vertices[ci];
            float ax=v[0]-u[0],ay=v[1]-u[1],az=v[2]-u[2];
            float bx=w[0]-u[0],by=w[1]-u[1],bz=w[2]-u[2];
            float x=ay*bz-az*by,y=az*bx-ax*bz,z=ax*by-ay*bx;
            for(int id:new int[]{ai,bi,ci}){n[id][0]+=x;n[id][1]+=y;n[id][2]+=z;}
        }
        int off=accessorOffset(p.normalAccessor,12),step=stride(p.normalAccessor,12);
        ByteBuffer buf=ByteBuffer.wrap(out).order(ByteOrder.LITTLE_ENDIAN);
        for(int i=0;i<n.length;i++){
            float x=n[i][0],y=n[i][1],z=n[i][2];
            float l=(float)Math.sqrt(x*x+y*y+z*z);
            if(l<1e-8f){x=0;y=1;z=0;l=1;}
            buf.putFloat(off+i*step,x/l);buf.putFloat(off+i*step+4,y/l);buf.putFloat(off+i*step+8,z/l);
        }
    }
    public byte[] exportGlb() throws Exception{
        byte[] updated=source.clone();
        ByteBuffer bb=ByteBuffer.wrap(updated).order(ByteOrder.LITTLE_ENDIAN);
        for(Part p:parts){
            int off=accessorOffset(p.positionAccessor,12),step=stride(p.positionAccessor,12);
            float[] lo={Float.POSITIVE_INFINITY,Float.POSITIVE_INFINITY,Float.POSITIVE_INFINITY};
            float[] hi={Float.NEGATIVE_INFINITY,Float.NEGATIVE_INFINITY,Float.NEGATIVE_INFINITY};
            for(int i=0;i<p.vertices.length;i++)for(int j=0;j<3;j++){
                float value=p.vertices[i][j];
                if(!Float.isFinite(value))throw new IllegalArgumentException("Nonfinite edit");
                bb.putFloat(off+i*step+j*4,value);
                lo[j]=Math.min(lo[j],value);hi[j]=Math.max(hi[j],value);
            }
            JSONObject accessor=accessors.getJSONObject(p.positionAccessor);
            JSONArray min=new JSONArray(),max=new JSONArray();
            for(int k=0;k<3;k++){min.put(lo[k]);max.put(hi[k]);}
            accessor.put("min",min).put("max",max);
            updateNormals(p,updated);
        }
        // Preserve original BIN byte-for-byte except edited FLOAT coordinates
        // and optional recomputed NORMAL streams; all texture and material data
        // stay in their original BIN offsets.
        byte[] j=root.toString().getBytes(StandardCharsets.UTF_8);
        int jlen=(j.length+3)&~3;
        int total=12+8+jlen+8+binSize;
        ByteBuffer dst=ByteBuffer.allocate(total).order(ByteOrder.LITTLE_ENDIAN);
        dst.putInt(GLB_MAGIC).putInt(2).putInt(total);
        dst.putInt(jlen).putInt(JSON).put(j);
        while((dst.position()&3)!=0)dst.put((byte)' ');
        dst.putInt(binSize).putInt(BIN).put(updated,binOffset,binSize);
        return dst.array();
    }
}
