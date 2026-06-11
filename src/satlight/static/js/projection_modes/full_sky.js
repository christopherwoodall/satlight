// Full-sky projection: the whole sphere. Zenith center, horizon mid-radius,
// nadir at the edge. Visible and below-horizon satellites are shown together.
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
  return ((90 - alt) / 180) * R;
}

function project(az, alt, g) {
  const rad = (az * Math.PI) / 180;
  const r = radiusForAlt(alt, g.R);
  return {
    x: g.cx + g.flipX * r * Math.sin(rad),
    y: g.cy - r * Math.cos(rad),
    scale: 1,
    alpha: alt >= 0 ? 1 : 0.6,
    clamped: false,
    angle: rad,
  };
}

function drawGuides(ctx, g, palette) {
  ctx.lineWidth = 1;
  ctx.globalAlpha = 0.35;
  ctx.strokeStyle = palette.dim;
  // zenith(90), horizon(0), nadir(-90) rings
  for (const alt of [60, 30, 0, -30, -60]) {
    ctx.beginPath();
    ctx.arc(g.cx, g.cy, radiusForAlt(alt, g.R), 0, Math.PI * 2);
    ctx.stroke();
  }

  // emphasize the horizon ring
  ctx.globalAlpha = 0.6;
  ctx.strokeStyle = palette.mint;
  ctx.beginPath();
  ctx.arc(g.cx, g.cy, radiusForAlt(0, g.R), 0, Math.PI * 2);
  ctx.stroke();

  ctx.globalAlpha = 0.8;
  ctx.fillStyle = palette.cyan;
  ctx.font = "11px 'Segoe UI', Arial, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  for (const [label, az] of COMPASS) {
    const rad = (az * Math.PI) / 180;
    const lr = radiusForAlt(0, g.R) + 14;
    ctx.fillText(
      label,
      g.cx + g.flipX * lr * Math.sin(rad),
      g.cy - lr * Math.cos(rad),
    );
  }
  ctx.globalAlpha = 1;
}

projections.register("full_sky", {
  id: "full_sky",
  label: "FULL SKY",
  project,
  drawGuides,
});
