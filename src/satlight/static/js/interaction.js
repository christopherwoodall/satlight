// Pointer interaction: scroll-to-zoom (toward cursor), drag-to-pan, double-click
// reset, and hover tooltips. All event-driven; nothing here runs on the render
// loop. Hover hit-tests the screen positions stashed by the canvas each frame
// and asks the server (over the existing WebSocket) which city the satellite is
// flying over.
//
// Events are attached to `window` (not the #sky canvas) so they fire regardless
// of which positioned element is visually on top in the stacking order.
import { state, on, emit } from "./state.js";
import { sendQuery } from "./websocket.js";

const ZOOM_MIN = 0.5;
const ZOOM_MAX = 8;
const HIT_RADIUS = 13;

let tip = null;
let dragging = false;
let dragX = 0;
let dragY = 0;
let lastMove = 0;
let hoverIndex = -1;
let cityText = "";

function hideTip() {
  if (tip) tip.classList.add("hidden");
  state.hoverId = null;
  hoverIndex = -1;
  cityText = "";
}

function renderTip(mouseX, mouseY) {
  if (hoverIndex < 0 || !tip) return;
  const i = hoverIndex;
  const f = state.frame;
  const name = state.meta.names[i] || "UNKNOWN";
  const type = state.meta.types[i] || "OTHER";
  const az = f.az[i].toFixed(1);
  const alt = f.alt[i].toFixed(1);
  const lit = f.sunlit[i] ? "SUNLIT" : "IN SHADOW";
  tip.innerHTML =
    `<div class="tip-name">${name}</div>` +
    `<div class="tip-row"><span>${type}</span><span>${lit}</span></div>` +
    `<div class="tip-row"><span>AZ ${az}&deg;</span><span>ALT ${alt}&deg;</span></div>` +
    `<div class="tip-city">${cityText || "LOCATING&hellip;"}</div>`;

  const pad = 16;
  let x = mouseX + pad;
  let y = mouseY + pad;
  if (x + tip.offsetWidth > window.innerWidth) x = mouseX - tip.offsetWidth - pad;
  if (y + tip.offsetHeight > window.innerHeight) y = mouseY - tip.offsetHeight - pad;
  tip.style.left = x + "px";
  tip.style.top = y + "px";
  tip.classList.remove("hidden");
}

function nearestSat(mx, my) {
  const sx = state.screen.x;
  const sy = state.screen.y;
  if (!sx) return -1;
  let best = -1;
  let bestD = HIT_RADIUS * HIT_RADIUS;
  for (let i = 0; i < state.screen.n; i++) {
    const x = sx[i];
    if (Number.isNaN(x)) continue;
    const dx = x - mx;
    const dy = sy[i] - my;
    const d = dx * dx + dy * dy;
    if (d < bestD) {
      bestD = d;
      best = i;
    }
  }
  return best;
}

function isInHud(clientX, clientY) {
  const hud = document.getElementById("hud");
  if (!hud) return false;
  const r = hud.getBoundingClientRect();
  return clientX >= r.left && clientX <= r.right && clientY >= r.top && clientY <= r.bottom;
}

function isModalOpen() {
  const modal = document.getElementById("settings-modal");
  return modal && !modal.classList.contains("hidden");
}

function onMove(ev) {
  if (isModalOpen()) {
    if (hoverIndex >= 0) hideTip();
    return;
  }

  if (dragging) {
    state.view.panX += ev.clientX - dragX;
    state.view.panY += ev.clientY - dragY;
    dragX = ev.clientX;
    dragY = ev.clientY;
    emit("view");
    return;
  }

  if (isInHud(ev.clientX, ev.clientY)) {
    if (hoverIndex >= 0) hideTip();
    return;
  }

  const now = performance.now();
  if (now - lastMove < 30) return;
  lastMove = now;

  if (!state.frame) return;
  const idx = nearestSat(ev.clientX, ev.clientY);
  if (idx < 0) {
    if (hoverIndex >= 0) hideTip();
    return;
  }
  if (idx !== hoverIndex) {
    hoverIndex = idx;
    cityText = "";
    const id = state.meta.ids[idx];
    state.hoverId = id;
    sendQuery(id);
  }
  renderTip(ev.clientX, ev.clientY);
}

function onWheel(ev) {
  if (isModalOpen()) return;
  ev.preventDefault();
  const v = state.view;
  const factor = Math.exp(-ev.deltaY * 0.0012);
  const next = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, v.zoom * factor));
  const s = next / v.zoom;
  const cx = window.innerWidth / 2 + v.panX;
  const cy = window.innerHeight / 2 + v.panY;
  v.panX = ev.clientX - s * (ev.clientX - cx) - window.innerWidth / 2;
  v.panY = ev.clientY - s * (ev.clientY - cy) - window.innerHeight / 2;
  v.zoom = next;
  emit("view");
}

export function startInteraction() {
  tip = document.getElementById("tooltip");
  if (!tip) return;

  window.addEventListener("wheel", onWheel, { passive: false });
  window.addEventListener("mousedown", (ev) => {
    if (isModalOpen() || isInHud(ev.clientX, ev.clientY)) return;
    dragging = true;
    dragX = ev.clientX;
    dragY = ev.clientY;
    hideTip();
  });
  window.addEventListener("mouseup", () => {
    dragging = false;
  });
  window.addEventListener("mousemove", onMove);
  window.addEventListener("mouseleave", hideTip);
  window.addEventListener("dblclick", () => {
    if (isModalOpen()) return;
    state.view.zoom = 1;
    state.view.panX = 0;
    state.view.panY = 0;
    emit("view");
  });

  on("satinfo", (info) => {
    if (info.id !== state.hoverId || hoverIndex < 0) return;
    cityText = info.city
      ? `OVER ${info.city.toUpperCase()}${info.country ? ", " + info.country : ""}`
      : "OVER OPEN OCEAN";
    const tipCity = tip.querySelector(".tip-city");
    if (tipCity) tipCity.textContent = cityText;
  });
}
