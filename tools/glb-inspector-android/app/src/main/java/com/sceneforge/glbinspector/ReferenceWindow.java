package com.sceneforge.glbinspector;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import android.graphics.drawable.GradientDrawable;

import java.io.InputStream;

/**
 * Offline floating photo reference for model revision inspection.
 * Uses local Android document URIs and remembers size, location and last granted reference.
 * Can be dragged, pinned, resized, collapsed/expanded or hidden. No network permission.
 */
public final class ReferenceWindow extends FrameLayout {
    private static final String PREFS = "sceneforge_reference_v1";
    private final Activity activity;
    private final SharedPreferences prefs;
    private final Runnable onChoose;
    private ImageView image;
    private TextView label, empty;
    private Button pinButton, opacityButton;
    private boolean pinned, expanded, applyingPosition;
    private float startRawX, startRawY, startX, startY;
    private int startW, startH, opacityStep;
    private float lastXFraction = 0.5f, lastYFraction = 0.45f;
    private String referenceName = "";
    private Uri referenceUri;
    private int dp(float x) {
        return (int) (x * getResources().getDisplayMetrics().density + 0.5f);
    }

    public ReferenceWindow(Activity activity, Runnable onChoose) {
        super(activity);
        this.activity = activity;
        this.onChoose = onChoose;
        this.prefs = activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        pinned = prefs.getBoolean("pinned", false);
        opacityStep = prefs.getInt("opacity", 0);
        lastXFraction = prefs.getFloat("x", 0.5f);
        lastYFraction = prefs.getFloat("y", 0.45f);
        build();
        String remembered = prefs.getString("uri", "");
        if (!remembered.isEmpty()) {
            try { loadImage(Uri.parse(remembered), prefs.getString("name", "REFERENCE")); }
            catch (Exception ignored) {}
        }
    }

    private GradientDrawable background(int fill, int border) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(fill);
        drawable.setCornerRadius(dp(10));
        drawable.setStroke(dp(1), border);
        return drawable;
    }
    private Button miniButton(String title) {
        Button b = new Button(activity);
        b.setAllCaps(false);
        b.setText(title);
        b.setTextSize(10);
        b.setMinWidth(0);
        b.setMinimumWidth(0);
        b.setPadding(0, 0, 0, 0);
        b.setTextColor(Color.rgb(231, 241, 248));
        b.setBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.rgb(39, 54, 66)));
        return b;
    }

    private void build() {
        setBackground(background(Color.rgb(20, 27, 35), Color.rgb(93, 133, 148)));
        setElevation(dp(13));
        setClipToOutline(true);

        LinearLayout body = new LinearLayout(activity);
        body.setOrientation(LinearLayout.VERTICAL);
        addView(body, new FrameLayout.LayoutParams(-1, -1));

        LinearLayout header = new LinearLayout(activity);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(8), dp(1), dp(4), dp(1));
        header.setBackgroundColor(Color.rgb(27, 37, 47));
        label = new TextView(activity);
        label.setText("REFERENCE  ·  TAP LOAD");
        label.setTextSize(11);
        label.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        label.setTextColor(Color.rgb(230, 237, 245));
        label.setSingleLine();
        label.setEllipsize(android.text.TextUtils.TruncateAt.END);
        header.addView(label, new LinearLayout.LayoutParams(0, dp(40), 1f));

        pinButton = miniButton(pinned ? "UNPIN" : "PIN");
        pinButton.setOnClickListener(v -> {
            pinned = !pinned;
            pinButton.setText(pinned ? "UNPIN" : "PIN");
            prefs.edit().putBoolean("pinned", pinned).apply();
        });
        header.addView(pinButton, new LinearLayout.LayoutParams(dp(46), dp(34)));

        opacityButton = miniButton("100%");
        opacityButton.setOnClickListener(v -> {
            opacityStep = (opacityStep + 1) % 3;
            applyOpacity();
            prefs.edit().putInt("opacity", opacityStep).apply();
        });
        header.addView(opacityButton, new LinearLayout.LayoutParams(dp(48), dp(34)));

        Button expand = miniButton("⛶");
        expand.setOnClickListener(v -> toggleExpand());
        header.addView(expand, new LinearLayout.LayoutParams(dp(33), dp(34)));
        Button close = miniButton("×");
        close.setOnClickListener(v -> { savePosition(); setVisibility(GONE); });
        header.addView(close, new LinearLayout.LayoutParams(dp(30), dp(34)));

        body.addView(header, new LinearLayout.LayoutParams(-1, dp(41)));

        FrameLayout photoArea = new FrameLayout(activity);
        photoArea.setBackgroundColor(Color.rgb(40, 47, 54));
        image = new ImageView(activity);
        image.setScaleType(ImageView.ScaleType.FIT_CENTER);
        image.setAdjustViewBounds(false);
        photoArea.addView(image, new FrameLayout.LayoutParams(-1, -1));
        empty = new TextView(activity);
        empty.setText("PHOTO REFERENCE\n\nTap here to load a PNG or JPG");
        empty.setTextSize(12);
        empty.setGravity(Gravity.CENTER);
        empty.setTextColor(Color.rgb(178, 199, 209));
        photoArea.addView(empty, new FrameLayout.LayoutParams(-1, -1));
        photoArea.setOnClickListener(v -> onChoose.run());
        body.addView(photoArea, new LinearLayout.LayoutParams(-1, 0, 1f));

        TextView grip = new TextView(activity);
        grip.setText("  LOAD PHOTO                     ⋰ RESIZE");
        grip.setTextSize(10);
        grip.setGravity(Gravity.CENTER_VERTICAL);
        grip.setTextColor(Color.rgb(181, 204, 213));
        grip.setBackgroundColor(Color.rgb(27, 37, 47));
        grip.setOnClickListener(v -> onChoose.run());
        body.addView(grip, new LinearLayout.LayoutParams(-1, dp(23)));

        View resizeHandle = new View(activity);
        resizeHandle.setBackground(background(Color.rgb(57, 130, 139), Color.rgb(156, 214, 223)));
        FrameLayout.LayoutParams resizeParams =
                new FrameLayout.LayoutParams(dp(28), dp(28), Gravity.RIGHT | Gravity.BOTTOM);
        addView(resizeHandle, resizeParams);
        resizeHandle.setOnTouchListener((v, event) -> {
            if (pinned) return true;
            switch (event.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    startRawX = event.getRawX();
                    startRawY = event.getRawY();
                    startW = getWidth();
                    startH = getHeight();
                    return true;
                case MotionEvent.ACTION_MOVE:
                    FrameLayout parent = getParent() instanceof FrameLayout ? (FrameLayout) getParent() : null;
                    if (parent == null) return true;
                    FrameLayout.LayoutParams params = (FrameLayout.LayoutParams) getLayoutParams();
                    params.width = Math.min(parent.getWidth() - (int)getX() - dp(6),
                            Math.max(dp(185), startW + (int)(event.getRawX() - startRawX)));
                    params.height = Math.min(parent.getHeight() - (int)getY() - dp(6),
                            Math.max(dp(125), startH + (int)(event.getRawY() - startRawY)));
                    params.width = Math.max(dp(120), params.width);
                    params.height = Math.max(dp(100), params.height);
                    setLayoutParams(params);
                    return true;
                case MotionEvent.ACTION_UP:
                    savePosition();return true;
                default:return true;
            }
        });

        header.setOnTouchListener((v,event)->{
            if (pinned) return false;
            switch(event.getActionMasked()){
                case MotionEvent.ACTION_DOWN:
                    startRawX=event.getRawX();startRawY=event.getRawY();
                    startX=getX();startY=getY();
                    return true;
                case MotionEvent.ACTION_MOVE:
                    FrameLayout parent=getParent() instanceof FrameLayout?(FrameLayout)getParent():null;
                    if(parent==null)return true;
                    setX(Math.max(0,Math.min(parent.getWidth()-getWidth(),startX+event.getRawX()-startRawX)));
                    setY(Math.max(0,Math.min(parent.getHeight()-getHeight(),startY+event.getRawY()-startRawY)));
                    return true;
                case MotionEvent.ACTION_UP:savePosition();return true;
                default:return true;
            }
        });
        applyOpacity();
    }

    private void applyOpacity() {
        float alpha = opacityStep == 0 ? 1.0f : opacityStep == 1 ? 0.85f : 0.68f;
        setAlpha(alpha);
        opacityButton.setText(Math.round(alpha * 100) + "%");
    }

    public void loadImage(Uri uri, String name) {
        referenceUri = uri;
        referenceName = name == null ? "Reference photo" : name;
        label.setText("REFERENCE  ·  " + referenceName);
        prefs.edit().putString("uri", uri.toString()).putString("name", referenceName).apply();
        new Thread(() -> {
            try {
                BitmapFactory.Options bounds = new BitmapFactory.Options();
                bounds.inJustDecodeBounds = true;
                try (InputStream stream = activity.getContentResolver().openInputStream(uri)) {
                    if (stream == null) throw new IllegalArgumentException("Unreadable photo");
                    BitmapFactory.decodeStream(stream, null, bounds);
                }
                int sample=1;
                while(bounds.outWidth/sample>1600 || bounds.outHeight/sample>1600) sample*=2;
                BitmapFactory.Options opts = new BitmapFactory.Options();
                opts.inSampleSize=sample;
                Bitmap bitmap;
                try (InputStream stream = activity.getContentResolver().openInputStream(uri)) {
                    if (stream == null) throw new IllegalArgumentException("Unreadable photo");
                    bitmap=BitmapFactory.decodeStream(stream,null,opts);
                }
                if(bitmap==null)throw new IllegalArgumentException("Unsupported reference image");
                activity.runOnUiThread(()->{
                    image.setImageBitmap(bitmap);
                    empty.setVisibility(GONE);
                    setVisibility(VISIBLE);
                });
            } catch (Exception ex) {
                activity.runOnUiThread(()->Toast.makeText(activity,
                        "Photo load failed: "+ex.getMessage(),Toast.LENGTH_LONG).show());
            }
        }, "reference-decoder").start();
    }

    public String referenceName() { return referenceName; }
    public boolean hasImage() { return image.getDrawable() != null; }
    public boolean isPinned() { return pinned; }

    public void showPanel() {
        setVisibility(VISIBLE);
        post(this::restorePosition);
    }
    public void restorePosition() {
        if (!(getParent() instanceof FrameLayout)) return;
        FrameLayout parent=(FrameLayout)getParent();
        if (parent.getWidth()<1 || parent.getHeight()<1) return;
        FrameLayout.LayoutParams params=(FrameLayout.LayoutParams)getLayoutParams();
        int preferredW = prefs.getInt("width", dp(265));
        int preferredH = prefs.getInt("height", dp(188));
        params.width=Math.min(preferredW,Math.max(dp(165),parent.getWidth()-dp(12)));
        params.height=Math.min(preferredH,Math.max(dp(120),parent.getHeight()-dp(12)));
        setLayoutParams(params);
        post(()->{
            setX(Math.max(0,(parent.getWidth()-getWidth())*lastXFraction));
            setY(Math.max(0,(parent.getHeight()-getHeight())*lastYFraction));
        });
    }
    public void savePosition() {
        if (!(getParent() instanceof FrameLayout)) return;
        FrameLayout parent=(FrameLayout)getParent();
        if (parent.getWidth()<1 || parent.getHeight()<1) return;
        lastXFraction=Math.max(0f,Math.min(1f,getX()/Math.max(1,parent.getWidth()-getWidth())));
        lastYFraction=Math.max(0f,Math.min(1f,getY()/Math.max(1,parent.getHeight()-getHeight())));
        prefs.edit().putFloat("x",lastXFraction).putFloat("y",lastYFraction)
                .putInt("width",getWidth()).putInt("height",getHeight()).apply();
    }
    private void toggleExpand(){
        if(!(getParent() instanceof FrameLayout))return;
        FrameLayout parent=(FrameLayout)getParent();
        expanded=!expanded;
        if(!expanded){restorePosition();return;}
        savePosition();
        FrameLayout.LayoutParams p=(FrameLayout.LayoutParams)getLayoutParams();
        p.width=(int)(parent.getWidth()*0.89f);
        p.height=(int)(parent.getHeight()*0.79f);
        setLayoutParams(p);
        setX((parent.getWidth()-p.width)/2f);
        setY((parent.getHeight()-p.height)/2f);
    }
}
