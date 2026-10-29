"""Validate the renderer-produced controls identity artifact."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Mapping


MAX_APPEARANCE_BYTES = 64 * 1024
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?\Z", re.ASCII)
REQUIRED_COLORS = {
    "canvas",
    "surface",
    "raised",
    "input",
    "border",
    "separator",
    "text",
    "secondary",
    "muted",
    "accent",
    "accent_ink",
    "focus",
    "selection",
    "selection_text",
    "warning",
    "error",
    "success",
}


@dataclass(frozen=True, slots=True)
class ControlsAppearance:
    candidate: str
    colors: Mapping[str, str]
    current_background: str
    current_outline: str
    ui_font: str
    ui_pt: float


def _hex(value: object, field: str) -> str:
    if not isinstance(value, str) or not HEX_COLOR.fullmatch(value):
        raise ValueError(f"appearance {field} must be a 6- or 8-digit hex color")
    return value.lower()


def load_appearance(path: str | Path) -> ControlsAppearance:
    path = Path(path)
    if path.is_symlink():
        raise ValueError("appearance path must not be a symlink")
    raw = path.read_bytes()
    if len(raw) > MAX_APPEARANCE_BYTES:
        raise ValueError("appearance file exceeds its size limit")
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("unsupported controls appearance schema")
    candidate = value.get("candidate")
    colors = value.get("colors")
    derived = value.get("derived")
    fonts = value.get("fonts")
    if (
        not isinstance(candidate, str)
        or not isinstance(colors, dict)
        or not isinstance(derived, dict)
        or not isinstance(fonts, dict)
    ):
        raise ValueError("controls appearance is missing its canonical fields")
    missing = REQUIRED_COLORS - set(colors)
    if missing:
        raise ValueError("controls appearance is missing color roles: " + ", ".join(sorted(missing)))
    validated_colors = {name: _hex(colors[name], f"colors.{name}") for name in colors}
    background = _hex(derived.get("current_background"), "derived.current_background")
    outline = _hex(derived.get("current_outline"), "derived.current_outline")
    ui_font = fonts.get("ui_font")
    ui_pt = fonts.get("ui_pt")
    if not isinstance(ui_font, str) or not ui_font or len(ui_font) > 128:
        raise ValueError("appearance fonts.ui_font is invalid")
    if isinstance(ui_pt, bool) or not isinstance(ui_pt, (int, float)) or not 6 <= ui_pt <= 72:
        raise ValueError("appearance fonts.ui_pt must be between 6 and 72")
    return ControlsAppearance(
        candidate=candidate,
        colors=validated_colors,
        current_background=background,
        current_outline=outline,
        ui_font=ui_font,
        ui_pt=float(ui_pt),
    )


def default_appearance_path() -> Path:
    config_home = Path.home() / ".config"
    import os

    if os.environ.get("XDG_CONFIG_HOME"):
        config_home = Path(os.environ["XDG_CONFIG_HOME"])
    return config_home / "niri-plus" / "controls-appearance.json"


def default_theme_path() -> Path:
    import os

    config_home = Path.home() / ".config"
    if os.environ.get("XDG_CONFIG_HOME"):
        config_home = Path(os.environ["XDG_CONFIG_HOME"])
    return config_home / "rofi" / "niri-plus-controls.rasi"
