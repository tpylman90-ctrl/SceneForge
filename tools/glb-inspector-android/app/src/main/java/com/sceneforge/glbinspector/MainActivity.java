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
import android.view.WindowInsets;
import com.google.android.filament.IndirectLight;
import com.google.android.filament.LightManager;
import com.google.android.filament.Skybox;
import com.google.android.filament.Texture;
import com.google.android.filament.EntityManager;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import com.google.android.filament.Filament;
import com.google.android.filament.gltfio.Gltfio;
import com.google.android.filament.Engine;
import com.google.android.filament.android.UiHelper;
import com.google.android.filament.utils.ModelViewer;
import com.google.android.filament.utils.Float3;
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
    private boolean studioEnabled = true;
    private Button studioButton;
    private byte[] sourceGlb;
    private ByteBuffer displayedGlb;
    private GlbInspectionVariants.Mode displayMode = GlbInspectionVariants.Mode.TEXTURED;
    private final Button[] modeButtons = new Button[3];
    private boolean modeBusy = false;
    private String sourceSummary = "";
    private long openRequest = 0;
    // Keep all studio lighting local. No network, HDR download, or model alterations.
    private static final float[] STUDIO_LEVELS = {16000f, 26000f, 38000f, 54000f};
    private int studioLevel = 2;
    private Button lightButton;
    private IndirectLight studioIbl;
    private Texture reflectionCube;
    private Skybox studioBackground;
    private final int[] studioLights = new int[3];

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        // ModelViewer uses gltfio JNI in its constructor. Filament.init() alone is insufficient.
        Gltfio.init();
        buildUi();

        // A null manipulator leaves camera control to the app; presets are repeatable.
        viewer = new ModelViewer(surface, Engine.create(),
                new UiHelper(UiHelper.ContextErrorPolicy.DONT_CHECK), null);
        viewer.setAutoPlayAnimations(true);
        viewer.getView().setAntiAliasing(com.google.android.filament.View.AntiAliasing.FXAA);
        setupStudioLighting();
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
        if(intent.getBooleanExtra("sceneforge_launch_shape_lab_test",false)) {
            handler.postDelayed(() -> startActivity(new Intent(this, ShapeLabActivity.class)
                    .putExtra("sceneforge_verify_shape_lab",true)), 1000);
        }
        // Launch the non-exported comparison screen through this application's own UID.
        // This exists only for the Android emulator integration test.
        if (intent.getBooleanExtra("sceneforge_launch_compare_test", false)) {
            handler.postDelayed(() -> startActivity(new Intent(this, CompareActivity.class)
                    .putExtra("sceneforge_verify_compare", true)), 1100);
        }
        if (intent.getBooleanExtra("sceneforge_verify_modes", false)) {
            handler.postDelayed(this::verifyModesForCi, 1500L);
        }
        if (Intent.ACTION_VIEW.equals(intent.getAction()) && intent.getData() != null) {
            openUri(intent.getData());
        }
    }

    /** Run only when explicitly invoked by the GitHub Android emulator smoke test. */
    private void verifyModesForCi() {
        new Thread(() -> {
            try {
                byte[] square = GlbInspectionVariants.diagnosticSquare();
                byte[] clay = GlbInspectionVariants.create(square, GlbInspectionVariants.Mode.CLAY);
                byte[] wire = GlbInspectionVariants.create(square, GlbInspectionVariants.Mode.WIREFRAME);
                // A two-triangle square must have five distinct real topology edges.
                ByteBuffer h = ByteBuffer.wrap(wire).order(ByteOrder.LITTLE_ENDIAN);
                JSONObject root = new JSONObject(new String(wire, 20, h.getInt(12),
                        StandardCharsets.UTF_8).trim());
                JSONObject prim = root.getJSONArray("meshes").getJSONObject(0)
                        .getJSONArray("primitives").getJSONObject(0);
                JSONObject indices = root.getJSONArray("accessors").getJSONObject(prim.getInt("indices"));
                if (prim.getInt("mode") != 1 || indices.getInt("count") != 10) {
                    throw new IllegalStateException("Wireframe edges did not match indexed triangles");
                }
                runOnUiThread(() -> {
                    try {
                        byte[][] models = {square, clay, wire, square};
                        String[] labels = {"TEXTURED", "CLAY", "WIREFRAME", "RESTORED"};
                        for (int i = 0; i < models.length; i++) {
                            ByteBuffer payload = ByteBuffer.allocateDirect(models[i].length);
                            payload.put(models[i]).flip();
                            viewer.loadModelGlb(payload);
                            if (viewer.getAsset() == null) {
                                throw new IllegalStateException(labels[i] + " did not load into Filament");
                            }
                            viewer.transformToUnitCube(new Float3(0f, 0f, -4f));
                            displayedGlb = payload;
                            android.util.Log.i("SCENEFORGE_MODE_TEST", labels[i] + "_PASSED");
                        }
                        sourceGlb = square;
                        sourceSummary = "Native GLB mode verification";
                        modelLoaded = true;
                        displayMode = GlbInspectionVariants.Mode.TEXTURED;
                        syncModeButtons();
                        status.setText(sourceSummary);
                        android.util.Log.i("SCENEFORGE_MODE_TEST", "ALL_MODES_PASSED");
                    } catch (Throwable ex) {
                        android.util.Log.e("SCENEFORGE_MODE_TEST", "FAILED", ex);
                        status.setText("Mode test failed: " + ex.getMessage());
                    }
                });
            } catch (Throwable ex) {
                android.util.Log.e("SCENEFORGE_MODE_TEST", "FAILED", ex);
            }
        }, "glb-mode-diagnostic").start();
    }

    private void buildUi() {
        LinearLayout main = new LinearLayout(this);
        main.setOrientation(LinearLayout.VERTICAL);
        main.setBackgroundColor(BG);
        setContentView(main);
        // Android 15/16 enforce edge-to-edge for target 35. Keep controls inside system bars.
        main.setOnApplyWindowInsetsListener((v, insets) -> {
            int left, right, top, bottom;
            if (Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars());
                left = bars.left; right = bars.right;
                top = bars.top; bottom = bars.bottom;
            } else {
                left = insets.getSystemWindowInsetLeft();
                right = insets.getSystemWindowInsetRight();
                top = insets.getSystemWindowInsetTop();
                bottom = insets.getSystemWindowInsetBottom();
            }
            v.setPadding(left, top, right, bottom);
            return insets;
        });
        main.requestApplyInsets();

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
        addPreset(presets, "SIDE", 90, 0);
        addPreset(presets, "ISO", 33, 18);
        addPreset(presets, "FRONT", 180, 0);
        addPreset(presets, "REAR", 0, 0);
        addPreset(presets, "LEFT", -90, 0);
        addPreset(presets, "RIGHT", 90, 0);
        addPreset(presets, "TOP", 0, 89);
        addPreset(presets, "BOTTOM", 0, -89);
        scroll.addView(presets);
        main.addView(scroll);

        // Inspection modes are separate from camera angles, and do not alter the source file.
        LinearLayout modeRow = new LinearLayout(this);
        modeRow.setGravity(Gravity.CENTER_VERTICAL);
        modeRow.setPadding(dp(12), dp(2), dp(12), dp(3));
        addModeButton(modeRow, "TEXTURED", GlbInspectionVariants.Mode.TEXTURED, 0);
        addModeButton(modeRow, "CLAY", GlbInspectionVariants.Mode.CLAY, 1);
        addModeButton(modeRow, "WIREFRAME", GlbInspectionVariants.Mode.WIREFRAME, 2);
        main.addView(modeRow);
        syncModeButtons();

        LinearLayout utilities = new LinearLayout(this);
        utilities.setGravity(Gravity.CENTER_VERTICAL);
        utilities.setPadding(dp(12), dp(3), dp(12), dp(3));
        Button compareButton = button("COMPARE TWO GLBs");
        compareButton.setOnClickListener(v ->
                startActivity(new Intent(this, CompareActivity.class)));
        utilities.addView(compareButton, new LinearLayout.LayoutParams(0, dp(44), 1f));
        studioButton = button("STUDIO ON");
        studioButton.setBackgroundTintList(android.content.res.ColorStateList.valueOf(ACCENT));
        studioButton.setTextColor(BG);
        studioButton.setOnClickListener(v -> {
            studioEnabled = !studioEnabled;
            studioButton.setText(studioEnabled ? "STUDIO ON" : "STUDIO OFF");
            studioButton.setBackgroundTintList(android.content.res.ColorStateList.valueOf(
                    studioEnabled ? ACCENT : PANEL));
            studioButton.setTextColor(studioEnabled ? BG : TEXT);
            if (modelLoaded) displayAs(displayMode, true);
        });
        LinearLayout.LayoutParams studioParams = new LinearLayout.LayoutParams(0, dp(44), 0.65f);
        studioParams.leftMargin = dp(8);
        utilities.addView(studioButton, studioParams);
        main.addView(utilities);

        Button shapeLab=button("SHAPE LAB  •  EDIT ACTUAL GEOMETRY");
        shapeLab.setBackgroundTintList(android.content.res.ColorStateList.valueOf(ACCENT));
        shapeLab.setTextColor(BG);
        shapeLab.setOnClickListener(v -> openShapeLab());
        LinearLayout.LayoutParams shapeParams=new LinearLayout.LayoutParams(-1,dp(43));
        shapeParams.setMargins(dp(12),0,dp(12),dp(4));
        main.addView(shapeLab,shapeParams);

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
        lightButton = button("LIGHT 3/4");
        lightButton.setOnClickListener(v -> {
            studioLevel = (studioLevel + 1) % STUDIO_LEVELS.length;
            if (studioIbl != null) studioIbl.setIntensity(STUDIO_LEVELS[studioLevel]);
            lightButton.setText("LIGHT " + (studioLevel + 1) + "/4");
        });
        LinearLayout.LayoutParams lightP = new LinearLayout.LayoutParams(0, dp(45), 0.8f);
        lightP.leftMargin = dp(9);
        actions.addView(lightButton, lightP);
        main.addView(actions);
    }

    /**
     * Offline environment lighting. Filament requires an IBL for metallic GLB materials
     * to reflect their surroundings. A few direct lights alone leave painted metal black.
     * We synthesize a neutral HDR-like multi-softbox reflection cubemap in linear RGB.
     * The mip levels approximate progressively rougher reflections for glTF PBR surfaces.
     */
    private void setupStudioLighting() {
        Engine engine = viewer.getEngine();

        // Subtle slate backdrop instead of the renderer's default black sky.
        studioBackground = new Skybox.Builder()
                .color(0.095f, 0.12f, 0.16f, 1.0f)
                .build(engine);
        viewer.getScene().setSkybox(studioBackground);
        // Sun built into ModelViewer casts the floor shadow; retain it in studio mode.

        reflectionCube = new Texture.Builder()
                .width(32).height(32).levels(6)
                .sampler(Texture.Sampler.SAMPLER_CUBEMAP)
                .format(Texture.InternalFormat.RGBA8)
                .build(engine);
        for (int level = 0; level < 6; level++) {
            int dim = Math.max(1, 32 >> level);
            ByteBuffer pixels = ByteBuffer.allocateDirect(dim * dim * 6 * 4);
            for (int face = 0; face < 6; face++) {
                for (int y = 0; y < dim; y++) {
                    for (int x = 0; x < dim; x++) {
                        float u = (2f * (x + 0.5f) / dim) - 1f;
                        float v = (2f * (y + 0.5f) / dim) - 1f;
                        float[] d = cubeDirection(face, u, v);
                        float rough = level / 5f;
                        // Broad softbox overhead, cool left bounce and warm right strip.
                        float roof = softPanel(d, -0.25f, 0.85f, -0.36f,
                                0.45f + rough * 0.45f, 0.22f + rough * 0.65f);
                        float left = softPanel(d, -0.80f, 0.25f, 0.45f,
                                0.28f + rough * 0.55f, 0.42f + rough * 0.55f);
                        float right = softPanel(d, 0.88f, 0.42f, -0.05f,
                                0.25f + rough * 0.60f, 0.60f + rough * 0.55f);
                        float base = 0.45f + 0.13f * Math.max(0f, d[1]);
                        float contrast = 1.0f - 0.55f * rough;
                        float r = base + contrast * (0.39f * roof + 0.15f * left + 0.23f * right);
                        float g = base + contrast * (0.40f * roof + 0.20f * left + 0.20f * right);
                        float b = base + contrast * (0.42f * roof + 0.27f * left + 0.16f * right);
                        pixels.put((byte) (255f * clamp(r, 0f, 1f)));
                        pixels.put((byte) (255f * clamp(g, 0f, 1f)));
                        pixels.put((byte) (255f * clamp(b, 0f, 1f)));
                        pixels.put((byte) 255);
                    }
                }
            }
            pixels.flip();
            // Six stacked cubemap faces in one upload, RGBA8 avoids HDR extension requirements.
            reflectionCube.setImage(engine, level, 0, 0, 0, dim, dim, 6,
                    new Texture.PixelBufferDescriptor(pixels, Texture.Format.RGBA, Texture.Type.UBYTE));
        }

        float[] sh = new float[27];
        // Pre-scaled L0 irradiance: neutral diffuse fill, preserving GLB material colors.
        sh[0] = 0.63f;
        sh[1] = 0.67f;
        sh[2] = 0.73f;
        studioIbl = new IndirectLight.Builder()
                .reflections(reflectionCube)
                .irradiance(3, sh)
                .intensity(STUDIO_LEVELS[studioLevel])
                .build(engine);
        viewer.getScene().setIndirectLight(studioIbl);

        // Camera-facing key plus softer side/rim sources reveal undercuts and rear geometry.
        studioLights[0] = addStudioLight(engine, -0.35f, -0.90f, -0.55f,
                40000f, 1.0f, 0.98f, 0.94f);
        studioLights[1] = addStudioLight(engine, 0.86f, -0.25f, 0.45f,
                23000f, 0.78f, 0.87f, 1.0f);
        studioLights[2] = addStudioLight(engine, -0.55f, -0.32f, 0.83f,
                15000f, 1.0f, 0.86f, 0.71f);
        // A softer exposure keeps the black panels legible without burning bright paint.
        viewer.getCamera().setExposure(13.0f, 1.0f / 125.0f, 100.0f);
    }

    private int addStudioLight(Engine engine, float x, float y, float z,
                               float lux, float r, float g, float b) {
        int light = EntityManager.get().create();
        new LightManager.Builder(LightManager.Type.DIRECTIONAL)
                .color(r, g, b)
                .intensity(lux)
                .direction(x, y, z)
                .castShadows(false)
                .build(engine, light);
        viewer.getScene().addEntity(light);
        return light;
    }

    private static float[] cubeDirection(int face, float u, float v) {
        float x = 0f, y = 0f, z = 0f;
        switch (face) {
            case 0: x = 1f; y = -v; z = -u; break;
            case 1: x = -1f; y = -v; z = u; break;
            case 2: x = u; y = 1f; z = v; break;
            case 3: x = u; y = -1f; z = -v; break;
            case 4: x = u; y = -v; z = 1f; break;
            default: x = -u; y = -v; z = -1f;
        }
        float len = (float) Math.sqrt(x*x + y*y + z*z);
        return new float[]{x / len, y / len, z / len};
    }

    private static float softPanel(float[] d, float x, float y, float z,
                                   float width, float height) {
        float len = (float) Math.sqrt(x*x + y*y + z*z);
        float cosine = (d[0]*x + d[1]*y + d[2]*z) / len;
        float a = (1f - cosine) / Math.max(0.04f, width * height);
        return (float) Math.exp(-5f * a * a);
    }

    private void addModeButton(LinearLayout row, String label,
                               GlbInspectionVariants.Mode mode, int index) {
        Button b = button(label);
        modeButtons[index] = b;
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, dp(41), 1f);
        if (index > 0) p.leftMargin = dp(7);
        row.addView(b, p);
        b.setOnClickListener(v -> displayAs(mode));
    }

    private void syncModeButtons() {
        GlbInspectionVariants.Mode[] modes = GlbInspectionVariants.Mode.values();
        for (int i = 0; i < modeButtons.length; i++) {
            Button b = modeButtons[i];
            if (b == null) continue;
            boolean active = modes[i] == displayMode;
            b.setBackgroundTintList(android.content.res.ColorStateList.valueOf(active ? ACCENT : PANEL));
            b.setTextColor(active ? Color.rgb(7, 20, 28) : TEXT);
            b.setAlpha(modeBusy ? 0.55f : 1.0f);
            b.setEnabled(!modeBusy);
        }
    }

    private void displayAs(GlbInspectionVariants.Mode mode) {
        displayAs(mode, false);
    }

    private void displayAs(GlbInspectionVariants.Mode mode, boolean forceReload) {
        if (!modelLoaded || sourceGlb == null) {
            error("Open a GLB model first.");
            return;
        }
        if (modeBusy || (displayMode == mode && !forceReload)) return;
        modeBusy = true;
        syncModeButtons();
        status.setText("Preparing " + mode.name().toLowerCase(Locale.US) + " geometry...");
        byte[] original = sourceGlb;
        long revision = openRequest;
        final boolean floor = studioEnabled;
        new Thread(() -> {
            try {
                byte[] variant = GlbInspectionVariants.create(original, mode);
                if (floor && mode != GlbInspectionVariants.Mode.WIREFRAME) {
                    try { variant = StudioGlb.withFloor(variant); }
                    catch (Exception ignored) { /* retain inspectable GLB */ }
                }
                ByteBuffer buffer = ByteBuffer.allocateDirect(variant.length);
                buffer.put(variant);
                buffer.flip();
                runOnUiThread(() -> {
                    if (revision != openRequest) return;
                    try {
                        viewer.loadModelGlb(buffer);
                        if (viewer.getAsset() == null) {
                            throw new IllegalArgumentException("Renderer rejected inspection variant");
                        }
                        viewer.transformToUnitCube(new Float3(0f, 0f, -4f));
                        displayedGlb = buffer;
                        displayMode = mode;
                        status.setText(sourceSummary + " • " + mode.name());
                    } catch (Exception ex) {
                        error("View mode failed: " + ex.getMessage());
                    } finally {
                        modeBusy = false;
                        syncModeButtons();
                    }
                });
            } catch (Exception ex) {
                runOnUiThread(() -> {
                    if (revision != openRequest) return;
                    modeBusy = false;
                    syncModeButtons();
                    error("View mode unavailable: " + ex.getMessage());
                });
            }
        }, "glb-inspection-mode").start();
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

    private void openShapeLab() {
        Intent intent=new Intent(this,ShapeLabActivity.class);
        if(sourceGlb==null||sourceGlb.length==0){
            startActivity(intent); // Shape Lab supplies its own native GLB picker.
            return;
        }
        final byte[] source=sourceGlb;
        final String name=modelName;
        new Thread(()->{
            try {
                File data=new File(getCacheDir(),"sceneforge-shapelab-source.glb");
                try(FileOutputStream out=new FileOutputStream(data)){
                    out.write(source);
                }
                intent.putExtra("source_path",data.getAbsolutePath());
                intent.putExtra("source_name",name);
                runOnUiThread(()->startActivity(intent));
            }catch(Exception ex){runOnUiThread(()->error("Shape Lab import: "+ex.getMessage()));}
        },"sceneforge-shapelab-import").start();
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
        final long revision = ++openRequest;
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
                byte[] preview = data;
                if (studioEnabled) {
                    try { preview = StudioGlb.withFloor(data); }
                    catch (Exception ignored) { /* original always remains available */ }
                }
                ByteBuffer buffer = ByteBuffer.allocateDirect(preview.length);
                buffer.put(preview);
                buffer.flip();
                runOnUiThread(() -> {
                    if (revision != openRequest) return;
                    try {
                        viewer.loadModelGlb(buffer);
                        if (viewer.getAsset() == null)
                            throw new IllegalArgumentException("The renderer could not load this GLB");
                        viewer.transformToUnitCube(new Float3(0f, 0f, -4f));
                        sourceGlb = data;
                        displayedGlb = buffer;
                        displayMode = GlbInspectionVariants.Mode.TEXTURED;
                        modeBusy = false;
                        sourceSummary = summary;
                        syncModeButtons();
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
