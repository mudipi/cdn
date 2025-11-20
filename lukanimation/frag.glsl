#ifdef GL_ES
precision mediump float;
#endif

uniform vec2 u_resolution;
uniform float u_time;
uniform vec2 u_mouse;
uniform sampler2D u_text;
uniform float u_tile_amount;
uniform float u_feather;
uniform int u_display;

float rand(vec2 co){
	return fract(sin(dot(co.xy,vec2(12.9898,78.233))) * 43758.5453);
}

float smin(float d1, float d2, float k) {
	return -log(exp(-k * d1) + exp(-k * d2)) / k;
}

void main() {
	vec2 uv = gl_FragCoord.xy / u_resolution.xy;
	vec2 mouse = u_mouse / u_resolution.xy;

	vec2 gv = fract(uv * u_tile_amount + .25);

	float box1 = distance(gv, vec2(0., 1.));
	float box3 = distance(gv, vec2(1., 1.));
	float box5 = distance(gv, vec2(.5, .5));
	float box7 = distance(gv, vec2(.0, .0));
	float box9 = distance(gv, vec2(1., 0.));

	float box2 = distance(gv, vec2(.5, 1.));
	float box4 = distance(gv, vec2(.0, .5));
	float box6 = distance(gv, vec2(1., .5));
	float box8 = distance(gv, vec2(.5, .0));

	float k = 32.;

	float b; 
	b = smin(box2, box4, k);
	b = smin(b, box6, k);
	b = smin(b, box8, k);

	float br;
	br = smin(box1, box3, k);
	br = smin(br, box5, k);
	br = smin(br, box7, k);
	br = smin(br, box9, k);

	float tile = smin(b, 1.-br, 1.);
	tile = (tile + .47) * 2.;

	float t1 = sin(u_time - (uv.x*2.)) * .5 + .5;
	float t2 = sin(u_time - (uv.y*5.)) * .5 + .5;
	float threshold = mix(t1, t2, .5);

	float m = 1. - distance(uv, mouse) * 5.;
	m = max(0., m);
	m *= step(m, 1.);

	threshold = threshold + m - 2. * threshold * m;

	float noise = rand(uv) * u_feather * .5 - u_feather * .25;
	threshold += noise;

	float composed = step(tile, threshold);

	float c = composed;

	if(u_display == 1) c = tile;
	if(u_display == 2) {
		float line = step(fract(tile*10.), .2);
		float fill = floor(tile*10.) / 10.;
		c = mix(fill, 1., line);
	}
	if(u_display == 3) c = threshold;

	vec2 text_uv = uv;
	text_uv.y = 1.-text_uv.y;
	float text = texture2D(u_text, text_uv).r;
	text = step(.5, text);

	if(u_display == 0) {
		c = c + text - 2. * c * text;
	}

	vec3 color1 = vec3(1., .92, .98);
	vec3 color2 = vec3(0., .3, .24);

	vec3 col = mix(color1, color2, c);

	gl_FragColor = vec4(col,1.0);
}
