"""Procedural placeholder icon generation.

Generates 32x32 transparent RGBA PNGs (one per renderer) if they are missing.
Uses a tiny self-contained PNG encoder so SatLight has no image-library
dependency. Icons are intentionally simple, low-brightness pastel glyphs; the
canvas renderers build their own offscreen sprites for the live view, so these
files only need to exist as friendly placeholders / fallbacks.
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

SIZE = 32

# Low-brightness, projector-safe pastels (no pure white).
_PINK = (230, 150, 180)
_LAVENDER = (180, 170, 230)
_MINT = (150, 220, 180)
_CYAN = (140, 200, 210)


class _Canvas:
    """A tiny RGBA pixel buffer with a couple of fill primitives."""

    def __init__(self, size: int = SIZE) -> None:
        self.size = size
        self.px = bytearray(size * size * 4)

    def set(self, x: int, y: int, rgb: tuple[int, int, int], alpha: int = 255) -> None:
        if 0 <= x < self.size and 0 <= y < self.size:
            i = (y * self.size + x) * 4
            self.px[i] = rgb[0]
            self.px[i + 1] = rgb[1]
            self.px[i + 2] = rgb[2]
            self.px[i + 3] = alpha

    def rect(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        rgb: tuple[int, int, int],
        alpha: int = 255,
    ) -> None:
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.set(x, y, rgb, alpha)

    def disc(
        self,
        cx: float,
        cy: float,
        r: float,
        rgb: tuple[int, int, int],
        alpha: int = 255,
    ) -> None:
        r2 = r * r
        for y in range(self.size):
            for x in range(self.size):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r2:
                    self.set(x, y, rgb, alpha)

    def encode_png(self) -> bytes:
        raw = bytearray()
        stride = self.size * 4
        for y in range(self.size):
            raw.append(0)  # filter type: none
            raw.extend(self.px[y * stride : (y + 1) * stride])
        compressed = zlib.compress(bytes(raw), 9)

        def chunk(tag: bytes, data: bytes) -> bytes:
            body = tag + data
            return (
                struct.pack(">I", len(data))
                + body
                + struct.pack(">I", zlib.crc32(body))
            )

        ihdr = struct.pack(">IIBBBBB", self.size, self.size, 8, 6, 0, 0, 0)
        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", compressed)
            + chunk(b"IEND", b"")
        )


def _starlink() -> _Canvas:
    c = _Canvas()
    c.rect(13, 6, 19, 26, _PINK)  # body
    c.rect(3, 12, 12, 20, _PINK, 200)  # left panel
    c.rect(20, 12, 29, 20, _PINK, 200)  # right panel
    c.rect(15, 3, 17, 6, _PINK, 230)  # antenna
    return c


def _iss() -> _Canvas:
    c = _Canvas()
    c.rect(13, 13, 19, 19, _LAVENDER)  # core module
    c.rect(2, 9, 12, 13, _LAVENDER, 200)  # upper-left panel
    c.rect(2, 19, 12, 23, _LAVENDER, 200)  # lower-left panel
    c.rect(20, 9, 30, 13, _LAVENDER, 200)  # upper-right panel
    c.rect(20, 19, 30, 23, _LAVENDER, 200)  # lower-right panel
    c.rect(15, 4, 17, 28, _LAVENDER, 160)  # truss
    return c


def _default() -> _Canvas:
    c = _Canvas()
    c.disc(16, 16, 9, _CYAN, 120)  # soft halo
    c.disc(16, 16, 5, _MINT)  # core dot
    return c


_GENERATORS = {
    "starlink.png": _starlink,
    "iss.png": _iss,
    "default.png": _default,
}


def ensure_placeholder_icons(img_dir: Path) -> list[Path]:
    """Create any missing icon PNGs in ``img_dir``. Returns the paths written."""
    img_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, generator in _GENERATORS.items():
        path = img_dir / name
        if path.exists():
            continue
        path.write_bytes(generator().encode_png())
        written.append(path)
    return written
