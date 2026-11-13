package com.sceneforge.glbinspector;

import android.util.Log;
import org.json.JSONArray;
import org.json.JSONObject;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;

/** Tiny deterministic vertex-export regression test for native editor. */
public final class SurfaceLabSmoke {
    private static final String TAG="SCENEFORGE_SHAPE_TEST";
    private static final int JSON=0x4e4f534a, BIN=0x004e4942;
    private SurfaceLabSmoke(){}
    private static JSONArray arr(float... numbers){
        JSONArray a=new JSONArray();
        for(float x:numbers)a.put(x);
        return a;
    }
    private static byte[] sampleGlb() throws Exception {
        JSONObject root=new JSONObject().put("asset",new JSONObject().put("version","2.0"))
                .put("buffers",new JSONArray().put(new JSONObject().put("byteLength",44)))
                .put("bufferViews",new JSONArray()
                        .put(new JSONObject().put("buffer",0).put("byteOffset",0).put("byteLength",36))
                        .put(new JSONObject().put("buffer",0).put("byteOffset",36).put("byteLength",6)))
                .put("accessors",new JSONArray()
                        .put(new JSONObject().put("bufferView",0).put("componentType",5126)
                                .put("type","VEC3").put("count",3)
                                .put("min",arr(-1f,0f,0f)).put("max",arr(1f,0f,1f)))
                        .put(new JSONObject().put("bufferView",1).put("componentType",5123)
                                .put("type","SCALAR").put("count",3).put("min",new JSONArray().put(0))
                                .put("max",new JSONArray().put(2))))
                .put("meshes",new JSONArray().put(new JSONObject().put("name","Test Hood")
                        .put("primitives",new JSONArray().put(new JSONObject()
                                .put("attributes",new JSONObject().put("POSITION",0))
                                .put("indices",1).put("mode",4)))))
                .put("nodes",new JSONArray().put(new JSONObject().put("mesh",0)))
                .put("scenes",new JSONArray().put(new JSONObject()
                        .put("nodes",new JSONArray().put(0))))
                .put("scene",0);
        byte[] j=root.toString().getBytes(StandardCharsets.UTF_8);
        int jsonLen=(j.length+3)&~3;
        int size=12+8+jsonLen+8+44;
        ByteBuffer bb=ByteBuffer.allocate(size).order(ByteOrder.LITTLE_ENDIAN);
        bb.putInt(0x46546c67).putInt(2).putInt(size);
        bb.putInt(jsonLen).putInt(JSON).put(j);
        while((bb.position()&3)!=0)bb.put((byte)' ');
        bb.putInt(44).putInt(BIN);
        for(float v:new float[]{-1,0,0, 1,0,0, 0,0,1})bb.putFloat(v);
        bb.putShort((short)0).putShort((short)1).putShort((short)2);
        while((bb.position()&3)!=0)bb.put((byte)0);
        return bb.array();
    }
    public static void execute(){
        try {
            byte[] src=sampleGlb();
            GlbSurfaceEditor engine=new GlbSurfaceEditor(src);
            if(engine.parts().size()!=1)throw new IllegalStateException("Missing mesh");
            GlbSurfaceEditor.Part p=engine.parts().get(0);
            float old=p.vertices[2][1];
            GlbSurfaceEditor.Stroke stroke=engine.beginStroke(p,new float[]{0,0,1},0,2f,false);
            stroke.apply(.12f,.35f);
            engine.commit(stroke);
            float modified=p.vertices[2][1];
            if(!(modified>old+.2f))throw new IllegalStateException("Vertex failed to deform");
            byte[] export=engine.exportGlb();
            GlbSurfaceEditor reopened=new GlbSurfaceEditor(export);
            float saved=reopened.parts().get(0).vertices[2][1];
            if(Math.abs(saved-modified)>1e-5f)throw new IllegalStateException("Vertex edit lost on GLB reload");
            if(!engine.undo())throw new IllegalStateException("Undo missing");
            if(Math.abs(p.vertices[2][1]-old)>1e-6f)throw new IllegalStateException("Undo didn't restore");
            engine.resetPart(p);
            if(Math.abs(p.vertices[2][1]-p.original[2][1])>1e-6f)
                throw new IllegalStateException("Reset failed");
            Log.i(TAG,"REAL_VERTEX_DEFORM_UNDO_EXPORT_REIMPORT_PASSED");
        } catch(Exception ex) {
            Log.e(TAG,"SHAPE_LAB_SELF_TEST_FAILED",ex);
        }
    }
}
