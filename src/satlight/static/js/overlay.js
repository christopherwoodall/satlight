// Event-driven guide overlay (compass, altitude rings, zenith). It lives on its
// own transparent canvas above the animated sky and only redraws on demand
// (resize / zoom / pan / mode / toggle / first-frame), so it stays crisp and
// never smears with the satellite trails. The active projection plugin draws its
// own guides.
import { state, on } from "./state.js";
import { themes } from "./registry.js";
import { getGeometry, activeProjection } from "./canvas.js";

let canvas = null;
let ctx = null;
let cssW = 0;
let cssH = 0;
let firstFrameDrawn = false;

function resize() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  cssW = window.innerWidth;
  cssH = window.innerHeight;
  canvas.width = Math.floor(cssW * dpr);
  canvas.height = Math.floor(cssH * dpr);
  canvas.style.width = cssW + "px";
  canvas.style.height = cssH + "px";
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

export function redrawGuides() {
  if (!ctx) return;
  ctx.clearRect(0, 0, cssW, cssH);
  if (!state.display.guides) return;
  const proj = activeProjection();
  if (proj.drawGuides) proj.drawGuides(ctx, getGeometry(), themes.get(state.theme));
}

export function startOverlay() {
  canvas = document.getElementById("guides");
  if (!canvas) return;
  ctx = canvas.getContext("2d");
  resize();
  redrawGuides();

  window.addEventListener("resize", () => {
    resize();
    redrawGuides();
  });

  on("view", redrawGuides);

  // Redraw on the first frame to catch layout changes that happen after boot.
  on("frame", () => {
    if (!firstFrameDrawn) {
      firstFrameDrawn = true;
      redrawGuides();
    }
  });
}
