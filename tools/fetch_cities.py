#!/usr/bin/env python3
"""One-time fetch of a compact world city list for the "flying over" lookup.

Uses Natural Earth 50m populated places (public domain, ~1.2k major cities) and
reduces it to a small name/country/lat/lon list. This is a build-time asset and
does NOT touch Celestrak. The result is committed under
static/assets/geo/cities.json and used server-side, fully offline.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx

URL = (
    "https://raw.githubusercontent.com/martynafford/natural-earth-geojson/"
    "master/50m/cultural/ne_50m_populated_places_simple.json"
)
OUT = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "satlight"
    / "static"
    / "assets"
    / "geo"
    / "cities.json"
)


def main() -> None:
    resp = httpx.get(URL, timeout=60.0, follow_redirects=True)
    resp.raise_for_status()
    data = resp.json()

    cities = []
    for feature in data["features"]:
        props = feature["properties"]
        lon, lat = feature["geometry"]["coordinates"]
        cities.append(
            {
                "name": props.get("name") or props.get("nameascii") or "Unknown",
                "country": props.get("adm0name") or "",
                "cc": props.get("iso_a2") or "",
                "lat": round(float(lat), 4),
                "lon": round(float(lon), 4),
            }
        )

    cities.sort(key=lambda c: c["name"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cities, ensure_ascii=False))
    print(f"wrote {OUT} ({len(cities)} cities, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
