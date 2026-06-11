// Starlink renderer: a tiny satellite glyph (body + two solar wings).
import { renderers } from "../registry.js";

const RES = 32;
const BASE = 13;
const cache = new Map();

function buildSprite(color) {
  const c = document.createElement("canvas");
  c.width = c.height = RES;
  const ctx = c.getContext("2d");
  const m = RES / 2;
  ctx.fillStyle = color;

  // body
  ctx.fillRect(m - 2, m - 6, 4, 12);
  // wings
  ctx.globalAlpha = 0.8;
  ctx.fillRect(m - 13, m - 3, 9, 6);
  ctx.fillRect(m + 4, m - 3, 9, 6);
  // soft core
  ctx.globalAlpha = 1;
  ctx.beginPath();
  ctx.arc(m, m, 2.2, 0, Math.PI * 2);
  ctx.fill();
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

renderers.register("STARLINK", { id: "STARLINK", draw });
