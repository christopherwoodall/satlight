// Ceiling projection: zenith at center, horizon at the screen edge.
// Below-horizon satellites clamp to the horizon ring (dim, small, with a
// directional tick drawn by the canvas). Honors g.flipX (ceiling E/W flip).
import { projections } from "../registry.js";

const COMPASS = [
  ["N", 0],
  ["NE", 45],
  ["E", 90],
  ["SE", 135],
  ["S", 180],
  ["SW", 225],
  ["W", 270],
  ["NW", 315],
];

function radiusForAlt(alt, R) {
  return ((90 - alt) / 90) * R;
}

function project(az, alt, g) {
  const rad = (az * Math.PI) / 180;
  let r;
  let scale = 1;
  let alpha = 1;
  let clamped = false;

  if (alt >= 0) {
    r = radiusForAlt(alt, g.R);
  } else {
    r = g.R;
    clamped = true;
    scale = 0.6;
    alpha = 0.45;
  }

  return {
    x: g.cx + g.flipX * r * Math.sin(rad),
    y: g.cy - r * Math.cos(rad),
    scale,
    alpha,
    clamped,
    angle: rad,
  };
}

function drawGuides(ctx, g, palette) {
  ctx.lineWidth = 1;
  ctx.globalAlpha = 0.35;
  ctx.strokeStyle = palette.dim;
  for (const alt of [0, 30, 60]) {
    ctx.beginPath();
    ctx.arc(g.cx, g.cy, radiusForAlt(alt, g.R), 0, Math.PI * 2);
    ctx.stroke();
  }

  // zenith marker
  ctx.globalAlpha = 0.5;
  ctx.strokeStyle = palette.lavender;
  ctx.beginPath();
  ctx.moveTo(g.cx - 5, g.cy);
  ctx.lineTo(g.cx + 5, g.cy);
  ctx.moveTo(g.cx, g.cy - 5);
  ctx.lineTo(g.cx, g.cy + 5);
  ctx.stroke();

  // compass labels just outside the horizon ring
  ctx.globalAlpha = 0.8;
  ctx.fillStyle = palette.cyan;
  ctx.font = "11px 'Segoe UI', Arial, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  for (const [label, az] of COMPASS) {
    const rad = (az * Math.PI) / 180;
    const lr = g.R + 14;
    ctx.fillText(
      label,
      g.cx + g.flipX * lr * Math.sin(rad),
      g.cy - lr * Math.cos(rad),
    );
  }
  ctx.globalAlpha = 1;
}

projections.register("ceiling", {
  id: "ceiling",
  label: "CEILING",
  project,
  drawGuides,
});
