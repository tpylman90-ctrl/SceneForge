package com.sceneforge.glbinspector;

import android.content.Context;
import android.graphics.Color;
import android.opengl.Matrix;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import com.google.android.filament.Box;
import com.google.android.filament.Camera;
import com.google.android.filament.Engine;
import com.google.android.filament.Material;
import com.google.android.filament.MaterialInstance;
import com.google.android.filament.RenderableManager;
import com.google.android.filament.TransformManager;
import com.google.android.filament.View;
import com.google.android.filament.gltfio.FilamentAsset;
import com.google.android.filament.utils.ModelViewer;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Native Filament entity picking and non-destructive per-renderable inspection.
 * Source GLB and material bytes are never modified. A picked entity is a genuine
 * glTF renderable, and hit positions are reconstructed from actual depth readback.
 */
public final class PartInspector {
    public interface PickListener {
        void onPicked(Hit hit);
    }
    public static final class Hit {
        public int entity, index, primitiveCount;
        public String name;
        public float u,v;
        public double[] world = new double[3];
        public float depth;
        public float[] dimensions = new float[3];
        public String summary() {
            return String.format(Locale.US,"%s • %d primitives • size %.3f × %.3f × %.3f GLB units",
                    name,primitiveCount,dimensions[0],dimensions[1],dimensions[2]);
        }
    }
    private static final String TAG="SCENEFORGE_INSPECT";
    private final Context context;
    private final ModelViewer viewer;
    private final Engine engine;
    private final RenderableManager renderables;
    private final TransformManager transforms;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final Map<Integer,MaterialInstance[]> originalMaterials=new HashMap<>();
    private final Map<Integer,Integer> originalLayers=new HashMap<>();
    private final Map<Integer,float[]> originalLocalTransforms=new HashMap<>();
    private int[] entities=new int[0];
    private Material selectedMaterial, zebraMaterial;
    private MaterialInstance highlightInstance, zebraInstance;
    private int selectedEntity=0, generation=0;
    private boolean zebra, solo, exploded;
    private float explodedAmount=0f;
    private float sourceScale=1f;

    public PartInspector(Context context,ModelViewer viewer) {
        this.context=context;this.viewer=viewer;
        engine=viewer.getEngine();
        renderables=engine.getRenderableManager();
        transforms=engine.getTransformManager();
    }

    private Material loadMaterial(String filename) {
        try(InputStream input=context.getAssets().open("materials/"+filename);
            ByteArrayOutputStream bytes=new ByteArrayOutputStream()){
            byte[] block=new byte[16384];int n;
            while((n=input.read(block))!=-1)bytes.write(block,0,n);
            byte[] content=bytes.toByteArray();
            ByteBuffer direct=ByteBuffer.allocateDirect(content.length).order(ByteOrder.nativeOrder());
            direct.put(content).flip();
            return new Material.Builder().payload(direct,content.length).build(engine);
        }catch(Exception ex){
            Log.e(TAG,"Failed to load inspection shader "+filename,ex);
            return null;
        }
    }
    public void onNewModel() {
        generation++;
        selectedEntity=0;zebra=false;solo=false;exploded=false;explodedAmount=0;
        originalMaterials.clear();originalLayers.clear();originalLocalTransforms.clear();
        FilamentAsset asset=viewer.getAsset();
        if(asset==null){entities=new int[0];return;}
        entities=asset.getRenderableEntities();
        Box box=asset.getBoundingBox();
        float[] half=box.getHalfExtent();
        sourceScale=Math.max(0.001f,Math.max(half[0],Math.max(half[1],half[2])));
        // ModelViewer uses scale=1 / maxHalfExtent, hence 1 normalized world
        // unit corresponds to maxHalfExtent original glTF units.
        for(int entity:entities){
            int ri=renderables.getInstance(entity);
            if(ri==0)continue;
            int count=renderables.getPrimitiveCount(ri);
            MaterialInstance[] original=new MaterialInstance[count];
            for(int p=0;p<count;p++)original[p]=renderables.getMaterialInstanceAt(ri,p);
            originalMaterials.put(entity,original);
            originalLayers.put(entity,renderables.getLayerMask(ri));
            int ti=transforms.getInstance(entity);
            if(ti!=0)originalLocalTransforms.put(entity,transforms.getTransform(ti,null).clone());
        }
        Log.i(TAG,"PARTS_READY "+entities.length+" scale="+sourceScale);
    }
    public int entityCount(){return entities.length;}
    public String selectedName(){
        if(selectedEntity==0)return "No selected part";
        FilamentAsset a=viewer.getAsset();
        if(a==null)return "No selected part";
        String name=a.getName(selectedEntity);
        return name==null||name.trim().isEmpty()?"Entity "+selectedEntity:name;
    }
    public int selectedEntity(){return selectedEntity;}
    private boolean valid(int e){return originalMaterials.containsKey(e);}
    public void pick(float x,float y,int w,int h,PickListener listener){
        if(w<=0||h<=0){listener.onPicked(null);return;}
        Camera cam=viewer.getCamera();
        // Capture matrices at request time, not at async callback time.
        double[] cameraModel=cam.getModelMatrix(null);
        double[] projection=cam.getProjectionMatrix(null);
        int requestedGeneration=generation;
        final int fx=Math.max(0,Math.min(w-1,(int)x));
        final int fy=Math.max(0,Math.min(h-1,(int)(h-y)));
        viewer.getView().pick(fx,fy,main,result->{
            if(generation!=requestedGeneration)return;
            if(result.renderable==0||!valid(result.renderable)){
                listener.onPicked(null);return;
            }
            Hit hit=new Hit();
            hit.entity=result.renderable;
            hit.u=Math.max(0,Math.min(1,x/w));
            hit.v=Math.max(0,Math.min(1,y/h));
            hit.depth=result.depth;
            for(int i=0;i<entities.length;i++)if(entities[i]==hit.entity){hit.index=i;break;}
            FilamentAsset asset=viewer.getAsset();
            hit.name=asset.getName(hit.entity);
            if(hit.name==null||hit.name.isEmpty())hit.name="Part "+(hit.index+1);
            int ri=renderables.getInstance(hit.entity);
            hit.primitiveCount=renderables.getPrimitiveCount(ri);
            float[] ext=renderables.getAxisAlignedBoundingBox(ri).getHalfExtent();
            for(int i=0;i<3;i++)hit.dimensions[i]=ext[i]*2f; // local glTF units
            double[] world=unproject(result.fragCoords,w,h,projection,cameraModel);
            if(world!=null)hit.world=world;
            listener.onPicked(hit);
        });
    }
    /** Reversed-Z Filament NDC reconstructed using the actual GPU depth / camera matrices. */
    public static double[] unproject(float[] frag,int width,int height,double[] projection,double[] cameraModel){
        if(frag==null||frag.length<3)return null;
        float[] p=new float[16],inv=new float[16];
        for(int i=0;i<16;i++)p[i]=(float)projection[i];
        if(!Matrix.invertM(inv,0,p,0))return null;
        double[] clip={2.0*frag[0]/Math.max(1,width)-1,
                2.0*frag[1]/Math.max(1,height)-1,2.0*frag[2]-1,1};
        double[] view=new double[4];
        for(int r=0;r<4;r++)for(int c=0;c<4;c++)view[r]+=inv[c*4+r]*clip[c];
        if(Math.abs(view[3])<1e-10)return null;
        for(int i=0;i<3;i++)view[i]/=view[3];
        double[] world=new double[3];
        for(int r=0;r<3;r++){
            world[r]=cameraModel[12+r];
            for(int c=0;c<3;c++)world[r]+=cameraModel[c*4+r]*view[c];
        }
        return world;
    }
    public void select(Hit hit){
        selectedEntity=(hit==null?0:hit.entity);
        applyMaterials();
    }
    private void ensureMaterials(){
        if(selectedMaterial==null){
            selectedMaterial=loadMaterial("selection.filamat");
            if(selectedMaterial!=null)highlightInstance=selectedMaterial.createInstance();
        }
        if(zebraMaterial==null){
            zebraMaterial=loadMaterial("zebra.filamat");
            if(zebraMaterial!=null){
                zebraInstance=zebraMaterial.createInstance();
                zebraInstance.setParameter("frequency",17.0f);
            }
        }
    }
    public boolean zebraEnabled(){return zebra;}
    public void toggleZebra(){
        zebra=!zebra;
        applyMaterials();
    }
    public void adjustZebraFrequency(float frequency) {
        ensureMaterials();
        if(zebraInstance!=null)zebraInstance.setParameter("frequency",frequency);
    }
    private void applyMaterials(){
        ensureMaterials();
        for(int entity:entities){
            int ri=renderables.getInstance(entity);
            if(ri==0)continue;
            MaterialInstance[] source=originalMaterials.get(entity);
            if(source==null)continue;
            boolean isFloor=false;
            FilamentAsset a=viewer.getAsset();
            if(a!=null){
                String n=a.getName(entity);
                isFloor=n!=null && n.toLowerCase(Locale.ROOT).contains("studiofloor");
            }
            for(int i=0;i<source.length;i++){
                MaterialInstance use=source[i];
                if(zebra&&!isFloor&&zebraInstance!=null)use=zebraInstance;
                if(entity==selectedEntity&&highlightInstance!=null)use=highlightInstance;
                if(use!=null)renderables.setMaterialInstanceAt(ri,i,use);
            }
        }
    }
    public void hideSelection(){
        if(selectedEntity==0)return;
        int ri=renderables.getInstance(selectedEntity);
        if(ri!=0)renderables.setLayerMask(ri,0x01,0);
        selectedEntity=0;applyMaterials();
    }
    public void toggleSolo(){
        if(selectedEntity==0 && !solo)return;
        solo=!solo;
        for(int entity:entities){
            int ri=renderables.getInstance(entity);
            if(ri==0)continue;
            if(solo && entity!=selectedEntity){
                String name=viewer.getAsset().getName(entity);
                if(name!=null && name.toLowerCase(Locale.ROOT).contains("studiofloor"))continue;
                renderables.setLayerMask(ri,0x01,0);
            }else {
                Integer original=originalLayers.get(entity);
                if(original!=null)renderables.setLayerMask(ri,0xFF,original);
            }
        }
    }
    public void showAll(){
        solo=false;selectedEntity=0;
        for(int entity:entities){
            int ri=renderables.getInstance(entity);
            if(ri==0)continue;
            Integer original=originalLayers.get(entity);
            if(original!=null)renderables.setLayerMask(ri,0xFF,original);
        }
        explode(0f);
        applyMaterials();
    }
    public boolean exploded(){return exploded;}
    public void explode(float amount){
        explodedAmount=Math.max(0,Math.min(1,amount));exploded=explodedAmount>0.001f;
        if(entities.length==0)return;
        // This is a view-only temporary assembly separation, not a destructive edit.
        float centerX=0f,centerY=0f,centerZ=0f;
        int count=0;
        Map<Integer,float[]> centers=new HashMap<>();
        for(int entity:entities){
            int ri=renderables.getInstance(entity),ti=transforms.getInstance(entity);
            if(ri==0||ti==0)continue;
            String name=viewer.getAsset().getName(entity);
            if(name!=null&&name.toLowerCase(Locale.ROOT).contains("studiofloor"))continue;
            float[] world=transforms.getWorldTransform(ti,null);
            float[] local=renderables.getAxisAlignedBoundingBox(ri).getCenter();
            float x=world[0]*local[0]+world[4]*local[1]+world[8]*local[2]+world[12];
            float y=world[1]*local[0]+world[5]*local[1]+world[9]*local[2]+world[13];
            float z=world[2]*local[0]+world[6]*local[1]+world[10]*local[2]+world[14];
            centers.put(entity,new float[]{x,y,z});
            centerX+=x;centerY+=y;centerZ+=z;count++;
        }
        if(count==0)return;
        centerX/=count;centerY/=count;centerZ/=count;
        transforms.openLocalTransformTransaction();
        try {
            for(int entity:entities){
                int ti=transforms.getInstance(entity);
                float[] original=originalLocalTransforms.get(entity);
                if(ti==0||original==null)continue;
                float[] current=original.clone();
                float[] center=centers.get(entity);
                if(center!=null&&exploded){
                    float dx=center[0]-centerX,dy=center[1]-centerY,dz=center[2]-centerZ;
                    float norm=(float)Math.sqrt(dx*dx+dy*dy+dz*dz);
                    if(norm<0.02f){ // deterministic separation for assemblies centered on same origin
                        dx=(entity%5)-2;dy=((entity/5)%5)-2;dz=((entity/25)%5)-2;
                        norm=(float)Math.sqrt(dx*dx+dy*dy+dz*dz);
                    }
                    float scalar=0.9f*explodedAmount/Math.max(norm,0.01f);
                    current[12]+=dx*scalar;
                    current[13]+=dy*scalar;
                    current[14]+=dz*scalar;
                }
                transforms.setTransform(ti,current);
            }
        }finally{transforms.commitLocalTransformTransaction();}
    }
    public float unitsPerNormalizedWorld(){return sourceScale;}
    public static double distanceInGlbUnits(Hit a,Hit b,float sourceScale){
        if(a==null||b==null||a.world==null||b.world==null)return Double.NaN;
        double dx=a.world[0]-b.world[0],dy=a.world[1]-b.world[1],dz=a.world[2]-b.world[2];
        return Math.sqrt(dx*dx+dy*dy+dz*dz)*sourceScale;
    }
    public void destroy(){
        // Restore imported material bindings before releasing our custom materials.
        if(viewer.getAsset()!=null)showAll();
        if(highlightInstance!=null)engine.destroyMaterialInstance(highlightInstance);
        if(zebraInstance!=null)engine.destroyMaterialInstance(zebraInstance);
        if(selectedMaterial!=null)engine.destroyMaterial(selectedMaterial);
        if(zebraMaterial!=null)engine.destroyMaterial(zebraMaterial);
    }
}
