package com.sceneforge.glbinspector;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.res.ColorStateList;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowInsets;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.AdapterView;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;

/**
 * Free, native offline Shape Lab: touch-deform actual GLB POSITION vertices.
 * 2D orthographic surface cage, NOT rendered fake contour edits.
 *
 * SAF picker/export always preserve the original GLB; this editor writes only
 * a user-selected NEW filename. Unsupported compressed or transformed meshes
 * fail clearly instead of being damaged.
 */
public final class ShapeLabActivity extends Activity {
    private static final int BG=Color.rgb(12,17,26), PANEL=Color.rgb(29,40,57);
    private static final int TEXT=Color.rgb(230,236,243), ACCENT=Color.rgb(35,196,187);
    private static final int OPEN=9201, SAVE=9202, PICK_PHOTO=9203;
    private GlbSurfaceEditor engine;
    private GlbSurfaceEditor.Part selected;
    private ShapeCanvas editorCanvas;
    private Spinner partSpinner;
    private TextView info, tip;
    private CheckBox mirrorCheck;
    private SeekBar radiusBar;
    private float radius=.70f;
    private int cameraView=0;
    private String sourceName="Forge";
    private Bitmap reference;
    private boolean showReference=false;

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        buildUi();
        String cache=getIntent().getStringExtra("source_path");
        sourceName=getIntent().getStringExtra("source_name");
        if(sourceName==null)sourceName="Vehicle";
        if(cache!=null)readModel(new File(cache));
    }
    private int dp(float x){return (int)(x*getResources().getDisplayMetrics().density+.5f);}
    private Button button(String label){
        Button b=new Button(this);
        b.setText(label);b.setAllCaps(false);b.setTextSize(12);
        b.setTextColor(TEXT);
        b.setBackgroundTintList(ColorStateList.valueOf(PANEL));
        return b;
    }
    private void buildUi(){
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(BG);setContentView(root);
        root.setOnApplyWindowInsetsListener((v,insets)->{
            if(android.os.Build.VERSION.SDK_INT>=30){
                android.graphics.Insets b=insets.getInsets(WindowInsets.Type.systemBars());
                v.setPadding(b.left,b.top,b.right,b.bottom);
            }else{
                v.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),
                        insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            }
            return insets;
        });
        root.requestApplyInsets();

        LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);
        Button back=button("BACK");back.setOnClickListener(v->finish());
        header.addView(back,new LinearLayout.LayoutParams(dp(75),dp(42)));
        TextView title=new TextView(this);title.setText("SCENEFORGE  /  SHAPE LAB");
        title.setTextSize(15);title.setTextColor(TEXT);
        title.setPadding(dp(9),0,0,0);
        header.addView(title,new LinearLayout.LayoutParams(0,dp(42),1));
        Button load=button("OPEN GLB");load.setOnClickListener(v->pick(OPEN,"*/*"));
        header.addView(load,new LinearLayout.LayoutParams(dp(100),dp(42)));
        root.addView(header);

        info=new TextView(this);info.setText("Select a GLB to edit actual mesh curvature.");
        info.setTextSize(12);info.setTextColor(TEXT);info.setPadding(dp(12),dp(6),dp(12),dp(6));
        root.addView(info);

        partSpinner=new Spinner(this);partSpinner.setBackgroundTintList(ColorStateList.valueOf(ACCENT));
        LinearLayout.LayoutParams spin=new LinearLayout.LayoutParams(-1,dp(44));
        spin.setMargins(dp(10),0,dp(10),dp(4));
        root.addView(partSpinner,spin);
        partSpinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            @Override public void onItemSelected(AdapterView<?> parent,View v,int idx,long id){
                if(engine==null||idx<0||idx>=engine.parts().size())return;
                selected=engine.parts().get(idx);setInfo();editorCanvas.invalidate();
            }
            @Override public void onNothingSelected(AdapterView<?> p){}
        });

        LinearLayout views=new LinearLayout(this);
        for(int i=0;i<3;i++){
            final int v=i;
            Button b=button(new String[]{"SIDE","TOP","FRONT"}[i]);
            b.setOnClickListener(w->{cameraView=v;editorCanvas.invalidate();setInfo();});
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(40),1);
            lp.leftMargin=dp(4);
            views.addView(b,lp);
        }
        Button photo=button("REF PHOTO");
        photo.setOnClickListener(v->{
            if(reference==null)pick(PICK_PHOTO,"image/*");
            else {showReference=!showReference;editorCanvas.invalidate();}
        });
        views.addView(photo,new LinearLayout.LayoutParams(0,dp(40),1.1f));
        root.addView(views);

        FrameLayout work=new FrameLayout(this);
        work.setBackgroundColor(Color.rgb(19,25,35));
        editorCanvas=new ShapeCanvas();
        work.addView(editorCanvas,new FrameLayout.LayoutParams(-1,-1));
        root.addView(work,new LinearLayout.LayoutParams(-1,0,1f));

        tip=new TextView(this);
        tip.setText("Select a surface. Drag on its wireframe to reshape; drag radius blends neighboring vertices.");
        tip.setTextColor(TEXT);tip.setTextSize(11);
        tip.setPadding(dp(10),dp(3),dp(10),dp(5));
        root.addView(tip);

        LinearLayout options=new LinearLayout(this);options.setGravity(Gravity.CENTER_VERTICAL);
        options.setPadding(dp(7),0,dp(7),0);
        TextView lab=new TextView(this);lab.setText("BRUSH");lab.setTextSize(11);
        lab.setTextColor(TEXT);options.addView(lab);
        radiusBar=new SeekBar(this);radiusBar.setMax(180);radiusBar.setProgress(50);
        options.addView(radiusBar,new LinearLayout.LayoutParams(0,dp(42),1f));
        radiusBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            @Override public void onProgressChanged(SeekBar b,int x,boolean user){
                radius=.2f+x*.01f;setInfo();
            }
            @Override public void onStartTrackingTouch(SeekBar b){}
            @Override public void onStopTrackingTouch(SeekBar b){}
        });
        mirrorCheck=new CheckBox(this);mirrorCheck.setText("MIRROR");
        mirrorCheck.setTextSize(11);mirrorCheck.setTextColor(TEXT);
        mirrorCheck.setButtonTintList(ColorStateList.valueOf(ACCENT));mirrorCheck.setChecked(true);
        options.addView(mirrorCheck);
        root.addView(options);

        LinearLayout actions=new LinearLayout(this);actions.setPadding(dp(5),0,dp(5),dp(8));
        Button undo=button("UNDO");undo.setOnClickListener(v->{
            if(engine!=null&&engine.undo()){editorCanvas.invalidate();setInfo();}
            else say("Nothing to undo");
        });
        Button reset=button("RESET PART");reset.setOnClickListener(v->{
            if(engine!=null&&selected!=null)new AlertDialog.Builder(this)
                    .setTitle("Reset selected component?")
                    .setMessage("Restore the selected mesh vertices to the imported original.")
                    .setPositiveButton("Reset",(d,w)->{engine.resetPart(selected);editorCanvas.invalidate();setInfo();})
                    .setNegativeButton("Cancel",null).show();
        });
        Button save=button("SAVE NEW GLB");
        save.setBackgroundTintList(ColorStateList.valueOf(ACCENT));
        save.setTextColor(BG);save.setOnClickListener(v->{
            if(engine==null){say("Open a GLB first");return;}
            Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);
            i.addCategory(Intent.CATEGORY_OPENABLE);
            i.setType("model/gltf-binary");
            i.putExtra(Intent.EXTRA_TITLE,sourceName.replaceAll("[^a-zA-Z0-9_-]","_")+"_ShapeLab.glb");
            startActivityForResult(i,SAVE);
        });
        for(Button b:new Button[]{undo,reset,save}){
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(44),1);
            lp.leftMargin=dp(4);actions.addView(b,lp);
        }
        root.addView(actions);
    }
    private void setInfo(){
        if(engine==null)return;
        String name=selected==null?"none":selected.name;
        String view=new String[]{"SIDE (Z/Y)","TOP (X/Z)","FRONT (X/Y)"}[cameraView];
        info.setText(engine.parts().size()+" editable components  •  "+view+"  •  "+name);
        tip.setText("Brush "+String.format(java.util.Locale.US,"%.2f",radius)+" m  •  Drag mesh surface to deform REAL vertices  •  undo/export saves a new GLB");
    }
    private void pick(int request,String type){
        Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);i.setType(type);
        startActivityForResult(i,request);
    }
    private void readModel(File source){
        new Thread(()->{
            try(InputStream in=new FileInputStream(source)){
                ByteArrayOutputStream b=new ByteArrayOutputStream();
                byte[] buf=new byte[8192];int n;
                while((n=in.read(buf))!=-1){
                    if(b.size()+n>80*1024*1024)throw new IllegalArgumentException("80 MB maximum");
                    b.write(buf,0,n);
                }
                GlbSurfaceEditor edited=new GlbSurfaceEditor(b.toByteArray());
                runOnUiThread(()->setEditor(edited));
            }catch(Exception e){runOnUiThread(()->say("Open failed: "+e.getMessage()));}
        },"sceneforge-shape-lab-load").start();
    }
    private void readModel(Uri uri){
        new Thread(()->{
            try(InputStream in=getContentResolver().openInputStream(uri)){
                if(in==null)throw new IllegalArgumentException("File unavailable");
                ByteArrayOutputStream b=new ByteArrayOutputStream();
                byte[] buf=new byte[8192];int n;
                while((n=in.read(buf))!=-1){
                    if(b.size()+n>80*1024*1024)throw new IllegalArgumentException("80 MB maximum");
                    b.write(buf,0,n);
                }
                GlbSurfaceEditor edited=new GlbSurfaceEditor(b.toByteArray());
                runOnUiThread(()->setEditor(edited));
            }catch(Exception e){runOnUiThread(()->say("Open failed: "+e.getMessage()));}
        },"sceneforge-shape-lab-load").start();
    }
    private void setEditor(GlbSurfaceEditor value){
        engine=value;
        ArrayList<String> names=new ArrayList<>();
        for(GlbSurfaceEditor.Part p:engine.parts())names.add(p.name);
        ArrayAdapter<String> adapter=new ArrayAdapter<>(this,android.R.layout.simple_spinner_item,names);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        partSpinner.setAdapter(adapter);
        int focus=0;
        for(int i=0;i<names.size();i++)
            if(names.get(i).contains("ContinuousFuselage")||names.get(i).contains("MainSideArmor")){
                focus=i;break;
            }
        partSpinner.setSelection(focus);
        selected=engine.parts().get(focus);
        setInfo();editorCanvas.invalidate();say("Loaded "+names.size()+" editable components.");
    }
    private void say(String what){Toast.makeText(this,what,Toast.LENGTH_LONG).show();}
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(result!=RESULT_OK||data==null||data.getData()==null)return;
        Uri uri=data.getData();
        if(request==OPEN){
            sourceName="Vehicle";
            android.database.Cursor c=getContentResolver().query(uri,null,null,null,null);
            if(c!=null)try{if(c.moveToFirst()){
                int ix=c.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME);
                if(ix>=0)sourceName=c.getString(ix).replaceAll("(?i)\\.glb$","");
            }}finally{c.close();}
            readModel(uri);
        }else if(request==PICK_PHOTO){
            try(InputStream in=getContentResolver().openInputStream(uri)){
                if(in==null)throw new IllegalArgumentException("Image unavailable");
                BitmapFactory.Options opts=new BitmapFactory.Options();
                opts.inSampleSize=2;
                reference=BitmapFactory.decodeStream(in,null,opts);
                showReference=reference!=null;
                editorCanvas.invalidate();
            }catch(Exception e){say("Reference failed: "+e.getMessage());}
        }else if(request==SAVE){
            new Thread(()->{
                try(OutputStream out=getContentResolver().openOutputStream(uri)){
                    if(out==null)throw new IllegalArgumentException("Cannot open destination");
                    byte[] bytes=engine.exportGlb();
                    // Validate length, signature and byte alignment before writing.
                    java.nio.ByteBuffer head=java.nio.ByteBuffer.wrap(bytes).order(java.nio.ByteOrder.LITTLE_ENDIAN);
                    if(head.getInt(0)!=0x46546c67||head.getInt(8)!=bytes.length)
                        throw new IllegalArgumentException("Export integrity check failed");
                    out.write(bytes);out.flush();
                    runOnUiThread(()->say("New edited GLB exported. Open it in SceneForge Inspector to review in 3D."));
                }catch(Exception e){runOnUiThread(()->say("Export failed: "+e.getMessage()));}
            },"sceneforge-shape-lab-export").start();
        }
    }

    private final class ShapeCanvas extends View {
        private final Paint paint=new Paint(3);
        private float scale,centerU,centerV;
        private float minU,minV,maxU,maxV;
        private GlbSurfaceEditor.Stroke stroke;
        private float downX,downY;
        private boolean moved;

        ShapeCanvas(){super(ShapeLabActivity.this);setLayerType(View.LAYER_TYPE_SOFTWARE,null);}
        private int U(){return GlbSurfaceEditor.horiz(cameraView);}
        private int V(){return GlbSurfaceEditor.vert(cameraView);}
        private boolean flipU(){return cameraView==0;} // Nose on the LEFT in side elevation.
        private boolean flipV(){return cameraView==1;} // Nose toward the bottom in top projection.
        private float sx(float u){return getWidth()*.5f+(flipU()?-1:1)*(u-centerU)*scale;}
        private float sy(float v){return getHeight()*.5f-(flipV()?-1:1)*(v-centerV)*scale;}
        private float fromX(float sx){return centerU+(sx-getWidth()*.5f)/scale*(flipU()?-1:1);}
        private float fromY(float sy){return centerV-(sy-getHeight()*.5f)/scale*(flipV()?-1:1);}
        private void setColor(int color,float strokeWidth){paint.setColor(color);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(strokeWidth);}
        private void measure(){
            float[][] bounds=engine.sceneBounds();
            int u=U(),v=V();
            minU=bounds[0][u];maxU=bounds[1][u];minV=bounds[0][v];maxV=bounds[1][v];
            centerU=(maxU+minU)*.5f;centerV=(maxV+minV)*.5f;
            float rangeU=Math.max(.3f,maxU-minU),rangeV=Math.max(.3f,maxV-minV);
            scale=Math.min((getWidth()-dp(50))/rangeU,(getHeight()-dp(50))/rangeV);
            if(!Float.isFinite(scale)||scale<1)scale=1;
            scale*=.91f;
        }
        @Override protected void onDraw(Canvas canvas){
            super.onDraw(canvas);
            canvas.drawColor(Color.rgb(20,26,35));
            if(engine==null||selected==null)return;
            measure();
            if(reference!=null&&showReference){
                paint.setStyle(Paint.Style.FILL);paint.setColor(Color.WHITE);paint.setAlpha(90);
                float ratio=Math.min((float)getWidth()/reference.getWidth(),(float)getHeight()/reference.getHeight());
                int w=(int)(reference.getWidth()*ratio),h=(int)(reference.getHeight()*ratio);
                canvas.drawBitmap(reference,null,new android.graphics.Rect((getWidth()-w)/2,(getHeight()-h)/2,
                        (getWidth()+w)/2,(getHeight()+h)/2),paint);
                paint.setAlpha(255);
            }
            // True metric rulers. Gray meshes retain visual relation to nearby
            // parts. Selected mesh shows actual triangle edges, not a fake image.
            setColor(Color.rgb(53,68,80),dp(.65f));
            float startU=(float)Math.floor(minU);
            for(float u=startU;u<=maxU+1;u+=1f)
                canvas.drawLine(sx(u),0,sx(u),getHeight(),paint);
            for(float v=(float)Math.floor(minV);v<=maxV+1;v+=1f)
                canvas.drawLine(0,sy(v),getWidth(),sy(v),paint);

            for(GlbSurfaceEditor.Part part:engine.parts()){
                float[][] bounds=part.bounds();
                if(part!=selected){
                    setColor(Color.argb(90,141,157,176),dp(.7f));
                    canvas.drawRect(Math.min(sx(bounds[0][U()]),sx(bounds[1][U()])),
                            Math.min(sy(bounds[0][V()]),sy(bounds[1][V()])),
                            Math.max(sx(bounds[0][U()]),sx(bounds[1][U()])),
                            Math.max(sy(bounds[0][V()]),sy(bounds[1][V()])),paint);
                    continue;
                }
                setColor(Color.rgb(40,221,204),dp(.8f));
                int triangles=part.indices.length/3,step=Math.max(1,triangles/2000);
                for(int f=0;f<part.indices.length;f+=3*step){
                    float[] a=part.vertices[part.indices[f]];
                    float[] b=part.vertices[part.indices[f+1]];
                    float[] c=part.vertices[part.indices[f+2]];
                    canvas.drawLine(sx(a[U()]),sy(a[V()]),sx(b[U()]),sy(b[V()]),paint);
                    canvas.drawLine(sx(b[U()]),sy(b[V()]),sx(c[U()]),sy(c[V()]),paint);
                    canvas.drawLine(sx(c[U()]),sy(c[V()]),sx(a[U()]),sy(a[V()]),paint);
                }
                // Surface cage squares approximate editable cross-section regions;
                // they are controls, not claims about the model's source topology.
                setColor(Color.argb(105,250,198,84),dp(.9f));
                float a=bounds[0][U()],b=bounds[1][U()];
                float c=bounds[0][V()],d=bounds[1][V()];
                for(int j=0;j<=8;j++){
                    float z=a+(b-a)*j/8f;
                    canvas.drawLine(sx(z),sy(c),sx(z),sy(d),paint);
                }
                for(int j=0;j<=4;j++){
                    float z=c+(d-c)*j/4f;
                    canvas.drawLine(sx(a),sy(z),sx(b),sy(z),paint);
                }
            }
            if(stroke!=null){
                setColor(Color.argb(180,255,201,95),dp(1.5f));
                canvas.drawCircle(downX,downY,radius*scale,paint);
            }
            paint.setColor(TEXT);paint.setStyle(Paint.Style.FILL);paint.setTextSize(dp(11));
            canvas.drawText("Surface cage / "+new String[]{"SIDE","TOP","FRONT"}[cameraView]+" • drag cyan geometry",dp(12),dp(21),paint);
        }
        @Override public boolean onTouchEvent(MotionEvent e){
            if(engine==null||selected==null)return true;
            if(e.getPointerCount()!=1){stroke=null;return true;}
            int action=e.getActionMasked();
            if(action==MotionEvent.ACTION_DOWN){
                measure();
                float[][] bounds=selected.bounds();
                float u=fromX(e.getX()),v=fromY(e.getY());
                if(u<bounds[0][U()]-.25||u>bounds[1][U()]+.25||
                        v<bounds[0][V()]-.25||v>bounds[1][V()]+.25)return true;
                float[] at={0,0,0};
                for(int j=0;j<3;j++)at[j]=(bounds[0][j]+bounds[1][j])*.5f;
                at[U()]=u;at[V()]=v;
                stroke=engine.beginStroke(selected,at,cameraView,radius,mirrorCheck.isChecked());
                downX=e.getX();downY=e.getY();moved=false;
                invalidate();return true;
            }
            if(action==MotionEvent.ACTION_MOVE){
                if(stroke==null)return true;
                float du=fromX(e.getX())-fromX(downX);
                float dv=fromY(e.getY())-fromY(downY);
                stroke.apply(du,dv);moved=Math.abs(du)+Math.abs(dv)>.002f;
                invalidate();return true;
            }
            if(action==MotionEvent.ACTION_UP){
                if(stroke!=null&&moved)engine.commit(stroke);
                stroke=null;invalidate();return true;
            }
            if(action==MotionEvent.ACTION_CANCEL){
                // Interrupted drag is rolled back and cannot be committed.
                if(stroke!=null){stroke.apply(0,0);stroke=null;invalidate();}
                return true;
            }
            return true;
        }
    }
}
