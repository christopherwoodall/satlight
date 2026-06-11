// WebSocket client with auto-reconnect. Handles two message types: a one-shot
// "catalog" (static metadata) and recurring "frame" (dynamic arrays).
import { state, emit } from "./state.js";

let socket = null;
let reconnectTimer = null;

function url() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${location.host}/ws`;
}

function handle(message) {
  if (message.type === "catalog") {
    state.meta = {
      count: message.count,
      ids: message.ids,
      names: message.names,
      types: message.types,
    };
    emit("catalog", state.meta);
  } else if (message.type === "frame") {
    state.frame = message;
    state.frameReceivedAt = performance.now();
    state.interval = message.interval || state.interval;
    emit("frame", message);
  } else if (message.type === "satinfo") {
    emit("satinfo", message);
  }
}

export function sendQuery(id) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: "query", id }));
  }
}

export function connect() {
  socket = new WebSocket(url());

  socket.addEventListener("open", () => {
    state.connected = true;
    emit("connection", true);
  });

  socket.addEventListener("message", (ev) => {
    handle(JSON.parse(ev.data));
  });

  const drop = () => {
    state.connected = false;
    emit("connection", false);
    if (!reconnectTimer) {
      reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connect();
      }, 1500);
    }
  };

  socket.addEventListener("close", drop);
  socket.addEventListener("error", () => socket.close());
}
