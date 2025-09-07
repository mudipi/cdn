# picarousel

![Vanilla JS](https://img.shields.io/badge/vanilla-JS-yellow.svg) ![Version](https://img.shields.io/badge/version-1.0.0-blue.svg) ![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)

Compact, dependency-free slider/carousel with RTL support, optional infinite looping, autoplay, pointer dragging, and accessible dots.

---

## Quick start

1. Put `picarousel.js` in your project and include it, **or** use a CDN link.
2. Create markup (see demo below).
3. Call `createSlider({ selector: '#mySlider', infinite: true, autoplay: true })`.

```html
<!-- local -->
<script src="picarousel.js"></script>

<!-- or CDN -->
<script src="https://rawcdn.githack.com/mudipi/cdn/refs/heads/main/carousel/picarousel.js"></script>
```

**Live preview:** save the `demo.html` and `demo.css` shown below into the same folder and open `demo.html` in a browser.

**OR**

**HTML Preview:** - https://rawcdn.githack.com/mudipi/cdn/refs/heads/main/carousel/html-preview/demo.html

---

## Tiny options summary

* `selector` (required) — root selector or element.
* `trackSelector` — selector for the track container (default `.slider-track`).
* `slideSelector` — selector for each slide element (default `.slide`).
* `dotsSelector` — selector for the pagination dots container (default `.slider-dots`).
* `prevSelector` — selector for the "previous" navigation button (default `.prev`).
* `nextSelector` — selector for the "next" navigation button (default `.next`).
* `toggleSelector` — selector for the play/pause toggle button (default `.toggle`).
* `speed` (ms) — transition duration (default `500`).
* `delay` (ms) — autoplay delay (default `2000`).
* `infinite` (bool) — clone-based seamless loop.
* `loop` (bool) — finite wrap (smooth forward wrap when `true`).
* `autoplay` (bool) — start autoplay on init.
* `pauseOnHover` (bool) — pause while pointer is over slider.
* `easing` — CSS transition-timing-function (default `'ease'`).
* `direction` — `'ltr'|'rtl'` (visual ordering; RTL reorders DOM internally).

---

## API (returned object)

* `next()`, `prev()` — move slides.
* `goToUserIndex(i)` — go to visual slide index (0..n-1).
* `play()`, `pause()` — autoplay control.
* `destroy()` — remove listeners & clones.
* `getState()` — debug info.

---

## Demo files (save and open `demo.html`)


### demo.html

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>picarousel - Demo</title>
  <link rel="stylesheet" href="demo.css">
</head>
<body>
  <div id="mySlider" class="picarousel">
    <div class="slider-track">
      <div class="slide"><img src="https://picsum.photos/800/300?1" alt="1"></div>
      <div class="slide"><img src="https://picsum.photos/800/300?2" alt="2"></div>
      <div class="slide"><img src="https://picsum.photos/800/300?3" alt="3"></div>
    </div>
    <button class="prev" aria-label="Prev">‹</button>
    <button class="next" aria-label="Next">›</button>
    <button class="toggle" aria-pressed="true">Play</button>
    <div class="slider-dots"></div>
  </div>

  <!-- Use local file or CDN as you prefer -->
  <!-- local -->
  <script src="picarousel.js"></script>
  <!-- or CDN -->
  <!-- <script src="https://rawcdn.githack.com/mudipi/cdn/refs/heads/main/carousel/picarousel.js"><script> -->

  <script>
    createSlider({
      selector: '#mySlider',
      speed: 600,
      delay: 3000,
      infinite: true,
      autoplay: true,
      direction: 'ltr'
    });
  </script>
</body>
</html>
```

### demo.css

```css
:root{--size:800px}
body{font-family:system-ui,Arial;margin:24px;}
.picarousel{width:var(--size);max-width:100%;position:relative;overflow:hidden}
.slider-track{display:flex;transition:transform .6s ease}
.slide{flex:0 0 100%;box-sizing:border-box}
.slide img{width:100%;display:block}
.prev,.next,.toggle{position:absolute;top:50%;transform:translateY(-50%);background:#fff;border:1px solid #ddd;padding:8px;border-radius:6px;cursor:pointer}
.prev{left:8px}
.next{right:8px}
.toggle{left:50%;transform:translate(-50%,-50%);bottom:10px;top:auto}
.slider-dots{position:absolute;left:50%;transform:translateX(-50%);bottom:14px;display:flex;gap:6px}
.slider-dot{width:10px;height:10px;border-radius:50%;background:#eee;border:none}
.slider-dot.active{background:#333}
```

---

## Short notes

* For symmetric continuous looping in both directions use `infinite: true`.
* RTL mode reorders slides internally — use `goToUserIndex(i)` for visual indexing.
