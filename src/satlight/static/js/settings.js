// Settings modal. Event-driven: it is only built/updated when opened or saved,
// never on the animation loop.
import { state, on, emit } from "./state.js";
import { createTeleportMap } from "./teleportMap.js";

const el = (id) => document.getElementById(id);

const EFFECT_LABELS = {
  trail: "TRAILS",
  orbitTrack: "ORBIT TRACKS",
  shadowFade: "SHADOW FADE",
};

const DISPLAY_LABELS = {
  guides: "GUIDES",
  ceilingFlip: "CEILING FLIP",
  belowHorizon: "BELOW HORIZON",
};

let map = null;

function buildToggles(hostId, store, labels, onChange) {
  const host = el(hostId);
  host.innerHTML = "";
  for (const key of Object.keys(store)) {
    const btn = document.createElement("button");
    btn.className = "filter-chip" + (store[key] ? " on" : "");
    btn.textContent = labels[key] || key.toUpperCase();
    btn.addEventListener("click", () => {
      store[key] = !store[key];
      btn.classList.toggle("on");
      if (onChange) onChange();
    });
    host.appendChild(btn);
  }
}

function syncMarkerFromInputs() {
  if (!map) return;
  const lat = parseFloat(el("set-lat").value);
  const lon = parseFloat(el("set-lon").value);
  if (!Number.isNaN(lat) && !Number.isNaN(lon)) map.setMarker(lat, lon);
}

async function open() {
  el("set-lat").value = state.observer.latitude.toFixed(4);
  el("set-lon").value = state.observer.longitude.toFixed(4);
  el("set-elev").value = String(state.observer.elevation_m);
  buildToggles("effects-row", state.effects, EFFECT_LABELS, null);
  buildToggles("display-row", state.display, DISPLAY_LABELS, () => emit("view"));

  el("settings-modal").classList.remove("hidden");

  if (!map) {
    map = await createTeleportMap(el("teleport-map"), (lat, lon) => {
      el("set-lat").value = lat.toFixed(4);
      el("set-lon").value = lon.toFixed(4);
    });
  }
  map.setMarker(state.observer.latitude, state.observer.longitude);
}

function close() {
  el("settings-modal").classList.add("hidden");
}

async function save() {
  const body = {
    latitude: parseFloat(el("set-lat").value),
    longitude: parseFloat(el("set-lon").value),
    elevation_m: parseFloat(el("set-elev").value),
  };
  const res = await fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const updated = await res.json();
  state.observer = updated;
  emit("observer", updated);
  close();
}

export function initSettings() {
  on("open-settings", open);
  el("set-cancel").addEventListener("click", close);
  el("set-save").addEventListener("click", save);
  el("set-lat").addEventListener("input", syncMarkerFromInputs);
  el("set-lon").addEventListener("input", syncMarkerFromInputs);
}
