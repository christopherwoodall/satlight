// Shared, mutable application state. A tiny event emitter lets the (event-driven)
// HUD / settings / map react without continuously polling.

const listeners = new Map();

export function on(event, fn) {
  if (!listeners.has(event)) listeners.set(event, new Set());
  listeners.get(event).add(fn);
}

export function emit(event, detail) {
  const set = listeners.get(event);
  if (set) for (const fn of set) fn(detail);
}

export const state = {
  // static catalog metadata (index-aligned with frame arrays)
  meta: { count: 0, ids: [], names: [], types: [] },
  // latest dynamic frame + arrival time for interpolation
  frame: null,
  frameReceivedAt: 0,
  interval: 1.0,

  // ui / plugin selection
  mode: "ceiling",
  theme: "kawaiiLcars",
  filters: new Set(), // enabled classifications
  effects: { trail: true, orbitTrack: false, shadowFade: true },

  // display toggles
  display: { guides: true, ceilingFlip: false, belowHorizon: true },

  // pan / zoom view transform
  view: { zoom: 1, panX: 0, panY: 0 },

  // per-frame projected screen positions (reused buffers) for hover hit-testing
  screen: { x: null, y: null, n: 0 },
  hoverId: null,

  observer: { latitude: 0, longitude: 0, elevation_m: 0 },
  config: { modes: [], classifications: [] },

  connected: false,
};
