// === KAMERA / ROZPIKSELOWANA ŚCIANA =======================================

let capture;
let pixelSize = 7;   // większa wartość = większe piksele = szybciej
let cols;
let rows;
let gammaZ = 0.5;
let t = 0;

let BASE_ORANGE; // #f95d2d

// === ZIELONY KOD (tylko pisanie, bez scrolla) ==============================

let codeLines = [];
let codeLineHeight;
let currentLine = 0;
let currentChar = 0;

// ile znaków na sekundę ma się pisać
let charsPerSecond = 18;
let charAccumulator = 0;

let codeMarginLeft = 40;
let codeMarginBottom = 40;
let typingFinished = false;

function setup() {
  let parent = document.getElementById("canvasWrap");
  let w = parent.clientWidth;
  let h = parent.clientHeight;

  let canvas = createCanvas(w, h);
  canvas.parent("canvasWrap");

  frameRate(60);
  colorMode(RGB, 255);

  BASE_ORANGE = color('#f95d2d');

  // siatka z pixelSize
  cols = floor(width / pixelSize);
  rows = floor(height / pixelSize);

  // mała kamera do pikselizacji
  capture = createCapture(VIDEO);
  capture.size(cols, rows);  // niska rozdzielczość -> mocna pikselizacja
  capture.hide();

  noStroke();

  // konfiguracja tekstu do overlay
  textFont("monospace");
  textSize(18);
  textAlign(LEFT, TOP);
  codeLineHeight = textAscent() + textDescent() + 4;

  initCodeLines(); 
}

function draw() {
  drawSoftDarkBackgroundZ();
  drawZordonWall();
  drawCodeOverlay();
}


function drawZordonWall() {
  capture.loadPixels();
  if (!capture.pixels || capture.pixels.length === 0) return;

  let cellW = width / cols;
  let cellH = height / rows;

  let orBase = red(BASE_ORANGE);
  let ogBase = green(BASE_ORANGE);
  let obBase = blue(BASE_ORANGE);

  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      let sx = capture.width - x - 1;
      let sy = y;
      let index = (sx + sy * capture.width) * 4;
      let r = capture.pixels[index];
      let g = capture.pixels[index + 1];
      let b = capture.pixels[index + 2];
      let rawBright = (r + g + b) / 3;
      let bright = 255 * pow((rawBright / 255), gammaZ);

      let z = map(bright, 0, 255, 3, 0);
      let sizeMult = map(bright, 0, 255, 0.5, 1.6);

      let cellX = x * cellW;
      let cellY = y * cellH;

      let jitterX = map(
        noise(x * 0.1, y * 0.1, t * 0.01),
        0, 1,
        -z * 2, z * 2
      );
      let jitterY = map(
        noise(x * 0.1 + 100, y * 0.1 + 100, t * 0.01),
        0, 1,
        -z * 2, z * 2
      );

      let cx = cellX + cellW * 0.5 + jitterX;
      let cy = cellY + cellH * 0.5 + jitterY;

      let colR, colG, colB;
      let whiteAccent = bright > 160;

      if (whiteAccent) {
        let tCol = map(bright, 160, 255, 0.4, 1.0);
        tCol = constrain(tCol, 0.4, 1.0);
        colR = lerp(orBase, 255, tCol);
        colG = lerp(ogBase, 255, tCol);
        colB = lerp(obBase, 255, tCol);
      } else {
        let tCol = map(bright, 0, 160, 0.2, 1.0);
        tCol = constrain(tCol, 0.2, 1.0);
        colR = lerp(0, orBase, tCol);
        colG = lerp(0, ogBase, tCol * 0.9);
        colB = lerp(0, obBase, tCol * 0.8);
      }

      let alphaVal = map(bright, 0, 255, 50, 255);
      alphaVal = constrain(alphaVal, 40, 255);

      fill(0, 0, 0, alphaVal * 0.6);
      rect(
        cx + 4,
        cy + 4,
        cellW * sizeMult,
        cellH * sizeMult,
        2
      );

      fill(colR, colG, colB, alphaVal);
      rect(
        cx,
        cy,
        cellW * sizeMult,
        cellH * sizeMult,
        2
      );
    }
  }

  t += 1;
}

function drawSoftDarkBackgroundZ() {
  background(0, 0, 0);

  push();
  translate(width / 2, height / 2);
  noStroke();
  for (let r = max(width, height) * 1.2; r > 0; r -= 100) {
    let alpha = map(r, 0, max(width, height) * 1.2, 90, 0);
    fill(5, 5, 12, alpha);
    ellipse(0, 0, r * 1.4, r);
  }
  pop();
}

// === ZIELONY KOD – DEFINICJA TEKSTU =======================================

function initCodeLines() {
  codeLines = [
    "// particle system diagnostics",
    "",
    "const MAX_PARTICLES = 1024;",
    "const TIME_STEP = 1.0 / 60.0;",
    "",
    "class Vec2 {",
    "  constructor(x, y) {",
    "    this.x = x;",
    "    this.y = y;",
    "  }",
    "  add(v) {",
    "    this.x += v.x;",
    "    this.y += v.y;",
    "    return this;",
    "  }",
    "  scale(s) {",
    "    this.x *= s;",
    "    this.y *= s;",
    "    return this;",
    "  }",
    "  lengthSq() {",
    "    return this.x * this.x + this.y * this.y;",
    "  }",
    "}",
    "",
    "class Particle {",
    "  constructor(pos, vel, life) {",
    "    this.pos = pos;",
    "    this.vel = vel;",
    "    this.life = life;",
    "    this.age = 0;",
    "    this.alive = true;",
    "  }",
    "  step(dt, field) {",
    "    if (!this.alive) return;",
    "    const force = field.sample(this.pos);",
    "    this.vel.add(force.scale(dt));",
    "    this.pos.add(this.vel.scale(dt));",
    "    this.age += dt;",
    "    if (this.age > this.life) {",
    "      this.alive = false;",
    "    }",
    "  }",
    "}",
    "",
    "class VectorField {",
    "  constructor(seed) {",
    "    this.seed = seed;",
    "  }",
    "  sample(p) {",
    "    const nx = noise(p.x * 0.01, this.seed);",
    "    const ny = noise(p.y * 0.01, this.seed + 10);",
    "    const vx = map(nx, 0, 1, -1.0, 1.0);",
    "    const vy = map(ny, 0, 1, -1.0, 1.0);",
    "    return new Vec2(vx, vy);",
    "  }",
    "}",
    "",
    "class ParticleSystem {",
    "  constructor() {",
    "    this.items = [];",
    "    this.field = new VectorField(42.0);",
    "  }",
    "  spawn(pos, count) {",
    "    for (let i = 0; i < count; i++) {",
    "      const angle = random(TWO_PI);",
    "      const speed = random(0.4, 2.2);",
    "      const vx = cos(angle) * speed;",
    "      const vy = sin(angle) * speed;",
    "      const life = random(0.8, 3.0);",
    "      if (this.items.length >= MAX_PARTICLES) break;",
    "      this.items.push(",
    "        new Particle(",
    "          new Vec2(pos.x, pos.y),",
    "          new Vec2(vx, vy),",
    "          life",
    "        )",
    "      );",
    "    }",
    "  }",
    "  update(dt) {",
    "    for (let p of this.items) {",
    "      p.step(dt, this.field);",
    "    }",
    "    this.items = this.items.filter(p => p.alive);",
    "  }",
    "  debugStats() {",
    "    const alive = this.items.length;",
    "    let totalLife = 0;",
    "    for (let p of this.items) {",
    "      totalLife += p.life;",
    "    }",
    "    const avgLife = alive > 0 ? totalLife / alive : 0;",
    "    return { alive, avgLife };",
    "  }",
    "}",
    "",
    "let system = new ParticleSystem();",
    "let accumulator = 0.0;",
    "",
    "function updateSimulation(dt) {",
    "  accumulator += dt;",
    "  while (accumulator >= TIME_STEP) {",
    "    accumulator -= TIME_STEP;",
    "    const cx = width * 0.5;",
    "    const cy = height * 0.4;",
    "    if (system.items.length < MAX_PARTICLES) {",
    "      system.spawn(new Vec2(cx, cy), 12);",
    "    }",
    "    system.update(TIME_STEP);",
    "  }",
    "}",
    "",
    "function debugLog(frameTime) {",
    "  const stats = system.debugStats();",
    "  console.log(",
    "    '[frame]', frameTime.toFixed(3),",
    "    'alive:', stats.alive,",
    "    'avgLife:', stats.avgLife.toFixed(2)",
    "  );",
    "}",
    "",
    "// end of particle system diagnostics"
  ];

  currentLine = 0;
  currentChar = 0;
  typingFinished = false;
  charAccumulator = 0;
}

// === ZIELONY KOD – RYSOWANIE OD DOŁU W GÓRĘ ===============================

function drawCodeOverlay() {
  push();
  textFont("monospace");
  textSize(18);
  textAlign(LEFT, TOP);
  fill(0, 255, 70);

  if (!typingFinished) {
    charAccumulator += (deltaTime / 1000) * charsPerSecond;

    while (charAccumulator >= 1 && !typingFinished) {
      let lineText = codeLines[currentLine];
      currentChar++;
      if (currentChar > lineText.length) {
        currentLine++;
        currentChar = 0;
        if (currentLine >= codeLines.length) {
          typingFinished = true;
          currentLine = codeLines.length - 1;
          currentChar = codeLines[currentLine].length;
          break;
        }
      }
      charAccumulator -= 1;
    }
  }

  let baseY = height - codeMarginBottom - codeLineHeight;

  for (let i = 0; i <= currentLine; i++) {
    let lineIndex = currentLine - i;
    let fullLine = codeLines[lineIndex];
    let y = baseY - i * codeLineHeight;

    let toDraw = "";

    if (!typingFinished && lineIndex === currentLine) {
      toDraw = fullLine.substring(0, currentChar);
    } else {
      toDraw = fullLine;
    }

    if (toDraw.length > 0 && y > -codeLineHeight && y < height + codeLineHeight) {
      text(toDraw, codeMarginLeft, y);
    }
  }

  pop();
}