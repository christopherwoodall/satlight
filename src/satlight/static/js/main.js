// Entry point. Imports plugin modules (they self-register), loads config, then
// starts the canvas, HUD, settings, and the WebSocket stream.
import { state } from "./state.js";
import { connect } from "./websocket.js";
import { startCanvas } from "./canvas.js";
import { startOverlay } from "./overlay.js";
import { startInteraction } from "./interaction.js";
import { initHud } from "./hud.js";
import { initSettings } from "./settings.js";

// Plugin registrations (add a file + an import line to extend SatLight).
import "./themes/kawaiiLcars.js";
import "./projection_modes/ceiling.js";
import "./projection_modes/full_sky.js";
import "./projection_modes/stereographic.js";
import "./renderers/defaultRenderer.js";
import "./renderers/starlinkRenderer.js";
import "./renderers/issRenderer.js";
import "./effects/trailEffect.js";
import "./effects/orbitTrackEffect.js";
import "./effects/shadowFadeEffect.js";

async function boot() {
  const cfg = await (await fetch("/api/config")).json();
  state.config = { modes: cfg.modes, classifications: cfg.classifications };
  state.observer = cfg.observer;
  state.interval = cfg.update_interval || 1.0;
  state.filters = new Set(cfg.classifications);

  const def = cfg.modes.find((m) => m.default) || cfg.modes[0];
  if (def) state.mode = def.id;

  initHud();
  initSettings();
  startCanvas();
  try { startOverlay(); } catch (e) { console.warn("overlay:", e); }
  try { startInteraction(); } catch (e) { console.warn("interaction:", e); }
  connect();
}

boot();
