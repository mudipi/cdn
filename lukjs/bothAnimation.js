const anim1 = (p) => {

  let capture;
  let pixelSize = 8;
  let cols, rows;
  let gammaZ = 0.5;
  let t = 0;

  let BASE_ORANGE;
  let codeLines = [];
  let codeLineHeight;
  let currentLine = 0;
  let currentChar = 0;
  let charsPerSecond = 14;
  let charAccumulator = 0;
  let codeMarginLeft = 40;
  let codeMarginBottom = 40;
  let typingFinished = false;

  p.setup = function () {
    let parent = document.getElementById("canvasWrap");
    let w = parent.clientWidth;
    let h = parent.clientHeight;

    let c = p.createCanvas(w, h);
    c.parent("canvasWrap");

    p.frameRate(60);
    p.colorMode(p.RGBA, 255, 0);

    BASE_ORANGE = p.color('#f95d2d');

    cols = p.floor(p.width / pixelSize);
    rows = p.floor(p.height / pixelSize);

    capture = p.createCapture(p.VIDEO);
    capture.size(cols, rows);
    capture.hide();

    p.noStroke();
    p.textFont("monospace");
    p.textSize(18);
    p.textAlign(p.LEFT, p.TOP);
    codeLineHeight = p.textAscent() + p.textDescent() + 4;

    initCodeLines();
  };

  p.draw = function () {
    drawSoftDarkBackgroundZ();
    drawZordonWall();
  };

  function drawZordonWall() {
    capture.loadPixels();
    if (!capture.pixels || capture.pixels.length === 0) return;

    let cellW = p.width / cols;
    let cellH = p.height / rows;

    let orBase = p.red(BASE_ORANGE);
    let ogBase = p.green(BASE_ORANGE);
    let obBase = p.blue(BASE_ORANGE);

    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {

        let sx = capture.width - x - 1;
        let sy = y;
        let index = (sx + sy * capture.width) * 4;

        let r = capture.pixels[index];
        let g = capture.pixels[index + 1];
        let b = capture.pixels[index + 2];

        let rawBright = (r + g + b) / 3;
        let bright = 255 * p.pow((rawBright / 255), gammaZ);

        let z = p.map(bright, 0, 255, 3, 0);
        let sizeMult = p.map(bright, 0, 255, 0.5, 1.6);

        let cellX = x * cellW;
        let cellY = y * cellH;

        let jitterX = p.map(p.noise(x * 0.1, y * 0.1, t * 0.01), 0, 1, -z * 2, z * 2);
        let jitterY = p.map(p.noise(x * 0.1 + 100, y * 0.1 + 100, t * 0.01), 0, 1, -z * 2, z * 2);

        let cx = cellX + cellW * 0.5 + jitterX;
        let cy = cellY + cellH * 0.5 + jitterY;

        let d = p.dist(cx, cy, p.mouseX, p.mouseY);
        if (d < 150) {
          let force = (150 - d) / 150;
          let ang = p.atan2(cy - p.mouseY, cx - p.mouseX);
          cx += p.cos(ang) * force * 28;
          cy += p.sin(ang) * force * 28;
        }

        let colR, colG, colB;
        let whiteAccent = bright > 160;

        if (whiteAccent) {
          let tCol = p.map(bright, 160, 255, 0.4, 1.0);
          tCol = p.constrain(tCol, 0.4, 1.0);
          colR = p.lerp(orBase, 255, tCol);
          colG = p.lerp(ogBase, 255, tCol);
          colB = p.lerp(obBase, 255, tCol);
        } else {
          let tCol = p.map(bright, 0, 160, 0.2, 1.0);
          tCol = p.constrain(tCol, 0.2, 1.0);
          colR = p.lerp(0, orBase, tCol);
          colG = p.lerp(0, ogBase, tCol * 0.9);
          colB = p.lerp(0, obBase, tCol * 0.8);
        }

        let alphaVal = p.map(bright, 0, 255, 50, 255);
        alphaVal = p.constrain(alphaVal, 40, 255);

        p.fill(0, 0, 0, alphaVal * 0.6);
        p.rect(cx + 4, cy + 4, cellW * sizeMult, cellH * sizeMult, 2);

        p.fill(colR, colG, colB, alphaVal);
        p.rect(cx, cy, cellW * sizeMult, cellH * sizeMult, 2);
      }
    }

    t += 1;
  }

  function drawSoftDarkBackgroundZ() {
    p.clear();
  }

  function initCodeLines() {
    codeLines = ["// example"];
  }
};

new p5(anim1);