function createSlider(options = {}) {
  const {
    selector,
    trackSelector = '.slider-track',
    slideSelector = '.slide',
    dotsSelector = '.slider-dots',
    prevSelector = '.prev',
    nextSelector = '.next',
    toggleSelector = '.toggle',
    speed = 500,
    delay = 2000,
    loop = true,
    infinite = false,
    autoplay = true,
    pauseOnHover = true,
    easing = 'ease',
    // direction: 'ltr' (left-to-right) or 'rtl' (right-to-left)
    direction = (options.direction || 'ltr').toLowerCase()
  } = options;

  // Validate direction
  if (direction !== 'ltr' && direction !== 'rtl') {
    console.warn('Invalid direction. Using ltr as default.');
    direction = 'ltr';
  }

  const root = typeof selector === 'string' ? document.querySelector(selector) : selector;
  if (!root) { console.warn('slider root not found', selector); return; }
  const track = root.querySelector(trackSelector);
  if (!track) { console.warn('track not found'); return; }
  let originalSlides = Array.from(track.querySelectorAll(slideSelector));
  if (!originalSlides.length) { console.warn('no slides'); return; }

  let dotsContainer = root.querySelector(dotsSelector);
  const btnPrev = root.querySelector(prevSelector);
  const btnNext = root.querySelector(nextSelector);
  const btnToggle = root.querySelector(toggleSelector);

  // State
  const realCount = originalSlides.length;
  let workingSlides = [];                 // current DOM order slides (may include clones)
  let slideWidth = 0;
  let currentIndex = 0; // index in workingSlides (DOM order)
  let playing = Boolean(autoplay);
  let timerId = null;
  let isDragging = false;
  let dragStartX = 0;
  let dragCurrentX = 0;
  let transitionInProgress = false;
  let manualPause = false;

  // handler refs for destroy()
  let handlePointerDown, handlePointerMove, handlePointerUp, handleBlur;
  let handleResize, handleMouseEnter, handleMouseLeave;

  // 1) Annotate original slides with their real index (0..n-1).
  originalSlides.forEach((s, i) => {
    s.dataset.realIndex = String(i);
  });

  // 2) Reorder DOM if direction === 'rtl' so visual left→right corresponds to indices 0..n-1
  function ensureDomVisualOrder() {
    // Build an array of elements in the visual order we want
    const visualOrder = (direction === 'rtl') ? originalSlides.slice().reverse() : originalSlides.slice();

    // Remove all slide elements from track and re-append in visual order
    visualOrder.forEach(s => track.appendChild(s));

    // After reordering, compute and set visualIndex dataset on each slide (visual left-to-right index)
    const slidesNow = Array.from(track.querySelectorAll(slideSelector));
    slidesNow.forEach((s, visualIdx) => {
      s.dataset.visualIndex = String(visualIdx);
    });

    // Set the direction on the root element for CSS styling
    root.setAttribute('data-direction', direction);

    // Apply proper CSS transform origin based on direction
    track.style.transformOrigin = direction === 'rtl' ? 'right center' : 'left center';
  }

  function computeSlideWidth() {
    const s = track.querySelector(slideSelector);
    if (!s) return;
    const rect = s.getBoundingClientRect();
    const style = getComputedStyle(s);
    const mr = parseFloat(style.marginRight || 0);
    const ml = parseFloat(style.marginLeft || 0);
    slideWidth = rect.width + ml + mr;
  }

  // compute translateX for DOM index
  function computeX(domIndex) {
    const base = -slideWidth * domIndex;
    // For RTL, we need to offset the entire track to align to the right edge
    if (direction === 'rtl') {
      const totalWidth = slideWidth * workingSlides.length;
      const containerWidth = root.clientWidth;
      return base + (totalWidth - containerWidth);
    }
    return base;
  }

  function setupClones() {
    // remove previous clones
    track.querySelectorAll('[data-clone="true"], [data-temp-clone="true"]').forEach(n => n.remove());

    // workingSlides reflect current DOM slides (visual order, no clones yet)
    workingSlides = Array.from(track.querySelectorAll(slideSelector));

    if (infinite && realCount > 1) {
      // clone first & last of the current visual order
      const first = workingSlides[0].cloneNode(true);
      const last = workingSlides[workingSlides.length - 1].cloneNode(true);

      first.setAttribute('data-clone', 'true');
      last.setAttribute('data-clone', 'true');

      // preserve metadata so mapping remains consistent
      first.dataset.realIndex = workingSlides[0].dataset.realIndex;
      last.dataset.realIndex = workingSlides[workingSlides.length - 1].dataset.realIndex;
      first.dataset.visualIndex = '-1';
      last.dataset.visualIndex = String(workingSlides.length); // temporary visual position

      // append/prepend clones
      track.appendChild(first);
      track.insertBefore(last, track.firstElementChild);

      // refresh workingSlides to include clones
      workingSlides = Array.from(track.querySelectorAll(slideSelector));
      currentIndex = 1; // show the real first (clone at index 0)
    } else {
      // no clones
      workingSlides = Array.from(track.querySelectorAll(slideSelector));
      currentIndex = 0;
    }

    computeSlideWidth();
    setTrackTransform(computeX(currentIndex), false);
  }

  function buildDots() {
    if (!dotsContainer) {
      dotsContainer = document.createElement('div');
      dotsContainer.className = (dotsSelector || '.slider-dots').replace(/^\./, '') || 'slider-dots';
      root.appendChild(dotsContainer);
    }
    dotsContainer.innerHTML = '';

    const visualIndices = [...Array(realCount).keys()]; // always 0..n-1

    visualIndices.forEach(visualIdx => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'slider-dot';
      b.dataset.visualIndex = String(visualIdx);

      const domIndex = infinite ? visualIdx + 1 : visualIdx;
      b.dataset.domIndex = String(domIndex);

      const slideForVisual = Array.from(track.querySelectorAll(slideSelector))
        .find(s => s.dataset.visualIndex === String(visualIdx));
      if (slideForVisual) b.dataset.realIndex = slideForVisual.dataset.realIndex;

      b.setAttribute('aria-label', 'Go to slide ' + (visualIdx + 1));
      dotsContainer.appendChild(b);
    });

    const onDotsClick = (ev) => {
      const b = ev.target.closest('button[data-visual-index]');
      if (!b) return;

      let visualIndex = Number(b.dataset.visualIndex);

      // 🔄 Flip the mapping if direction is rtl
      if (direction === 'rtl') {
        visualIndex = realCount - 1 - visualIndex;
      }

      // Convert visualIndex to domIndex
      const domIndex = infinite ? visualIndex + 1 : visualIndex;

      goTo(domIndex);
    };

    dotsContainer.__pislider_onclick = onDotsClick;
    dotsContainer.addEventListener('click', onDotsClick);

    updateDots();
  }

  function updateDots() {
    if (!dotsContainer) return;
    const dots = Array.from(dotsContainer.children);
    dots.forEach(d => {
      d.classList.remove('active');
      d.removeAttribute('aria-current');
    });

    const visualIndex = Number(workingSlides[currentIndex].dataset.visualIndex) || 0;

    let activeDot;
    if (direction === 'rtl') {
      // rtl → highlight goes right-to-left
      const inverted = realCount - 1 - visualIndex;
      activeDot = dots[inverted];
    } else {
      // ltr → highlight goes left-to-right
      activeDot = dots[visualIndex];
    }

    if (activeDot) {
      activeDot.classList.add('active');
      activeDot.setAttribute('aria-current', 'true');
    }
  }

  function setTrackTransform(x, withTransition = true) {
    if (withTransition) track.style.transition = `transform ${speed}ms ${easing}`;
    else track.style.transition = 'none';
    track.style.transform = `translateX(${x}px)`;
  }

  // Normal goTo by DOM index
  function goTo(index, { skipAnimation = false } = {}) {
    if (transitionInProgress) return;
    transitionInProgress = true;

    // clamp / wrap for finite or loop
    if (!infinite) {
      if (!loop) {
        index = Math.max(0, Math.min(index, workingSlides.length - 1));
      } else {
        index = ((index % workingSlides.length) + workingSlides.length) % workingSlides.length;
      }
    }

    setTrackTransform(computeX(index), !skipAnimation);

    let called = false;
    const cleanup = () => {
      // in infinite we must jump when moving to clones
      if (infinite) {
        if (index === workingSlides.length - 1) {
          // moved to clone-first -> jump to real first
          currentIndex = 1;
          setTrackTransform(computeX(currentIndex), false);
        } else if (index === 0) {
          // moved to clone-last -> jump to real last
          currentIndex = workingSlides.length - 2;
          setTrackTransform(computeX(currentIndex), false);
        } else {
          currentIndex = index;
        }
      } else {
        currentIndex = index;
      }
      updateDots();
      transitionInProgress = false;
    };

    const onEnd = (e) => {
      if (e && e.target !== track) return;
      if (called) return;
      called = true;
      track.removeEventListener('transitionend', onEnd);
      cleanup();
    };
    track.addEventListener('transitionend', onEnd);
    // fallback
    setTimeout(() => { if (!called) onEnd(); }, speed + 160);
  }

  // Helper for user-facing visual indexing (left-to-right)
  function goToUserIndex(userVisualIndex) {
    // userVisualIndex: 0..realCount-1 (left-to-right visually)
    const dot = dotsContainer && dotsContainer.querySelector(`button[data-visual-index="${userVisualIndex}"]`);
    if (dot) {
      const domIndex = Number(dot.dataset.domIndex);
      goTo(domIndex);
    } else {
      // fallback: compute dom index
      goTo(infinite ? userVisualIndex + 1 : userVisualIndex);
    }
  }

  // Smooth wrap for finite + loop: animate to a temp clone then jump to first
  function wrapToStartSmooth() {
    if (transitionInProgress) return;
    transitionInProgress = true;

    // clone the visual-first (workingSlides[0]) and append to the end
    const firstReal = workingSlides[0];
    const temp = firstReal.cloneNode(true);
    temp.setAttribute('data-temp-clone', 'true');
    // copy dataset so mapping remains consistent
    temp.dataset.realIndex = firstReal.dataset.realIndex;
    temp.dataset.visualIndex = String(workingSlides.length);
    track.appendChild(temp);

    // animate to the appended temp index
    const targetIndex = workingSlides.length; // temp is at this index
    setTrackTransform(computeX(targetIndex), true);

    let called = false;
    const onEnd = (e) => {
      if (e && e.target !== track) return;
      if (called) return;
      called = true;
      track.removeEventListener('transitionend', onEnd);

      try { temp.remove(); } catch (e) { }
      // reset to real first
      workingSlides = Array.from(track.querySelectorAll(slideSelector));
      setTrackTransform(computeX(0), false);
      currentIndex = 0;
      updateDots();
      transitionInProgress = false;
    };
    track.addEventListener('transitionend', onEnd);

    // fallback
    setTimeout(() => {
      if (!called) {
        try { track.removeEventListener('transitionend', onEnd); } catch (e) { }
        try { temp.remove(); } catch (e) { }
        workingSlides = Array.from(track.querySelectorAll(slideSelector));
        setTrackTransform(computeX(0), false);
        currentIndex = 0;
        updateDots();
        transitionInProgress = false;
      }
    }, speed + 220);
  }

  // next/previous in visual terms (left-to-right)
  function next() {
    const target = currentIndex + 1;
    // If finite and at visual end => wrap smoothly if loop true
    if (!infinite) {
      if (currentIndex === workingSlides.length - 1) {
        if (loop) {
          // jump to end (no smooth reverse wrap implemented)
          goTo(workingSlides.length);
          return;
        }
        // else clamp
        return;
      }
    }
    goTo(target);
  }

  function prev() {
    const target = currentIndex - 1;
    if (!infinite) {
      if (currentIndex === 0) {
        if (loop) {
          // jump to end (no smooth reverse wrap implemented)
          goTo(workingSlides.length - 1);
          return;
        }
        return;
      }
    }
    goTo(target);
  }

  // autoplay controls
  function updateToggleButton() {
    if (!btnToggle) return;
    if (playing) {
      btnToggle.classList.remove('paused');
      btnToggle.classList.add('playing');
      btnToggle.setAttribute('aria-pressed', 'true');
    } else {
      btnToggle.classList.remove('playing');
      btnToggle.classList.add('paused');
      btnToggle.setAttribute('aria-pressed', 'false');
    }
  }

  function startAutoplay() {
    if (!autoplay || manualPause) return;
    stopAutoplay();
    playing = true;
    updateToggleButton();

    timerId = setInterval(() => {
      if (!transitionInProgress) {
        if (direction === 'rtl') {
          next();
        } else {
          prev();
        }
      }
    }, Math.max(200, delay) + speed);
  }

  function stopAutoplay() {
    playing = false;
    updateToggleButton();
    if (timerId) { clearInterval(timerId); timerId = null; }
  }

  // dragging pointers
  function pointerDown(x, pointerId) {
    isDragging = true;
    dragStartX = x;
    dragCurrentX = x;
    transitionInProgress = false;
    stopAutoplay();
    track.style.transition = 'none';
  }
  function pointerMove(x) {
    if (!isDragging) return;
    dragCurrentX = x;
    const diff = dragCurrentX - dragStartX;
    const base = computeX(currentIndex);
    setTrackTransform(base + diff, false);
  }
  function pointerUp() {
    if (!isDragging) return;
    const diff = dragCurrentX - dragStartX;
    isDragging = false;
    const threshold = Math.max(40, slideWidth * 0.15);
    if (Math.abs(diff) > threshold) {
      if (diff > 0) prev(); else next();
    } else {
      goTo(currentIndex);
    }
    if (autoplay) startAutoplay();
  }

  function addPointerListeners() {
    handlePointerDown = (ev) => {
      if (ev.target.closest('button, .slider-dot')) return;
      if (ev.pointerType === 'mouse' && ev.button !== 0) return;
      ev.preventDefault();
      try { track.setPointerCapture(ev.pointerId); } catch (e) { }
      pointerDown(ev.clientX, ev.pointerId);
    };
    track.addEventListener('pointerdown', handlePointerDown);

    handlePointerMove = (ev) => {
      if (!isDragging) return;
      pointerMove(ev.clientX);
    };
    window.addEventListener('pointermove', handlePointerMove);

    handlePointerUp = (ev) => {
      if (isDragging) {
        try { track.releasePointerCapture(ev.pointerId); } catch (e) { }
        pointerUp();
      }
    };
    window.addEventListener('pointerup', handlePointerUp);

    handleBlur = () => { if (isDragging) pointerUp(); };
    window.addEventListener('blur', handleBlur);
  }

  // Buttons handlers
  const onPrevClick = (e) => { e.stopPropagation(); prev(); };
  const onNextClick = (e) => { e.stopPropagation(); next(); };
  const onToggleClick = (e) => {
    e.stopPropagation();
    if (playing) { manualPause = true; stopAutoplay(); }
    else { manualPause = false; startAutoplay(); }
  };

  if (btnPrev) btnPrev.addEventListener('click', onPrevClick);
  if (btnNext) btnNext.addEventListener('click', onNextClick);
  if (btnToggle) btnToggle.addEventListener('click', onToggleClick);

  if (pauseOnHover) {
    handleMouseEnter = () => { if (playing) stopAutoplay(); };
    handleMouseLeave = () => { if (autoplay && !manualPause && !playing) startAutoplay(); };
    root.addEventListener('mouseenter', handleMouseEnter);
    root.addEventListener('mouseleave', handleMouseLeave);
  }

  handleResize = () => {
    if (typeof handleResize._t !== 'undefined') clearTimeout(handleResize._t);
    handleResize._t = setTimeout(() => {
      computeSlideWidth();
      setTrackTransform(computeX(currentIndex), false);
    }, 80);
  };
  window.addEventListener('resize', handleResize);

  // assign data attributes and initialize
  function preloadSlides(sliderRoot) {
    const slideEls = sliderRoot.querySelectorAll(slideSelector);
    slideEls.forEach(slide => {
      // CSS background-image
      const style = getComputedStyle(slide);
      const bg = style.backgroundImage || '';
      if (bg && bg !== 'none') {
        const m = bg.match(/url\((?:'|")?(.*?)(?:'|")?\)/);
        if (m && m[1]) { const img = new Image(); img.src = m[1]; }
      }
      const imgTag = slide.querySelector('img');
      if (imgTag && imgTag.src) { const img = new Image(); img.src = imgTag.src; }
    });
  }

  function init() {
    ensureDomVisualOrder();     // reorder DOM slides for rtl if needed
    computeSlideWidth();
    setupClones();
    track.style.willChange = 'transform';
    buildDots();
    addPointerListeners();
    updateToggleButton();
    if (autoplay) startAutoplay();
    root.setAttribute('role', 'region');
    root.setAttribute('aria-roledescription', 'carousel');
    try { root.setAttribute('dir', direction); } catch (e) { }
    preloadSlides(root);
  }

  init();

  return {
    next, prev, goToUserIndex, play: () => { manualPause = false; startAutoplay(); }, pause: () => { manualPause = true; stopAutoplay(); }, destroy() {
      stopAutoplay();
      window.removeEventListener('resize', handleResize);
      if (btnPrev) btnPrev.removeEventListener('click', onPrevClick);
      if (btnNext) btnNext.removeEventListener('click', onNextClick);
      if (btnToggle) btnToggle.removeEventListener('click', onToggleClick);
      if (pauseOnHover) {
        root.removeEventListener('mouseenter', handleMouseEnter);
        root.removeEventListener('mouseleave', handleMouseLeave);
      }
      if (dotsContainer && dotsContainer.__pislider_onclick) {
        dotsContainer.removeEventListener('click', dotsContainer.__pislider_onclick);
        delete dotsContainer.__pislider_onclick;
      }
      if (handlePointerDown) track.removeEventListener('pointerdown', handlePointerDown);
      if (handlePointerMove) window.removeEventListener('pointermove', handlePointerMove);
      if (handlePointerUp) window.removeEventListener('pointerup', handlePointerUp);
      if (handleBlur) window.removeEventListener('blur', handleBlur);

      track.querySelectorAll('[data-clone="true"], [data-temp-clone="true"]').forEach(n => n.remove());
      track.style.transition = '';
      track.style.transform = '';
    },
    getState() { return { realCount, workingCount: workingSlides.length, currentIndex, playing, infinite, direction }; }
  };
}