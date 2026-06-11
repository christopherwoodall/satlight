// Theme: Projector-Safe Kawaii LCARS. Low-brightness pastels on pure black.
import { themes } from "../registry.js";

const kawaiiLcars = {
  id: "kawaiiLcars",
  label: "KAWAII LCARS",
  bg: "#000000",
  pink: "#e69ab4",
  lavender: "#b4aae6",
  mint: "#96dcb4",
  cyan: "#8cc8d2",
  text: "#c4bce0",
  dim: "rgba(180,170,230,0.35)",
  // Per-classification accent used by renderers/effects.
  accents: {
    STARLINK: "#e69ab4",
    ISS: "#b4aae6",
    OTHER: "#8cc8d2",
    default: "#96dcb4",
  },
};

themes.register(kawaiiLcars.id, kawaiiLcars);

export default kawaiiLcars;
