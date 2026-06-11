// Trail effect: instead of clearing the canvas each frame, paint a faint black
// veil so satellites leave gentle fading trails as they drift.
import { effects } from "../registry.js";

const trailEffect = {
  id: "trail",
  // Returns true to signal it handled the frame background.
  background(ctx, w, h) {
    ctx.globalAlpha = 1;
    ctx.fillStyle = "rgba(0,0,0,0.16)";
    ctx.fillRect(0, 0, w, h);
    return true;
  },
};

effects.register(trailEffect.id, trailEffect);

export default trailEffect;
