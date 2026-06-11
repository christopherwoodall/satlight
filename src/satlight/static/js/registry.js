// Minimal plugin registries. Each plugin module self-registers on import; main.js
// imports the modules. Adding a capability = add a file + one import line.

function createRegistry() {
  const map = new Map();
  return {
    register(id, value) {
      map.set(id, value);
    },
    get(id) {
      return map.get(id);
    },
    has(id) {
      return map.has(id);
    },
    all() {
      return [...map.values()];
    },
    ids() {
      return [...map.keys()];
    },
  };
}

export const renderers = createRegistry();
export const effects = createRegistry();
export const projections = createRegistry();
export const themes = createRegistry();
