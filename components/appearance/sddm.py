#!/usr/bin/env python3
"""Pure SDDM theme derivation and standalone local preview helper."""

import argparse
import hashlib
import json
from pathlib import Path
import re


IDENTITY_CANDIDATE = "neutral-slate"
PUBLIC_KITTY_COLOR_KEYS = (
    "background",
    "foreground",
    "cursor",
    "cursor_text_color",
    "selection_background",
    "selection_foreground",
)
COLOR_KEYS = (
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
    "visited_link",
    "secure_surface",
    "secure_input",
    "secure_button",
)
OPTIONAL_BACKGROUND_COLOR_KEYS = ("workspace_background", "overview_background")
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}\Z")


def _selected_profile(identity):
    if not isinstance(identity, dict) or identity.get("schema_version") != 2:
        raise ValueError("expected a schema-2 appearance identity")
    # Accept the compact public identity download as well as the source file.
    if "candidates" not in identity and isinstance(identity.get("direction"), dict):
        identity = {
            "schema_version": identity["schema_version"],
            "status": "selected",
            "selected_candidate": identity.get("selected_candidate"),
            "candidates": [identity["direction"]],
            "shared": identity.get("shared"),
            "terminal": identity.get("terminal"),
        }
    if identity.get("status") != "selected" or identity.get("selected_candidate") != IDENTITY_CANDIDATE:
        raise ValueError("expected the selected Neutral Slate identity")
    profiles = identity.get("candidates")
    if not isinstance(profiles, list):
        raise ValueError("schema-2 identity has no candidate list")
    matches = [profile for profile in profiles if isinstance(profile, dict) and profile.get("id") == IDENTITY_CANDIDATE]
    if len(matches) != 1:
        raise ValueError("schema-2 identity must define exactly one selected Neutral Slate candidate")
    profile = matches[0]
    colors = profile.get("colors")
    if not isinstance(colors, dict) or any(not isinstance(colors.get(key), str) or not HEX_COLOR.fullmatch(colors[key]) for key in COLOR_KEYS):
        raise ValueError("selected identity has incomplete or invalid desktop role colors")
    if any(
        key in colors and (not isinstance(colors[key], str) or not HEX_COLOR.fullmatch(colors[key]))
        for key in OPTIONAL_BACKGROUND_COLOR_KEYS
    ):
        raise ValueError("selected identity has invalid optional desktop background colors")
    shared = identity.get("shared")
    if not isinstance(shared, dict):
        raise ValueError("schema-2 identity has no shared typography and geometry")
    terminal = identity.get("terminal")
    if not isinstance(terminal, dict) or terminal.get("variant") != "balanced-plus":
        raise ValueError("expected the separate Balanced+ terminal identity")
    terminal_colors = terminal.get("colors")
    if not isinstance(terminal_colors, dict) or any(not isinstance(terminal_colors.get(key), str) or not HEX_COLOR.fullmatch(terminal_colors[key]) for key in PUBLIC_KITTY_COLOR_KEYS):
        raise ValueError("terminal identity has incomplete Kitty colors")
    ansi = terminal.get("ansi")
    if not isinstance(ansi, list) or len(ansi) != 16 or any(not isinstance(color, str) or not HEX_COLOR.fullmatch(color) for color in ansi):
        raise ValueError("terminal identity must define sixteen ANSI colors")
    if not isinstance(profile.get("ui_font"), str) or not isinstance(profile.get("mono_font"), str):
        raise ValueError("selected identity has incomplete font families")
    if not isinstance(shared.get("overlay_opacity"), (int, float)) or not 0 <= shared["overlay_opacity"] <= 1:
        raise ValueError("shared overlay opacity must be between zero and one")
    return profile, colors, shared, terminal


def derive_sddm_theme(source, identity):
    """Return deterministic SDDM theme name, digest, and marker-free core bytes."""
    source = Path(source)
    profile, colors, shared, _ = _selected_profile(identity)
    if source.is_symlink() or not (source / "Main.qml").is_file():
        raise ValueError("Source must be the unpacked pinned SDDM theme directory")
    palette = {
        "1e1e2e": colors["secure_surface"][1:],
        "181825": "181818",
        "11111b": "111111",
        "313244": colors["secure_input"][1:],
        "45475a": "444444",
        "585b70": "585858",
        "6c7086": "777777",
        "cdd6f4": colors["text"][1:],
        "89b4fa": colors["secure_button"][1:],
        "a6adc8": colors["secondary"][1:],
        "f38ba8": colors["error"][1:],
        "f5e0dc": colors["text"][1:],
    }
    files = {}
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError("Theme source must contain regular files, without symlinks")
        if not path.is_file():
            continue
        data = path.read_bytes()
        if path.suffix == ".qml":
            text = data.decode()
            if "org.kde.plasma" in text:
                raise ValueError("The selected greeter must remain independent of Plasma")
            text = re.sub(
                r"#[0-9a-fA-F]{6}\b",
                lambda match: "#" + palette.get(match[0][1:].lower(), match[0][1:]),
                text,
            )
            if path.name in {"UserField.qml", "PasswordField.qml"}:
                text = text.replace("  horizontalAlignment:", '  placeholderTextColor: "#999999"\n  horizontalAlignment:')
            data = text.encode()
        files[path.relative_to(source).as_posix()] = data
    files["theme.conf.user"] = (
        "[General]\nCustomBackground=false\nLoginBackground=false\n"
        f"Font={profile['ui_font']}\nFontSize={shared['ui_pt']}\n"
    ).encode()
    digest = hashlib.sha256()
    for name, data in sorted(files.items()):
        digest.update(name.encode() + b"\0" + data + b"\0")
    identity_digest = digest.hexdigest()
    return {
        "name": "niri-neutral-" + identity_digest[:12],
        "sha256": identity_digest,
        "files": files,
    }


def derive(source, output, identity):
    """Write the same standalone local preview used by the public download."""
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError("Choose a new output directory; existing paths are preserved")
    result = derive_sddm_theme(source, identity)
    marker = (json.dumps({"owner": "niri-plus-example", "sha256": result["sha256"]}) + "\n").encode()
    output.mkdir(parents=True)
    destination = output / result["name"]
    for relative, data in result["files"].items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (destination / ".niri-plus-theme.json").write_bytes(marker)
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--identity", required=True, type=Path)
    args = parser.parse_args(argv)
    print(derive(args.source, args.output, json.loads(args.identity.read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
