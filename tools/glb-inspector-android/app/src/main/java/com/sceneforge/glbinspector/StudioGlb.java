package com.sceneforge.glbinspector;

import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

/**
 * Builds a temporary studio floor into the render-only GLB.
 * No source GLB is modified on disk. Floor is omitted in wireframe mode.
 *
 * The PBR floor is actual shadow-receiving geometry, not a fake bitmap.
 * This is a preview helper, not a GLB exporter.
 */
public final class StudioGlb {
    private static final int GLB_MAGIC = 0x46546c67, JSON_CHUNK = 0x4e4f534a, BIN_CHUNK = 0x004e4942;
    private StudioGlb() {}

    public static byte[] withFloor(byte[] input) throws Exception {
        if (input.length < 28) return input;
        ByteBuffer src = ByteBuffer.wrap(input).order(ByteOrder.LITTLE_ENDIAN);
        if (src.getInt(0) != GLB_MAGIC || src.getInt(4) != 2 || src.getInt(8) != input.length) return input;
        int off = 12, jsonStart = -1, jsonLen = 0, binStart = -1, binLen = 0;
        while (off + 8 <= input.length) {
            int len = src.getInt(off), type = src.getInt(off + 4);
            if (len < 0 || (long)off + len + 8 > input.length) return input;
            if (type == JSON_CHUNK) { jsonStart = off + 8; jsonLen = len; }
            else if (type == BIN_CHUNK) { binStart = off + 8; binLen = len; }
            off += 8 + len;
        }
        if (jsonStart < 0 || binStart < 0) return input;
        JSONObject root = new JSONObject(new String(input, jsonStart, jsonLen, StandardCharsets.UTF_8).trim());
        JSONArray meshes = root.optJSONArray("meshes"), accessors = root.optJSONArray("accessors");
        JSONArray views = root.optJSONArray("bufferViews"), buffers = root.optJSONArray("buffers");
        JSONArray scenes = root.optJSONArray("scenes"), nodes = root.optJSONArray("nodes");
        if (meshes == null || accessors == null || views == null || buffers == null
                || nodes == null || scenes == null || scenes.length() == 0 || buffers.length() == 0) return input;
        if (buffers.getJSONObject(0).has("uri")) return input;
        if (root.optJSONObject("extensions") != null && root.getJSONObject("extensions").has("EXT_mesh_gpu_instancing"))
            return input;

        // POSITION ranges approximate the scene's vertical extent, avoiding GPU readback.
        double minX = Double.POSITIVE_INFINITY, minY = minX, minZ = minX;
        double maxX = Double.NEGATIVE_INFINITY, maxY = maxX, maxZ = maxX;
        for (int i = 0; i < meshes.length(); i++) {
            JSONArray primitives = meshes.getJSONObject(i).optJSONArray("primitives");
            if (primitives == null) continue;
            for (int j = 0; j < primitives.length(); j++) {
                JSONObject attrs = primitives.getJSONObject(j).optJSONObject("attributes");
                if (attrs == null) continue;
                int index = attrs.optInt("POSITION", -1);
                if (index < 0 || index >= accessors.length()) continue;
                JSONObject accessor = accessors.getJSONObject(index);
                JSONArray mins = accessor.optJSONArray("min"), maxs = accessor.optJSONArray("max");
                if (mins == null || maxs == null || mins.length() != 3 || maxs.length() != 3) continue;
                minX = Math.min(minX, mins.getDouble(0)); maxX = Math.max(maxX, maxs.getDouble(0));
                minY = Math.min(minY, mins.getDouble(1)); maxY = Math.max(maxY, maxs.getDouble(1));
                minZ = Math.min(minZ, mins.getDouble(2)); maxZ = Math.max(maxZ, maxs.getDouble(2));
            }
        }
        if (!Double.isFinite(minY) || maxX <= minX || maxZ <= minZ) return input;
        double sx = maxX - minX, sy = maxY - minY, sz = maxZ - minZ;
        double largest = Math.max(sx, Math.max(sy, sz));
        // Oversized enough for a floor and shadow, small enough not to shrink model drastically.
        double cx = (maxX + minX) * 0.5, cz = (maxZ + minZ) * 0.5;
        double hx = Math.max(sx * 0.85, largest * 0.62);
        double hz = Math.max(sz * 0.85, largest * 0.62);
        double y = minY - Math.max(sy * 0.13, largest * 0.055);
        float[] xyz = {
                (float)(cx - hx),(float)y,(float)(cz - hz),
                (float)(cx + hx),(float)y,(float)(cz - hz),
                (float)(cx + hx),(float)y,(float)(cz + hz),
                (float)(cx - hx),(float)y,(float)(cz + hz)
        };

        ByteArrayOutputStream b = new ByteArrayOutputStream(binLen + 128);
        b.write(input, binStart, binLen);
        pad4(b);
        int vertexOff = b.size();
        for (float v: xyz) putFloat(b,v);
        int normalOff = b.size();
        for (int i=0;i<4;i++) { putFloat(b,0);putFloat(b,1);putFloat(b,0); }
        int indexOff = b.size();
        for (int v: new int[]{0,2,1,0,3,2}) { b.write(v); b.write(0); }
        pad4(b);

        int vertViewId=views.length();
        views.put(new JSONObject().put("buffer",0).put("byteOffset",vertexOff).put("byteLength",48).put("target",34962));
        int normViewId=views.length();
        views.put(new JSONObject().put("buffer",0).put("byteOffset",normalOff).put("byteLength",48).put("target",34962));
        int idxViewId=views.length();
        views.put(new JSONObject().put("buffer",0).put("byteOffset",indexOff).put("byteLength",12).put("target",34963));
        int posId=accessors.length();
        accessors.put(new JSONObject().put("bufferView",vertViewId).put("componentType",5126)
                .put("count",4).put("type","VEC3")
                .put("min",new JSONArray().put((float)(cx-hx)).put((float)y).put((float)(cz-hz)))
                .put("max",new JSONArray().put((float)(cx+hx)).put((float)y).put((float)(cz+hz))));
        int normalId=accessors.length();
        accessors.put(new JSONObject().put("bufferView",normViewId).put("componentType",5126)
                .put("count",4).put("type","VEC3"));
        int indexId=accessors.length();
        accessors.put(new JSONObject().put("bufferView",idxViewId).put("componentType",5123)
                .put("count",6).put("type","SCALAR"));
        JSONArray materials=root.optJSONArray("materials");
        if(materials==null){materials=new JSONArray();root.put("materials",materials);}
        int materialId=materials.length();
        materials.put(new JSONObject().put("name","SceneForge Studio Floor")
                .put("doubleSided",true).put("alphaMode","OPAQUE")
                .put("pbrMetallicRoughness",new JSONObject()
                        .put("baseColorFactor",new JSONArray("[0.31,0.32,0.34,1]"))
                        .put("metallicFactor",0.0).put("roughnessFactor",0.96)));
        int meshId=meshes.length();
        meshes.put(new JSONObject().put("name","SceneForge preview floor")
                .put("primitives",new JSONArray().put(new JSONObject()
                        .put("attributes",new JSONObject().put("POSITION",posId).put("NORMAL",normalId))
                        .put("indices",indexId).put("material",materialId).put("mode",4))));
        int nodeId=nodes.length();
        nodes.put(new JSONObject().put("name","SceneForge studio floor").put("mesh",meshId));
        int sceneId=root.optInt("scene",0);
        if(sceneId<0 || sceneId>=scenes.length()) sceneId=0;
        JSONObject scene=scenes.getJSONObject(sceneId);
        JSONArray roots=scene.optJSONArray("nodes");
        if(roots==null){roots=new JSONArray();scene.put("nodes",roots);}
        roots.put(nodeId);
        buffers.getJSONObject(0).put("byteLength",b.size());

        byte[] jsonBytes=root.toString().getBytes(StandardCharsets.UTF_8), bin=b.toByteArray();
        int jlen=(jsonBytes.length+3)&~3, blen=(bin.length+3)&~3, length=12+8+jlen+8+blen;
        ByteBuffer out=ByteBuffer.allocate(length).order(ByteOrder.LITTLE_ENDIAN);
        out.putInt(GLB_MAGIC).putInt(2).putInt(length);
        out.putInt(jlen).putInt(JSON_CHUNK).put(jsonBytes);
        while((out.position()&3)!=0)out.put((byte)' ');
        out.putInt(blen).putInt(BIN_CHUNK).put(bin);
        while((out.position()&3)!=0)out.put((byte)0);
        return out.array();
    }
    private static void pad4(ByteArrayOutputStream b){while((b.size()&3)!=0)b.write(0);}
    private static void putFloat(ByteArrayOutputStream b,float f){
        int n=Float.floatToIntBits(f);
        for(int i=0;i<4;i++)b.write((n >>>(8*i))&255);
    }
}
