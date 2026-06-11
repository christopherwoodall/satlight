"""Projection-mode descriptor plugins.

Projection math lives in the frontend (it is a pure rendering concern), but each
mode is declared here so the server can advertise the available modes to the
client. Add a mode by dropping a ``*.py`` file exposing a ``MODE`` dict with at
least ``id`` and ``label``. No existing file changes.
"""

from __future__ import annotations

import importlib
import pkgutil

_modes: list[dict] | None = None


def list_modes() -> list[dict]:
    global _modes
    if _modes is not None:
        return _modes

    found: list[dict] = []
    for info in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f"{__name__}.{info.name}")
        mode = getattr(module, "MODE", None)
        if isinstance(mode, dict) and "id" in mode:
            found.append(mode)
    found.sort(key=lambda m: m.get("order", 100))
    _modes = found
    return found
