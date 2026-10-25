#!/usr/bin/env python3
"""Export a focused, source-driven comparison of the three neutral directions."""
import argparse
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
ORDER = ["graphite-blue", "neutral-slate", "slate-blue"]
FONTS = ["inter", "noto", "noto-medium", "noto-semibold", "meslo", "source-han"]


def ratio(a, b):
    def luminance(color):
        values = [int(color[i:i + 2], 16) / 255 for i in [1, 3, 5]]
        return sum(weight * (value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4) for value, weight in zip(values, [.2126, .7152, .0722]))
    a, b = luminance(a), luminance(b)
    return (max(a, b) + .05) / (min(a, b) + .05)


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids = []
        self.h1 = 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "h1":
            self.h1 += 1


def build(output):
    output = output.absolute()
    if output.is_symlink() or output.resolve().is_relative_to(ROOT.parent):
        raise ValueError("comparison export must be outside the checkout")
    if output.exists() and any(output.iterdir()):
        raise ValueError("comparison export must be empty")
    identity = json.loads((ROOT / "identity.json").read_text())
    candidates = [next(c for c in identity["candidates"] if c["id"] == name) for name in ORDER]
    output.mkdir(parents=True, exist_ok=True)
    for font in FONTS:
        for folder, extension in [("fonts", "woff2"), ("licenses", "txt")]:
            target = output / "assets" / folder / (font + "." + extension)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / "assets" / folder / target.name, target)
    provenance = json.loads((ROOT / "assets/provenance.json").read_text())
    provenance["files"] = [item for item in provenance["files"] if item["path"] in {f"assets/fonts/{font}.woff2" for font in FONTS}]
    for key in ["icon_source", "icon_attribution", "license_text_source", "native_images"]:
        provenance.pop(key, None)
    (output / "assets/provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    model = {"source": "design/identity.json", "source_sha256": hashlib.sha256((ROOT / "identity.json").read_bytes()).hexdigest(), "scope": "Design comparison; all composed surfaces are mockups, not installed configuration.", "shared": identity["shared"], "candidates": candidates}
    (output / "identity.json").write_text(json.dumps(model, indent=2) + "\n")
    notes = {
        "graphite-blue": ("Darker charcoal · defined blue", "Deepest base. The same blue has slightly more contrast against these darker surfaces."),
        "neutral-slate": ("Softer charcoal · pale steel blue", "Lighter, warmer text and surfaces. The pale accent has more luminance contrast, but less color saturation."),
        "slate-blue": ("Neutral Slate base · Graphite Blue accent", "The warmer neutral base with the stronger blue character. Current working direction; still a design target."),
    }
    scenes = (ROOT / "comparison-scenes.html").read_text()
    cards = []
    for candidate in candidates:
        colors = candidate["colors"]
        variables = ";".join(f"--{key.replace('_', '-')}:{value}" for key, value in colors.items())
        font = "CompareNoto" if candidate["ui_asset"] == "noto.woff2" else "CompareInter"
        swatches = ''.join(f'<span><i style="background:{colors[role]}" aria-hidden="true"></i><small>{role}</small><code>{colors[role]}</code></span>' for role in ["canvas", "surface", "accent", "selection"])
        tagline, description = notes[candidate["id"]]
        cards.append(f'''<article class="comparison-card" data-candidate="{candidate['id']}"><header><p class="card-label">{'Working blend' if candidate['id'] == 'slate-blue' else 'Original exploration'}</p><h2>{candidate['name']}</h2><p>{tagline}</p></header><div class="mock-canvas" style="{variables}" data-original-font="{font}">{scenes}</div><div class="swatches">{swatches}</div><p class="card-note">{description}</p></article>''')
    rows = []
    for role in candidates[0]["colors"]:
        values = [candidate["colors"][role] for candidate in candidates]
        cells = ''.join(f'<td><i class="table-swatch" style="background:{value}" aria-hidden="true"></i><code>{value}</code></td>' for value in values)
        rows.append(f'<tr data-shared="{str(len(set(values)) == 1).lower()}"><th scope="row">{escape(role.replace("_", " "))}</th>{cells}</tr>')
    contrast = []
    for label, first, second in [("Main text / surface", "text", "surface"), ("Accent / surface", "accent", "surface"), ("Selected text / selection", "selection_text", "selection")]:
        cells = ''.join(f'<td>{ratio(c["colors"][first], c["colors"][second]):.2f}:1</td>' for c in candidates)
        contrast.append(f'<tr><th scope="row">{label}</th>{cells}</tr>')
    html = (ROOT / "comparison.html").read_text()
    for key, value in {"CARDS": ''.join(cards), "ROWS": ''.join(rows), "CONTRAST": ''.join(contrast)}.items():
        html = html.replace("@@" + key + "@@", value)
    if "@@" in html:
        raise ValueError("unresolved comparison slot")
    page = Page(html)
    if page.h1 != 1 or len(page.ids) != len(set(page.ids)):
        raise ValueError("invalid heading or duplicate id")
    (output / "index.html").write_text(html)
    for name in ["comparison.css", "comparison.js"]:
        shutil.copyfile(ROOT / name, output / name)
    for item in provenance["files"]:
        if hashlib.sha256((output / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("font provenance mismatch")
    print(json.dumps({"candidates": ORDER, "scenes": 4, "files": sum(p.is_file() for p in output.rglob("*")), "shared_auth_colors": True}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
