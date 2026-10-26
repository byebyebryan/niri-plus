#!/usr/bin/env python3
"""Derive a local Neutral Slate SDDM preview; never install or activate it."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def derive(source, output, identity):
    if output.exists() or output.is_symlink():
        raise ValueError("Choose a new output directory; existing paths are preserved")
    if source.is_symlink() or not (source / "Main.qml").is_file():
        raise ValueError("Source must be the unpacked pinned SDDM theme directory")
    if identity.get("schema_version") != 2 or identity.get("selected_candidate") != "neutral-slate":
        raise ValueError("Expected the selected schema-2 Neutral Slate identity")
    direction = identity.get("direction") or next(
        item for item in identity["candidates"] if item["id"] == "neutral-slate")
    colors = direction["colors"]
    palette = {
        "1e1e2e": colors["secure_surface"][1:], "181825": "181818", "11111b": "111111",
        "313244": colors["secure_input"][1:], "45475a": "444444", "585b70": "585858",
        "6c7086": "777777", "cdd6f4": colors["text"][1:],
        "89b4fa": colors["secure_button"][1:], "a6adc8": colors["secondary"][1:],
        "f38ba8": colors["error"][1:], "f5e0dc": colors["text"][1:],
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
            text = re.sub(r"#[0-9a-fA-F]{6}\b", lambda m: "#" + palette.get(m[0][1:].lower(), m[0][1:]), text)
            if path.name in {"UserField.qml", "PasswordField.qml"}:
                text = text.replace("  horizontalAlignment:", '  placeholderTextColor: "#999999"\n  horizontalAlignment:')
            data = text.encode()
        files[str(path.relative_to(source))] = data
    files["theme.conf.user"] = b"[General]\nCustomBackground=false\nLoginBackground=false\nFont=Noto Sans\nFontSize=11\n"
    digest = hashlib.sha256()
    for name, data in sorted(files.items()):
        digest.update(name.encode() + b"\0" + data + b"\0")
    name = "niri-neutral-" + digest.hexdigest()[:12]
    files[".niri-plus-theme.json"] = (json.dumps({"owner": "niri-plus-example", "sha256": digest.hexdigest()}) + "\n").encode()
    output.mkdir(parents=True)
    destination = output / name
    for relative, data in files.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--identity", required=True, type=Path)
    args = parser.parse_args()
    print(derive(args.source, args.output, json.loads(args.identity.read_text())))


if __name__ == "__main__":
    main()
