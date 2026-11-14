package com.sceneforge.glbinspector;

import android.content.Context;
import android.util.Log;

import com.google.android.filament.Camera;
import com.google.android.filament.ColorGrading;
import com.google.android.filament.Engine;
import com.google.android.filament.IndirectLight;
import com.google.android.filament.Texture;
import com.google.android.filament.View;
import com.google.android.filament.utils.KTX1Loader;
import com.google.android.filament.utils.Utils;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.util.WeakHashMap;

/**
 * Explicit high-fidelity preview settings. These do not invent geometric detail
 * or alter the GLB's normals, texture maps or imported PBR material parameters.
 *
 * HDR IBL is a physically based prefiltered environment generated offline by
 * Filament cmgen from a CC0 Poly Haven studio HDR image, then bundled in the APK.
 */
public final class StudioQuality {
    private static final String TAG = "SceneForgeStudio";
    public enum Preset { PERFORMANCE, STUDIO, PHOTO }
    private static final WeakHashMap<View, ColorGrading> GRADING = new WeakHashMap<>();
    private static boolean utilsReady = false;
    private StudioQuality() {}

    public static synchronized void initUtils() {
        if (!utilsReady) {
            Utils.init();
            utilsReady = true;
        }
    }

    public static final class Environment {
        public final IndirectLight ibl;
        public final Texture texture;
        private Environment(IndirectLight ibl, Texture texture) {
            this.ibl = ibl;
            this.texture = texture;
        }
        public void release(Engine engine) {
            if (ibl != null) engine.destroyIndirectLight(ibl);
            if (texture != null) engine.destroyTexture(texture);
        }
    }

    public static Environment loadHdrStudio(Context context, Engine engine) {
        try {
            initUtils();
            byte[] bytes;
            try (InputStream stream = context.getAssets().open("studio/studio_ibl.ktx");
                 ByteArrayOutputStream out = new ByteArrayOutputStream()) {
                byte[] buffer = new byte[32768];
                int count;
                while ((count = stream.read(buffer)) >= 0) {
                    out.write(buffer, 0, count);
                    if (out.size() > 20 * 1024 * 1024)
                        throw new IllegalArgumentException("Unexpected oversized studio IBL");
                }
                bytes = out.toByteArray();
            }
            ByteBuffer direct = ByteBuffer.allocateDirect(bytes.length);
            direct.put(bytes);
            direct.flip();
            KTX1Loader.IndirectLightBundle bundle =
                    KTX1Loader.INSTANCE.createIndirectLight(engine, direct,
                            new KTX1Loader.Options());
            if (bundle.getIndirectLight() == null || bundle.getCubemap() == null)
                throw new IllegalStateException("Studio KTX has no IBL / spherical harmonics");
            // Studio Small 09 contains its photographic softboxes in true HDR rather than
            // approximating reflections with a synthetic LDR gradient.
            bundle.getIndirectLight().setIntensity(30000.0f);
            Log.i(TAG, "PREFILTERED_HDR_STUDIO_LOADED bytes=" + bytes.length);
            return new Environment(bundle.getIndirectLight(), bundle.getCubemap());
        } catch (Throwable e) {
            Log.w(TAG, "Studio IBL unavailable; falling back to built-in lights", e);
            return null;
        }
    }

    public static void apply(Engine engine, View view, Camera camera, Preset preset) {
        boolean photo = preset == Preset.PHOTO;
        boolean studio = preset == Preset.STUDIO;
        boolean high = photo || studio;

        View.RenderQuality quality = new View.RenderQuality();
        quality.hdrColorBuffer = photo ? View.QualityLevel.ULTRA :
                (studio ? View.QualityLevel.HIGH : View.QualityLevel.MEDIUM);
        view.setRenderQuality(quality);

        View.DynamicResolutionOptions scaling = new View.DynamicResolutionOptions();
        scaling.enabled = !high;
        scaling.minScale = 0.75f;
        scaling.maxScale = 1.0f;
        scaling.quality = View.QualityLevel.MEDIUM;
        view.setDynamicResolutionOptions(scaling);

        View.TemporalAntiAliasingOptions taa = new View.TemporalAntiAliasingOptions();
        taa.enabled = high;
        taa.feedback = photo ? 0.10f : 0.15f;
        taa.sharpness = photo ? 0.15f : 0.05f;
        view.setTemporalAntiAliasingOptions(taa);
        view.setAntiAliasing(high ? View.AntiAliasing.NONE : View.AntiAliasing.FXAA);

        View.MultiSampleAntiAliasingOptions msaa = new View.MultiSampleAntiAliasingOptions();
        msaa.enabled = photo;
        msaa.sampleCount = 4;
        view.setMultiSampleAntiAliasingOptions(msaa);

        View.AmbientOcclusionOptions ao = new View.AmbientOcclusionOptions();
        ao.enabled = high;
        ao.aoType = photo ? View.AmbientOcclusionOptions.AmbientOcclusionType.GTAO :
                View.AmbientOcclusionOptions.AmbientOcclusionType.SAO;
        ao.radius = 0.45f;
        ao.intensity = photo ? 0.9f : 0.75f;
        ao.power = 1.0f;
        ao.quality = photo ? View.QualityLevel.HIGH : View.QualityLevel.MEDIUM;
        ao.resolution = photo ? 1.0f : 0.5f;
        view.setAmbientOcclusionOptions(ao);

        View.BloomOptions bloom = new View.BloomOptions();
        bloom.enabled = high;
        bloom.strength = photo ? 0.07f : 0.035f;
        bloom.quality = photo ? View.QualityLevel.MEDIUM : View.QualityLevel.LOW;
        view.setBloomOptions(bloom);

        View.ScreenSpaceReflectionsOptions ssr = new View.ScreenSpaceReflectionsOptions();
        ssr.enabled = photo;
        ssr.maxDistance = 2.0f;
        ssr.stride = 2.0f;
        view.setScreenSpaceReflectionsOptions(ssr);
        view.setDithering(View.Dithering.TEMPORAL);

        view.setShadowingEnabled(high);
        view.setShadowType(photo ? View.ShadowType.PCSS : View.ShadowType.PCF);

        ColorGrading cg = new ColorGrading.Builder()
                .quality(photo ? ColorGrading.QualityLevel.HIGH : ColorGrading.QualityLevel.MEDIUM)
                .toneMapping(ColorGrading.ToneMapping.ACES)
                .luminanceScaling(true)
                .contrast(1.0f)
                .vibrance(1.0f)
                .build(engine);
        ColorGrading old = GRADING.put(view, cg);
        view.setColorGrading(cg);
        if (old != null) engine.destroyColorGrading(old);

        // Keep fixed photographic exposure to evaluate materials consistently.
        // A high-quality render should not falsely change the underlying albedo.
        camera.setExposure(13.0f, 1f / 125.0f, 100.0f);
        Log.i(TAG, "QUALITY_MODE_" + preset.name());
    }

    public static void release(Engine engine, View view) {
        ColorGrading grading = GRADING.remove(view);
        if (grading != null) {
            view.setColorGrading(null);
            engine.destroyColorGrading(grading);
        }
    }
}
