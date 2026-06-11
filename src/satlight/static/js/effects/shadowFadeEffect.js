// Shadow-fade effect: satellites in Earth's shadow (not sunlit) dim smoothly,
// giving a cinematic sense of them slipping into night.
import { effects } from "../registry.js";

const shadowFadeEffect = {
  id: "shadowFade",
  // alpha multiplier per satellite based on its sunlit flag.
  alpha(sat) {
    return sat.sunlit ? 1 : 0.3;
  },
};

effects.register(shadowFadeEffect.id, shadowFadeEffect);

export default shadowFadeEffect;
