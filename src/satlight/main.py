"""SatLight FastAPI application: static UI, settings API, and WebSocket stream."""

from __future__ import annotations

import contextlib
import json
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .assets import ensure_placeholder_icons
from .config import Config
from .projection_modes import list_modes
from .satellite_classifiers import available_classifications
from .services.catalog import load_catalog, maybe_refresh_catalog
from .services.cities import CityIndex
from .services.groundgrid import compute_ground_grid
from .services.observer import ObserverStore
from .services.propagation import PropagationEngine
from .services.streamer import AppState, start_stream_task, stop_stream_task

_STATIC_DIR = Path(__file__).parent / "static"


class SettingsBody(BaseModel):
    latitude: float
    longitude: float
    elevation_m: float


def _observer_payload(state: AppState) -> dict:
    obs = state.observer.current
    return {
        "latitude": obs.latitude,
        "longitude": obs.longitude,
        "elevation_m": obs.elevation_m,
    }


def create_app() -> FastAPI:
    cfg = Config.load()
    ensure_placeholder_icons(_STATIC_DIR / "assets" / "img")

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        observer = ObserverStore(cfg)
        cities = CityIndex.load(_STATIC_DIR / "assets" / "geo" / "cities.json")
        await maybe_refresh_catalog(cfg)
        engine = PropagationEngine(cfg, load_catalog(cfg))
        state = AppState(cfg=cfg, observer=observer, engine=engine, cities=cities)
        app.state.app_state = state
        task = start_stream_task(state)
        try:
            yield
        finally:
            await stop_stream_task(task)

    app = FastAPI(title="SatLight", version="0.1.0", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(_STATIC_DIR / "index.html")

    @app.get("/api/config")
    async def api_config() -> dict:
        state: AppState = app.state.app_state
        return {
            "observer": _observer_payload(state),
            "modes": list_modes(),
            "classifications": available_classifications(),
            "update_interval": cfg.update_interval_seconds,
        }

    @app.get("/api/settings")
    async def get_settings() -> dict:
        return _observer_payload(app.state.app_state)

    @app.get("/api/groundgrid")
    async def api_groundgrid() -> dict:
        state: AppState = app.state.app_state
        rings = compute_ground_grid(
            _STATIC_DIR / "assets" / "geo" / "world.json", state.observer.current
        )
        return {"rings": rings}

    @app.post("/api/settings")
    async def post_settings(body: SettingsBody) -> dict:
        state: AppState = app.state.app_state
        state.observer.update(body.latitude, body.longitude, body.elevation_m)
        return _observer_payload(state)

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket) -> None:
        state: AppState = app.state.app_state
        await state.hub.connect(ws)
        try:
            await ws.send_json(state.engine.catalog())
            while True:
                raw = await ws.receive_text()
                try:
                    msg = json.loads(raw)
                except ValueError:
                    continue
                if msg.get("type") == "query" and "id" in msg:
                    await ws.send_json(state.satellite_info(int(msg["id"])))
        except WebSocketDisconnect:
            state.hub.disconnect(ws)
        except RuntimeError:
            state.hub.disconnect(ws)

    return app


app = create_app()


def run() -> None:
    import uvicorn

    cfg = Config.load()
    uvicorn.run(app, host=cfg.host, port=cfg.port)


if __name__ == "__main__":
    run()
