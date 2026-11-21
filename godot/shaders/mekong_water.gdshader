shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

uniform vec4 near_bank_color : source_color = vec4(0.35, 0.48, 0.33, 0.70);
uniform vec4 deep_channel_color : source_color = vec4(0.10, 0.30, 0.30, 0.93);
uniform vec4 foam_color : source_color = vec4(0.72, 0.78, 0.59, 1.0);
uniform float water_depth_m = 4.5;
uniform float wave_height = 0.075;
uniform float wave_speed = 0.48;
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest, repeat_disable;

varying vec3 world_position;

void vertex() {
    vec3 world_start = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
    float wave = sin(world_start.x * 1.29 + TIME * 1.1 * wave_speed) * 0.55;
    wave += cos(world_start.z * 0.84 - TIME * 1.6 * wave_speed) * 0.3;
    wave += sin((world_start.x + world_start.z) * 3.1 + TIME * 1.9 * wave_speed) * 0.15;
    VERTEX.y += wave * wave_height;
    world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
    float raw_depth = textureLod(depth_tex, SCREEN_UV, 0.0).r;
    #if CURRENT_RENDERER == RENDERER_COMPATIBILITY
        vec3 ndc = vec3(SCREEN_UV, raw_depth) * 2.0 - 1.0;
    #else
        vec3 ndc = vec3(SCREEN_UV * 2.0 - 1.0, raw_depth);
    #endif
    vec4 b = INV_PROJECTION_MATRIX * vec4(ndc, 1.0);
    b.xyz /= max(abs(b.w), 0.0001);
    vec3 behind = (INV_VIEW_MATRIX * vec4(b.xyz, 1.0)).xyz;
    float dep = max(0.0, world_position.y - behind.y);
    float t = clamp(dep / water_depth_m, 0.0, 1.0);
    float ripple = sin(world_position.x * 2.7 + TIME*1.0) * sin(world_position.z*2.1 - TIME*.7);
    float foam = (1.0-smoothstep(0.03, 0.32, dep)) * (0.65 + 0.25*ripple);
    vec4 color = mix(near_bank_color, deep_channel_color, t);
    color.rgb = mix(color.rgb, foam_color.rgb, clamp(foam,0.0,0.7));
    ALBEDO = color.rgb;
    ALPHA = color.a;
    ROUGHNESS = 0.20;
    SPECULAR = 0.95;
    METALLIC = 0.04;
}
