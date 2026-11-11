shader_type canvas_item;
render_mode unshaded;

// Whole-screen "painted on paper" finish: gentle saturation lift, warm tint,
// paper grain and mottling, and a soft vignette. Tune the uniforms (or remove
// the layer in world_view.gd) to change or disable the look.

uniform sampler2D screen_texture : hint_screen_texture, filter_linear_mipmap;
uniform float grain_strength : hint_range(0.0, 0.2) = 0.05;
uniform float vignette_strength : hint_range(0.0, 1.0) = 0.2;
uniform float saturation : hint_range(0.5, 1.8) = 1.12;
uniform vec3 warm_tint = vec3(1.0, 0.975, 0.92);
uniform float paper_scale : hint_range(0.5, 4.0) = 1.0;

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float value_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash21(i);
	float b = hash21(i + vec2(1.0, 0.0));
	float c = hash21(i + vec2(0.0, 1.0));
	float d = hash21(i + vec2(1.0, 1.0));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

void fragment() {
	vec3 color = texture(screen_texture, SCREEN_UV).rgb;
	float luma = dot(color, vec3(0.299, 0.587, 0.114));
	color = mix(vec3(luma), color, saturation);
	color *= warm_tint;

	vec2 px = FRAGCOORD.xy / paper_scale;
	float fine = hash21(px) - 0.5;
	float mottling = value_noise(px * 0.035) - 0.5;
	float fibre = value_noise(vec2(px.x * 0.9, px.y * 0.06)) - 0.5;
	color += (fine * 0.7 + mottling * 0.9 + fibre * 0.4) * grain_strength;

	vec2 centered = SCREEN_UV - vec2(0.5);
	float edge = smoothstep(0.35, 0.85, length(centered * vec2(1.0, 1.15)));
	color *= 1.0 - edge * edge * vignette_strength;

	COLOR = vec4(color, 1.0);
}
