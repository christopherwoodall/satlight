// Orbit-track effect: draws a faint predicted path through the server-computed
// future track (+5/+10/+15 min) for above-horizon satellites.
import { effects } from "../registry.js";

const orbitTrackEffect = {
  id: "orbitTrack",
  track(ctx, api) {
    const { project, g, az, alt, trackAz, trackAlt, color } = api;
    if (!trackAz || !trackAlt) return;

    const start = project(az, alt, g);
    ctx.globalAlpha = 0.22;
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    for (let k = 0; k < trackAz.length; k++) {
      const p = project(trackAz[k], trackAlt[k], g);
      ctx.lineTo(p.x, p.y);
    }
    ctx.stroke();
  },
};

effects.register(orbitTrackEffect.id, orbitTrackEffect);

export default orbitTrackEffect;
