package com.sceneforge.glbinspector;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.View;

import org.json.JSONArray;
import org.json.JSONObject;

import java.security.MessageDigest;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/**
 * Local, offline revision feedback with explicit camera-snapshot viewport anchors.
 *
 * IMPORTANT: v1 anchors are 2D screen coordinates at the recorded camera pose, not raycast
 * world-space positions; their JSON makes that distinction explicit for consuming AI systems.
 */
public final class FeedbackStore {
    private static final String PREFS="sceneforge_feedback_v1";
    public static final String[] TYPES={
            "Silhouette", "Body-panel transition", "Proportion", "Topology",
            "Alignment", "Surface continuity", "Material / texture", "Missing detail", "Other"
    };
    public static final String[] SEVERITIES={"Low","Medium","High","Critical"};

    public static final class Note {
        public String id, modelName, modelSha256, issueType, severity, description, mode;
        public int pane;
        public float u,v,azimuth,elevation,distance;
        public boolean orthographic;
        public long createdUtcMillis;

        public JSONObject toJson() throws Exception {
            JSONObject o=new JSONObject();
            o.put("id",id);
            o.put("target",new JSONObject()
                    .put("pane",pane==0?"A":"B")
                    .put("glb_filename",modelName)
                    .put("sha256",modelSha256));
            o.put("issue_type",issueType);
            o.put("severity",severity);
            o.put("description",description);
            o.put("created_utc",utc(createdUtcMillis));
            o.put("inspection_mode",mode);
            o.put("anchor",new JSONObject()
                    .put("type","view_snapshot_normalized")
                    .put("units","relative_to_model_viewport")
                    .put("x",round(u))
                    .put("y",round(v))
                    .put("world_position",JSONObject.NULL)
                    .put("is_surface_raycast",false)
                    .put("camera",new JSONObject()
                            .put("azimuth_degrees",round(azimuth))
                            .put("elevation_degrees",round(elevation))
                            .put("orbit_distance",round(distance))
                            .put("projection",orthographic?"orthographic":"perspective")));
            return o;
        }
        public static Note fromJson(JSONObject o) {
            try {
                Note n=new Note();
                n.id=o.getString("id");
                JSONObject target=o.getJSONObject("target");
                n.pane="B".equals(target.optString("pane"))?1:0;
                n.modelName=target.optString("glb_filename");
                n.modelSha256=target.optString("sha256");
                n.issueType=o.optString("issue_type");
                n.severity=o.optString("severity");
                n.description=o.optString("description");
                n.createdUtcMillis=System.currentTimeMillis();
                n.mode=o.optString("inspection_mode","TEXTURED");
                JSONObject anchor=o.getJSONObject("anchor");
                n.u=(float)anchor.getDouble("x");
                n.v=(float)anchor.getDouble("y");
                JSONObject camera=anchor.getJSONObject("camera");
                n.azimuth=(float)camera.getDouble("azimuth_degrees");
                n.elevation=(float)camera.getDouble("elevation_degrees");
                n.distance=(float)camera.getDouble("orbit_distance");
                n.orthographic="orthographic".equals(camera.getString("projection"));
                return n;
            } catch(Exception ignored) {return null;}
        }
    }

    private final SharedPreferences prefs;
    private final List<Note> notes=new ArrayList<>();

    public FeedbackStore(Context context) {
        prefs=context.getSharedPreferences(PREFS,Context.MODE_PRIVATE);
        try {
            JSONArray array=new JSONArray(prefs.getString("annotations","[]"));
            for(int i=0;i<array.length();i++){
                Note note=Note.fromJson(array.getJSONObject(i));
                if(note!=null)notes.add(note);
            }
        }catch(Exception ignored){}
    }

    public static String sha256(byte[] input) {
        try{
            byte[] digest=MessageDigest.getInstance("SHA-256").digest(input);
            StringBuilder sb=new StringBuilder(64);
            for(byte b:digest)sb.append(String.format(Locale.US,"%02x",b&255));
            return sb.toString();
        }catch(Exception ex){return "unavailable";}
    }
    private static String utc(long millis) {
        return new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'",Locale.US)
                {{setTimeZone(java.util.TimeZone.getTimeZone("UTC"));}}.format(new Date(millis));
    }
    private static double round(float f) {return Math.round(f*100000d)/100000d;}

    public List<Note> all() {return new ArrayList<>(notes);}
    public List<Note> forModel(String sha256) {
        List<Note> selected=new ArrayList<>();
        if(sha256==null || sha256.isEmpty())return selected;
        for(Note n:notes)if(sha256.equals(n.modelSha256))selected.add(n);
        return selected;
    }
    public int countFor(String leftHash, String rightHash) {
        int count=0;
        for(Note n:notes)if(n.modelSha256.equals(leftHash)||n.modelSha256.equals(rightHash))count++;
        return count;
    }
    public void add(Note n){notes.add(n);save();}
    public void remove(Note n){notes.remove(n);save();}
    public void save(){
        JSONArray out=new JSONArray();
        for(Note n:notes){
            try{out.put(n.toJson());}catch(Exception ignored){}
        }
        prefs.edit().putString("annotations",out.toString()).apply();
    }

    public JSONObject export(String modelA, String hashA, String modelB, String hashB,
                             String referencePhotoName, boolean synched,
                             String viewMode) throws Exception {
        JSONObject result=new JSONObject();
        result.put("schema","sceneforge.model-feedback/v1");
        result.put("exported_at_utc",utc(System.currentTimeMillis()));
        result.put("software","SceneForge GLB Inspector Android");
        result.put("coordinate_convention",
                "Viewport x/y are normalized [0,1], origin at top-left; captured camera pose required.");
        result.put("anchor_limitations",
                "Screen-view annotations, not 3D raycast surface points. Restore camera before applying corrections.");
        result.put("pair",new JSONObject()
                .put("A",new JSONObject().put("filename",modelA==null?"":modelA)
                        .put("sha256",hashA==null?"":hashA))
                .put("B",new JSONObject().put("filename",modelB==null?"":modelB)
                        .put("sha256",hashB==null?"":hashB)));
        result.put("comparison",new JSONObject()
                .put("synchronized_cameras",synched)
                .put("display_mode",viewMode)
                .put("reference_photo_filename",referencePhotoName==null?"":referencePhotoName));
        JSONArray issues=new JSONArray();
        for(Note n:notes){
            if(n.modelSha256.equals(hashA)||n.modelSha256.equals(hashB))issues.put(n.toJson());
        }
        result.put("issues",issues);
        result.put("instructions_for_ai",
                "Use each issue's description, severity, target GLB SHA-256 and recorded camera pose. " +
                "Match any attached A/B PNG to the normalized viewport anchor. " +
                "Inspect and change model geometry only after confirming the defect; do not treat anchors as 3D vertex positions.");
        return result;
    }

    /** The pin overlay draws visible markers only when the saved viewpoint is restored. */
    public static final class MarkerOverlay extends View {
        private final Paint paint=new Paint(3);
        private final FeedbackStore store;
        private final int paneIndex;
        private String activeHash;
        private float azimuth,elevation,distance;
        private boolean orthographic;
        private final float density;

        public MarkerOverlay(Context c,FeedbackStore s,int pane){
            super(c);
            store=s;paneIndex=pane;density=getResources().getDisplayMetrics().density;
            setWillNotDraw(false);
            setClickable(false);
        }
        public void update(String hash,float a,float e,float d,boolean ortho) {
            activeHash=hash;azimuth=a;elevation=e;distance=d;orthographic=ortho;
            invalidate();
        }
        public List<Note> visibleNotes(){
            List<Note> visible=new ArrayList<>();
            if(activeHash==null || activeHash.isEmpty())return visible;
            for(Note n:store.notes) {
                if(n.pane!=paneIndex || !activeHash.equals(n.modelSha256))continue;
                if(n.orthographic!=orthographic)continue;
                float angle=((n.azimuth-azimuth+540f)%360f)-180f;
                if(Math.abs(angle)>3f||Math.abs(n.elevation-elevation)>3f
                        ||Math.abs(n.distance-distance)>0.16f)continue;
                visible.add(n);
            }
            return visible;
        }
        @Override protected void onDraw(Canvas c) {
            super.onDraw(c);
            for(Note n:visibleNotes()) {
                float x=n.u*getWidth(),y=n.v*getHeight();
                paint.setStyle(Paint.Style.FILL);
                paint.setColor(Color.rgb(11,26,35));
                c.drawCircle(x,y,12*density,paint);
                paint.setStyle(Paint.Style.STROKE);
                paint.setStrokeWidth(2*density);
                paint.setColor(Color.rgb(32,224,206));
                c.drawCircle(x,y,12*density,paint);
                paint.setStyle(Paint.Style.FILL);
                paint.setColor(Color.WHITE);
                paint.setTextAlign(Paint.Align.CENTER);
                paint.setTypeface(TypefaceHolder.BOLD);
                paint.setTextSize(12*density);
                c.drawText(String.valueOf(store.notes.indexOf(n)+1),x,y+4*density,paint);
            }
        }
        public void drawOnExport(Canvas c,int width,int height) {
            float scale=height/Math.max(1f,getHeight());
            for(Note n:visibleNotes()){
                float x=n.u*width,y=n.v*height;
                paint.setColor(Color.rgb(13,43,49));paint.setStyle(Paint.Style.FILL);
                c.drawCircle(x,y,11*density*scale,paint);
                paint.setColor(Color.CYAN);paint.setStyle(Paint.Style.STROKE);
                paint.setStrokeWidth(2*density*scale);c.drawCircle(x,y,11*density*scale,paint);
                paint.setStyle(Paint.Style.FILL);
                paint.setTextSize(12*density*scale);paint.setTextAlign(Paint.Align.CENTER);
                paint.setColor(Color.WHITE);
                c.drawText(String.valueOf(store.notes.indexOf(n)+1),x,y+4*density*scale,paint);
            }
        }
    }
    private static final class TypefaceHolder {
        static final android.graphics.Typeface BOLD=android.graphics.Typeface.DEFAULT_BOLD;
    }
}
