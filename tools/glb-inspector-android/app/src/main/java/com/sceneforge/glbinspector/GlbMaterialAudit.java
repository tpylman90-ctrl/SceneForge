package com.sceneforge.glbinspector;

import org.json.JSONArray;
import org.json.JSONObject;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/**
 * Pure GLB-v2 JSON material diagnostic. Never guesses what a bitmap looks like
 * and never mistakes a material count for proof that texture images are present.
 */
public final class GlbMaterialAudit {
    private GlbMaterialAudit() {}

    public static final class Report {
        public int materials, images, baseColorMaps, normalMaps, emissiveMaps;
        public int darkFactors, extremeMetallic, externalImages, embeddedImages, webpImages, basisuImages;
        public int pngImages, jpegImages, missingUvMeshes, geometryMeshes, unsupportedExtensionCount;
        public String otherImageFormats="", unsupportedExtensions="";
        public boolean parseError;
        public String error="";
        public String headline(){
            if(parseError)return "Material inspection unavailable: "+error;
            return String.format(Locale.US,"%d materials · %d images (%d embedded) · %d base-color maps · %d very dark factors",
                    materials,images,embeddedImages,baseColorMaps,darkFactors);
        }
        public String detail(){
            StringBuilder b=new StringBuilder();
            b.append("SOURCE GLB MATERIAL REPORT\n\n").append(headline()).append("\n\n");
            b.append("Normal maps: ").append(normalMaps).append("\n");
            b.append("Emissive maps: ").append(emissiveMaps).append("\n");
            b.append("Metallic materials (factor ≥0.95): ").append(extremeMetallic).append("\n");
            b.append("External image URI references: ").append(externalImages).append("\n");
            b.append("PNG / JPEG images: ").append(pngImages).append(" / ").append(jpegImages).append("\n");
            b.append("WebP / KTX2(BasisU) images: ").append(webpImages).append(" / ").append(basisuImages).append("\n");
            b.append("Meshes with missing UV0 and textured materials: ").append(missingUvMeshes).append("\n");
            if(!unsupportedExtensions.isEmpty())b.append("Texture extensions: ").append(unsupportedExtensions).append("\n");
            b.append("\nINTERPRETATION\n");
            if(images==0)
                b.append("No image resources are declared. 'Materials' only means shader/parameter entries; the vehicle may have flat colors rather than textures.\n");
            else if(baseColorMaps==0)
                b.append("Image resources exist, but no material references a base-color texture. Their colors will not automatically become paint.\n");
            else
                b.append("Base-color textures are referenced. The decoder/GPU or the exported factors may still affect the result; images are not verified just by the JSON.\n");
            if(darkFactors>0)
                b.append(darkFactors).append(" base-color factors are near black. They multiply any base-color texture, so even a bright PNG can render black.\n");
            if(extremeMetallic>0)
                b.append("Highly metallic materials require useful image-based reflections. This is not proof of a renderer fault.\n");
            if(webpImages>0)
                b.append("WebP-encoded glTF textures can be unsupported by prebuilt Android gltfio. Consider PNG/JPEG textures.\n");
            if(basisuImages>0)
                b.append("KTX2/BasisU textures need compatible decoder support.\n");
            if(externalImages>0)
                b.append("External image URI references may be unavailable when opening a standalone GLB.\n");
            if(missingUvMeshes>0)
                b.append("Some textured mesh primitives lack TEXCOORD_0.\n");
            b.append("\nREVEAL DARK is a temporary inspection-only material-factor rescue. It does not permanently change this GLB or recreate missing textures.");
            return b.toString();
        }
    }

    static JSONObject json(byte[] original) throws Exception {
        if(original==null || original.length<20)throw new IllegalArgumentException("Incomplete GLB");
        ByteBuffer bb=ByteBuffer.wrap(original).order(ByteOrder.LITTLE_ENDIAN);
        if(bb.getInt(0)!=0x46546C67 || bb.getInt(4)!=2)
            throw new IllegalArgumentException("Not glTF binary v2");
        int size=bb.getInt(12),type=bb.getInt(16);
        if(type!=0x4E4F534A || size<2 || size>original.length-20)
            throw new IllegalArgumentException("GLB JSON chunk absent");
        return new JSONObject(new String(original,20,size,StandardCharsets.UTF_8).trim());
    }

    public static Report inspect(byte[] source) {
        Report r=new Report();
        try{
            JSONObject gltf=json(source);
            JSONArray mats=gltf.optJSONArray("materials");
            r.materials=mats==null?0:mats.length();
            JSONArray images=gltf.optJSONArray("images");
            r.images=images==null?0:images.length();
            if(images!=null)for(int i=0;i<images.length();i++){
                JSONObject img=images.optJSONObject(i);
                if(img==null)continue;
                if(img.has("bufferView"))r.embeddedImages++;
                if(img.has("uri"))r.externalImages++;
                String mime=img.optString("mimeType","").toLowerCase(Locale.ROOT);
                String uri=img.optString("uri","").toLowerCase(Locale.ROOT);
                if(mime.contains("png")||uri.endsWith(".png"))r.pngImages++;
                else if(mime.contains("jpeg")||uri.endsWith(".jpg")||uri.endsWith(".jpeg"))r.jpegImages++;
                else if(mime.contains("webp")||uri.endsWith(".webp"))r.webpImages++;
                else if(mime.contains("ktx2")||uri.endsWith(".ktx2"))r.basisuImages++;
            }
            if(mats!=null)for(int i=0;i<mats.length();i++){
                JSONObject mat=mats.optJSONObject(i);
                if(mat==null)continue;
                JSONObject pbr=mat.optJSONObject("pbrMetallicRoughness");
                if(pbr!=null){
                    if(pbr.has("baseColorTexture"))r.baseColorMaps++;
                    if(pbr.optDouble("metallicFactor",1.0)>=0.95)r.extremeMetallic++;
                    JSONArray color=pbr.optJSONArray("baseColorFactor");
                    if(color!=null&&color.length()>=3&&color.optDouble(0,1)<0.045
                            &&color.optDouble(1,1)<0.045&&color.optDouble(2,1)<0.045)
                        r.darkFactors++;
                }
                if(mat.has("normalTexture"))r.normalMaps++;
                if(mat.has("emissiveTexture"))r.emissiveMaps++;
            }
            JSONArray meshes=gltf.optJSONArray("meshes");
            r.geometryMeshes=meshes==null?0:meshes.length();
            if(meshes!=null)for(int i=0;i<meshes.length();i++){
                JSONArray primitives=meshes.getJSONObject(i).optJSONArray("primitives");
                if(primitives==null)continue;
                for(int j=0;j<primitives.length();j++){
                    JSONObject p=primitives.getJSONObject(j);
                    int m=p.optInt("material",-1);
                    if(m<0||mats==null||m>=mats.length())continue;
                    JSONObject pbr=mats.getJSONObject(m).optJSONObject("pbrMetallicRoughness");
                    JSONObject attributes=p.optJSONObject("attributes");
                    if(pbr!=null && pbr.has("baseColorTexture")
                            && (attributes==null || !attributes.has("TEXCOORD_0")))
                        r.missingUvMeshes++;
                }
            }
            JSONArray extensions=gltf.optJSONArray("extensionsUsed");
            if(extensions!=null){
                StringBuilder x=new StringBuilder();
                for(int i=0;i<extensions.length();i++){
                    String name=extensions.optString(i);
                    if(name.contains("texture")||name.contains("basisu")){
                        if(x.length()>0)x.append(", ");
                        x.append(name);
                        if("KHR_texture_basisu".equals(name) && r.basisuImages==0)r.basisuImages=1;
                    }
                }
                r.unsupportedExtensions=x.toString();
            }
        }catch(Exception ex){r.parseError=true;r.error=ex.getMessage();}
        return r;
    }
}
