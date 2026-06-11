// Default renderer: a soft pastel dot. Used for OTHER and any unmatched type.
import { renderers } from "../registry.js";

const RES = 28; // sprite resolution (drawn larger, scaled down for crispness)
const BASE = 11; // on-screen base diameter in CSS px
const cache = new Map();

function buildSprite(color) {
  const c = document.createElement("canvas");
  c.width = c.height = RES;
  const ctx = c.getContext("2d");
  const cx = RES / 2;
  const grad = ctx.createRadialGradient(cx, cx, 0, cx, cx, cx);
  grad.addColorStop(0, color);
  grad.addColorStop(0.55, color);
  grad.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.arc(cx, cx, cx, 0, Math.PI * 2);
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

renderers.register("default", { id: "default", draw });
