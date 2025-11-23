const anim2 = (p) => {

  let particles = [];

  p.setup = function () {
    let canvas = p.createCanvas(p.windowWidth, p.windowHeight);
    canvas.parent("canvas-container");

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
};

new p5(anim2);