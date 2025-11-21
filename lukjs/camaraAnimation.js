const vert = `
  attribute vec3 aPosition;
  attribute vec2 aTexCoord;
  
  varying vec2 vTexCoord;
  
  void main() {
    vTexCoord = vec2(aTexCoord.x, 1.0 - aTexCoord.y);
    vec4 positionVec4 = vec4(aPosition, 1.0);
    positionVec4.xy = positionVec4.xy * 2.0 - 1.0;
    gl_Position = positionVec4;
  }
`;

const sobelShaderSource = `
  precision mediump float;
  
  varying vec2 vTexCoord;
  uniform sampler2D tex0;
  uniform vec2 texSize;
  
  const vec3 W = vec3(0.2125, 0.7154, 0.0721);
  
  void main() {
    vec2 onePixel = vec2(1.0, 1.0) / texSize;

    float brightnessTL = dot(texture2D(tex0, vTexCoord + onePixel * vec2(-1, -1)).rgb, W);
    float brightnessT = dot(texture2D(tex0, vTexCoord + onePixel * vec2(0, -1)).rgb, W);
    float brightnessTR = dot(texture2D(tex0, vTexCoord + onePixel * vec2(1, -1)).rgb, W);
    float brightnessBL = dot(texture2D(tex0, vTexCoord + onePixel * vec2(-1, 1)).rgb, W);
    float brightnessB = dot(texture2D(tex0, vTexCoord + onePixel * vec2(0, 1)).rgb, W);
    float brightnessBR = dot(texture2D(tex0, vTexCoord + onePixel * vec2(1, 1)).rgb, W);
    
    float gradient = brightnessTL * -1.0 +
      brightnessT * -2.0 +
      brightnessTR * -1.0 +
      brightnessBL * 1.0 +
      brightnessB * 2.0 +
      brightnessBR * 1.0;
      
    float normalizedGradient = clamp(abs(gradient) * 5.0, 0.0, 1.0);

    vec4 edgeColor = vec4(0.0, 0.8, 1.0, 1.0); // Set the desired color for the edges (high sky blue)

    // Mix the edge color with the black background based on the edge intensity
    gl_FragColor = mix(vec4(0.0), edgeColor, normalizedGradient);
  }
`;

let cameras = [];
let currentCamera = 0;
let video;
let sobelShader;
let lastTap = 0;  // Store the time of the last tap
let tapThreshold = 200;  // Set the threshold for double-tap in milliseconds
let parentDiv;

async function getCameras() {
  const devices = await navigator.mediaDevices.enumerateDevices();
  cameras = devices.filter(device => device.kind === 'videoinput');
}

function setup() {
  getCameras().then(() => {
    if (cameras.length > 0) {

      parentDiv = document.getElementById("canvas-wrapper");

      let w = parentDiv.clientWidth;
      let h = parentDiv.clientHeight;

      createVideoStream();
      let cnv = createCanvas(w, h, WEBGL);
      cnv.parent(parentDiv);  // attach canvas inside div

      sobelShader = createShader(vert, sobelShaderSource);

    } else {
      console.error("No cameras available");
    }
  });
}

function windowResized() {
  let w = parentDiv.clientWidth;
  let h = parentDiv.clientHeight;
  resizeCanvas(w, h);
}

function createVideoStream() {
  const constraints = {
    video: {
      deviceId: {
        exact: cameras[currentCamera].deviceId
      }
    }
  };
  
  video = createCapture(constraints, () => {
    video.hide();
  });
}

function switchCamera() {
  currentCamera = (currentCamera + 1) % cameras.length;
  video.remove(); // Remove the previous video element
  createVideoStream();
}

function draw() {
  if (video) {
    background(0);
    shader(sobelShader);
    sobelShader.setUniform('tex0', video);
    sobelShader.setUniform('texSize', [video.width, video.height]);
    rect(-width / 2, -height / 2, width, height);
  }
}

// Switch the camera when the canvas is double-tapped
function touchStarted() {
  if (millis() - lastTap < tapThreshold){  // Check if the time since the last tap is less than the threshold
    switchCamera();
  }
  lastTap = millis();  // Update the time of the last tap
  return false; // This line is used to prevent default touch behavior that can cause the canvas to move around the page.
}

function keyPressed(){
  save("img_" + month() + '-' + day() + '_' + hour() + '-' + minute() + '-' + second() + ".jpg");
}