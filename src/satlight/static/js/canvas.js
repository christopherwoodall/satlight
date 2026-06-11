// The only continuously-animating surface (60 FPS). It interpolates each
// satellite from its current position toward the server-provided "next" position
// across the 1 Hz window, then delegates to projection / effect / renderer
// plugins. No per-satellite DOM; sprites are reused and allocations are minimal.
import { state } from "./state.js";
import { projections, renderers, effects, themes } from "./registry.js";

let ctx = null;
let canvas = null;
let cssW = 0;
let cssH = 0;

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

// Shared geometry, including zoom / pan / ceiling-flip, used by the render loop
// and by the (event-driven) guide overlay so they stay perfectly aligned.
export function getGeometry() {
  const baseR = (Math.min(cssW, cssH) / 2) * 0.94;
  const v = state.view;
  return {
    cx: cssW / 2 + v.panX,
    cy: cssH / 2 + v.panY,
    R: baseR * v.zoom,
    flipX: state.display.ceilingFlip ? -1 : 1,
    w: cssW,
    h: cssH,
  };
}

export function activeProjection() {
  return projections.get(state.mode) || projections.get("ceiling");
}

function wrapDelta(a, b) {
  return ((b - a + 540) % 360) - 180;
}

function ensureScreenBuffers(n) {
  if (!state.screen.x || state.screen.x.length < n) {
    state.screen.x = new Float32Array(n);
    state.screen.y = new Float32Array(n);
  }
}

function render() {
  const palette = themes.get(state.theme);
  const enabled = effects.all().filter((e) => state.effects[e.id]);

  let handled = false;
  for (const e of enabled) {
    if (e.background) handled = e.background(ctx, cssW, cssH) || handled;
  }
  if (!handled) {
    ctx.globalAlpha = 1;
    ctx.fillStyle = palette.bg;
    ctx.fillRect(0, 0, cssW, cssH);
  }

  const frame = state.frame;
  if (frame && frame.count) {
    const proj = activeProjection();
    const g = getGeometry();

    const frac = Math.min(
      1,
      (performance.now() - state.frameReceivedAt) / 1000 / (state.interval || 1),
    );

    const types = state.meta.types;
    const trackEffects = enabled.filter((e) => e.track);
    const alphaEffects = enabled.filter((e) => e.alpha);
    const showBelow = state.display.belowHorizon;

    ensureScreenBuffers(frame.count);
    const sx = state.screen.x;
    const sy = state.screen.y;
    state.screen.n = frame.count;

    for (let i = 0; i < frame.count; i++) {
      sx[i] = NaN;
      const type = types[i] || "OTHER";
      if (!state.filters.has(type)) continue;
      if (!showBelow && frame.alt[i] < 0) continue;

      const az = frame.az[i] + wrapDelta(frame.az[i], frame.next_az[i]) * frac;
      const alt = frame.alt[i] + (frame.next_alt[i] - frame.alt[i]) * frac;

      const p = proj.project(az, alt, g);
      if (p.x < -24 || p.x > cssW + 24 || p.y < -24 || p.y > cssH + 24) continue;

      sx[i] = p.x;
      sy[i] = p.y;

      const color = palette.accents[type] || palette.accents.default;

      if (frame.visible[i] && trackEffects.length) {
        for (const e of trackEffects) {
          e.track(ctx, {
            project: proj.project,
            g,
            az,
            alt,
            trackAz: frame.track_az[i],
            trackAlt: frame.track_alt[i],
            color,
          });
        }
      }

      let alpha = p.alpha;
      if (alphaEffects.length) {
        const sat = { sunlit: frame.sunlit[i] };
        for (const e of alphaEffects) alpha *= e.alpha(sat);
      }

      const renderer = renderers.get(type) || renderers.get("default");
      renderer.draw(ctx, p.x, p.y, p.scale, alpha, color);

      if (p.clamped) {
        ctx.globalAlpha = alpha * 0.7;
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(p.x + Math.sin(p.angle) * 7, p.y - Math.cos(p.angle) * 7);
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;
  }

  requestAnimationFrame(render);
}

export function startCanvas() {
  canvas = document.getElementById("sky");
  ctx = canvas.getContext("2d");
  resize();
  window.addEventListener("resize", resize);
  requestAnimationFrame(render);
}
