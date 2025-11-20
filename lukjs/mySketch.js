const PIXEL_DENSITY = 1;
let theShader;
let canvas;
let f;
let textGraphic;

let control = {
	tileAmount: 30,
	feather: 0.04,
	display: 0
};

window.onload = function () {
	var gui = new dat.GUI();
	gui.domElement.id = 'gui';
	gui.add(control, 'tileAmount', 1, 100).name("Tile Amount");
	gui.add(control, 'feather', 0, 1).name("Feather");
	gui.add(control, 'display', { Composed: 0, Tile: 1, 'Contour Line': 2, Threshold: 3 }).name("Display");
};

function preload() {
	// LOAD SHADERS FROM WEBFLOW URL
	theShader = loadShader(
		"https://raw.githack.com/mudipi/cdn/main/vert.glsl",
		"https://raw.githack.com/mudipi/cdn/main/frag.glsl"
	);

	// font from CDN
	f = loadFont("https://cdnjs.cloudflare.com/ajax/libs/topcoat/0.8.0/font/SourceCodePro-Bold.otf");
}

function setup() {
	pixelDensity(PIXEL_DENSITY);
	canvas = createCanvas(1000, 1000, WEBGL);
	noStroke();

	// 2D buffer for text
	textGraphic = createGraphics(1000, 1000);
	textGraphic.pixelDensity(PIXEL_DENSITY);
	textGraphic.background(0);
	textGraphic.textFont(f);
	textGraphic.textSize(120);
	textGraphic.fill(255);
	textGraphic.textAlign(LEFT, TOP);

	textGraphic.text("Halftone", 50, 200);
	textGraphic.text("square", 50, 340);

	shader(theShader);
}

function draw() {

	theShader.setUniform("u_resolution", [width, height]);
	theShader.setUniform("u_mouse", [mouseX, height - mouseY]);
	theShader.setUniform("u_time", millis() / 1000.0);
	theShader.setUniform("u_text", textGraphic);
	theShader.setUniform("u_tile_amount", control.tileAmount);
	theShader.setUniform("u_feather", control.feather);
	theShader.setUniform("u_display", control.display);

	rect(-width / 2, -height / 2, width, height);
}
