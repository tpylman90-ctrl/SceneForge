package com.sceneforge.glbinspector;

import android.app.Activity;
import android.content.ContentValues;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.provider.MediaStore;
import android.util.Log;
import android.widget.Toast;

import com.google.android.filament.Engine;
import com.google.android.filament.RenderTarget;
import com.google.android.filament.Renderer;
import com.google.android.filament.Texture;
import com.google.android.filament.View;
import com.google.android.filament.Viewport;
import com.google.android.filament.utils.ModelViewer;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.util.Locale;

/**
 * Real offscreen Filmament GPU render at higher-than-screen resolution.
 * This is not a PixelCopy upscale: it creates an independent render target,
 * rerenders actual GLB geometry, and reads back its real GPU pixels.
 */
public final class HiResCapture {
    private static final String TAG="SCENEFORGE_HIRES";
    private HiResCapture(){}

    public static void capture(Activity activity, ModelViewer viewer, int screenWidth,
                               int screenHeight, int magnification, String filename) {
        if(viewer==null || viewer.getAsset()==null) {
            Toast.makeText(activity,"Open a GLB first",Toast.LENGTH_LONG).show();return;
        }
        int multiplier=Math.max(1,Math.min(4,magnification));
        int width=Math.min(4096,screenWidth*multiplier);
        int height=Math.min(4096,screenHeight*multiplier);
        final int safeMaxPixels=11_000_000; // ~44 MB GPU RGBA plus readback bitmap
        if((long)width*height>safeMaxPixels){
            double scale=Math.sqrt(safeMaxPixels/((double)width*height));
            width=Math.max(1,(int)(width*scale));
            height=Math.max(1,(int)(height*scale));
        }
        if(width<=0||height<=0)return;
        Engine engine=viewer.getEngine();
        Renderer renderer=viewer.getRenderer();
        Texture color=null, depth=null;
        RenderTarget target=null;
        View captureView=null;
        try {
            color=new Texture.Builder().width(width).height(height).levels(1)
                    .sampler(Texture.Sampler.SAMPLER_2D)
                    .format(Texture.InternalFormat.RGBA8)
                    .usage(Texture.Usage.COLOR_ATTACHMENT | Texture.Usage.SAMPLEABLE | Texture.Usage.BLIT_SRC)
                    .build(engine);
            depth=new Texture.Builder().width(width).height(height).levels(1)
                    .sampler(Texture.Sampler.SAMPLER_2D)
                    .format(Texture.InternalFormat.DEPTH24)
                    .usage(Texture.Usage.DEPTH_ATTACHMENT)
                    .build(engine);
            target=new RenderTarget.Builder()
                    .texture(RenderTarget.AttachmentPoint.COLOR0,color)
                    .texture(RenderTarget.AttachmentPoint.DEPTH,depth)
                    .build(engine);
            captureView=engine.createView();
            captureView.setScene(viewer.getScene());
            captureView.setCamera(viewer.getCamera());
            captureView.setRenderTarget(target);
            captureView.setViewport(new Viewport(0,0,width,height));
            StudioQuality.apply(engine,captureView,viewer.getCamera(),StudioQuality.Preset.PHOTO);
            renderer.renderStandaloneView(captureView);

            final View viewFinal=captureView;
            final Texture colorFinal=color,depthFinal=depth;
            final RenderTarget targetFinal=target;
            final int w=width,h=height;
            final ByteBuffer pixels=ByteBuffer.allocateDirect(w*h*4);
            final Handler handler=new Handler(Looper.getMainLooper());
            renderer.readPixels(targetFinal,0,0,w,h,
                    new Texture.PixelBufferDescriptor(pixels,Texture.Format.RGBA,Texture.Type.UBYTE,
                            handler,()->{
                        try{
                            pixels.rewind();
                            int[] argb=new int[w*h];
                            // OpenGL / Filament readback starts at bottom-left.
                            for(int y=0;y<h;y++){
                                int destRow=(h-1-y)*w;
                                for(int x=0;x<w;x++){
                                    int r=pixels.get()&255,g=pixels.get()&255;
                                    int b=pixels.get()&255,a=pixels.get()&255;
                                    argb[destRow+x]=Color.argb(a,r,g,b);
                                }
                            }
                            Bitmap bmp=Bitmap.createBitmap(argb,w,h,Bitmap.Config.ARGB_8888);
                            new Thread(()->{
                                try{
                                    save(activity,bmp,filename);
                                    activity.runOnUiThread(()->Toast.makeText(activity,
                                            "Saved real "+w+"×"+h+" HDR studio render",Toast.LENGTH_LONG).show());
                                }catch(Exception ex){
                                    activity.runOnUiThread(()->Toast.makeText(activity,
                                            "High-resolution save failed: "+ex.getMessage(),
                                            Toast.LENGTH_LONG).show());
                                }finally{bmp.recycle();}
                            },"hires-image-save").start();
                            Log.i(TAG,"REAL_OFFSCREEN_RENDER_SAVED "+w+"x"+h);
                        }catch(Throwable ex){
                            Log.e(TAG,"Offscreen capture failed",ex);
                            Toast.makeText(activity,"High-res render failed: "+ex.getMessage(),
                                    Toast.LENGTH_LONG).show();
                        }finally {
                            release(engine,viewFinal,targetFinal,colorFinal,depthFinal);
                        }
                    }));
            Toast.makeText(activity,"Rendering at "+w+"×"+h+" pixels",Toast.LENGTH_SHORT).show();
        }catch(Throwable ex){
            Log.e(TAG,"Unable to start high-resolution capture",ex);
            release(engine,captureView,target,color,depth);
            Toast.makeText(activity,"High-resolution render unavailable: "+ex.getMessage(),
                    Toast.LENGTH_LONG).show();
        }
    }
    private static void release(Engine e,View v,RenderTarget t,Texture color,Texture depth){
        try{
            if(v!=null){StudioQuality.release(e,v);v.setRenderTarget(null);e.destroyView(v);}
            if(t!=null)e.destroyRenderTarget(t);
            if(color!=null)e.destroyTexture(color);
            if(depth!=null)e.destroyTexture(depth);
        }catch(Throwable ex){Log.w(TAG,"Offscreen cleanup",ex);}
    }
    private static void save(Activity activity,Bitmap bmp,String filename)throws Exception {
        if(Build.VERSION.SDK_INT>=29){
            ContentValues values=new ContentValues();
            values.put(MediaStore.Images.Media.DISPLAY_NAME,filename);
            values.put(MediaStore.Images.Media.MIME_TYPE,"image/png");
            values.put(MediaStore.Images.Media.RELATIVE_PATH,Environment.DIRECTORY_PICTURES+"/SceneForge Inspector");
            values.put(MediaStore.Images.Media.IS_PENDING,1);
            Uri uri=activity.getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI,values);
            if(uri==null)throw new IllegalStateException("Image MediaStore unavailable");
            try{
                try(OutputStream out=activity.getContentResolver().openOutputStream(uri)){
                    if(out==null||!bmp.compress(Bitmap.CompressFormat.PNG,100,out))
                        throw new IllegalStateException("PNG write failed");
                }
                values.clear();values.put(MediaStore.Images.Media.IS_PENDING,0);
                activity.getContentResolver().update(uri,values,null,null);
            }catch(Exception ex){activity.getContentResolver().delete(uri,null,null);throw ex;}
        }else{
            File dir=activity.getExternalFilesDir(Environment.DIRECTORY_PICTURES);
            if(dir==null)throw new IllegalStateException("Storage unavailable");
            try(OutputStream out=new FileOutputStream(new File(dir,filename))){
                if(!bmp.compress(Bitmap.CompressFormat.PNG,100,out))
                    throw new IllegalStateException("PNG write failed");
            }
        }
    }
}
