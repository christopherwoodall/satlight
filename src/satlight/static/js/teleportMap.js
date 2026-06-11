// Interactive equirectangular world map drawn from a local GeoJSON asset.
// Fully offline. Click <-> lat/lon are two-way bound by the caller.
import { themes } from "./registry.js";
import { state } from "./state.js";

let geo = null;

async function loadGeo() {
  if (geo) return geo;
  const res = await fetch("/static/assets/geo/world.json?v=0.1.0");
  geo = await res.json();
  return geo;
}

function eachRing(geometry, fn) {
  if (geometry.type === "Polygon") {
    for (const ring of geometry.coordinates) fn(ring);
  } else if (geometry.type === "MultiPolygon") {
    for (const poly of geometry.coordinates) for (const ring of poly) fn(ring);
  }
}

export async function createTeleportMap(canvas, onPick) {
  const data = await loadGeo();
  const palette = themes.get(state.theme);
  let marker = null; // {lat, lon}

  function lonToX(lon, w) {
    return ((lon + 180) / 360) * w;
  }
  function latToY(lat, h) {
    return ((90 - lat) / 180) * h;
  }
  function xToLon(x, w) {
    return (x / w) * 360 - 180;
  }
  function yToLat(y, h) {
    return 90 - (y / h) * 180;
  }

  function draw() {
    const w = canvas.width;
    const h = canvas.height;
    const ctx = canvas.getContext("2d");

    ctx.fillStyle = "#05060a";
    ctx.fillRect(0, 0, w, h);

    // graticule
    ctx.strokeStyle = palette.dim;
    ctx.lineWidth = 1;
    ctx.globalAlpha = 0.4;
    ctx.beginPath();
    for (let lon = -180; lon <= 180; lon += 30) {
      ctx.moveTo(lonToX(lon, w), 0);
      ctx.lineTo(lonToX(lon, w), h);
    }
    for (let lat = -60; lat <= 60; lat += 30) {
      ctx.moveTo(0, latToY(lat, h));
      ctx.lineTo(w, latToY(lat, h));
    }
    ctx.stroke();
    ctx.globalAlpha = 1;

    // land
    ctx.fillStyle = palette.mint;
    ctx.globalAlpha = 0.32;
    for (const feature of data.features) {
      eachRing(feature.geometry, (ring) => {
        ctx.beginPath();
        for (let i = 0; i < ring.length; i++) {
          const x = lonToX(ring[i][0], w);
          const y = latToY(ring[i][1], h);
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.fill();
      });
    }
    ctx.globalAlpha = 1;

    // marker
    if (marker) {
      const x = lonToX(marker.lon, w);
      const y = latToY(marker.lat, h);
      ctx.strokeStyle = palette.pink;
      ctx.fillStyle = palette.pink;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x - 7, y);
      ctx.lineTo(x + 7, y);
      ctx.moveTo(x, y - 7);
      ctx.lineTo(x, y + 7);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  canvas.addEventListener("click", (ev) => {
    const rect = canvas.getBoundingClientRect();
    const x = ((ev.clientX - rect.left) / rect.width) * canvas.width;
    const y = ((ev.clientY - rect.top) / rect.height) * canvas.height;
    const lon = xToLon(x, canvas.width);
    const lat = yToLat(y, canvas.height);
    marker = { lat, lon };
    draw();
    if (onPick) onPick(lat, lon);
  });

  return {
    setMarker(lat, lon) {
      marker = { lat, lon };
      draw();
    },
    redraw: draw,
  };
}
