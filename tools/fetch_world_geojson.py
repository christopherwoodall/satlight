#!/usr/bin/env python3
"""One-time fetch of the simplified world land GeoJSON used by the teleport map.

This is a build-time asset fetch (Natural Earth 110m land, public domain). It is
NOT the satellite catalog and does not touch Celestrak. Run once; the result is
committed under static/assets/geo/world.json and used fully offline at runtime.
"""

from __future__ import annotations

from pathlib import Path

import httpx

URL = (
    "https://raw.githubusercontent.com/martynafford/natural-earth-geojson/"
    "master/110m/physical/ne_110m_land.json"
)
OUT = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "satlight"
    / "static"
    / "assets"
    / "geo"
    / "world.json"
)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    resp = httpx.get(URL, timeout=60.0, follow_redirects=True)
    resp.raise_for_status()
    OUT.write_text(resp.text)
    print(f"wrote {OUT} ({len(resp.content)} bytes)")


if __name__ == "__main__":
    main()
