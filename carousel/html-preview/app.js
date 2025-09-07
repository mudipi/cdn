const firstSlider = createSlider({
  selector: '.my-slider1',
  speed: 500,
  delay: 2000,
  infinite: false,
  autoplay: true,
  pauseOnHover: false,
  direction: 'ltr'
});

const secondSlider = createSlider({
  selector: '.my-slider2',
  speed: 500,
  delay: 2000,
  infinite: true,
  autoplay: true,
  direction: 'ltr'
});

const thirdSlider = createSlider({
  selector: '.my-slider3',
  speed: 500,
  delay: 2000,
  infinite: true,
  autoplay: true,
  direction: 'ltr'
});

const fourthSlider = createSlider({
  selector: '.my-slider4',
  speed: 500,
  delay: 2000,
  infinite: false,
  autoplay: false,
  direction: 'ltr'
});

const fifthSlider = createSlider({
  selector: '.my-slider5',
  speed: 500,
  delay: 2000,
  infinite: true,
  autoplay: true,
  direction: 'rtl'
});

const sixthSlider = createSlider({
  selector: '.my-slider6',
  speed: 500,
  delay: 2000,
  infinite: false,
  autoplay: false,
  direction: 'rtl'
});

window.slider1 = firstSlider;
window.slider2 = secondSlider;
window.slider3 = thirdSlider;
window.slider4 = fourthSlider;
window.slider5 = fifthSlider;
window.slider6 = sixthSlider;
