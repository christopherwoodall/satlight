"""WebSocket streaming hub and the 1 Hz broadcast loop.

The loop only does work while at least one client is connected (calm and cheap).
On connect a client receives the static ``catalog`` message once, then a
``frame`` message every ``update_interval_seconds``.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from dataclasses import dataclass, field

from fastapi import WebSocket

from ..config import Config
from .catalog import load_catalog, maybe_refresh_catalog
from .cities import CityIndex
from .observer import ObserverStore
from .propagation import PropagationEngine


class Hub:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()

    @property
    def has_clients(self) -> bool:
        return bool(self._clients)

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._clients.discard(ws)

    async def broadcast(self, message: str) -> None:
        dead: list[WebSocket] = []
        for ws in self._clients:
            try:
                await ws.send_text(message)
            except (RuntimeError, ConnectionError):
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


@dataclass
class AppState:
    cfg: Config
    observer: ObserverStore
    engine: PropagationEngine
    cities: CityIndex
    hub: Hub = field(default_factory=Hub)

    def reload_catalog(self) -> None:
        self.engine = PropagationEngine(self.cfg, load_catalog(self.cfg))

    def satellite_info(self, norad_id: int) -> dict:
        """Ground point + nearest city for one satellite (on-demand)."""
        point = self.engine.ground_point(norad_id)
        if point is None:
            return {"type": "satinfo", "id": norad_id, "city": None}
        lat, lon = point
        city = self.cities.nearest(lat, lon)
        return {
            "type": "satinfo",
            "id": norad_id,
            "sub_lat": round(lat, 3),
            "sub_lon": round(lon, 3),
            "city": city.name if city else None,
            "country": city.cc if city else None,
        }


async def stream_loop(state: AppState) -> None:
    """Broadcast frames at the configured cadence; periodically refresh catalog."""
    cfg = state.cfg
    refresh_every = max(1, int(1800 / max(cfg.update_interval_seconds, 0.1)))
    tick = 0
    while True:
        if state.hub.has_clients:
            frame = state.engine.frame(state.observer.current)
            await state.hub.broadcast(json.dumps(frame))

        tick += 1
        if tick % refresh_every == 0 and await maybe_refresh_catalog(cfg):
            state.reload_catalog()

        await asyncio.sleep(cfg.update_interval_seconds)


def start_stream_task(state: AppState) -> asyncio.Task:
    return asyncio.create_task(stream_loop(state))


async def stop_stream_task(task: asyncio.Task) -> None:
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
