// window.Webflow ||= [];
// window.Webflow.push(() => {

  // ---------- ANIM 1 (full restored, Webflow-safe) ----------
  new p5((p) => {

    // --- original variables ---
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

    // keep track of created canvas so we can resize it on window resize
    let myCanvas;

    p.setup = function () {
      // wait for the DOM element to exist
      const parent = document.getElementById("canvasWrap");
      if (!parent) {
        console.error("canvasWrap not found. Make sure a div with id='canvasWrap' exists.");
        return;
      }

      // create canvas sized to parent
      const w = parent.clientWidth;
      const h = parent.clientHeight;
      myCanvas = p.createCanvas(w, h);
      myCanvas.parent("canvasWrap");

      p.frameRate(60);
      // safe colorMode call
      p.colorMode(p.RGBA, 255);

      BASE_ORANGE = p.color('#f95d2d');

      cols = p.floor(p.width / pixelSize) || 1;
      rows = p.floor(p.height / pixelSize) || 1;

      // camera capture
      try {
        capture = p.createCapture(p.VIDEO, () => {
          // callback when stream started
          // try to set capture size relative to cols/rows
          if (capture && cols && rows) {
            capture.size(cols, rows);
          }
        });
        capture.size(cols, rows);
        capture.hide();
      } catch (e) {
        console.warn("Camera init failed:", e);
      }

      p.noStroke();
      p.textFont("monospace");
      p.textSize(18);
      p.textAlign(p.LEFT, p.TOP);
      codeLineHeight = Math.round(p.textAscent() + p.textDescent() + 4);

      initCodeLines();

      // handle window resize to keep canvas fitting the parent
      const resizeObserver = new ResizeObserver(() => {
        resizeToParent();
      });
      resizeObserver.observe(parent);

      // also handle page/window resize
      window.addEventListener("resize", resizeToParent);
    };

    p.draw = function () {
      // background / clear
      drawSoftDarkBackgroundZ();

      // draw the pixelized camera wall
      drawZordonWall();

      // draw typing/code overlay on top
      drawCodeOverlay();

      // increment time counter for noise etc
      t += 1;
    };

    // ---------- drawing the zordon/pixel wall ----------
    function drawZordonWall() {
      if (!capture || !capture.pixels || capture.pixels.length === 0) {
        // fallback -- show a subtle animated grid if camera not ready
        drawFallbackGrid();
        return;
      }

      capture.loadPixels();
      if (!capture.pixels || capture.pixels.length === 0) {
        drawFallbackGrid();
        return;
      }

      let cellW = p.width / cols;
      let cellH = p.height / rows;

      let orBase = p.red(BASE_ORANGE);
      let ogBase = p.green(BASE_ORANGE);
      let obBase = p.blue(BASE_ORANGE);

      for (let y = 0; y < rows; y++) {
        for (let x = 0; x < cols; x++) {

          // sample mirrored x so camera looks like a mirror (same as original)
          let sx = Math.max(0, Math.min(capture.width - 1, capture.width - x - 1));
          let sy = Math.max(0, Math.min(capture.height - 1, y));
          let index = (sx + sy * capture.width) * 4;

          let r = capture.pixels[index] || 0;
          let g = capture.pixels[index + 1] || 0;
          let b = capture.pixels[index + 2] || 0;

          let rawBright = (r + g + b) / 3;
          let bright = 255 * Math.pow((rawBright / 255), gammaZ);

          let z = p.map(bright, 0, 255, 3, 0);
          let sizeMult = p.map(bright, 0, 255, 0.5, 1.6);

          let cellX = x * cellW;
          let cellY = y * cellH;

          // jitter using noise + time
          let jitterX = p.map(p.noise(x * 0.1, y * 0.1, t * 0.01), 0, 1, -z * 2, z * 2);
          let jitterY = p.map(p.noise(x * 0.1 + 100, y * 0.1 + 100, t * 0.01), 0, 1, -z * 2, z * 2);

          let cx = cellX + cellW * 0.5 + jitterX;
          let cy = cellY + cellH * 0.5 + jitterY;

          // mouse repel/push effect
          let d = p.dist(cx, cy, p.mouseX, p.mouseY);
          if (d < 150) {
            let force = (150 - d) / 150;
            let ang = p.atan2(cy - p.mouseY, cx - p.mouseX);
            cx += p.cos(ang) * force * 28;
            cy += p.sin(ang) * force * 28;
          }

          // color mapping similar to original
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

          // soft shadow / depth
          p.fill(0, 0, 0, alphaVal * 0.6);
          p.rect(cx + 4, cy + 4, cellW * sizeMult, cellH * sizeMult, 2);

          // main colored rect
          p.fill(colR, colG, colB, alphaVal);
          p.rect(cx, cy, cellW * sizeMult, cellH * sizeMult, 2);
        }
      }
    }

    function drawFallbackGrid() {
      // simple animated grid for when camera isn't ready
      p.push();
      p.noStroke();
      for (let y = 0; y < rows; y++) {
        for (let x = 0; x < cols; x++) {
          let cellW = p.width / cols;
          let cellH = p.height / rows;
          let a = p.map(p.noise(x * 0.1, y * 0.1, t * 0.01), 0, 1, 30, 120);
          p.fill(20, 20, 20, a);
          p.rect(x * cellW, y * cellH, cellW, cellH);
        }
      }
      p.pop();
    }

    // ---------- soft background (kept minimal like original) ----------
    function drawSoftDarkBackgroundZ() {
      // original used clear(); we keep subtle dark fill to avoid artifacts in some browsers
      p.clear();
      // optional very faint vignette
      p.push();
      p.noStroke();
      p.fill(4, 4, 6, 10);
      p.rect(0, 0, p.width, p.height);
      p.pop();
    }

    // ---------- typing / code overlay ----------
    function initCodeLines() {
      // restore your original example content (you can change to whatever)
      codeLines = [
        "// example",
        "function helloWorld() {",
        "  console.log('hello from anim1');",
        "}",
        "",
        "// camera + pixel wall",
      ];
      currentLine = 0;
      currentChar = 0;
      typingFinished = false;
      charAccumulator = 0;
    }

    function drawCodeOverlay() {
      // compute delta time (seconds) to drive typing
      let dt = Math.max(0, p.deltaTime || (1000 / 60));
      // convert ms to seconds
      dt = dt / 1000;

      if (!typingFinished) {
        charAccumulator += dt * charsPerSecond;
        while (charAccumulator >= 1) {
          charAccumulator -= 1;
          currentChar++;
          if (currentLine < codeLines.length && currentChar > codeLines[currentLine].length) {
            // advance line
            currentChar = 0;
            currentLine++;
            if (currentLine >= codeLines.length) {
              typingFinished = true;
              break;
            }
          }
        }
      }

      // draw the code box bottom-left-ish (as original margins)
      p.push();
      p.textSize(18);
      p.textAlign(p.LEFT, p.TOP);
      let boxX = codeMarginLeft;
      let totalHeight = codeLineHeight * Math.max(1, codeLines.length);
      let boxY = p.height - codeMarginBottom - totalHeight;

      // translucent background
      p.fill(10, 10, 12, 180);
      p.rect(boxX - 12, boxY - 8, 420, totalHeight + 16, 6);

      p.fill(180, 240, 255);
      p.noStroke();

      // render text lines with typing progress
      for (let i = 0; i < codeLines.length; i++) {
        let textToShow = codeLines[i];
        if (i < currentLine) {
          // fully printed
        } else if (i === currentLine && !typingFinished) {
          textToShow = codeLines[i].substring(0, Math.min(currentChar, codeLines[i].length));
        } else if (i > currentLine && !typingFinished) {
          textToShow = "";
        }

        p.fill(200, 230, 255, 255);
        p.text(textToShow, boxX - 6, boxY + i * codeLineHeight);
      }

      p.pop();
    }

    // ---------- resize helper ----------
    function resizeToParent() {
      const parent = document.getElementById("canvasWrap");
      if (!parent || !myCanvas) return;
      const w = parent.clientWidth;
      const h = parent.clientHeight;
      if (w === 0 || h === 0) return;
      p.resizeCanvas(w, h);
      // recompute cols/rows & update capture size
      cols = Math.max(1, p.floor(p.width / pixelSize));
      rows = Math.max(1, p.floor(p.height / pixelSize));
      if (capture) {
        try {
          capture.size(cols, rows);
        } catch (e) {
          // some browsers reject changing resolution after start
        }
      }
    }

    // ---------- cleanup if p5 instance is removed ----------
    p.remove = function () {
      try {
        if (capture && capture.elt && capture.elt.srcObject) {
          // stop camera tracks
          const tracks = capture.elt.srcObject.getTracks();
          tracks.forEach(t => t.stop());
        }
      } catch (e) {}
    };

  }, document.getElementById("canvasWrap"));

  // ---------- ANIM 2 (unchanged, but Webflow-safe attach) ----------
  new p5((p) => {

    let particles = [];

    p.setup = function () {
      const parent = document.getElementById("canvas-container");
      const w = parent ? parent.clientWidth : p.windowWidth;
      const h = parent ? parent.clientHeight : p.windowHeight;

      let c = p.createCanvas(w, h);
      if (parent) c.parent("canvas-container");

      p.colorMode(p.HSB, 360, 100, 100, 100);

      for (let i = 0; i < 150; i++) {
        particles.push(new Particle());
      }

      // resize handling
      const resizeObserver = new ResizeObserver(() => {
        if (parent) p.resizeCanvas(parent.clientWidth, parent.clientHeight);
        else p.resizeCanvas(p.windowWidth, p.windowHeight);
      });
      if (parent) resizeObserver.observe(parent);
      window.addEventListener("resize", () => {
        if (parent) p.resizeCanvas(parent.clientWidth, parent.clientHeight);
        else p.resizeCanvas(p.windowWidth, p.windowHeight);
      });
    };

    p.draw = function () {
      p.background(14, 82, 98);

      for (let part of particles) {
        part.update();
        part.show();
      }

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          let d = p.dist(particles[i].pos.x, particles[i].pos.y, particles[j].pos.x, particles[j].pos.y);

          if (d < 130) {
            p.stroke(0, 0, 130, p.map(d, 0, 130, 100, 0));
            p.strokeWeight(1.2);
            p.line(particles[i].pos.x, particles[i].pos.y, particles[j].pos.x, particles[j].pos.y);
          }
        }
      }
    };

    class Particle {
      constructor() {
        this.pos = p.createVector(p.random(p.width), p.random(p.height));
        this.vel = p5.Vector.random2D().mult(p.random(0.5, 1.5));
        this.size = p.random(2, 4);
      }

      update() {
        let mouse = p.createVector(p.mouseX, p.mouseY);
        let dir = p5.Vector.sub(mouse, this.pos);
        let d = dir.mag();

        if (d < 100) {
          dir.setMag(0.5);
          this.vel.add(dir);
          this.vel.limit(3);
        }

        this.pos.add(this.vel);
        this.edges();
      }

      show() {
        p.noStroke();
        p.fill(0, 0, 100, 50);
        p.ellipse(this.pos.x, this.pos.y, this.size);
      }

      edges() {
        if (this.pos.x < 0) this.pos.x = p.width;
        if (this.pos.x > p.width) this.pos.x = 0;
        if (this.pos.y < 0) this.pos.y = p.height;
        if (this.pos.y > p.height) this.pos.y = 0;
      }
    }

  }, document.getElementById("canvas-container"));

// });
