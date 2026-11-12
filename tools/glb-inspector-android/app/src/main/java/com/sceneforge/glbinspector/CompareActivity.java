package com.sceneforge.glbinspector;

import android.app.Activity;
import android.content.ContentValues;
import android.content.Intent;
import android.content.res.Configuration;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.ArrayAdapter;
import android.app.AlertDialog;
import org.json.JSONObject;
import java.nio.charset.StandardCharsets;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.provider.MediaStore;
import android.provider.OpenableColumns;
import android.view.Choreographer;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.PixelCopy;
import android.view.ScaleGestureDetector;
import android.view.SurfaceView;
import android.view.View;
import android.view.WindowInsets;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import com.google.android.filament.Engine;
import com.google.android.filament.EntityManager;
import com.google.android.filament.IndirectLight;
import com.google.android.filament.LightManager;
import com.google.android.filament.Skybox;
import com.google.android.filament.Texture;
import com.google.android.filament.android.UiHelper;
import com.google.android.filament.gltfio.Gltfio;
import com.google.android.filament.utils.Float3;
import com.google.android.filament.utils.ModelViewer;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/**
 * Genuine simultaneous native GLB A/B comparison. Uses separate Filament engines and
 * SurfaceViews; no web views and no screenshot-for-the-second-model tricks.
 * Models are normalized independently, while camera controls can be synchronized.
 */
public final class CompareActivity extends Activity implements Choreographer.FrameCallback {
    private static final int BG=Color.rgb(11,16,25);
    private static final int PANEL=Color.rgb(26,37,54);
    private static final int TEXT=Color.rgb(228,236,245);
    private static final int MUTED=Color.rgb(166,181,198);
    private static final int ACCENT=Color.rgb(29,186,180);
    private static final int PICK_A=8121, PICK_B=8122, PICK_PHOTO=8123, EXPORT_JSON=8124;

    private final Handler handler=new Handler(Looper.getMainLooper());
    private final Pane[] panes=new Pane[2];
    private LinearLayout viewportRow;
    private FrameLayout viewportContainer;
    private ReferenceWindow referenceWindow;
    private FeedbackStore feedback;
    private boolean marking=false;
    private Button markButton, issueButton;
    private String pendingFeedbackExport = "";
    private TextView message;
    private Button syncButton, projectionButton;
    private boolean sync=true, orthographic=true, running=false;
    private GlbInspectionVariants.Mode mode=GlbInspectionVariants.Mode.TEXTURED;
    private final Button[] modeButtons=new Button[3];
    private boolean preparing=false;
    private long modeRevision=0;
    private int snapshotNumber=0;
    private int frameCounter=0;

    private static final class Pane {
        int index;
        SurfaceView surface;
        FrameLayout frame;
        TextView caption;
        FeedbackStore.MarkerOverlay markers;
        String hash = "";
        float downX, downY;
        ModelViewer viewer;
        ByteBuffer currentDirect;
        byte[] original;
        String name;
        long request=0;
        float azimuth=90, elevation=9, distance=4.1f;
        float lastX,lastY;
        boolean pinching=false;
        ScaleGestureDetector scale;
        IndirectLight ibl;
        Texture reflections;
        Skybox sky;
        int[] fillLights=new int[2];
    }

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        Gltfio.init();
        feedback=new FeedbackStore(this);
        buildUi();
        for(int i=0;i<2;i++) createRenderer(panes[i]);
        updateCameras();
        if(getIntent().getBooleanExtra("sceneforge_verify_compare",false)) {
            handler.postDelayed(this::verifyComparisonInEmulator,1600);
        }
    }

    private int dp(float dp){return (int)(dp*getResources().getDisplayMetrics().density+0.5f);}
    private Button button(String text){
        Button b=new Button(this);
        b.setAllCaps(false);
        b.setText(text);b.setTextSize(12);
        b.setTextColor(TEXT);
        b.setBackgroundTintList(android.content.res.ColorStateList.valueOf(PANEL));
        return b;
    }
    private void buildUi(){
        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(BG);
        setContentView(root);
        root.setOnApplyWindowInsetsListener((v,insets)->{
            if(Build.VERSION.SDK_INT>=30){
                android.graphics.Insets i=insets.getInsets(WindowInsets.Type.systemBars());
                v.setPadding(i.left,i.top,i.right,i.bottom);
            }else{
                v.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),
                        insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            }
            return insets;
        });
        root.requestApplyInsets();

        LinearLayout toolbar=new LinearLayout(this);
        toolbar.setGravity(Gravity.CENTER_VERTICAL);toolbar.setPadding(dp(8),dp(5),dp(8),dp(2));
        Button back=button("BACK");back.setOnClickListener(v->finish());
        toolbar.addView(back,new LinearLayout.LayoutParams(dp(74),dp(43)));
        TextView title=new TextView(this);title.setText("3D MODEL  •  A/B COMPARE");
        title.setTextSize(15);title.setTextColor(TEXT);
        LinearLayout.LayoutParams t=new LinearLayout.LayoutParams(0,dp(43),1f);
        t.leftMargin=dp(8);toolbar.addView(title,t);
        syncButton=button("SYNC ON");
        syncButton.setOnClickListener(v->{
            sync=!sync;
            syncButton.setText(sync?"SYNC ON":"SYNC OFF");
            syncButton.setBackgroundTintList(android.content.res.ColorStateList.valueOf(sync?ACCENT:PANEL));
            syncButton.setTextColor(sync?BG:TEXT);
            if(sync){copyAngles(panes[0],panes[1]);updateCameras();}
        });
        toolbar.addView(syncButton,new LinearLayout.LayoutParams(dp(91),dp(43)));
        root.addView(toolbar);
        syncButton.setBackgroundTintList(android.content.res.ColorStateList.valueOf(ACCENT));syncButton.setTextColor(BG);

        LinearLayout load=new LinearLayout(this);load.setPadding(dp(8),0,dp(8),dp(4));
        Button a=button("OPEN LEFT GLB"); a.setOnClickListener(v->choose(PICK_A));
        Button b=button("OPEN RIGHT GLB"); b.setOnClickListener(v->choose(PICK_B));
        load.addView(a,new LinearLayout.LayoutParams(0,dp(43),1f));
        LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(0,dp(43),1f);bp.leftMargin=dp(8);
        load.addView(b,bp);root.addView(load);

        message=new TextView(this);
        message.setText("Two live GLBs • synced orbit/zoom • rotate phone for side-by-side");
        message.setTextSize(12);message.setTextColor(MUTED);message.setPadding(dp(12),0,dp(10),dp(6));
        root.addView(message);

        viewportRow=new LinearLayout(this);
        viewportRow.setBackgroundColor(Color.rgb(21,24,28));
        boolean wide=getResources().getConfiguration().orientation==Configuration.ORIENTATION_LANDSCAPE;
        viewportRow.setOrientation(wide?LinearLayout.HORIZONTAL:LinearLayout.VERTICAL);
        for(int i=0;i<2;i++){
            Pane p=new Pane();p.index=i;p.name=i==0?"LEFT MODEL":"RIGHT MODEL";
            p.frame=new FrameLayout(this);
            p.frame.setBackgroundColor(Color.rgb(26,30,36));
            p.surface=new SurfaceView(this);
            p.frame.addView(p.surface,new FrameLayout.LayoutParams(-1,-1));
            p.caption=new TextView(this);p.caption.setText((i==0?"A":"B")+"   •   "+p.name);
            p.caption.setTextSize(12);p.caption.setTextColor(TEXT);
            p.caption.setBackgroundColor(0xb2081017);
            p.caption.setPadding(dp(9),dp(5),dp(9),dp(5));
            FrameLayout.LayoutParams cp=new FrameLayout.LayoutParams(-2,-2,Gravity.TOP|Gravity.LEFT);
            cp.setMargins(dp(8),dp(8),0,0);p.frame.addView(p.caption,cp);
            p.markers=new FeedbackStore.MarkerOverlay(this,feedback,i);
            p.frame.addView(p.markers,new FrameLayout.LayoutParams(-1,-1));
            p.caption.bringToFront();
            panes[i]=p;
            LinearLayout.LayoutParams fp=wide?
                    new LinearLayout.LayoutParams(0,-1,1f):
                    new LinearLayout.LayoutParams(-1,0,1f);
            if(i==1){if(wide)fp.leftMargin=dp(3);else fp.topMargin=dp(3);}
            viewportRow.addView(p.frame,fp);
        }
        viewportContainer=new FrameLayout(this);
        viewportContainer.addView(viewportRow,new FrameLayout.LayoutParams(-1,-1));
        referenceWindow=new ReferenceWindow(this,()->choosePhoto());
        viewportContainer.addView(referenceWindow,new FrameLayout.LayoutParams(dp(270),dp(188),
                Gravity.TOP | Gravity.LEFT));
        viewportContainer.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,oright,ob)->{
            if(r-l!=oright-ol || b-t!=ob-ot) referenceWindow.post(referenceWindow::restorePosition);
        });
        root.addView(viewportContainer,new LinearLayout.LayoutParams(-1,0,1f));
        referenceWindow.post(referenceWindow::restorePosition);

        HorizontalScrollView cameraScroll=new HorizontalScrollView(this);
        cameraScroll.setHorizontalScrollBarEnabled(false);
        LinearLayout cams=new LinearLayout(this);cams.setPadding(dp(8),dp(5),dp(8),dp(5));
        addPreset(cams,"SIDE",90,0);
        addPreset(cams,"ISO",33,18);
        addPreset(cams,"FRONT",180,0);
        addPreset(cams,"REAR",0,0);
        addPreset(cams,"TOP",0,89);
        addPreset(cams,"LEFT",-90,0);
        addPreset(cams,"RIGHT",90,0);
        cameraScroll.addView(cams);root.addView(cameraScroll);

        LinearLayout bottom=new LinearLayout(this);bottom.setPadding(dp(7),0,dp(7),dp(4));
        addMode(bottom,"PAINT",GlbInspectionVariants.Mode.TEXTURED,0);
        addMode(bottom,"CLAY",GlbInspectionVariants.Mode.CLAY,1);
        addMode(bottom,"WIRE",GlbInspectionVariants.Mode.WIREFRAME,2);
        projectionButton=button("ORTHO");
        projectionButton.setOnClickListener(v->{orthographic=!orthographic;projectionButton.setText(orthographic?"ORTHO":"3D");updateCameras();});
        LinearLayout.LayoutParams proj=new LinearLayout.LayoutParams(0,dp(42),0.8f);
        proj.leftMargin=dp(4);bottom.addView(projectionButton,proj);
        root.addView(bottom);

        HorizontalScrollView feedbackScroll=new HorizontalScrollView(this);
        feedbackScroll.setHorizontalScrollBarEnabled(false);
        LinearLayout feedbackRow=new LinearLayout(this);
        feedbackRow.setPadding(dp(7),dp(1),dp(7),dp(2));
        Button photoButton=button("REF PHOTO");
        photoButton.setOnClickListener(v->referenceWindow.showPanel());
        feedbackRow.addView(photoButton,new LinearLayout.LayoutParams(dp(105),dp(38)));
        markButton=button("MARK PANEL");
        markButton.setOnClickListener(v->{
            marking=!marking;
            syncMarkButton();
            message.setText(marking ? "Tap a body panel in A or B to describe a defect." :
                    "Orbit mode • drag to rotate, pinch to zoom.");
        });
        LinearLayout.LayoutParams markP=new LinearLayout.LayoutParams(dp(113),dp(38));
        markP.leftMargin=dp(5);feedbackRow.addView(markButton,markP);
        issueButton=button("ISSUES 0");
        issueButton.setOnClickListener(v->showIssues());
        LinearLayout.LayoutParams issueP=new LinearLayout.LayoutParams(dp(105),dp(38));
        issueP.leftMargin=dp(5);feedbackRow.addView(issueButton,issueP);
        Button exportButton=button("EXPORT JSON");
        exportButton.setOnClickListener(v->exportFeedback());
        LinearLayout.LayoutParams exportP=new LinearLayout.LayoutParams(dp(116),dp(38));
        exportP.leftMargin=dp(5);feedbackRow.addView(exportButton,exportP);
        feedbackScroll.addView(feedbackRow);
        root.addView(feedbackScroll);
        syncMarkButton();

        LinearLayout actions=new LinearLayout(this);actions.setPadding(dp(8),0,dp(8),dp(7));
        Button png=button("SAVE A/B PNG");png.setOnClickListener(v->captureBoth());
        Button reset=button("RESET VIEWS");reset.setOnClickListener(v->{
            for(Pane p:panes){p.azimuth=90;p.elevation=9;p.distance=4.1f;}updateCameras();
        });
        actions.addView(png,new LinearLayout.LayoutParams(0,dp(43),1f));
        LinearLayout.LayoutParams resetP=new LinearLayout.LayoutParams(0,dp(43),1f);
        resetP.leftMargin=dp(7);actions.addView(reset,resetP);
        root.addView(actions);
        syncModeButtons();
        updateIssueCount();
    }

    private void syncMarkButton() {
        if(markButton==null)return;
        markButton.setText(marking ? "TAP TO MARK" : "MARK PANEL");
        markButton.setBackgroundTintList(android.content.res.ColorStateList.valueOf(marking?ACCENT:PANEL));
        markButton.setTextColor(marking?BG:TEXT);
    }
    private void updateIssueCount() {
        if(issueButton!=null && panes[0]!=null && panes[1]!=null)
            issueButton.setText("ISSUES "+feedback.countFor(panes[0].hash,panes[1].hash));
        for(Pane p:panes)if(p!=null&&p.markers!=null)p.markers.invalidate();
    }

    private void addPreset(LinearLayout row,String label,float az,float el) {
        Button b=button(label);
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(dp(79),dp(42));p.rightMargin=dp(4);
        row.addView(b,p);
        b.setOnClickListener(v->{
            for(Pane pane:panes){pane.azimuth=az;pane.elevation=el;pane.distance=4.1f;}
            updateCameras();
        });
    }
    private void addMode(LinearLayout row,String label,GlbInspectionVariants.Mode m,int index){
        Button b=button(label);modeButtons[index]=b;
        LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(0,dp(42),1f);
        if(index>0)params.leftMargin=dp(4);row.addView(b,params);
        b.setOnClickListener(v->selectMode(m));
    }
    private void syncModeButtons(){
        for(int i=0;i<3;i++){
            if(modeButtons[i]==null)continue;
            boolean active=GlbInspectionVariants.Mode.values()[i]==mode;
            modeButtons[i].setBackgroundTintList(android.content.res.ColorStateList.valueOf(active?ACCENT:PANEL));
            modeButtons[i].setTextColor(active?BG:TEXT);
            modeButtons[i].setEnabled(!preparing);
        }
    }
    @Override public void onConfigurationChanged(Configuration config){
        super.onConfigurationChanged(config);
        if(viewportRow!=null){
            boolean wide=config.orientation==Configuration.ORIENTATION_LANDSCAPE;
            viewportRow.setOrientation(wide?LinearLayout.HORIZONTAL:LinearLayout.VERTICAL);
            for(int i=0;i<2;i++){
                LinearLayout.LayoutParams p=wide?
                        new LinearLayout.LayoutParams(0,-1,1):
                        new LinearLayout.LayoutParams(-1,0,1);
                if(i==1){if(wide)p.leftMargin=dp(3);else p.topMargin=dp(3);}
                panes[i].frame.setLayoutParams(p);
            }
            handler.postDelayed(()->{
                updateCameras();
                if(referenceWindow!=null)referenceWindow.restorePosition();
            },150);
        }
    }

    private void createRenderer(Pane pane){
        pane.viewer=new ModelViewer(pane.surface,Engine.create(),
                new UiHelper(UiHelper.ContextErrorPolicy.DONT_CHECK),null);
        pane.viewer.setAutoPlayAnimations(false);
        pane.viewer.getView().setAntiAliasing(com.google.android.filament.View.AntiAliasing.FXAA);
        initStudio(pane);
        pane.scale=new ScaleGestureDetector(this,new ScaleGestureDetector.SimpleOnScaleGestureListener(){
            @Override public boolean onScale(ScaleGestureDetector detector){
                pane.distance=Math.max(2.0f,Math.min(18f,pane.distance/detector.getScaleFactor()));
                if(sync) copyAngles(pane,panes[1-pane.index]);
                updateCameras();pane.pinching=true;return true;
            }
        });
        pane.surface.setOnTouchListener((v,e)->touch(pane,e));
        pane.surface.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,oright,ob)->handler.post(this::updateCameras));
    }

    private boolean touch(Pane pane,MotionEvent e) {
        pane.scale.onTouchEvent(e);
        switch(e.getActionMasked()){
            case MotionEvent.ACTION_DOWN:
                pane.lastX=e.getX();pane.lastY=e.getY();
                pane.downX=e.getX();pane.downY=e.getY();
                pane.pinching=false;return true;
            case MotionEvent.ACTION_POINTER_DOWN:pane.pinching=true;return true;
            case MotionEvent.ACTION_MOVE:
                if(e.getPointerCount()==1&&!pane.pinching&&!marking){
                    pane.azimuth+=(e.getX()-pane.lastX)*0.42f;
                    pane.elevation=Math.max(-89,Math.min(89,pane.elevation-(e.getY()-pane.lastY)*0.33f));
                    if(sync)copyAngles(pane,panes[1-pane.index]);
                    updateCameras();
                }
                pane.lastX=e.getX();pane.lastY=e.getY();return true;
            case MotionEvent.ACTION_UP:
                if(marking && !pane.pinching && pane.original!=null &&
                        Math.abs(e.getX()-pane.downX)<dp(12) &&
                        Math.abs(e.getY()-pane.downY)<dp(12)) {
                    float u=Math.max(0f,Math.min(1f,e.getX()/Math.max(1f,pane.surface.getWidth())));
                    float v=Math.max(0f,Math.min(1f,e.getY()/Math.max(1f,pane.surface.getHeight())));
                    editNote(pane,u,v,null);
                }
                pane.pinching=false;return true;
            case MotionEvent.ACTION_CANCEL:
                pane.pinching=false;return true;
        }
        return true;
    }
    private static void copyAngles(Pane from,Pane to){
        to.azimuth=from.azimuth;to.elevation=from.elevation;to.distance=from.distance;
    }
    private void updateCameras(){
        for(Pane p:panes){
            if(p.viewer==null)continue;
            double az=Math.toRadians(p.azimuth),el=Math.toRadians(p.elevation);
            double x=p.distance*Math.cos(el)*Math.sin(az);
            double y=p.distance*Math.sin(el);
            double z=-4+p.distance*Math.cos(el)*Math.cos(az);
            double upZ=Math.abs(p.elevation)>87?(p.elevation>0?-1:1):0;
            double upY=Math.abs(p.elevation)>87?0:1;
            p.viewer.getCamera().lookAt(x,y,z,0,0,-4,0,upY,upZ);
            int w=Math.max(1,p.surface.getWidth()),h=Math.max(1,p.surface.getHeight());
            double aspect=(double)w/h;
            if(p.markers!=null)
                p.markers.update(p.hash,p.azimuth,p.elevation,p.distance,orthographic);
            if(orthographic){
                // Fixed world-space framing on both panes (not an unequal perspective distortion).
                double halfY=Math.max(1.15,1.65*(p.distance/4.1));
                p.viewer.getCamera().setProjection(com.google.android.filament.Camera.Projection.ORTHO,
                        -halfY*aspect,halfY*aspect,-halfY,halfY,0.10,100.0);
            }else {
                p.viewer.getCamera().setLensProjection(45.0,aspect,0.10,100.0);
            }
        }
    }

    private void initStudio(Pane p) {
        Engine engine=p.viewer.getEngine();
        // The floor lives in the GLB preview, so this is a softly lit neutral backdrop.
        p.sky=new Skybox.Builder().color(0.068f,0.075f,0.084f,1f).build(engine);
        p.viewer.getScene().setSkybox(p.sky);
        p.reflections=new Texture.Builder().width(16).height(16).levels(5)
                .sampler(Texture.Sampler.SAMPLER_CUBEMAP)
                .format(Texture.InternalFormat.RGBA8).build(engine);
        for(int level=0;level<5;level++){
            int dim=Math.max(1,16>>level);
            ByteBuffer pixels=ByteBuffer.allocateDirect(dim*dim*6*4);
            for(int face=0;face<6;face++){
                for(int y=0;y<dim;y++)for(int x=0;x<dim;x++){
                    float u=(x+0.5f)/dim*2-1,v=(y+0.5f)/dim*2-1;
                    float c=0.36f+(face==2?0.22f:face==3?0.05f:0.12f);
                    float strip=(float)Math.exp(-Math.pow((u+(face%2==0?0.12f:-0.3f))/0.34,2)
                            -Math.pow((v+0.15f)/0.55,2));
                    float r=Math.min(1,c+0.42f*strip);
                    float g=Math.min(1,c+0.45f*strip);
                    float b=Math.min(1,c+0.48f*strip);
                    pixels.put((byte)(255*r));pixels.put((byte)(255*g));
                    pixels.put((byte)(255*b));pixels.put((byte)255);
                }
            }
            pixels.flip();
            p.reflections.setImage(engine,level,0,0,0,dim,dim,6,
                    new Texture.PixelBufferDescriptor(pixels,Texture.Format.RGBA,Texture.Type.UBYTE));
        }
        float[] sh=new float[27];sh[0]=0.70f;sh[1]=0.74f;sh[2]=0.78f;
        p.ibl=new IndirectLight.Builder().reflections(p.reflections).irradiance(3,sh)
                .intensity(30000).build(engine);
        p.viewer.getScene().setIndirectLight(p.ibl);
        p.fillLights[0]=addFill(p,-0.55f,-0.9f,-0.3f,42000,1f,0.97f,0.92f);
        p.fillLights[1]=addFill(p,0.75f,-0.4f,0.6f,23000,0.85f,0.9f,1f);
        p.viewer.getCamera().setExposure(13f,1f/125f,100f);
    }
    private int addFill(Pane p,float x,float y,float z,float lux,float r,float g,float b){
        int e=EntityManager.get().create();
        new LightManager.Builder(LightManager.Type.DIRECTIONAL).direction(x,y,z)
                .color(r,g,b).intensity(lux).castShadows(false).build(p.viewer.getEngine(),e);
        p.viewer.getScene().addEntity(e);return e;
    }

    private void choosePhoto() {
        Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("image/*");
        startActivityForResult(intent,PICK_PHOTO);
    }
    private void choose(int request){
        Intent pick=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        pick.addCategory(Intent.CATEGORY_OPENABLE);pick.setType("*/*");
        startActivityForResult(pick,request);
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(result!=RESULT_OK || data==null || data.getData()==null)return;
        if(request==PICK_A || request==PICK_B) {
            loadUri(panes[request==PICK_A?0:1],data.getData());
        } else if(request==PICK_PHOTO) {
            Uri uri=data.getData();
            try {
                getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);
            } catch(SecurityException ignored){}
            referenceWindow.loadImage(uri,displayName(uri));
            referenceWindow.showPanel();
        } else if(request==EXPORT_JSON) {
            Uri dest=data.getData();
            String json=pendingFeedbackExport;
            new Thread(()->{
                try(OutputStream out=getContentResolver().openOutputStream(dest)) {
                    if(out==null)throw new IllegalArgumentException("Destination unavailable");
                    out.write(json.getBytes(StandardCharsets.UTF_8));
                    runOnUiThread(()->Toast.makeText(this,"Feedback JSON exported",Toast.LENGTH_LONG).show());
                }catch(Exception ex){runOnUiThread(()->error("JSON export failed: "+ex.getMessage()));}
            },"feedback-json-export").start();
        }
    }
    private String displayName(Uri uri) {
        try(Cursor c=getContentResolver().query(uri,null,null,null,null)){
            if(c!=null&&c.moveToFirst()){
                int i=c.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if(i>=0)return c.getString(i);
            }
        }catch(Exception ignored){}
        return uri.getLastPathSegment()==null?"model.glb":uri.getLastPathSegment();
    }
    private void loadUri(Pane p,Uri uri){
        String name=displayName(uri);
        if(!name.toLowerCase(Locale.US).endsWith(".glb")){error("Select a .glb file");return;}
        p.caption.setText((p.index==0?"A":"B")+" • Loading "+name);
        long revision=++p.request;
        new Thread(()->{
            try{
                ByteArrayOutputStream data=new ByteArrayOutputStream();
                try(InputStream in=getContentResolver().openInputStream(uri)){
                    if(in==null)throw new IllegalArgumentException("File unreadable");
                    byte[] buf=new byte[16384];int count;
                    while((count=in.read(buf))>0){
                        if(data.size()+count>60*1024*1024)throw new IllegalArgumentException("60MB max per GLB in compare");
                        data.write(buf,0,count);
                    }
                }
                byte[] bytes=data.toByteArray();
                String originalHash=FeedbackStore.sha256(bytes);
                if(bytes.length<20||bytes[0]!='g'||bytes[1]!='l'||bytes[2]!='T'||bytes[3]!='F')
                    throw new IllegalArgumentException("Invalid GLB binary");
                byte[] renderBytes=prepareForView(bytes,mode);
                ByteBuffer direct=ByteBuffer.allocateDirect(renderBytes.length).order(ByteOrder.LITTLE_ENDIAN);
                direct.put(renderBytes).flip();
                runOnUiThread(()->{
                    if(p.request!=revision)return;
                    try{
                        loadInViewer(p,direct);
                        p.original=bytes;p.name=name;p.hash=originalHash;
                        if(p.markers!=null)p.markers.update(p.hash,p.azimuth,p.elevation,p.distance,orthographic);
                        updateIssueCount();
                        p.caption.setText((p.index==0?"A":"B")+" • "+name);
                        message.setText("A/B ready • rotate for side-by-side • drag either view to orbit");
                    }catch(Exception ex){error("GLB render: "+ex.getMessage());}
                });
            }catch(Exception ex){runOnUiThread(()->error("GLB error: "+ex.getMessage()));}
        },"compare-load").start();
    }
    private byte[] prepareForView(byte[] source,GlbInspectionVariants.Mode selected) throws Exception{
        byte[] variant=GlbInspectionVariants.create(source,selected);
        if(selected!=GlbInspectionVariants.Mode.WIREFRAME){
            // Some GLBs lack bounds or use unusual transforms. Keep original if studio floor
            // cannot be made safely; inspectability takes priority over decoration.
            try{return StudioGlb.withFloor(variant);}catch(Exception ignored){return variant;}
        }
        return variant;
    }
    private void loadInViewer(Pane p,ByteBuffer bytes){
        p.viewer.loadModelGlb(bytes);
        if(p.viewer.getAsset()==null)throw new IllegalArgumentException("glTF renderer rejected model");
        p.viewer.transformToUnitCube(new Float3(0,0,-4));
        p.currentDirect=bytes;updateCameras();
    }
    private void selectMode(GlbInspectionVariants.Mode selected){
        if(preparing||mode==selected)return;
        preparing=true;syncModeButtons();message.setText("Preparing "+selected.name()+" views…");
        long revision=++modeRevision;
        byte[][] originals={panes[0].original,panes[1].original};
        new Thread(()->{
            ByteBuffer[] transformed=new ByteBuffer[2];
            String errorText=null;
            try {
                for(int i=0;i<2;i++){
                    if(originals[i]==null)continue;
                    byte[] bytes=prepareForView(originals[i],selected);
                    transformed[i]=ByteBuffer.allocateDirect(bytes.length);
                    transformed[i].put(bytes).flip();
                }
            }catch(Exception ex){errorText=ex.getMessage();}
            final String issue=errorText;
            runOnUiThread(()->{
                if(revision!=modeRevision)return;
                try{
                    if(issue!=null)throw new IllegalStateException(issue);
                    for(int i=0;i<2;i++)if(transformed[i]!=null)loadInViewer(panes[i],transformed[i]);
                    mode=selected;message.setText("Viewing "+selected.name()+" on both GLBs");
                }catch(Exception ex){error("Compare mode: "+ex.getMessage());}
                finally{preparing=false;syncModeButtons();}
            });
        },"compare-mode").start();
    }

    /** Create/edit a view-anchored defect pin with structured issue classification. */
    private void editNote(Pane pane,float u,float v,FeedbackStore.Note existing) {
        if(pane.original==null || pane.hash.isEmpty()) {
            error("Load a GLB before marking defects.");
            return;
        }
        LinearLayout content=new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(20),dp(8),dp(20),dp(6));

        TextView help=new TextView(this);
        help.setText("Describe the exact shape or modeling correction here. The camera viewpoint and marker location are saved with the note.");
        help.setTextSize(12);
        help.setTextColor(MUTED);
        content.addView(help);

        TextView typeLabel=new TextView(this);
        typeLabel.setText("Issue category");
        typeLabel.setTextColor(TEXT);
        content.addView(typeLabel);
        Spinner category=new Spinner(this);
        ArrayAdapter<String> categories=new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,FeedbackStore.TYPES);
        category.setAdapter(categories);
        content.addView(category);

        TextView severityLabel=new TextView(this);
        severityLabel.setText("Priority");
        severityLabel.setTextColor(TEXT);
        content.addView(severityLabel);
        Spinner severity=new Spinner(this);
        ArrayAdapter<String> priorities=new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,FeedbackStore.SEVERITIES);
        severity.setAdapter(priorities);
        content.addView(severity);

        EditText note=new EditText(this);
        note.setHint("e.g. Rear haunch transitions into the cab too abruptly; blend roof armor back toward twin boosters");
        note.setTextColor(TEXT);
        note.setHintTextColor(MUTED);
        note.setMinLines(3);
        note.setMaxLines(5);
        note.setInputType(android.text.InputType.TYPE_CLASS_TEXT |
                android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE |
                android.text.InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        content.addView(note,new LinearLayout.LayoutParams(-1,dp(119)));

        if(existing!=null){
            for(int i=0;i<FeedbackStore.TYPES.length;i++)
                if(FeedbackStore.TYPES[i].equals(existing.issueType))category.setSelection(i);
            for(int i=0;i<FeedbackStore.SEVERITIES.length;i++)
                if(FeedbackStore.SEVERITIES[i].equals(existing.severity))severity.setSelection(i);
            note.setText(existing.description);
        }

        AlertDialog dialog=new AlertDialog.Builder(this)
                .setTitle((existing==null?"New defect":"Edit defect")+"  •  "+(pane.index==0?"A":"B"))
                .setView(content)
                .setPositiveButton("SAVE",null)
                .setNegativeButton("CANCEL",(d,which)->{})
                .create();
        dialog.setOnShowListener(ignored->{
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(vbutton->{
                String description=note.getText().toString().trim();
                if(description.isEmpty()) {
                    note.setError("Describe the correction you want");
                    return;
                }
                FeedbackStore.Note item=existing==null?new FeedbackStore.Note():existing;
                if(existing==null) {
                    item.id="issue-"+System.currentTimeMillis()+"-"+(feedback.all().size()+1);
                    item.createdUtcMillis=System.currentTimeMillis();
                    item.pane=pane.index;
                    item.modelName=pane.name;
                    item.modelSha256=pane.hash;
                    item.u=u;item.v=v;
                    item.azimuth=pane.azimuth;item.elevation=pane.elevation;
                    item.distance=pane.distance;
                    item.orthographic=orthographic;
                    item.mode=mode.name();
                }
                item.issueType=FeedbackStore.TYPES[category.getSelectedItemPosition()];
                item.severity=FeedbackStore.SEVERITIES[severity.getSelectedItemPosition()];
                item.description=description;
                if(existing==null)feedback.add(item);else feedback.save();
                marking=false;
                syncMarkButton();
                updateIssueCount();
                message.setText("Issue saved • "+item.issueType+". Export JSON to share with AssetWright.");
                dialog.dismiss();
            });
        });
        dialog.show();
    }

    private void showIssues() {
        java.util.ArrayList<FeedbackStore.Note> active=new java.util.ArrayList<>();
        for(FeedbackStore.Note n:feedback.all()){
            if(n.modelSha256.equals(panes[0].hash)||n.modelSha256.equals(panes[1].hash))active.add(n);
        }
        if(active.isEmpty()){
            new AlertDialog.Builder(this).setTitle("No annotations yet")
                    .setMessage("Tap MARK PANEL, then tap the area of a loaded GLB that needs work. Describe the defect and save it.")
                    .setPositiveButton("OK",null).show();
            return;
        }
        String[] entries=new String[active.size()];
        for(int i=0;i<active.size();i++){
            FeedbackStore.Note n=active.get(i);
            String description=n.description;
            if(description.length()>54)description=description.substring(0,54)+"…";
            entries[i]=(i+1)+". ["+(n.pane==0?"A":"B")+"] "+n.issueType+" / "+n.severity+"\n"+description;
        }
        new AlertDialog.Builder(this).setTitle("Recorded model corrections")
                .setItems(entries,(dialog,index)->issueActions(active.get(index)))
                .setNegativeButton("DONE",null).show();
    }

    private void issueActions(FeedbackStore.Note n) {
        new AlertDialog.Builder(this)
                .setTitle(n.issueType+" • "+(n.pane==0?"A":"B"))
                .setMessage(n.description)
                .setItems(new String[]{"Restore camera & locate pin","Edit description","Delete this issue"},(d,which)->{
                    if(which==0){
                        Pane pane=panes[n.pane];
                        pane.azimuth=n.azimuth;
                        pane.elevation=n.elevation;
                        pane.distance=n.distance;
                        if(sync)copyAngles(pane,panes[1-n.pane]);
                        orthographic=n.orthographic;
                        projectionButton.setText(orthographic?"ORTHO":"3D");
                        updateCameras();
                        try {
                            GlbInspectionVariants.Mode saved=GlbInspectionVariants.Mode.valueOf(n.mode);
                            if(saved!=mode)selectMode(saved);
                        }catch(Exception ignored){}
                        message.setText("Restored issue camera: "+n.issueType);
                    } else if(which==1){
                        Pane pane=panes[n.pane];
                        editNote(pane,n.u,n.v,n);
                    } else {
                        new AlertDialog.Builder(this).setTitle("Delete issue?")
                                .setMessage("Remove this recorded correction from local feedback?")
                                .setPositiveButton("DELETE",(dialog,button)->{
                                    feedback.remove(n);updateIssueCount();
                                })
                                .setNegativeButton("CANCEL",null).show();
                    }
                })
                .setNegativeButton("CLOSE",null).show();
    }

    private void exportFeedback() {
        if(panes[0].hash.isEmpty()&&panes[1].hash.isEmpty()){
            error("Load at least one GLB before exporting.");
            return;
        }
        try {
            JSONObject json=feedback.export(
                    panes[0].original==null?"":panes[0].name,panes[0].hash,
                    panes[1].original==null?"":panes[1].name,panes[1].hash,
                    referenceWindow.referenceName(),sync,mode.name());
            if(json.getJSONArray("issues").length()==0) {
                new AlertDialog.Builder(this).setTitle("No defect notes recorded")
                        .setMessage("Tap MARK PANEL, describe at least one defect, then export the feedback JSON.")
                        .setPositiveButton("OK",null).show();
                return;
            }
            pendingFeedbackExport=json.toString(2);
            String filename="SceneForge_Feedback_"+
                    new SimpleDateFormat("yyyyMMdd_HHmmss",Locale.US).format(new Date())+".json";
            Intent save=new Intent(Intent.ACTION_CREATE_DOCUMENT);
            save.addCategory(Intent.CATEGORY_OPENABLE);
            save.setType("application/json");
            save.putExtra(Intent.EXTRA_TITLE,filename);
            startActivityForResult(save,EXPORT_JSON);
        }catch(Exception ex){error("Could not prepare JSON: "+ex.getMessage());}
    }

    private void captureBoth(){
        if(panes[0].original==null||panes[1].original==null){
            error("Load both GLBs before exporting a comparison.");return;
        }
        SurfaceView a=panes[0].surface,b=panes[1].surface;
        if(a.getWidth()==0||a.getHeight()==0||b.getWidth()==0||b.getHeight()==0){
            error("Renderer not ready");return;
        }
        Bitmap left=Bitmap.createBitmap(a.getWidth(),a.getHeight(),Bitmap.Config.ARGB_8888);
        Bitmap right=Bitmap.createBitmap(b.getWidth(),b.getHeight(),Bitmap.Config.ARGB_8888);
        PixelCopy.request(a,left,status->{
            if(status!=PixelCopy.SUCCESS){left.recycle();right.recycle();error("Left screenshot failed");return;}
            PixelCopy.request(b,right,status2->{
                if(status2!=PixelCopy.SUCCESS){left.recycle();right.recycle();error("Right screenshot failed");return;}
                new Thread(()->{
                    Bitmap merged=null;
                    try{
                        // Always export horizontal A/B even if phone is held portrait.
                        int height=Math.min(1400,Math.max(left.getHeight(),right.getHeight()));
                        int w1=Math.max(1,Math.round(height*(float)left.getWidth()/left.getHeight()));
                        int w2=Math.max(1,Math.round(height*(float)right.getWidth()/right.getHeight()));
                        merged=Bitmap.createBitmap(w1+w2+6,height+44,Bitmap.Config.ARGB_8888);
                        Canvas c=new Canvas(merged);c.drawColor(Color.rgb(18,22,28));
                        Paint pp=new Paint(3);c.drawBitmap(left,null,new android.graphics.Rect(0,44,w1,height+44),pp);
                        c.drawBitmap(right,null,new android.graphics.Rect(w1+6,44,w1+6+w2,height+44),pp);
                        pp.setColor(TEXT);pp.setTextSize(22f);
                        c.drawText("A: "+panes[0].name,12,30,pp);
                        c.drawText("B: "+panes[1].name,w1+18,30,pp);
                        // Keep numbered feedback pins in the exported real-render PNG.
                        if(panes[0].markers!=null){
                            c.save();c.translate(0,44);
                            panes[0].markers.drawOnExport(c,w1,height);
                            c.restore();
                        }
                        if(panes[1].markers!=null){
                            c.save();c.translate(w1+6,44);
                            panes[1].markers.drawOnExport(c,w2,height);
                            c.restore();
                        }
                        String file="SceneForge_AB_"+new SimpleDateFormat("yyyyMMdd_HHmmss",Locale.US)
                                .format(new Date())+"_"+(++snapshotNumber)+".png";
                        savePng(merged,file);
                        runOnUiThread(()->Toast.makeText(this,"Saved comparison PNG",Toast.LENGTH_LONG).show());
                    }catch(Exception e){runOnUiThread(()->error("PNG export: "+e.getMessage()));}
                    finally{left.recycle();right.recycle();if(merged!=null)merged.recycle();}
                },"compare-save").start();
            },handler);
        },handler);
    }
    private void savePng(Bitmap bmp,String filename)throws Exception{
        if(Build.VERSION.SDK_INT>=29){
            ContentValues row=new ContentValues();
            row.put(MediaStore.Images.Media.DISPLAY_NAME,filename);
            row.put(MediaStore.Images.Media.MIME_TYPE,"image/png");
            row.put(MediaStore.Images.Media.RELATIVE_PATH,Environment.DIRECTORY_PICTURES+"/SceneForge Inspector");
            row.put(MediaStore.Images.Media.IS_PENDING,1);
            Uri dest=getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI,row);
            if(dest==null)throw new IllegalStateException("No gallery storage");
            try{
                try(OutputStream stream=getContentResolver().openOutputStream(dest)){
                    if(stream==null||!bmp.compress(Bitmap.CompressFormat.PNG,100,stream))
                        throw new IllegalStateException("PNG write failed");
                }
                row.clear();row.put(MediaStore.Images.Media.IS_PENDING,0);
                getContentResolver().update(dest,row,null,null);
            }catch(Exception ex){getContentResolver().delete(dest,null,null);throw ex;}
        }else{
            File dir=getExternalFilesDir(Environment.DIRECTORY_PICTURES);
            if(dir==null)throw new IllegalStateException("No picture storage");
            try(OutputStream stream=new FileOutputStream(new File(dir,filename))){
                if(!bmp.compress(Bitmap.CompressFormat.PNG,100,stream))
                    throw new IllegalStateException("PNG write failed");
            }
        }
    }
    private void verifyComparisonInEmulator(){
        new Thread(()->{
            try {
                byte[] sample=GlbInspectionVariants.diagnosticSquare();
                ByteBuffer[] direct=new ByteBuffer[2];
                for(int i=0;i<2;i++){
                    byte[] bytes=prepareForView(sample,GlbInspectionVariants.Mode.TEXTURED);
                    direct[i]=ByteBuffer.allocateDirect(bytes.length);direct[i].put(bytes).flip();
                }
                runOnUiThread(()->{
                    try{
                        for(int i=0;i<2;i++){
                            loadInViewer(panes[i],direct[i]);
                            panes[i].original=sample;
                            panes[i].name=i==0?"Diagnostic A":"Diagnostic B";
                            panes[i].caption.setText(panes[i].name);
                        }
                        sync=true;updateCameras();
                        referenceWindow.showPanel();
                        if(referenceWindow.getVisibility()!=View.VISIBLE)
                            throw new IllegalStateException("Reference photo window unavailable");
                        android.util.Log.i("SCENEFORGE_COMPARE_TEST","REFERENCE_WINDOW_PASSED");

                        FeedbackStore.Note sampleNote=new FeedbackStore.Note();
                        sampleNote.id="diagnostic-feedback-1";
                        sampleNote.modelName=panes[0].name;
                        sampleNote.modelSha256=FeedbackStore.sha256(sample);
                        panes[0].hash=sampleNote.modelSha256;
                        sampleNote.pane=0;
                        sampleNote.u=0.61f;sampleNote.v=0.44f;
                        sampleNote.azimuth=panes[0].azimuth;
                        sampleNote.elevation=panes[0].elevation;
                        sampleNote.distance=panes[0].distance;
                        sampleNote.orthographic=orthographic;
                        sampleNote.issueType="Surface continuity";
                        sampleNote.severity="High";
                        sampleNote.description="Smooth the rear cab-to-haunch panel transition";
                        sampleNote.createdUtcMillis=System.currentTimeMillis();
                        sampleNote.mode=mode.name();
                        feedback.add(sampleNote);
                        JSONObject exported=feedback.export(panes[0].name,panes[0].hash,
                                panes[1].name,panes[1].hash,referenceWindow.referenceName(),sync,mode.name());
                        if(exported.getJSONArray("issues").length()!=1)
                            throw new IllegalStateException("JSON issue export missing");
                        JSONObject anchor=exported.getJSONArray("issues").getJSONObject(0).getJSONObject("anchor");
                        if(anchor.getBoolean("is_surface_raycast"))
                            throw new IllegalStateException("Anchor accuracy mislabeled");
                        feedback.remove(sampleNote);
                        updateIssueCount();
                        android.util.Log.i("SCENEFORGE_COMPARE_TEST","FEEDBACK_JSON_PASSED");
                        android.util.Log.i("SCENEFORGE_COMPARE_TEST","TWO_LIVE_GLB_VIEWERS_PASSED");
                    }catch(Throwable ex){
                        android.util.Log.e("SCENEFORGE_COMPARE_TEST","FAILED",ex);
                    }
                });
            }catch(Throwable ex){android.util.Log.e("SCENEFORGE_COMPARE_TEST","FAILED",ex);}
        },"compare-smoke").start();
    }
    private void error(String text){message.setText(text);Toast.makeText(this,text,Toast.LENGTH_LONG).show();}
    @Override protected void onResume(){super.onResume();running=true;Choreographer.getInstance().postFrameCallback(this);}
    @Override protected void onPause(){running=false;Choreographer.getInstance().removeFrameCallback(this);super.onPause();}
    @Override public void doFrame(long nano){
        if(!running)return;
        // Two offscreen graphics contexts; cap to ~30fps to reduce battery/GPU pressure.
        if((++frameCounter&1)==0){
            for(Pane p:panes)if(p.viewer!=null)p.viewer.render(nano);
        }
        Choreographer.getInstance().postFrameCallback(this);
    }
    @Override protected void onDestroy(){
        running=false;
        for(Pane p:panes){
            if(p==null||p.viewer==null)continue;
            try{
                p.viewer.destroyModel();
                Engine e=p.viewer.getEngine();
                p.viewer.getScene().setIndirectLight(null);
                p.viewer.getScene().setSkybox(null);
                if(p.ibl!=null)e.destroyIndirectLight(p.ibl);
                if(p.sky!=null)e.destroySkybox(p.sky);
                if(p.reflections!=null)e.destroyTexture(p.reflections);
                for(int light:p.fillLights)if(light!=0){
                    p.viewer.getScene().remove(light);
                    e.destroyEntity(light);EntityManager.get().destroy(light);
                }
                p.viewer.destroy();
            }catch(Exception ignored){}
        }
        super.onDestroy();
    }
}
