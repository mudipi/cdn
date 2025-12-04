(function () {
  const DEFAULTS = { storageKey: "dark-mode" };
  const script = document.currentScript;
  const html = document.documentElement;

  const varList = (script.getAttribute("tr-color-vars") || "")
    .split(",")
    .map(v => v.trim())
    .filter(Boolean);

  function getColors(prefix) {
    const out = {};
    const styles = getComputedStyle(html);
    varList.forEach(name => {
      out[`--color--${name}`] = styles.getPropertyValue(`--${prefix}--${name}`).trim();
    });
    return out;
  }

  let lightColors = {};
  let darkColors = {};

  function refreshColors() {
    lightColors = getColors("color");
    darkColors = getColors("dark");
  }

  function applyColors(colors, animate = true) {
    if (animate && window.gsap) {
      gsap.to(html, { duration: 0.4, ease: "power1.out", ...colors });
    } else {
      for (const k in colors) html.style.setProperty(k, colors[k]);
    }
  }

  function setDark(enabled, animate = false) {
    localStorage.setItem(DEFAULTS.storageKey, enabled ? "true" : "false");
    html.classList.toggle("dark-mode", enabled);
    applyColors(enabled ? darkColors : lightColors, animate);
  }

  refreshColors();

  const saved = localStorage.getItem(DEFAULTS.storageKey);
  const system = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const initial = saved === null ? system : saved === "true";

  setDark(initial, false);

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[tr-color-toggle]").forEach(btn => {
      btn.addEventListener("click", () => {
        setDark(!html.classList.contains("dark-mode"), true);
      });
    });
  });
})();