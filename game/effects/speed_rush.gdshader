// SceneForge speed-sensitive peripheral rush, designed for mobile GPU budgets.
// Three screen taps only. The focal lane stays sharp; the outside of the
// image stretches radially as the craft approaches top speed.
// Rendered on a CanvasLayer below the driving HUD.
shader_type canvas_item;
render_mode unshaded;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear;
uniform float intensity : hint_range(0.0, 1.0) = 0.0;
uniform vec2 focus_uv = vec2(0.5, 0.48);

void fragment() {
    vec2 uv = SCREEN_UV;
    vec2 offset = uv - focus_uv;
    float aspect = SCREEN_PIXEL_SIZE.y / SCREEN_PIXEL_SIZE.x;
    float radius = length(offset * vec2(aspect, 1.0));

    // Do not blur the upcoming racing line, obstacles, or the cockpit center.
    float periphery = smoothstep(0.30, 0.92, radius);
    float rush = clamp(intensity * periphery, 0.0, 1.0);
    vec2 direction = offset / max(length(offset), 0.0001);
    vec2 smear = direction * (0.005 + radius * 0.008) * rush;

    vec3 crisp = texture(screen_texture, uv).rgb;
    vec3 trailing = texture(screen_texture, clamp(uv - smear, vec2(0.0), vec2(1.0))).rgb;
    vec3 leading = texture(screen_texture, clamp(uv + smear * 0.7, vec2(0.0), vec2(1.0))).rgb;
    vec3 blurred = crisp * 0.42 + trailing * 0.35 + leading * 0.23;
    COLOR = vec4(mix(crisp, blurred, rush), 1.0);
}
