
window.Webflow ||= [];
window.Webflow.push(() => {

  // ========== P5 INSTANCE 1 ==========
  new p5((p) => {
    let capture;
    let pixelSize = 8;
    let cols, rows;
    let gammaZ = 0.5;
    let t = 0;
    let BASE_ORANGE;

    p.setup = function () {
      const parent = document.getElementById("canvasWrap");
      const w = parent.clientWidth;
      const h = parent.clientHeight;

      const c = p.createCanvas(w, h);
      c.parent("canvasWrap");

      p.frameRate(60);
      BASE_ORANGE = p.color('#f95d2d');

      cols = p.floor(p.width / pixelSize);
      rows = p.floor(p.height / pixelSize);

      capture = p.createCapture(p.VIDEO, () => {
        console.log("Camera initialized");
      });
      capture.size(cols, rows);
      capture.hide();
    };

    p.draw = function () {
      p.clear();
      drawZordon();
    };

    function drawZordon() {
      if (!capture.loadedmetadata) return;
      capture.loadPixels();
      if (!capture.pixels.length) return;

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

          let bright = (r + g + b) / 3;

          p.fill(orBase, ogBase, obBase, bright);
          p.rect(x * cellW, y * cellH, cellW, cellH);
        }
      }
      t += 1;
    }
  });

  // ========== P5 INSTANCE 2 ==========
  new p5((p) => {
    let particles = [];

    p.setup = function () {
      const c = p.createCanvas(p.windowWidth, p.windowHeight);
      c.parent("canvas-container");

      p.colorMode(p.HSB, 360, 100, 100, 100);

      for (let i = 0; i < 150; i++) {
        particles.push(new Particle());
      }
    };

    p.draw = function () {
      p.background(14, 82, 98);

      for (let part of particles) {
        part.update();
        part.show();
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
  });

});
