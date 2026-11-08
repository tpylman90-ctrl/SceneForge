package com.sceneforge.glbinspector;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.LinkedHashSet;

/**
 * Produces transient, inspection-only versions of an actual binary glTF.
 *
 * CLAY rewrites PBR materials to a consistent opaque neutral ceramic while retaining all
 * node transforms, geometry, normals, UVs, skinning and mesh definitions.
 *
 * WIREFRAME rewrites triangular primitives to true GL_LINES primitives, building deduplicated
 * triangle edges directly from glTF index accessors (or sequential non-indexed vertices).
 * It does not approximate wire edges with a screen-space grid.
 *
 * Original bytes are never modified, and nothing is exported over the source GLB.
 */
public final class GlbInspectionVariants {
    public enum Mode { TEXTURED, CLAY, WIREFRAME }

    private static final int MAGIC = 0x46546c67;
    private static final int CHUNK_JSON = 0x4e4f534a;
    private static final int CHUNK_BIN = 0x004e4942;

    private GlbInspectionVariants() {}

    public static byte[] create(byte[] original, Mode mode) throws Exception {
        if (mode == Mode.TEXTURED) return original;
        if (original.length < 20) throw new IllegalArgumentException("Incomplete GLB");

        ByteBuffer raw = ByteBuffer.wrap(original).order(ByteOrder.LITTLE_ENDIAN);
        if (raw.getInt(0) != MAGIC || raw.getInt(4) != 2 || raw.getInt(8) != original.length) {
            throw new IllegalArgumentException("GLB must be version 2 with a valid length");
        }

        int jsonOff = -1, jsonSize = 0, binaryOff = -1, binarySize = 0;
        int offset = 12;
        while (offset + 8 <= original.length) {
            int size = raw.getInt(offset);
            int type = raw.getInt(offset + 4);
            if (size < 0 || (long) offset + 8L + size > original.length) {
                throw new IllegalArgumentException("Invalid GLB chunk length");
            }
            if (type == CHUNK_JSON) {
                jsonOff = offset + 8;
                jsonSize = size;
            } else if (type == CHUNK_BIN) {
                binaryOff = offset + 8;
                binarySize = size;
            }
            offset += 8 + size;
        }
        if (jsonOff < 0) throw new IllegalArgumentException("GLB JSON is missing");

        String metadata = new String(original, jsonOff, jsonSize, StandardCharsets.UTF_8).trim();
        JSONObject gltf = new JSONObject(metadata);
        JSONArray meshes = gltf.optJSONArray("meshes");
        if (meshes == null || meshes.length() == 0) {
            throw new IllegalArgumentException("This GLB has no meshes to inspect");
        }

        rewriteMaterials(gltf, mode);

        byte[] binary;
        if (binaryOff >= 0) {
            binary = Arrays.copyOfRange(original, binaryOff, binaryOff + binarySize);
        } else {
            binary = new byte[0];
        }
        if (mode == Mode.WIREFRAME) {
            binary = rewriteAsWireframe(gltf, binary);
        }
        return encode(gltf, binary);
    }

    private static void rewriteMaterials(JSONObject gltf, Mode mode) throws JSONException {
        JSONArray materials = gltf.optJSONArray("materials");
        int count = materials == null ? 0 : materials.length();
        // Keep at least one material so primitives without a material can use the same shader.
        JSONArray replacement = new JSONArray();
        for (int i = 0; i < Math.max(count, 1); i++) {
            JSONObject mat = new JSONObject();
            mat.put("name", mode == Mode.CLAY ? "SceneForge clay" : "SceneForge topology");
            mat.put("doubleSided", true);
            mat.put("alphaMode", "OPAQUE");
            JSONObject pbr = new JSONObject();
            pbr.put("baseColorFactor", mode == Mode.CLAY
                    ? new JSONArray("[0.73,0.77,0.80,1.0]")
                    : new JSONArray("[0.25,0.88,0.97,1.0]"));
            pbr.put("metallicFactor", 0.0);
            pbr.put("roughnessFactor", mode == Mode.CLAY ? 0.88 : 1.0);
            mat.put("pbrMetallicRoughness", pbr);
            if (mode == Mode.WIREFRAME) {
                mat.put("extensions", new JSONObject().put("KHR_materials_unlit", new JSONObject()));
            }
            replacement.put(mat);
        }
        gltf.put("materials", replacement);

        if (mode == Mode.WIREFRAME) {
            JSONArray used = gltf.optJSONArray("extensionsUsed");
            if (used == null) {
                used = new JSONArray();
                gltf.put("extensionsUsed", used);
            }
            boolean listed = false;
            for (int i = 0; i < used.length(); i++) {
                if ("KHR_materials_unlit".equals(used.optString(i))) listed = true;
            }
            if (!listed) used.put("KHR_materials_unlit");
        }

        // Ensure primitives without a material also receive our uniform inspection material.
        JSONArray meshes = gltf.getJSONArray("meshes");
        for (int m = 0; m < meshes.length(); m++) {
            JSONArray primitives = meshes.getJSONObject(m).optJSONArray("primitives");
            if (primitives == null) continue;
            for (int p = 0; p < primitives.length(); p++) {
                JSONObject primitive = primitives.getJSONObject(p);
                int assigned = primitive.optInt("material", 0);
                if (assigned < 0 || assigned >= replacement.length()) assigned = 0;
                primitive.put("material", assigned);
                // Material variant mappings refer to original material names/IDs and must not
                // override the temporary clay or wireframe material at render time.
                JSONObject extensions = primitive.optJSONObject("extensions");
                if (extensions != null) extensions.remove("KHR_materials_variants");
            }
        }
    }

    private static byte[] rewriteAsWireframe(JSONObject gltf, byte[] bin) throws Exception {
        JSONArray buffers = gltf.optJSONArray("buffers");
        JSONArray views = gltf.optJSONArray("bufferViews");
        JSONArray accessors = gltf.optJSONArray("accessors");
        if (bin.length == 0 || buffers == null || buffers.length() < 1 ||
                views == null || accessors == null) {
            throw new IllegalArgumentException("Wireframe requires GLB-embedded geometry data");
        }
        if (buffers.getJSONObject(0).has("uri")) {
            throw new IllegalArgumentException("Wireframe requires an embedded GLB buffer");
        }

        ByteArrayOutputStream target = new ByteArrayOutputStream(bin.length + 16384);
        target.write(bin);
        padToFour(target, (byte) 0);

        JSONArray meshes = gltf.getJSONArray("meshes");
        int converted = 0;
        int edgeCount = 0;

        for (int m = 0; m < meshes.length(); m++) {
            JSONArray primitives = meshes.getJSONObject(m).optJSONArray("primitives");
            if (primitives == null) continue;
            for (int p = 0; p < primitives.length(); p++) {
                JSONObject prim = primitives.getJSONObject(p);
                int mode = prim.optInt("mode", 4);
                if (mode != 4 && mode != 5 && mode != 6) continue;

                JSONObject attributes = prim.optJSONObject("attributes");
                if (attributes == null || !attributes.has("POSITION")) continue;
                int positionId = attributes.getInt("POSITION");
                if (positionId < 0 || positionId >= accessors.length()) continue;
                int vertexCount = accessors.getJSONObject(positionId).getInt("count");
                if (vertexCount < 3) continue;

                int[] triangleIndices;
                if (prim.has("indices")) {
                    int indexAccessorId = prim.getInt("indices");
                    triangleIndices = readIndices(accessors, views, bin, indexAccessorId);
                } else {
                    triangleIndices = new int[vertexCount];
                    for (int i = 0; i < vertexCount; i++) triangleIndices[i] = i;
                }

                // Keep first-seen order while eliminating shared interior edges.
                LinkedHashSet<Long> edges = new LinkedHashSet<>();
                if (mode == 4) { // TRIANGLES
                    for (int i = 0; i + 2 < triangleIndices.length; i += 3) {
                        triangle(edges, triangleIndices[i], triangleIndices[i+1],
                                triangleIndices[i+2], vertexCount);
                    }
                } else if (mode == 5) { // TRIANGLE_STRIP
                    for (int i = 0; i + 2 < triangleIndices.length; i++) {
                        triangle(edges, triangleIndices[i], triangleIndices[i+1],
                                triangleIndices[i+2], vertexCount);
                    }
                } else { // TRIANGLE_FAN
                    for (int i = 1; i + 1 < triangleIndices.length; i++) {
                        triangle(edges, triangleIndices[0], triangleIndices[i],
                                triangleIndices[i+1], vertexCount);
                    }
                }
                if (edges.isEmpty()) continue;

                int indexByteOffset = target.size();
                for (long edge : edges) {
                    int a = (int)(edge >>> 32);
                    int b = (int)edge;
                    writeInt(target, a);
                    writeInt(target, b);
                }
                int byteCount = edges.size() * 8;

                int viewId = views.length();
                JSONObject wireView = new JSONObject();
                wireView.put("buffer", 0);
                wireView.put("byteOffset", indexByteOffset);
                wireView.put("byteLength", byteCount);
                wireView.put("target", 34963); // ELEMENT_ARRAY_BUFFER
                views.put(wireView);

                int accessorId = accessors.length();
                JSONObject wireAccessor = new JSONObject();
                wireAccessor.put("bufferView", viewId);
                wireAccessor.put("componentType", 5125); // unsigned int
                wireAccessor.put("count", edges.size() * 2);
                wireAccessor.put("type", "SCALAR");
                accessors.put(wireAccessor);

                prim.put("mode", 1); // glTF LINES, not an artistic mesh overlay
                prim.put("indices", accessorId);
                converted++;
                edgeCount += edges.size();
            }
        }
        if (converted == 0) {
            throw new IllegalArgumentException("No supported triangle primitives for wireframe");
        }
        buffers.getJSONObject(0).put("byteLength", target.size());
        return target.toByteArray();
    }

    private static void triangle(LinkedHashSet<Long> edges, int a, int b, int c, int vertexCount) {
        if (a < 0 || b < 0 || c < 0 ||
                a >= vertexCount || b >= vertexCount || c >= vertexCount) return;
        edge(edges, a, b);
        edge(edges, b, c);
        edge(edges, c, a);
    }

    private static void edge(LinkedHashSet<Long> edges, int a, int b) {
        if (a == b) return;
        long key = ((long)Math.min(a, b) << 32) | ((long)Math.max(a, b) & 0xffffffffL);
        edges.add(key);
    }

    private static int[] readIndices(JSONArray accessors, JSONArray views, byte[] bin, int id)
            throws JSONException {
        if (id < 0 || id >= accessors.length()) {
            throw new IllegalArgumentException("Invalid index accessor");
        }
        JSONObject a = accessors.getJSONObject(id);
        if (a.has("sparse")) {
            throw new IllegalArgumentException("Sparse indices are not supported by wireframe");
        }
        if (!"SCALAR".equals(a.optString("type", "SCALAR"))) {
            throw new IllegalArgumentException("Index accessor must be scalar");
        }
        int viewId = a.optInt("bufferView", -1);
        if (viewId < 0 || viewId >= views.length()) {
            throw new IllegalArgumentException("Indices have no readable buffer view");
        }
        JSONObject v = views.getJSONObject(viewId);
        if (v.optInt("buffer", 0) != 0 || v.has("extensions")) {
            throw new IllegalArgumentException("Compressed or external index buffers are unsupported");
        }
        int component = a.getInt("componentType");
        int width = component == 5121 ? 1 : component == 5123 ? 2 : component == 5125 ? 4 : 0;
        if (width == 0) throw new IllegalArgumentException("Unsupported GLB index component type");
        int count = a.getInt("count");
        long start = (long)v.optInt("byteOffset", 0) + a.optInt("byteOffset", 0);
        int stride = v.optInt("byteStride", width);
        long viewLimit = (long)v.optInt("byteOffset", 0) + v.getInt("byteLength");
        if (count < 0 || stride < width ||
                (count > 0 && (start < 0 || start + (long)(count - 1) * stride + width > viewLimit)) ||
                (count > 0 && start + (long)(count - 1) * stride + width > bin.length)) {
            throw new IllegalArgumentException("Index data exceeds GLB buffer bounds");
        }

        ByteBuffer bytes = ByteBuffer.wrap(bin).order(ByteOrder.LITTLE_ENDIAN);
        int[] indices = new int[count];
        for (int i = 0; i < count; i++) {
            int at = (int)(start + (long)i * stride);
            indices[i] = width == 1 ? (bytes.get(at) & 0xff) :
                    width == 2 ? (bytes.getShort(at) & 0xffff) : bytes.getInt(at);
        }
        return indices;
    }

    /**
     * Tiny embedded geometry fixture for on-device parser/render smoke tests.
     * Contains a square made of two indexed triangles (four distinct vertices).
     */
    public static byte[] diagnosticSquare() throws Exception {
        ByteBuffer bin = ByteBuffer.allocate(60).order(ByteOrder.LITTLE_ENDIAN);
        bin.putFloat(-1f).putFloat(-1f).putFloat(0f);
        bin.putFloat(1f).putFloat(-1f).putFloat(0f);
        bin.putFloat(1f).putFloat(1f).putFloat(0f);
        bin.putFloat(-1f).putFloat(1f).putFloat(0f);
        for (int i : new int[]{0, 1, 2, 0, 2, 3}) bin.putShort((short)i);

        JSONObject root = new JSONObject();
        root.put("asset", new JSONObject().put("version", "2.0").put("generator", "SceneForge offline diagnostic"));
        root.put("buffers", new JSONArray().put(new JSONObject().put("byteLength", 60)));
        root.put("bufferViews", new JSONArray()
                .put(new JSONObject().put("buffer", 0).put("byteOffset", 0)
                        .put("byteLength", 48).put("target", 34962))
                .put(new JSONObject().put("buffer", 0).put("byteOffset", 48)
                        .put("byteLength", 12).put("target", 34963)));
        root.put("accessors", new JSONArray()
                .put(new JSONObject().put("bufferView", 0).put("componentType", 5126)
                        .put("count", 4).put("type", "VEC3")
                        .put("min", new JSONArray("[-1,-1,0]"))
                        .put("max", new JSONArray("[1,1,0]")))
                .put(new JSONObject().put("bufferView", 1).put("componentType", 5123)
                        .put("count", 6).put("type", "SCALAR")));
        root.put("materials", new JSONArray().put(new JSONObject()
                .put("doubleSided", true)
                .put("pbrMetallicRoughness", new JSONObject().put("baseColorFactor",
                        new JSONArray("[0.5,0.65,0.8,1]"))
                        .put("metallicFactor", 0.1).put("roughnessFactor", 0.7))));
        root.put("meshes", new JSONArray().put(new JSONObject().put("primitives",
                new JSONArray().put(new JSONObject()
                        .put("attributes", new JSONObject().put("POSITION", 0))
                        .put("indices", 1).put("material", 0).put("mode", 4)))));
        root.put("nodes", new JSONArray().put(new JSONObject().put("mesh", 0)));
        root.put("scenes", new JSONArray().put(new JSONObject().put("nodes", new JSONArray("[0]"))));
        root.put("scene", 0);
        return encode(root, bin.array());
    }

    private static byte[] encode(JSONObject gltf, byte[] bin) throws Exception {
        byte[] text = gltf.toString().getBytes(StandardCharsets.UTF_8);
        int jsonSize = (text.length + 3) & ~3;
        int binSize = (bin.length + 3) & ~3;
        long total = 12L + 8L + jsonSize + (binSize > 0 ? 8L + binSize : 0);
        if (total > Integer.MAX_VALUE) throw new IllegalArgumentException("Inspection GLB too large");

        ByteBuffer out = ByteBuffer.allocate((int)total).order(ByteOrder.LITTLE_ENDIAN);
        out.putInt(MAGIC).putInt(2).putInt((int)total);
        out.putInt(jsonSize).putInt(CHUNK_JSON);
        out.put(text);
        while ((out.position() & 3) != 0) out.put((byte)' ');
        if (binSize > 0) {
            out.putInt(binSize).putInt(CHUNK_BIN);
            out.put(bin);
            while ((out.position() & 3) != 0) out.put((byte)0);
        }
        return out.array();
    }

    private static void padToFour(ByteArrayOutputStream out, byte value) {
        while ((out.size() & 3) != 0) out.write(value);
    }

    private static void writeInt(ByteArrayOutputStream out, int v) {
        out.write(v & 0xff);
        out.write((v >>> 8) & 0xff);
        out.write((v >>> 16) & 0xff);
        out.write((v >>> 24) & 0xff);
    }
}
