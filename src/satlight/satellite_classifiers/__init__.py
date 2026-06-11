"""Satellite classifier plugins.

Each module in this package is a self-contained classifier. To add a new
classification, drop a new ``*.py`` file here exposing:

    CLASSIFICATION: str        # the label this plugin assigns
    PRIORITY: int              # lower runs first; first match wins
    def matches(name: str, norad_id: int) -> bool

No existing file needs to change. ``other.py`` is the lowest-priority catch-all.
"""

from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType

_plugins: list[ModuleType] | None = None


def _discover() -> list[ModuleType]:
    global _plugins
    if _plugins is not None:
        return _plugins

    found: list[ModuleType] = []
    for info in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f"{__name__}.{info.name}")
        if hasattr(module, "matches") and hasattr(module, "CLASSIFICATION"):
            found.append(module)
    found.sort(key=lambda m: getattr(m, "PRIORITY", 100))
    _plugins = found
    return found


def classify(name: str, norad_id: int) -> str:
    """Return the classification label for a satellite."""
    for plugin in _discover():
        if plugin.matches(name, norad_id):
            return plugin.CLASSIFICATION
    return "OTHER"


def available_classifications() -> list[str]:
    """Distinct classification labels offered by the installed plugins."""
    seen: list[str] = []
    for plugin in _discover():
        label = plugin.CLASSIFICATION
        if label not in seen:
            seen.append(label)
    return seen
