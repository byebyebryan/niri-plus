#!/usr/bin/env python3
"""Pure renderers for Niri Plus appearance artifacts and the SDDM preview."""

import argparse
import configparser
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
try:
    from .sddm import IDENTITY_CANDIDATE, PUBLIC_KITTY_COLOR_KEYS, _selected_profile, derive_sddm_theme
except ImportError:
    # runpy.run_path and direct execution have no package context. Load the
    # sibling component so the public API remains available in both modes.
    spec = importlib.util.spec_from_file_location("niri_plus_appearance_sddm", Path(__file__).with_name("sddm.py"))
    if spec is None or spec.loader is None:
        raise ImportError("appearance renderer requires its sibling sddm.py component")
    _sddm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_sddm)
    IDENTITY_CANDIDATE = _sddm.IDENTITY_CANDIDATE
    PUBLIC_KITTY_COLOR_KEYS = _sddm.PUBLIC_KITTY_COLOR_KEYS
    _selected_profile = _sddm._selected_profile
    derive_sddm_theme = _sddm.derive_sddm_theme

NATIVE_KITTY_COLOR_KEYS = (
    "foreground",
    "background",
    "background_opacity",
    "cursor",
    "cursor_text_color",
    "selection_foreground",
    "selection_background",
)


def _rgb(color):
    return ",".join(str(int(color[index:index + 2], 16)) for index in (1, 3, 5))


def _rgb_spaced(color):
    return ", ".join(str(int(color[index:index + 2], 16)) for index in (1, 3, 5))


def _json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def _mix_color(foreground, background, percent):
    """Resolve a reviewed state tint to opaque RGB for native toolkit inputs."""
    return "#" + "".join(
        f"{round((int(foreground[index:index + 2], 16) * percent + int(background[index:index + 2], 16) * (100 - percent)) / 100):02x}"
        for index in (1, 3, 5)
    )


def _controls_appearance(profile, colors, shared):
    return {
        "schema_version": 1,
        "candidate": IDENTITY_CANDIDATE,
        "colors": dict(colors),
        "derived": {
            "current_background": _mix_color(colors["success"], colors["surface"], 18),
            "current_outline": _mix_color(colors["success"], colors["separator"], 65),
        },
        "fonts": {"ui_font": profile["ui_font"], "ui_pt": shared["ui_pt"]},
    }


def _controls_rofi(profile, colors, shared):
    """A self-contained opt-in theme; other Plus pickers retain their theme."""
    derived = _controls_appearance(profile, colors, shared)["derived"]
    return _rofi(profile, colors, shared) + "\n" + "\n".join([
        "/* Controls only: independent current/default and keyboard-selection states. */",
        "element { border: 1px; border-color: transparent; padding: 9px 8px; }",
        'entry { placeholder: "Search devices"; }',
        "window { width: calc(52em min 96%); }",
        "element-text { border: 0px 0px 0px 3px; border-color: transparent; padding: 0px 0px 0px 8px; }",
        "element normal.normal { border-color: transparent; }",
        f"element normal.active {{ background-color: {derived['current_background']}; border-color: {derived['current_outline']}; }}",
        f"element selected.normal {{ background-color: {colors['selection']}; border-color: transparent; }}",
        f"element selected.active {{ background-color: {colors['selection']}; border-color: {derived['current_outline']}; }}",
        f"element-text selected.normal {{ border-color: {colors['focus']}; }}",
        f"element-text selected.active {{ border-color: {colors['focus']}; }}",
        "",
    ])


def _rofi(profile, colors, shared):
    opacity_byte = int(shared["overlay_opacity"] * 255)
    lines = [
        "/* Neutral Slate. dms-* aliases retain the public Rofi Plus styling contract. */",
        "* {",
        f"    dms-primary: {colors['accent']};",
        f"    dms-primary-container: {colors['selection']};",
        f"    dms-surface: {colors['surface']}{opacity_byte:02x};",
        f"    dms-surface-container: {colors['input']};",
        f"    dms-surface-container-high: {colors['raised']};",
        f"    dms-surface-text: {colors['text']};",
        f"    dms-surface-variant-text: {colors['secondary']};",
        f"    dms-outline: {colors['border']};",
        f"    dms-primary-muted: {colors['accent']}70;",
        f"    dms-warning: {colors['warning']};",
        f"    dms-warning-muted: {colors['warning']}80;",
        f"    dms-warning-container: {colors['input']};",
        f"    dms-danger: {colors['error']};",
        f"    dms-danger-muted: {colors['error']}80;",
        f"    dms-danger-container: {colors['input']};",
        f"    dms-highlight: bold {colors['accent']};",
        "    background-color: transparent;",
        "    text-color: @dms-surface-text;",
        f'    font: "{profile["ui_font"]} {shared["ui_pt"]}";',
        "}",
        "window {",
        f"    width: {shared['rofi_width_em']}em;",
        "    padding: 12px;",
        "    border: 1px;",
        "    border-color: @dms-outline;",
        "    border-radius: 0px;",
        "    background-color: @dms-surface;",
        '    transparency: "real";',
        "}",
        "mainbox { spacing: 10px; background-color: transparent; }",
        "inputbar {",
        "    padding: 8px 10px;",
        "    spacing: 10px;",
        "    border: 1px;",
        f"    border-color: {colors['focus']};",
        "    border-radius: 3px;",
        "    background-color: @dms-surface-container;",
        "    children: [ prompt, entry ];",
        "}",
        "prompt { padding: 3px 7px; border-radius: 3px; background-color: @dms-surface-container-high; text-color: @dms-primary; }",
        f'entry {{ padding: 0px 4px; placeholder: "Search applications"; placeholder-color: @dms-surface-variant-text; text-color: @dms-surface-text; cursor-color: {colors["focus"]}; }}',
        "listview { lines: 9; columns: 1; fixed-height: false; dynamic: true; scrollbar: false; spacing: 5px; background-color: transparent; }",
        "element { padding: 10px 12px; spacing: 12px; border: 0px 0px 0px 3px; border-color: transparent; border-radius: 3px; background-color: transparent; text-color: @dms-surface-text; }",
        f"element selected {{ background-color: @dms-primary-container; border-color: {colors['focus']}; text-color: {colors['selection_text']}; }}",
        "element active { background-color: @dms-surface-container-high; border-color: @dms-primary-muted; }",
        f"element selected.active {{ background-color: @dms-primary-container; border-color: {colors['focus']}; }}",
        "element-icon { size: 1.75em; vertical-align: 0.5; }",
        "element-text { vertical-align: 0.5; highlight: @dms-highlight; }",
        "message { padding: 8px 10px; border: 1px; border-color: @dms-outline; border-radius: 3px; background-color: @dms-surface-container; }",
        "textbox { text-color: @dms-surface-variant-text; }",
        "message textbox { markup: true; }",
        "mode-switcher, case-indicator { enabled: false; }",
    ]
    return "\n".join(lines) + "\n"


def _swaync(profile, colors, shared):
    alpha = str(shared["overlay_opacity"])
    lines = [
        "/* Neutral Slate over the selected fork's native GTK4 layout. */",
        '@import url("/etc/xdg/swaync/style.css");',
        ":root {",
        f"  --cc-bg: alpha({colors['surface']}, {alpha});",
        f"  --noti-bg: {_rgb_spaced(colors['surface'])};",
        f"  --noti-bg-alpha: {alpha};",
        f"  --noti-bg-darker: {colors['input']};",
        f"  --noti-bg-hover: {colors['raised']};",
        f"  --noti-bg-focus: {colors['selection']};",
        f"  --noti-border-color: {colors['border']};",
        f"  --text-color: {colors['text']};",
        f"  --text-color-disabled: {colors['muted']};",
        f"  --bg-selected: {colors['accent']};",
        "  --border-radius: 0px;",
        "  --notification-icon-size: 40px;",
        f"  --font-size-body: {shared['ui_pt']}pt;",
        f"  --font-size-summary: {shared['ui_pt']}pt;",
        "}",
        f'* {{ font-family: "{profile["ui_font"]}", "{shared["cjk_fallback"]}", sans-serif; }}',
        ".control-center { border: 1px solid var(--noti-border-color); }",
        ".widget-dashboard { margin-left: 16px; margin-right: 16px; }",
        f".widget-dashboard .dashboard-card {{ background: {colors['raised']}; border: 1px solid {colors['separator']}; }}",
        f".widget-dashboard .dashboard-card-title {{ color: {colors['secondary']}; }}",
        f".widget-dashboard .metric-label {{ color: {colors['muted']}; }}",
        ".notification-row .notification-background .notification.critical {",
        f"  background: alpha({colors['raised']}, {alpha});",
        f"  border: 2px solid {colors['error']};",
        "}",
        ".notification-row .notification-background .notification .notification-default-action { padding: 14px 16px; }",
        ".notification-row .notification-background .notification .notification-default-action .body { margin-top: 6px; }",
        ".notification-row .notification-background .notification .notification-alt-actions { padding: 0 12px 10px; }",
        ".notification-action > button, .widget-title > button { border-radius: 3px; }",
        f"button:focus-visible {{ outline: 2px solid {colors['focus']}; outline-offset: 2px; }}",
        f"progressbar trough {{ background: {colors['input']}; }}",
        f"progressbar progress {{ background: {colors['accent']}; }}",
    ]
    return "\n".join(lines) + "\n"


def _gtklock(profile, colors, shared):
    lines = [
        "/* Native password form; authentication and lock-service lifetime stay unchanged. */",
        f'window {{ background-image: none; background-color: {colors["secure_surface"]}; color: {colors["text"]}; font-family: "{profile["ui_font"]}"; font-size: {shared["ui_pt"]}pt; }}',
        "#time-box { margin-bottom: 28px; }",
        f"#clock-label {{ font-size: {shared['clock_pt']}pt; font-weight: 400; }}",
        f"#date-label {{ color: {colors['secondary']}; }}",
        "#input-label { margin-right: 8px; }",
        f"#input-field {{ min-height: 36px; padding: 4px 12px; background-image: none; background-color: {colors['secure_input']}; color: {colors['text']}; caret-color: {colors['focus']}; border: 1px solid {colors['border']}; border-radius: 3px; box-shadow: none; }}",
        f"#input-field:focus {{ border-color: {colors['focus']}; }}",
        f"#unlock-button {{ min-height: 36px; padding: 0 24px; background-image: none; background-color: {colors['secure_button']}; color: {colors['accent_ink']}; border: none; border-radius: 3px; box-shadow: none; text-shadow: none; font-weight: {shared['emphasis_weight']}; }}",
        f"#unlock-button:hover, #unlock-button:active {{ background-color: {colors['secondary']}; }}",
        f"#unlock-button:disabled {{ background-color: {colors['raised']}; color: {colors['muted']}; }}",
        f"#warning-label {{ color: {colors['warning']}; }}",
        f"#error-label {{ color: {colors['error']}; }}",
    ]
    return "\n".join(lines) + "\n"


def _qt_palette(colors, role_count):
    active = [
        colors["text"], colors["surface"], colors["raised"], colors["border"],
        colors["canvas"], colors["border"], colors["text"], colors["text"],
        colors["text"], colors["input"], colors["surface"], colors["canvas"],
        colors["selection"], colors["selection_text"], colors["accent"],
        colors["visited_link"], colors["raised"], colors["canvas"],
        colors["surface"], colors["text"], colors["muted"], colors["accent"],
    ]
    disabled = [
        colors["muted"], colors["surface"], colors["raised"], colors["border"],
        colors["canvas"], colors["border"], colors["muted"], colors["text"],
        colors["muted"], colors["input"], colors["surface"], colors["canvas"],
        colors["raised"], colors["muted"], colors["secondary"], colors["muted"],
        colors["raised"], colors["canvas"], colors["surface"], colors["muted"],
        colors["muted"], colors["secondary"],
    ]
    lines = ["[ColorScheme]"]
    for group in ("active", "disabled", "inactive"):
        values = disabled if group == "disabled" else active
        values = ["#ff" + color[1:] for color in values[:role_count]]
        lines.append(f"{group}_colors=" + ", ".join(values))
    return "\n".join(lines) + "\n"


def _kde_colors(colors):
    groups = ("Window", "View", "Button", "Selection", "Tooltip", "Complementary")
    lines = [
        "[General]",
        "Name=Neutral Slate",
        "ColorScheme=NeutralSlate",
        "shadeSortColumn=true",
        "",
    ]
    for group in groups:
        background = colors["surface"]
        foreground = colors["text"]
        if group == "View":
            background = colors["input"]
        elif group == "Button":
            background = colors["raised"]
        elif group == "Selection":
            background = colors["selection"]
            foreground = colors["selection_text"]
        entries = (
            ("BackgroundNormal", background),
            ("BackgroundAlternate", colors["raised"]),
            ("DecorationFocus", colors["focus"]),
            ("DecorationHover", colors["accent"]),
            ("ForegroundNormal", foreground),
            ("ForegroundInactive", colors["muted"]),
            ("ForegroundActive", colors["accent"]),
            ("ForegroundLink", colors["accent"]),
            ("ForegroundVisited", colors["visited_link"]),
            ("ForegroundNegative", colors["error"]),
            ("ForegroundNeutral", colors["warning"]),
            ("ForegroundPositive", colors["success"]),
        )
        lines.append(f"[Colors:{group}]")
        lines.extend(f"{key}={_rgb(value)}" for key, value in entries)
        lines.append("")
    lines.extend(
        [
            "[ColorEffects:Disabled]",
            "Enable=true",
            "ChangeSelectionColor=true",
            "ColorEffect=0",
            "ContrastEffect=0",
            "IntensityEffect=0",
            "",
            "[ColorEffects:Inactive]",
            "Enable=false",
            "ChangeSelectionColor=false",
        ]
    )
    return "\n".join(lines) + "\n"


def _niri_fragment(colors, shared):
    return (
        "// Neutral Slate appearance only. Merge this layout fragment into your existing\n"
        "// Niri layout block so current sizing, gaps, borders, shadows and behavior stay\n"
        "// under their current owner.\n"
        "layout {\n"
        f'    background-color "{colors["canvas"]}"\n'
        "\n"
        "    focus-ring {\n"
        f"        width {shared['niri_focus_px']}\n"
        f'        active-color "{colors["focus"]}"\n'
        f'        inactive-color "{colors["border"]}"\n'
        "    }\n"
        "}\n"
    )


def _identity_css(profile, colors, terminal):
    roles = {
        "bg": "canvas", "canvas": "canvas", "surface": "surface", "raised": "raised",
        "input": "input", "line": "separator", "border": "border", "text": "text",
        "secondary": "secondary", "muted": "muted", "blue": "accent", "accent": "accent",
        "accent-ink": "accent_ink", "focus": "focus", "selection": "selection",
        "selection-text": "selection_text", "green": "success", "success": "success",
        "warning": "warning", "error": "error", "secure-surface": "secure_surface",
        "secure-input": "secure_input", "secure-button": "secure_button",
    }
    values = ";".join(f"--{name}:{colors[role]}" for name, role in roles.items())
    values += f';--ui-family:"{profile["ui_font"]}";--mono-family:"{profile["mono_font"]}"'
    values += ";" + ";".join(f"--ansi-{index}:{color}" for index, color in enumerate(terminal["ansi"]))
    values += ";" + ";".join(f"--terminal-{key.replace('_', '-')}:{terminal['colors'][key]}" for key in PUBLIC_KITTY_COLOR_KEYS)
    return "/* Generated from design/identity.json */\n:root{" + values + "}\n"


def render(identity):
    """Return appearance artifacts from a raw schema-2 identity without I/O."""
    profile, colors, shared, terminal = _selected_profile(identity)
    theme = {
        "enabled": True,
        "profile": profile,
        "colors": colors,
        "shared": shared,
        "terminal": terminal,
    }
    public_kitty = [
        "# Niri Plus / Neutral Slate - Balanced+ terminal appearance.",
        "# Generated from design/identity.json; preserve your existing Kitty behavior.",
    ]
    public_kitty.extend(f"{key} {terminal['colors'][key]}" for key in PUBLIC_KITTY_COLOR_KEYS)
    public_kitty.append(f"background_opacity {terminal['background_opacity']}")
    public_kitty.extend(f"color{index} {color}" for index, color in enumerate(terminal["ansi"]))

    native_kitty = ["# Neutral Slate / Balanced+ terminal; independent of desktop surface colors."]
    native_kitty.extend(f"{key} {terminal['colors'][key]}" if key != "background_opacity" else f"background_opacity {terminal['background_opacity']}" for key in NATIVE_KITTY_COLOR_KEYS)
    native_kitty.extend(f"color{index} {color}" for index, color in enumerate(terminal["ansi"]))

    kde_colors = _kde_colors(colors)
    scheme = configparser.ConfigParser(interpolation=None)
    scheme.optionxform = str
    scheme.read_string(kde_colors)
    managed = {
        "UiSettings": {"ColorScheme": "NeutralSlate"},
        "General": {
            "ColorScheme": "NeutralSlate",
            "font": f"{profile['ui_font']},{shared['ui_pt']},-1,5,50,0,0,0,0,0",
            "fixed": f"{profile['mono_font']},{shared['terminal_pt']},-1,5,50,0,0,0,0,0",
        },
        "Icons": {"Theme": shared["icon_family"].lower().replace(" ", "-")},
    }
    for section in scheme.sections():
        if section.startswith(("Colors:", "ColorEffects:")):
            managed[section] = dict(scheme[section])

    fonts = {
        "ui_font": profile["ui_font"],
        "mono_font": profile["mono_font"],
        "cjk_fallback": shared["cjk_fallback"],
        "ui_pt": shared["ui_pt"],
        "secondary_pt": shared["secondary_pt"],
        "heading_pt": shared["heading_pt"],
        "terminal_pt": shared["terminal_pt"],
        "clock_pt": shared["clock_pt"],
    }
    role_data = {"schema_version": 1, "candidate": IDENTITY_CANDIDATE, "colors": colors}
    return {
        "neutral-slate.rasi": _rofi(profile, colors, shared),
        "niri-plus-controls.rasi": _controls_rofi(profile, colors, shared),
        "controls-appearance.json": _json_text(_controls_appearance(profile, colors, shared)),
        "swaync.css": _swaync(profile, colors, shared),
        "gtklock.css": _gtklock(profile, colors, shared),
        "qt5-palette.conf": _qt_palette(colors, 21),
        "qt6-palette.conf": _qt_palette(colors, 22),
        "NeutralSlate.colors": kde_colors,
        "niri-neutral-slate.kdl": _niri_fragment(colors, shared),
        "kitty-neutral-slate.conf": "\n".join(public_kitty) + "\n",
        "kitty-native-suffix.conf": "\n".join(native_kitty) + "\n",
        "theme.json": _json_text(theme),
        "roles.json": _json_text(role_data),
        "fonts.json": _json_text(fonts),
        "kdeglobals-managed.json": _json_text(managed),
        "identity.css": _identity_css(profile, colors, terminal),
    }


def _component_version():
    metadata_path = ROOT / "components/metadata.json"
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        return metadata["version"]
    manifest_path = ROOT / "manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return manifest["version"]
    raise ValueError("appearance CLI needs component metadata or a bundled manifest")


def _write_stage(identity_path, output):
    identity_path = Path(identity_path)
    output = Path(output).expanduser()
    if output.is_symlink() or output.exists():
        raise ValueError("--output must be a new directory")
    identity_bytes = identity_path.read_bytes()
    identity = json.loads(identity_bytes)
    artifacts = render(identity)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".niri-plus-appearance-", dir=output.parent))
    try:
        records = []
        for relative in sorted(artifacts):
            parsed = PurePosixPath(relative)
            if parsed.is_absolute() or parsed.as_posix() != relative or ".." in parsed.parts:
                raise ValueError(f"invalid appearance artifact path: {relative}")
            data = artifacts[relative].encode("utf-8")
            target = stage.joinpath(*parsed.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            records.append({"path": relative, "sha256": hashlib.sha256(data).hexdigest()})
        code_files = {}
        for name in ("__init__.py", "ini_merge.py", "render.py", "sddm.py"):
            relative = f"components/appearance/{name}"
            code_files[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        manifest = {
            "schema_version": 1,
            "renderer_version": _component_version(),
            "identity_sha256": hashlib.sha256(identity_bytes).hexdigest(),
            "code_sha256": code_files,
            "files": records,
        }
        (stage / "manifest.json").write_text(_json_text(manifest), encoding="utf-8")
        stage.rename(output)
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity", required=True, type=Path, help="reviewed schema-2 identity JSON")
    parser.add_argument("--output", required=True, type=Path, help="new output directory for staged appearance files")
    args = parser.parse_args(argv)
    try:
        output = _write_stage(args.identity, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps({"output": str(output), "artifacts": len(render(json.loads(args.identity.read_text(encoding="utf-8"))))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
