// ISS renderer: a small station glyph (core module, four panels, truss).
// Drawn slightly larger so the station stands out from the constellation.
import { renderers } from "../registry.js";

const RES = 40;
const BASE = 20;
const cache = new Map();

function buildSprite(color) {
  const c = document.createElement("canvas");
  c.width = c.height = RES;
  const ctx = c.getContext("2d");
  const m = RES / 2;
  ctx.fillStyle = color;

  // truss
  ctx.globalAlpha = 0.5;
  ctx.fillRect(m - 1, m - 14, 2, 28);
  // panels
  ctx.globalAlpha = 0.8;
  ctx.fillRect(m - 16, m - 9, 12, 5);
  ctx.fillRect(m - 16, m + 4, 12, 5);
  ctx.fillRect(m + 4, m - 9, 12, 5);
  ctx.fillRect(m + 4, m + 4, 12, 5);
  // core module
  ctx.globalAlpha = 1;
  ctx.fillRect(m - 4, m - 4, 8, 8);
  return c;
}

function sprite(color) {
  let s = cache.get(color);
  if (!s) {
    s = buildSprite(color);
    cache.set(color, s);
  }
  return s;
}

function draw(ctx, x, y, scale, alpha, color) {
  const w = BASE * scale;
  ctx.globalAlpha = alpha;
  ctx.drawImage(sprite(color), x - w / 2, y - w / 2, w, w);
}

renderers.register("ISS", { id: "ISS", draw });
