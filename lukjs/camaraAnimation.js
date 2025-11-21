
const vert = `
  attribute vec3 aPosition;
  attribute vec2 aTexCoord;
  varying vec2 vTexCoord;
  void main() {
    vTexCoord = aTexCoord;
    gl_Position = vec4(aPosition, 1.0);
  }
`;

const sobelShaderSource = `
  precision mediump float;

  varying vec2 vTexCoord;
  uniform sampler2D tex0;
  uniform vec2 texSize;

  const vec3 W = vec3(0.2125, 0.7154, 0.0721);

  void main() {
    vec2 onePixel = 1.0 / texSize;

    float tl = dot(texture2D(tex0, vTexCoord + onePixel * vec2(-1,-1)).rgb, W);
    float t  = dot(texture2D(tex0, vTexCoord + onePixel * vec2( 0,-1)).rgb, W);
    float tr = dot(texture2D(tex0, vTexCoord + onePixel * vec2( 1,-1)).rgb, W);
    float bl = dot(texture2D(tex0, vTexCoord + onePixel * vec2(-1, 1)).rgb, W);
    float b  = dot(texture2D(tex0, vTexCoord + onePixel * vec2( 0, 1)).rgb, W);
    float br = dot(texture2D(tex0, vTexCoord + onePixel * vec2( 1, 1)).rgb, W);

    float gradient = tl*-1.0 + t*-2.0 + tr*-1.0 + bl*1.0 + b*2.0 + br*1.0;

    float intensity = clamp(abs(gradient)*5.0, 0.0, 1.0);

    vec4 edgeColor = vec4(0.0, 0.8, 1.0, 1.0);

    gl_FragColor = mix(vec4(0.0), edgeColor, intensity);
  }
`;

let cameras = [];
let currentCamera = 0;
let video;
let sobelShader;
let lastTap = 0;
let tapThreshold = 250;

async function getCameras() {
  const devices = await navigator.mediaDevices.enumerateDevices();
  cameras = devices.filter(d => d.kind === "videoinput");
}

function setup() {
  createCanvas(windowWidth, windowHeight, WEBGL);
  noStroke();
  textureMode(NORMAL);

  sobelShader = createShader(vert, sobelShaderSource);

  getCameras().then(() => {
    if (cameras.length > 0) createVideoStream();
  });
}

function createVideoStream() {
  const constraints = {
    video: { deviceId: { exact: cameras[currentCamera].deviceId } }
  };

  if (video) video.remove();

  video = createCapture(constraints, () => {
    video.size(640, 480);
    video.hide();
    video.elt.play();  // iOS required
  });
}

function switchCamera() {
  if (cameras.length > 1) {
    currentCamera = (currentCamera + 1) % cameras.length;
    createVideoStream();
  }
}

function draw() {
  background(0);

  if (!video || video.width === 0) return; // avoid black screen

  shader(sobelShader);

  sobelShader.setUniform("tex0", video);
  sobelShader.setUniform("texSize", [video.width, video.height]);

  // draw fullscreen quad
  plane(width, height);
}

function touchStarted() {
  if (millis() - lastTap < tapThreshold) {
    switchCamera();
  }
  lastTap = millis();
  return false;
}

function keyPressed() {
  save("img_" + Date.now() + ".jpg");
}