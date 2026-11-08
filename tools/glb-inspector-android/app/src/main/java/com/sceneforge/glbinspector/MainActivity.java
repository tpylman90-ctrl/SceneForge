package com.sceneforge.glbinspector;

import android.app.Activity;
import android.content.ContentValues;
import android.content.Intent;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.Typeface;
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
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import com.google.android.filament.Filament;
import com.google.android.filament.Engine;
import com.google.android.filament.android.UiHelper;
import com.google.android.filament.utils.ModelViewer;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** Real offline GLB viewer. No WebView, user accounts, or network permission. */
public final class MainActivity extends Activity implements Choreographer.FrameCallback {
    private static final int PICK_MODEL = 240;
    private static final int BG = Color.rgb(11, 16, 25);
    private static final int PANEL = Color.rgb(26, 37, 54);
    private static final int TEXT = Color.rgb(227, 235, 245);
    private static final int MUTED = Color.rgb(151, 168, 190);
    private static final int ACCENT = Color.rgb(30, 188, 177);
    private final Handler handler = new Handler(Looper.getMainLooper());
    private SurfaceView surface;
    private ModelViewer viewer;
    private TextView title;
    private TextView status;
    private ScaleGestureDetector pinch;
    private boolean running = false;
    private boolean modelLoaded = false;
    private float azimuth = 33f, elevation = 18f, distance = 4.8f;
    private float lastX, lastY;
    private boolean wasPinching;
    private String modelName = "model";
    private int imageIndex = 1;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        Filament.init();
        buildUi();

        // A null manipulator leaves camera control to the app; presets are repeatable.
        viewer = new ModelViewer(surface, Engine.create(),
                new UiHelper(UiHelper.ContextErrorPolicy.DONT_CHECK), null);
        viewer.setAutoPlayAnimations(true);
        viewer.getView().setAntiAliasing(com.google.android.filament.View.AntiAliasing.FXAA);
        setCamera();
        pinch = new ScaleGestureDetector(this, new ScaleGestureDetector.SimpleOnScaleGestureListener() {
            @Override public boolean onScale(ScaleGestureDetector detector) {
                distance = clamp(distance / detector.getScaleFactor(), 2.0f, 18.0f);
                setCamera();
                wasPinching = true;
                return true;
            }
        });
        surface.setOnTouchListener((v, e) -> onModelTouch(e));
        Intent intent = getIntent();
        if (Intent.ACTION_VIEW.equals(intent.getAction()) && intent.getData() != null) {
            openUri(intent.getData());
        }
    }

    private void buildUi() {
        LinearLayout main = new LinearLayout(this);
        main.setOrientation(LinearLayout.VERTICAL);
        main.setBackgroundColor(BG);
        setContentView(main);

        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(dp(15), dp(12), dp(12), dp(8));
        title = new TextView(this);
        title.setText("SCENEFORGE  /  GLB INSPECTOR");
        title.setTextSize(17);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setTextColor(TEXT);
        bar.addView(title, new LinearLayout.LayoutParams(0, dp(42), 1));
        Button open = button("OPEN GLB");
        open.setOnClickListener(v -> chooseModel());
        bar.addView(open);
        main.addView(bar);

        status = new TextView(this);
        status.setText("Open a .glb from your phone. Drag to orbit • pinch to zoom.");
        status.setTextSize(12);
        status.setTextColor(MUTED);
        status.setPadding(dp(16), dp(0), dp(12), dp(9));
        main.addView(status);

        FrameLayout canvas = new FrameLayout(this);
        canvas.setBackgroundColor(Color.rgb(18, 25, 36));
        surface = new SurfaceView(this);
        canvas.addView(surface, new FrameLayout.LayoutParams(-1, -1));
        main.addView(canvas, new LinearLayout.LayoutParams(-1, 0, 1));

        HorizontalScrollView scroll = new HorizontalScrollView(this);
        scroll.setHorizontalScrollBarEnabled(false);
        LinearLayout presets = new LinearLayout(this);
        presets.setOrientation(LinearLayout.HORIZONTAL);
        presets.setPadding(dp(8), dp(9), dp(8), dp(8));
        addPreset(presets, "ISO", 33, 18);
        addPreset(presets, "FRONT", 180, 0);
        addPreset(presets, "REAR", 0, 0);
        addPreset(presets, "LEFT", -90, 0);
        addPreset(presets, "RIGHT", 90, 0);
        addPreset(presets, "TOP", 0, 89);
        addPreset(presets, "BOTTOM", 0, -89);
        scroll.addView(presets);
        main.addView(scroll);

        LinearLayout actions = new LinearLayout(this);
        actions.setPadding(dp(12), dp(4), dp(12), dp(13));
        actions.setGravity(Gravity.CENTER_VERTICAL);
        Button reset = button("RESET CAMERA");
        reset.setOnClickListener(v -> { azimuth = 33; elevation = 18; distance = 4.8f; setCamera(); });
        actions.addView(reset, new LinearLayout.LayoutParams(0, dp(45), 1));
        Button save = button("SAVE PNG");
        save.setOnClickListener(v -> saveSnapshot());
        LinearLayout.LayoutParams saveP = new LinearLayout.LayoutParams(0, dp(45), 1);
        saveP.leftMargin = dp(9);
        actions.addView(save, saveP);
        main.addView(actions);
    }

    private Button button(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextSize(12);
        b.setTextColor(TEXT);
        b.setAllCaps(false);
        b.setBackgroundTintList(android.content.res.ColorStateList.valueOf(PANEL));
        return b;
    }

    private void addPreset(LinearLayout row, String text, float az, float el) {
        Button b = button(text);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(dp(86), dp(45));
        p.rightMargin = dp(5);
        row.addView(b, p);
        b.setOnClickListener(v -> {
            azimuth = az;
            elevation = el;
            distance = 4.8f;
            setCamera();
        });
    }

    private boolean onModelTouch(MotionEvent e) {
        pinch.onTouchEvent(e);
        switch (e.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                lastX = e.getX();
                lastY = e.getY();
                wasPinching = false;
                return true;
            case MotionEvent.ACTION_POINTER_DOWN:
                wasPinching = true;
                return true;
            case MotionEvent.ACTION_MOVE:
                if (e.getPointerCount() == 1 && !wasPinching) {
                    azimuth += (e.getX() - lastX) * 0.4f;
                    elevation = clamp(elevation - (e.getY() - lastY) * 0.35f, -89f, 89f);
                    setCamera();
                }
                lastX = e.getX();
                lastY = e.getY();
                return true;
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                wasPinching = false;
                return true;
            default: return true;
        }
    }

    private static float clamp(float v, float lo, float hi) { return Math.max(lo, Math.min(hi, v)); }
    private void setCamera() {
        if (viewer == null) return;
        double a = Math.toRadians(azimuth), e = Math.toRadians(elevation);
        double x = distance * Math.cos(e) * Math.sin(a);
        double y = distance * Math.sin(e);
        double z = -4.0 + distance * Math.cos(e) * Math.cos(a);
        // Top and bottom views have a valid up vector to avoid lookAt degeneracy.
        double upZ = Math.abs(elevation) > 87 ? (elevation > 0 ? -1 : 1) : 0;
        double upY = Math.abs(elevation) > 87 ? 0 : 1;
        viewer.getCamera().lookAt(x, y, z, 0, 0, -4, 0, upY, upZ);
    }

    private void chooseModel() {
        Intent pick = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        pick.addCategory(Intent.CATEGORY_OPENABLE);
        pick.setType("*/*");
        startActivityForResult(pick, PICK_MODEL);
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == PICK_MODEL && result == RESULT_OK && data != null && data.getData() != null) {
            openUri(data.getData());
        }
    }

    private void openUri(Uri uri) {
        String name = getDisplayName(uri);
        if (!name.toLowerCase(Locale.ROOT).endsWith(".glb")) {
            error("Select a .glb model file.");
            return;
        }
        modelName = name.substring(0, name.length() - 4).replaceAll("[^a-zA-Z0-9_-]", "_");
        status.setText("Loading " + name + " …");
        new Thread(() -> {
            try {
                byte[] data;
                try (InputStream in = getContentResolver().openInputStream(uri);
                     ByteArrayOutputStream out = new ByteArrayOutputStream()) {
                    if (in == null) throw new IllegalArgumentException("Could not read file");
                    byte[] buf = new byte[16384];
                    int n;
                    while ((n = in.read(buf)) != -1) {
                        if (out.size() + n > 80 * 1024 * 1024)
                            throw new IllegalArgumentException("First version supports GLBs up to 80 MB");
                        out.write(buf, 0, n);
                    }
                    data = out.toByteArray();
                }
                if (data.length < 20 || data[0] != 'g' || data[1] != 'l'
                        || data[2] != 'T' || data[3] != 'F')
                    throw new IllegalArgumentException("Not a valid binary GLB");
                String summary = inspect(data);
                ByteBuffer buffer = ByteBuffer.allocateDirect(data.length);
                buffer.put(data);
                buffer.flip();
                runOnUiThread(() -> {
                    try {
                        viewer.loadModelGlb(buffer);
                        if (viewer.getAsset() == null)
                            throw new IllegalArgumentException("The renderer could not load this GLB");
                        viewer.transformToUnitCube();
                        modelLoaded = true;
                        azimuth = 33; elevation = 18; distance = 4.8f;
                        setCamera();
                        title.setText(name);
                        status.setText(summary);
                    } catch (Exception e) { error("GLB load failed: " + e.getMessage()); }
                });
            } catch (Exception ex) { runOnUiThread(() -> error(ex.getMessage())); }
        }, "glb-reader").start();
    }

    private String inspect(byte[] data) {
        try {
            ByteBuffer h = ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
            int length = h.getInt(12);
            int type = h.getInt(16);
            if (type != 0x4e4f534a || length <= 0 || length > data.length - 20)
                return "Valid GLB • statistics unavailable";
            JSONObject json = new JSONObject(new String(data, 20, length, StandardCharsets.UTF_8).trim());
            JSONArray meshes = json.optJSONArray("meshes");
            JSONArray accessors = json.optJSONArray("accessors");
            JSONArray materials = json.optJSONArray("materials");
            int triangles = 0;
            int count = meshes == null ? 0 : meshes.length();
            for (int i = 0; i < count; i++) {
                JSONArray primitives = meshes.getJSONObject(i).optJSONArray("primitives");
                if (primitives == null) continue;
                for (int k = 0; k < primitives.length(); k++) {
                    JSONObject prim = primitives.getJSONObject(k);
                    int mode = prim.optInt("mode", 4);
                    int accessor = prim.optInt("indices", -1);
                    if (accessor < 0) accessor = prim.optJSONObject("attributes").optInt("POSITION", -1);
                    if (accessor < 0 || accessors == null || accessor >= accessors.length()) continue;
                    int verts = accessors.getJSONObject(accessor).optInt("count", 0);
                    triangles += mode == 4 ? verts / 3 : (mode == 5 || mode == 6 ? Math.max(0, verts - 2) : 0);
                }
            }
            return "Meshes " + count + "   •   Source triangles " + triangles +
                    "   •   Materials " + (materials == null ? 0 : materials.length());
        } catch (Exception ignored) { return "GLB opened • statistics unavailable"; }
    }

    private String getDisplayName(Uri uri) {
        try (Cursor c = getContentResolver().query(uri, null, null, null, null)) {
            if (c != null && c.moveToFirst()) {
                int col = c.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (col >= 0) return c.getString(col);
            }
        } catch (Exception ignored) {}
        String path = uri.getLastPathSegment();
        return path == null ? "model.glb" : path;
    }

    private void saveSnapshot() {
        if (!modelLoaded) { error("Open a GLB first."); return; }
        if (surface.getWidth() < 1 || surface.getHeight() < 1) {
            error("Viewer is not ready."); return;
        }
        Bitmap bmp = Bitmap.createBitmap(surface.getWidth(), surface.getHeight(), Bitmap.Config.ARGB_8888);
        PixelCopy.request(surface, bmp, result -> {
            if (result != PixelCopy.SUCCESS) { bmp.recycle(); error("Could not capture rendered frame."); return; }
            String filename = modelName + "_" +
                    new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date()) +
                    "_" + (imageIndex++) + ".png";
            new Thread(() -> {
                try {
                    if (Build.VERSION.SDK_INT >= 29) {
                        ContentValues values = new ContentValues();
                        values.put(MediaStore.Images.Media.DISPLAY_NAME, filename);
                        values.put(MediaStore.Images.Media.MIME_TYPE, "image/png");
                        values.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/SceneForge Inspector");
                        values.put(MediaStore.Images.Media.IS_PENDING, 1);
                        Uri dest = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
                        if (dest == null) throw new IllegalStateException("Gallery storage unavailable");
                        try {
                            try (OutputStream out = getContentResolver().openOutputStream(dest)) {
                                if (out == null || !bmp.compress(Bitmap.CompressFormat.PNG, 100, out))
                                    throw new IllegalStateException("PNG write failed");
                            }
                            values.clear();
                            values.put(MediaStore.Images.Media.IS_PENDING, 0);
                            getContentResolver().update(dest, values, null, null);
                        } catch (Exception ex) { getContentResolver().delete(dest, null, null); throw ex; }
                    } else {
                        File dir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
                        if (dir == null) throw new IllegalStateException("No picture storage");
                        try (OutputStream out = new FileOutputStream(new File(dir, filename))) {
                            if (!bmp.compress(Bitmap.CompressFormat.PNG, 100, out))
                                throw new IllegalStateException("PNG write failed");
                        }
                    }
                    runOnUiThread(() -> Toast.makeText(this, "Saved PNG: " + filename, Toast.LENGTH_LONG).show());
                } catch (Exception e) { runOnUiThread(() -> error("PNG failed: " + e.getMessage())); }
                finally { bmp.recycle(); }
            }, "png-writer").start();
        }, handler);
    }

    private void error(String s) {
        status.setText(s);
        Toast.makeText(this, s, Toast.LENGTH_LONG).show();
    }
    private int dp(float v) { return (int)(v * getResources().getDisplayMetrics().density + 0.5f); }

    @Override protected void onResume() {
        super.onResume();
        running = true;
        Choreographer.getInstance().postFrameCallback(this);
    }
    @Override protected void onPause() {
        running = false;
        Choreographer.getInstance().removeFrameCallback(this);
        super.onPause();
    }
    @Override public void doFrame(long frameTimeNanos) {
        if (!running) return;
        if (viewer != null) viewer.render(frameTimeNanos);
        Choreographer.getInstance().postFrameCallback(this);
    }
}
