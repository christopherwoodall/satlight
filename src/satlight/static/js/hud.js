// Event-driven HUD. It only updates in response to events (frame, catalog,
// connection, observer/mode/filter changes), never on a continuous timer.
import { state, on, emit } from "./state.js";

const el = (id) => document.getElementById(id);

function formatObserver() {
  const o = state.observer;
  const ns = o.latitude >= 0 ? "N" : "S";
  const ew = o.longitude >= 0 ? "E" : "W";
  return `${Math.abs(o.latitude).toFixed(2)}${ns} ${Math.abs(o.longitude).toFixed(2)}${ew}`;
}

function modeLabel(id) {
  const m = state.config.modes.find((m) => m.id === id);
  return m ? m.label : id.toUpperCase();
}

function renderFilters() {
  const host = el("hud-filters");
  host.innerHTML = "";
  for (const cls of state.config.classifications) {
    const btn = document.createElement("button");
    btn.className = "filter-chip" + (state.filters.has(cls) ? " on" : "");
    btn.textContent = cls;
    btn.dataset.cls = cls;
    btn.addEventListener("click", () => {
      if (state.filters.has(cls)) state.filters.delete(cls);
      else state.filters.add(cls);
      btn.classList.toggle("on");
    });
    host.appendChild(btn);
  }
}

function cycleMode() {
  const modes = state.config.modes;
  if (!modes.length) return;
  const idx = modes.findIndex((m) => m.id === state.mode);
  state.mode = modes[(idx + 1) % modes.length].id;
  el("hud-mode").textContent = modeLabel(state.mode);
  emit("view");
}

export function initHud() {
  el("hud-mode").textContent = modeLabel(state.mode);
  el("hud-observer").textContent = formatObserver();
  el("hud-tracked").textContent = String(state.meta.count || 0);
  renderFilters();

  el("hud-mode").addEventListener("click", cycleMode);
  el("hud-settings").addEventListener("click", () => emit("open-settings"));

  on("frame", (f) => {
    let visible = 0;
    for (let i = 0; i < f.count; i++) visible += f.visible[i];
    el("hud-visible").textContent = String(visible);
  });
  on("catalog", (m) => {
    el("hud-tracked").textContent = String(m.count);
  });
  on("observer", () => {
    el("hud-observer").textContent = formatObserver();
  });
  on("connection", (ok) => {
    const node = el("hud-status");
    node.textContent = ok ? "LIVE" : "OFFLINE";
    node.classList.toggle("offline", !ok);
  });
}
