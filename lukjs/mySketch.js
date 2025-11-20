const PIXEL_DENSITY = 1;
let theShader;
let canvas;
let f;
let textGraphic;

let control = {
    tileAmount: 50, // base amount
    feather: 0.05,
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
    theShader = loadShader(
		"https://raw.githack.com/mudipi/cdn/main/lukjs/vert.glsl",
		"https://raw.githack.com/mudipi/cdn/main/lukjs/frag.glsl"
	);

    f = loadFont("https://cdnjs.cloudflare.com/ajax/libs/topcoat/0.8.0/font/SourceCodePro-Bold.otf");
}

function setup() {
    pixelDensity(PIXEL_DENSITY);

    let parent = document.getElementById("shader-container");
    let w = parent.offsetWidth;
    let h = parent.offsetHeight;

    canvas = createCanvas(w, h, WEBGL);
    canvas.parent("shader-container");
    noStroke();

    createTextGraphic(w, h);

    shader(theShader);
}

function createTextGraphic(w, h) {
    textGraphic = createGraphics(w, h);
    textGraphic.pixelDensity(PIXEL_DENSITY);
    textGraphic.background(0);
    textGraphic.textFont(f);
    textGraphic.textSize(h * 0.12);
    textGraphic.fill(255);
    textGraphic.textAlign(LEFT, TOP);

    /*textGraphic.text("Halftone", w * 0.05, h * 0.20);
    textGraphic.text("square", w * 0.05, h * 0.34);*/
}

function windowResized() {
    let parent = document.getElementById("shader-container");
    let w = parent.offsetWidth;
    let h = parent.offsetHeight;

    resizeCanvas(w, h);
    createTextGraphic(w, h);
}

function draw() {
    let parent = document.getElementById("shader-container");
    let w = parent.offsetWidth;
    let h = parent.offsetHeight;

    // Dynamically scale tileAmount based on parent size
    let scaleTile = control.tileAmount * (w / 1000 + h / 1000) / 2;

    theShader.setUniform("u_resolution", [width, height]);
    theShader.setUniform("u_mouse", [mouseX, height - mouseY]);
    theShader.setUniform("u_time", millis() / 1000.0);
    theShader.setUniform("u_text", textGraphic);
    theShader.setUniform("u_tile_amount", scaleTile); // scaled
    theShader.setUniform("u_feather", control.feather);
    theShader.setUniform("u_display", control.display);

    rect(-width / 2, -height / 2, width, height);
}