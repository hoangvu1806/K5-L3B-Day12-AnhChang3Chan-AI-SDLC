shader_type canvas_item;
render_mode unshaded;

uniform sampler2D scene_texture : repeat_disable, filter_linear;
uniform float blur_radius = 5.0;
uniform vec2 panel_size;
uniform float corner_radius = 14.0;

void fragment() {
    vec2 step_uv = SCREEN_PIXEL_SIZE * blur_radius;
    vec3 backdrop = vec3(0.0);
    // Read the 3D viewport texture to keep the water depth pass separate from the HUD.
    for (int x = -1; x <= 1; x++) {
        for (int y = -1; y <= 1; y++) {
            float weight = (2.0 - abs(float(x))) * (2.0 - abs(float(y)));
            backdrop += texture(scene_texture, SCREEN_UV + vec2(float(x), float(y)) * step_uv).rgb * weight;
        }
    }
    backdrop *= 0.0625;
    vec2 inner = abs((UV - 0.5) * panel_size) - (panel_size * 0.5 - corner_radius);
    float edge = length(max(inner, vec2(0.0))) + min(max(inner.x, inner.y), 0.0) - corner_radius;
    COLOR = vec4(backdrop, (1.0 - smoothstep(-0.5, 0.5, edge)) * 0.94);
}
