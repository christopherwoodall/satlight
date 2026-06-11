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

// ---- Background map: server-computed topocentric ground grid ----
// The server precomputes (az, alt) for every coastline vertex relative to the
// observer.  The frontend just projects those through the active projection
// plugin and draws -- identical coordinate space to the satellites.

let groundGrid = null; // { rings: [...] } from /api/groundgrid
let bgCache = null; // { key, paths } -- projected screen paths, rebuilt on view change
let gridObserverKey = ""; // observer lat/lon at time of last fetch

function fetchGroundGrid() {
  fetch("/api/groundgrid")
    .then((r) => r.json())
    .then((data) => {
      groundGrid = data;
      const obs = state.observer;
      gridObserverKey = `${obs.latitude},${obs.longitude}`;
      bgCache = null; // force reproject
    })
    .catch((e) => console.warn("groundgrid fetch failed:", e));
}

function bgCacheKey(g, mode) {
  const obs = state.observer;
  return `${g.cx},${g.cy},${g.R},${g.flipX},${mode},${obs.latitude},${obs.longitude}`;
}

function projectGroundRing(ring, proj, g) {
  const out = [];
  for (let i = 0; i < ring.length; i += 2) {
    if (ring[i] === null || ring[i + 1] === null) {
      out.push(NaN, NaN);
      continue;
    }
    const p = proj.project(ring[i], ring[i + 1], g);
    out.push(p.x, p.y);
  }
  return out;
}

function buildBgPaths(proj, g) {
  if (!groundGrid || !groundGrid.rings) return [];
  const paths = [];
  for (const ring of groundGrid.rings) {
    paths.push(projectGroundRing(ring, proj, g));
  }
  return paths;
}

function drawBgMap(proj, g, palette) {
  if (!groundGrid) return;

  // If observer changed, re-fetch the grid from the server.
  const obs = state.observer;
  const obsKey = `${obs.latitude},${obs.longitude}`;
  if (obsKey !== gridObserverKey) {
    fetchGroundGrid();
    return; // draw next frame after grid arrives
  }

  // Rebuild projected paths when geometry or observer changes.
  const key = bgCacheKey(g, state.mode);
  if (!bgCache || bgCache.key !== key) {
    bgCache = { key, paths: buildBgPaths(proj, g) };
  }

  // Clip to the horizon ring so continents don't bleed past it.
  ctx.save();
  ctx.beginPath();
  ctx.arc(g.cx, g.cy, g.R, 0, Math.PI * 2);
  ctx.clip();

  // Draw continents faintly, breaking paths at NaN gap sentinels.
  ctx.globalAlpha = 0.15;
  ctx.fillStyle = palette.mint;
  for (const flat of bgCache.paths) {
    let drawing = false;
    ctx.beginPath();
    for (let i = 0; i < flat.length; i += 2) {
      if (Number.isNaN(flat[i]) || Number.isNaN(flat[i + 1])) {
        if (drawing) {
          ctx.closePath();
          ctx.fill();
          ctx.beginPath();
          drawing = false;
        }
        continue;
      }
      if (!drawing) {
        ctx.moveTo(flat[i], flat[i + 1]);
        drawing = true;
      } else {
        ctx.lineTo(flat[i], flat[i + 1]);
      }
    }
    if (drawing) {
      ctx.closePath();
      ctx.fill();
    }
  }

  // Observer crosshair: the point directly overhead (observer's own location).
  // For an observer on the surface, their own lat/lon is at the zenith.
  const op = proj.project(0, 90, g);
  ctx.globalAlpha = 0.6;
  ctx.strokeStyle = palette.pink;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(op.x - 6, op.y);
  ctx.lineTo(op.x + 6, op.y);
  ctx.moveTo(op.x, op.y - 6);
  ctx.lineTo(op.x, op.y + 6);
  ctx.stroke();

  ctx.restore();
}

// ---- Canvas infrastructure ----

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

  const proj = activeProjection();
  const g = getGeometry();

  // Background map layer (behind satellites, after clear).
  if (state.display.bgMap) {
    drawBgMap(proj, g, palette);
  }

  const frame = state.frame;
  if (frame && frame.count) {
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
  // Pre-fetch the ground grid so it's ready when the user toggles MAP on.
  fetchGroundGrid();
  requestAnimationFrame(render);
}
