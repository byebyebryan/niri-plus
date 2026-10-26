#!/usr/bin/env python3
"""Build Niri Plus from readable Markdown and reviewed static assets."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re
import shutil
from string import Template
from urllib.parse import unquote, urljoin, urlsplit

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://dev.byebyebryan.com/niri-plus/"
BASE = urlsplit(SITE).path
PAGES = {
    "design/": ("docs/design.md", "Neutral Slate: appearance, behavior, palette, typography, and setup for the Niri Plus desktop."),
    "design/contrast/": ("docs/design/contrast.md", "Compare a clearer warm desktop and a separate pure-black terminal palette with the current Neutral Slate design."),
    "story/": ("docs/story.md", "The personal story behind a desktop shaped around Chrome, terminals, and coding agents."),
    "tour/": ("docs/tour.md", "Explore browser, terminal, notification, clipboard, and remote-host workflows."),
    "architecture/": ("docs/architecture.md", "How Niri, SwayNC, Rofi, Kitty, and small session services fit together."),
    "setup/": ("docs/setup.md", "Assemble the parts you want with portable examples and focused Arch Linux recipes."),
    "recipes/notifications/": ("docs/recipes/notifications.md", "SwayNC, the custom system panel, and notification integration under Niri."),
    "recipes/clipboard/": ("docs/recipes/clipboard.md", "Text and image clipboard history with Cliphist, Rofi, and session-scoped collectors."),
    "recipes/session/": ("docs/recipes/session.md", "Choose manual locking, idle behavior, and clear session service ownership."),
    "recipes/appearance/": ("docs/recipes/appearance.md", "Scoped Neutral Slate appearance fragments for Niri, Rofi, SwayNC, Gtklock, Qt, and KDE."),
    "recipes/terminal/": ("docs/recipes/terminal.md", "Kitty, Zsh, Powerlevel10k, history, completion, and the terminal-centered workflow."),
    "recipes/desktop-utilities/": ("docs/recipes/desktop-utilities.md", "Portable Network, Bluetooth, Audio, and Session entry points for a Niri desktop."),
    "reference/": ("docs/reference.md", "Search the keyboard reference, explore source versions, and download portable examples."),
}
SOURCES = {source: route for route, (source, _) in PAGES.items()}
ASSETS = {"style.css", "site.js", "contrast.css", "contrast.js", "favicon.svg", "social.png", "agent-plus.png", "panel.png", "panel-ethernet.png", "provenance.json", "LICENSES.txt"}
FONT_ASSETS = {f"assets/{directory}/{font}.{suffix}" for font in ["noto", "noto-medium", "noto-semibold", "meslo", "source-han"] for directory, suffix in [("fonts", "woff2"), ("licenses", "txt")]}
GENERATED = {"data/identity.json", "data/contrast-study.json", "assets/identity.css", "assets/fonts/provenance.json", "examples/kitty/neutral-slate.conf"}
PUBLIC_TOOLS = {"scripts/check-terminal.py"}


def working_identity(source_path="design/identity.json"):
    source = ROOT / source_path
    identity = json.loads(source.read_text())
    direction = next(c for c in identity["candidates"] if c["id"] == identity["working_direction"])
    if identity["selected_candidate"] != direction["id"] or identity["status"] != "selected":
        raise ValueError("public identity must project the selected candidate")
    return {"schema_version": identity["schema_version"], "status": "selected design", "selected_candidate": identity["selected_candidate"], "source": source_path, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "theme_scope": identity["theme_scope"], "shared": identity["shared"], "direction": direction, "terminal": identity["terminal"]}


def kitty_fragment(identity):
    terminal = identity["terminal"]
    lines = ["# Niri Plus / Neutral Slate - Balanced+ terminal appearance.", "# Generated from design/identity.json; preserve your existing Kitty behavior."]
    lines += [f"{option} {color}" for option, color in terminal["colors"].items()]
    lines += [f'background_opacity {terminal["background_opacity"]}']
    lines += [f"color{index} {color}" for index, color in enumerate(terminal["ansi"])]
    return "\n".join(lines) + "\n"


def identity_css(identity):
    colors = identity["direction"]["colors"]
    roles = {"bg": "canvas", "canvas": "canvas", "surface": "surface", "raised": "raised", "input": "input", "line": "separator", "border": "border", "text": "text", "secondary": "secondary", "muted": "muted", "blue": "accent", "accent": "accent", "accent-ink": "accent_ink", "focus": "focus", "selection": "selection", "selection-text": "selection_text", "green": "success", "success": "success", "warning": "warning", "error": "error", "secure-surface": "secure_surface", "secure-input": "secure_input", "secure-button": "secure_button"}
    values = ";".join(f"--{name}:{colors[role]}" for name, role in roles.items())
    values += f';--ui-family:"{identity["direction"]["ui_font"]}";--mono-family:"{identity["direction"]["mono_font"]}"'
    values += ";" + ";".join(f"--ansi-{i}:{c}" for i, c in enumerate(identity["terminal"]["ansi"]))
    values += ";" + ";".join(f"--terminal-{key.replace('_', '-')}:{color}" for key, color in identity["terminal"]["colors"].items())
    return "/* Generated from design/identity.json */\n:root{" + values + "}\n"


def identity_palette():
    identity = working_identity()
    colors = identity["direction"]["colors"]
    names = [("canvas", "Canvas"), ("surface", "Surface"), ("raised", "Raised surface"), ("input", "Input"), ("border", "Control border"), ("separator", "Quiet separator"), ("text", "Main text"), ("secondary", "Secondary text"), ("muted", "Muted text"), ("accent", "Accent"), ("accent_ink", "Text on accent"), ("focus", "Focus"), ("selection", "Selection"), ("selection_text", "Text on selection"), ("success", "Success"), ("warning", "Warning"), ("error", "Error"), ("visited_link", "Visited link"), ("secure_surface", "Login / lock surface"), ("secure_input", "Login / lock input"), ("secure_button", "Login / lock button")]
    swatches = ''.join(f'<div class="palette-swatch" role="listitem"><i style="--swatch:{colors[role]}" aria-hidden="true"></i><strong>{label}</strong><code>{colors[role]}</code></div>' for role, label in names)
    terminal = identity["terminal"]
    ansi = ''.join(f'<div class="ansi-slot" role="listitem"><i style="--ansi-color:{color}" aria-hidden="true"></i><strong>{index:02} · {escape(terminal["ansi_names"][index])}</strong><span>{escape(terminal["ansi_roles"][index])}</span><code>{color}</code></div>' for index, color in enumerate(terminal["ansi"]))
    framing = ''.join(f'<div class="palette-swatch" role="listitem"><i style="--swatch:{color}" aria-hidden="true"></i><strong>{escape(role.replace("_", " "))}</strong><code>{color}</code></div>' for role, color in terminal["colors"].items())
    return partial("identity-palette.html").replace("@@PALETTE@@", swatches).replace("@@TERMINAL_FRAMING@@", framing).replace("@@ANSI@@", ansi)


def identity_typography():
    identity = working_identity()
    ui_font = escape(identity["direction"]["ui_font"])
    mono_font = escape(identity["direction"]["mono_font"])
    return partial("identity-typography.html").replace("@@UI_FONT@@", ui_font).replace("@@MONO_FONT@@", mono_font)


def identity_gallery():
    identity = working_identity()
    terminal = identity["terminal"]
    ansi = ''.join(f'<span role="listitem" style="--ansi-color:{color}" aria-label="ANSI {index}: {escape(terminal["ansi_names"][index])} · {escape(terminal["ansi_roles"][index])} · {color}">{index:02}</span>' for index, color in enumerate(terminal["ansi"]))
    return partial("identity-gallery.html").replace("@@ANSI@@", ansi)


def contrast_ratio(first, second):
    def luminance(color):
        values = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
        return sum(v * weight for v, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
    low, high = sorted((luminance(first), luminance(second)))
    return (high + 0.05) / (low + 0.05)


def contrast_study():
    source = ROOT / "design/contrast-study.json"
    study = json.loads(source.read_text())
    if study["baseline_source"] != "design/history/neutral-slate-clear-blue.json":
        raise ValueError("contrast study requires the retained historical baseline")
    identity = working_identity(study["baseline_source"])
    if study["status"] != "comparison" or study["baseline_sha256"] != identity["source_sha256"]:
        raise ValueError("contrast proposal must match its reviewed baseline")
    colors = dict(identity["direction"]["colors"])
    colors["separator"] = colors["border"]
    desktop = {"id": "current", "name": "Current Neutral Slate", "status": "current baseline", "colors": colors, "overlay_opacity": identity["shared"]["overlay_opacity"]}
    terminal = identity["terminal"]
    roles = {"background": "background_role", "foreground": "foreground_role", "cursor": "cursor_role", "cursor_text_color": "cursor_text_role", "selection_background": "selection_background_role", "selection_foreground": "selection_foreground_role"}
    current = {"id": "current", "name": "Current terminal", **{option: colors[terminal[role]] for option, role in roles.items()}, "ansi": terminal["ansi"], "background_opacity": 1}
    black = {**current, "id": "black-only", "name": "Original colors on black", "background": "#000000"}
    terminal_models = [study["terminal"], *[{**study["terminal"], **sample} for sample in study["terminal_samples"]], study["terminal_reference"]]
    if any(len(model["ansi"]) != 16 for model in terminal_models) or set(study["desktop"]["colors"]) != set(colors):
        raise ValueError("contrast study must define complete desktop and ANSI colors")
    color_values = [*study["desktop"]["colors"].values(), *(color for model in terminal_models for color in [*model["ansi"], *(model[key] for key in roles)])]
    if any(not re.fullmatch(r"#[0-9a-f]{6}", value) for value in color_values):
        raise ValueError("contrast study expects opaque sRGB hex colors")
    pairs = [
        ("Main text / surface", "text", "surface"),
        ("Secondary text / surface", "secondary", "surface"),
        ("Muted text / surface", "muted", "surface"),
        ("Control border / surface", "border", "surface"),
        ("Control border / raised", "border", "raised"),
        ("Raised / surface", "raised", "surface"),
        ("Accent / surface", "accent", "surface"),
        ("Text on accent / accent", "accent_ink", "accent"),
        ("Selection fill / surface", "selection", "surface"),
        ("Selected text / selection", "selection_text", "selection"),
        ("Focus marker / selection", "focus", "selection"),
        ("Success / raised", "success", "raised"),
        ("Warning / raised", "warning", "raised"),
        ("Error / raised", "error", "raised"),
    ]
    measurements = [{"label": label, **{key: round(contrast_ratio(model["colors"][a], model["colors"][b]), 2) for key, model in [("current", desktop), ("proposal", study["desktop"])]}} for label, a, b in pairs]
    variants = terminal_models
    terminal_pairs = [{"label": terminal["ansi_names"][i], "slots": [i, i + 8], **{model["id"]: round(contrast_ratio(model["ansi"][i], model["ansi"][i + 8]), 2) for model in variants}} for i in range(1, 8)]
    return {**study, "source": "design/contrast-study.json", "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "baseline": {"desktop": desktop, "terminal": current, "terminal_on_black": black}, "terminal_variants": variants, "ansi_names": terminal["ansi_names"], "contrast_pairs": measurements, "terminal_pair_contrast": terminal_pairs}


def contrast_html():
    study = contrast_study()
    current = study["baseline"]["desktop"]
    desktops = []
    for key, model, label, note in [("current", current, "Previous baseline", "Warm charcoal, soft status colors, and the preceding Clear Blue accent."), ("proposal", study["desktop"], "Selected desktop", "Deeper neutrals, clearer control edges, stronger color character, and quiet interior dividers.")]:
        variables = ";".join(f"--d-{role.replace('_', '-')}:{value}" for role, value in model["colors"].items())
        desktops.append(f'<article class="study-card" data-desktop-card="{key}" style="{variables}"><header><p class="eyebrow">{label}</p><h3>{escape(model["name"])}</h3><p>{note}</p></header>{partial("contrast-desktop.html")}</article>')
    terminals = []
    labels = [("Balanced endpoint", "The preceding moderate palette, retained unchanged as the quieter endpoint."), ("Intermediate / 40% blend start", "A little more color than Balanced, with deliberate normal/bright separation."), ("Intermediate / 70% blend start", "Closer to Vivid, with extra shade separation where the normal colors would become too bright."), ("Vivid endpoint", "The preceding saturated palette, retained unchanged as the stronger endpoint.")]
    for model, (label, note) in zip(study["terminal_variants"], labels):
        if model["id"] == study["selected_terminal"]:
            label = "Selected terminal / Balanced+"
        keys = ["background", "foreground", "cursor", "cursor_text_color", "selection_background", "selection_foreground"]
        variables = ";".join(f"--t-{key.replace('_', '-')}:{model[key]}" for key in keys)
        variables += ";" + ";".join(f"--t-a{i}:{color}" for i, color in enumerate(model["ansi"]))
        ansi = ''.join(f'<span role="listitem" style="background:{color};color:{"#000000" if contrast_ratio(color, "#000000") >= contrast_ratio(color, "#ffffff") else "#ffffff"}" aria-label="ANSI {i}: {escape(study["ansi_names"][i])}, {color}">{i:02}</span>' for i, color in enumerate(model["ansi"]))
        paired_text = ''.join(f'<div class="study-pair" role="listitem"><span>{escape(study["ansi_names"][i])}</span><code data-pair-normal="{i}" style="color:{model["ansi"][i]}">{i:02} {escape(study["ansi_names"][i])}</code><code data-pair-bright="{i + 8}" style="color:{model["ansi"][i + 8]}">{i + 8:02} {escape(study["ansi_names"][i])}</code></div>' for i in range(1, 8))
        scene = partial("contrast-terminal.html").replace("@@ANSI@@", ansi).replace("@@PAIRS@@", paired_text).replace("@@BACKGROUND@@", model["background"]).replace("@@FOREGROUND@@", model["foreground"])
        group = ' data-view-group="middle"' if "blend_weight" in model else ''
        terminals.append(f'<article class="study-card" data-terminal-card="{model["id"]}"{group} style="{variables}"><header><p class="eyebrow">{label}</p><h3>{escape(model["name"])}</h3><p>{note}</p></header>{scene}</article>')
    def value_cell(color):
        return f'<td><span class="study-token-dot" style="--token-color:{color}" aria-hidden="true"></span><code>{color}</code></td>'
    desktop_values = ''.join(f'<tr><th scope="row">{escape(role.replace("_", " "))}</th>{value_cell(current["colors"][role])}{value_cell(color)}</tr>' for role, color in study["desktop"]["colors"].items())
    terminal_values = ''.join(f'<tr><th scope="row">{i:02} · {escape(study["ansi_names"][i])}</th>{"".join(value_cell(model["ansi"][i]) for model in study["terminal_variants"])}</tr>' for i in range(16))
    pair_values = ''.join(f'<tr><th scope="row">{pair["slots"][0]:02}/{pair["slots"][1]:02} · {escape(pair["label"])}</th>{"".join("<td>" + format(pair[model["id"]], ".2f") + ":1</td>" for model in study["terminal_variants"])}</tr>' for pair in study["terminal_pair_contrast"])
    contrast = ''.join(f'<tr><th scope="row">{escape(pair["label"])}</th><td>{pair["current"]:.2f}:1</td><td>{pair["proposal"]:.2f}:1</td></tr>' for pair in study["contrast_pairs"])
    html = partial("contrast-study.html")
    headers = ''.join(f'<th scope="col">{escape(model["name"])}</th>' for model in study["terminal_variants"])
    for key, value in {"DESKTOPS": ''.join(desktops), "TERMINALS": ''.join(terminals), "DESKTOP_VALUES": desktop_values, "TERMINAL_VALUES": terminal_values, "TERMINAL_HEADERS": headers, "PAIR_VALUES": pair_values, "CONTRAST": contrast}.items():
        html = html.replace("@@" + key + "@@", value)
    return html


def public_files():
    manifest = json.loads((ROOT / "examples/manifest.json").read_text())
    validate_identity_associations(manifest["files"])
    examples = {item["path"] for item in manifest["files"]}
    for name in examples:
        if not (name.startswith("examples/") or name in PUBLIC_TOOLS) or ".." in Path(name).parts:
            raise ValueError(f"invalid public example/tool path: {name}")
    return {"assets/" + x for x in ASSETS} | {"data/setup.json", "examples/manifest.json"} | examples | FONT_ASSETS | GENERATED


def validate_identity_associations(records):
    """Keep frozen native appearance files tied to the selected identity source."""
    identity_hash = hashlib.sha256((ROOT / "design/identity.json").read_bytes()).hexdigest()
    for record in records:
        path = record.get("path", "")
        if path.startswith("examples/theme/") and record.get("identity_sha256") != identity_hash:
            raise ValueError(f"stale identity association: {path}")


def link(source, target):
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or target.startswith(("#", "/")):
        return target
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(parsed.path)))
    suffix = ("?" + parsed.query if parsed.query else "") + ("#" + parsed.fragment if parsed.fragment else "")
    if resolved == "design/identity.json":
        return BASE + "data/identity.json" + suffix
    if resolved in SOURCES:
        return BASE + SOURCES[resolved] + suffix
    if resolved in public_files():
        return BASE + resolved + suffix
    raise ValueError(f"{source}: unregistered local link {target}")


def partial(name):
    return (ROOT / "site" / name).read_text().replace("@@BASE@@", BASE)


def panel():
    return f'''<figure class="panel-shot"><div class="media-label"><span>Native SwayNC fork</span><span>Actual rendering ↗</span></div><a class="panel-frame" href="{BASE}assets/panel.png" aria-label="Open the full isolated SwayNC screenshot" style="display:block"><img src="{BASE}assets/panel.png" alt="System, Network, and Bluetooth cards in the actual SwayNC fork" width="1280" height="800" loading="lazy"></a><figcaption>Actual fork in an isolated session, using its default theme. Sample wireless/GPU values; local CPU/RAM. Battery hides on this hardware. <a href="{BASE}assets/provenance.json">Media source</a>.</figcaption></figure>'''


def snapshot():
    data = json.loads((ROOT / "data/setup.json").read_text())
    fork = data["swaync"]
    deployment = data["deployment"]
    hosts = ", ".join(deployment["rollout_order"])
    return f'''<div class="snapshot"><div><span class="eyebrow">Appearance delivery / {escape(data['date'])}</span><strong>Neutral Slate · {escape(hosts)}</strong><p>Scoped delivery passed; normal-use visual and device checks remain.</p></div><dl><div><dt>Producer</dt><dd><code>{data['producer_revision'][:10]}</code></dd></div><div><dt>Consumer</dt><dd><code>{data['consumer_revision'][:10]}</code></dd></div><div><dt>SwayNC fork</dt><dd>{escape(fork['package'])} {escape(fork['version'])}</dd></div></dl><a href="{BASE}data/setup.json">Full delivery record ↗</a></div>'''


def render_markdown(source):
    text = (ROOT / source).read_text()
    parser = MarkdownIt("commonmark", {"html": False}).enable("table")
    enhancements = {}
    pattern = re.compile(r"^<!-- niri-plus:([a-z]+) -->\n(.*?)\n<!-- /niri-plus:\1 -->$", re.M | re.S)

    def slot(match):
        name, fallback = match.groups()
        if name not in {"workbench", "architecture", "keys", "snapshot", "panel", "overview", "gallery", "palette", "typography", "contrast"} or name in enhancements.values():
            raise ValueError(f"{source}: invalid enhancement {name}")
        if not fallback.strip():
            raise ValueError(f"{source}: empty Markdown fallback")
        for token in parser.parse(fallback):
            for child in token.children or []:
                if child.type in {"link_open", "image"}:
                    link(source, child.attrGet("href" if child.type == "link_open" else "src"))
        key = f"NIRIENHANCEMENT{len(enhancements)}"
        enhancements[key] = name
        return fallback if name == "keys" else key

    text = pattern.sub(slot, text)
    if "<!-- niri-plus:" in text or "<!-- /niri-plus:" in text:
        raise ValueError(f"{source}: unmatched enhancement")
    tokens = parser.parse(text)
    headings = []
    counts = Counter()
    for i, token in enumerate(tokens):
        if token.type == "heading_open":
            label = tokens[i + 1].content
            slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
            counts[slug] += 1
            anchor = slug if counts[slug] == 1 else f"{slug}-{counts[slug]}"
            token.attrSet("id", anchor)
            if token.tag == "h2":
                headings.append((anchor, label))
        for child in token.children or []:
            if child.type in {"link_open", "image"}:
                attr = "href" if child.type == "link_open" else "src"
                child.attrSet(attr, link(source, child.attrGet(attr)))
                if child.type == "image":
                    child.attrSet("loading", "lazy")
    parser.renderer.rules["table_open"] = lambda *_: '<div class="table-scroll" tabindex="0" role="region" aria-label="Scrollable reference table"><table>\n'
    parser.renderer.rules["table_close"] = lambda *_: '</table></div>\n'
    body = parser.renderer.render(tokens, parser.options, {})
    replacements = {"workbench": partial("workbench.html"), "architecture": partial("architecture.html"), "snapshot": snapshot(), "panel": panel(), "overview": partial("identity-overview.html"), "gallery": identity_gallery(), "palette": identity_palette(), "typography": identity_typography(), "contrast": contrast_html()}
    for key, name in enhancements.items():
        if name != "keys":
            body = body.replace(f"<p>{key}</p>", replacements[name])
    if "keys" in enhancements.values():
        control = '<div class="key-search" hidden data-key-search><label for="key-filter">Find a key or task</label><input id="key-filter" type="search" placeholder="Try clipboard, Mod, or window…" autocomplete="off"><p class="key-count" aria-live="polite" data-key-count></p></div>'
        body = body.replace('<h2 id="keyboard-reference">Keyboard reference</h2>', '<h2 id="keyboard-reference">Keyboard reference</h2>' + control, 1)
    title = (ROOT / source).read_text().splitlines()[0].removeprefix("# ")
    toc = ''.join(f'<a href="#{a}">{escape(t)}</a>' for a, t in headings)
    if source == "docs/design/contrast.md":
        return title, f'<article class="wrap contrast-study"><p class="eyebrow">Niri Plus / Contrast study</p>{body}</article>'
    if source == "docs/story.md":
        toc = '<p class="eyebrow">A personal setup</p><p>Browser interaction.<br>Terminal work.<br>Agents in the everyday.</p><a href="' + BASE + 'tour/">See the desktop →</a>'
    body = f'<div class="wrap document-layout"><aside class="on-this-page" aria-label="On this page"><span class="aside-label">{"The story" if source == "docs/story.md" else "On this page"}</span>{toc}</aside><article class="prose"><p class="eyebrow">Niri Plus / {"Personal story" if source == "docs/story.md" else "Desktop guide"}</p>{body}<div class="article-end"><a href="{BASE}setup/">Setup guide →</a><a href="https://github.com/byebyebryan/niri-plus/blob/main/{source}">Read on GitHub ↗</a></div></article></div>'
    return title, body


def shell(route, title, description, body):
    navigation = ''.join(f'<a href="{BASE}{r}"' + (' aria-current="page"' if route == r else '') + f'>{label}</a>' for r, label in [("story/", "Story"), ("tour/", "Tour"), ("design/", "Design"), ("setup/", "Setup"), ("reference/", "Reference")])
    page_assets = f'<link rel="stylesheet" href="{BASE}assets/contrast.css"><script defer src="{BASE}assets/contrast.js"></script>' if route == "design/contrast/" else ""
    return Template((ROOT / "site/layout.html").read_text()).substitute(title=escape(title), description=escape(description, quote=True), canonical=SITE + route, site=SITE, base=BASE, navigation=navigation, body=body, page_assets=page_assets, theme_canvas=working_identity()["direction"]["colors"]["canvas"])


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = []
        self.links = []
        self.counts = Counter()
        self.canonicals = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.counts[tag] += 1
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonicals.append(attrs.get("href"))
        for attribute in ("src", "href"):
            if attrs.get(attribute):
                self.links.append(attrs[attribute])
        if tag == "img" and not attrs.get("alt"):
            raise ValueError("image is missing alt text")


def validate(output):
    inventory = {"index.html", *(route + "index.html" for route in PAGES), *public_files(), "sitemap.xml", ".nojekyll"}
    actual = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
    if actual != inventory:
        raise ValueError(f"public inventory mismatch: missing={inventory-actual}, extra={actual-inventory}")
    pages = {name: Page((output / name).read_text()) for name in actual if name.endswith(".html")}
    links = 0
    for name, page in pages.items():
        route = name.removesuffix("index.html")
        if page.counts["h1"] != 1 or page.counts["main"] != 1 or len(page.ids) != len(set(page.ids)):
            raise ValueError(f"{name}: invalid landmarks or duplicate IDs")
        if page.canonicals != [SITE + route]:
            raise ValueError(f"{name}: invalid canonical URL")
        for target in page.links:
            url = urlsplit(urljoin(SITE + route, target))
            if url.netloc != urlsplit(SITE).netloc or not url.path.startswith(BASE):
                continue
            dest = unquote(url.path[len(BASE):])
            dest += "index.html" if not dest or dest.endswith("/") else ""
            if dest not in actual:
                raise ValueError(f"{name}: missing target {target}")
            if url.fragment and dest in pages and unquote(url.fragment) not in pages[dest].ids:
                raise ValueError(f"{name}: missing anchor {target}")
            links += 1
    records = json.loads((ROOT / "assets/provenance.json").read_text())["files"] + json.loads((ROOT / "examples/manifest.json").read_text())["files"]
    records += [item for item in json.loads((ROOT / "design/assets/provenance.json").read_text())["files"] if item["path"] in FONT_ASSETS]
    for item in records:
        path = output / item["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"hash mismatch: {item['path']}")
    identity = working_identity()
    if json.loads((output / "data/identity.json").read_text()) != identity:
        raise ValueError("public identity differs from source")
    if json.loads((output / "data/contrast-study.json").read_text()) != contrast_study():
        raise ValueError("public contrast study differs from source")
    if (output / "assets/identity.css").read_text() != identity_css(identity) or (output / "examples/kitty/neutral-slate.conf").read_text() != kitty_fragment(identity):
        raise ValueError("generated appearance differs from identity source")
    return {"pages": len(pages), "files": len(actual), "local_links": links}


def build(output, portable=False):
    output = output.absolute()
    if output.is_symlink() or output.resolve() in {ROOT, ROOT.parent}:
        raise ValueError("unsafe output path")
    if output.resolve().is_relative_to(ROOT) and output.resolve() != ROOT / "dist":
        raise ValueError("only dist may be used as an in-checkout output")
    if output.exists() and any(output.iterdir()):
        raise ValueError("output must be empty; choose a new directory")
    output.mkdir(parents=True, exist_ok=True)
    identity = working_identity()
    fonts = json.loads((ROOT / "design/assets/provenance.json").read_text())
    examples = json.loads((ROOT / "examples/manifest.json").read_text())
    generated = {"data/identity.json": json.dumps(identity, indent=2) + "\n", "data/contrast-study.json": json.dumps(contrast_study(), indent=2) + "\n", "assets/identity.css": identity_css(identity), "examples/kitty/neutral-slate.conf": kitty_fragment(identity), "examples/manifest.json": json.dumps(examples, indent=2) + "\n", "assets/fonts/provenance.json": json.dumps({"files": [item for item in fonts["files"] if item["path"] in FONT_ASSETS]}, indent=2) + "\n"}
    for name in public_files():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if name in generated:
            target.write_text(generated[name])
            continue
        source = ROOT / name
        if name in FONT_ASSETS:
            source = ROOT / "design" / name
        if name in {"assets/style.css", "assets/site.js", "assets/contrast.css", "assets/contrast.js", "assets/favicon.svg"}:
            source = ROOT / "site" / Path(name).name
        shutil.copyfile(source, target)
    home = partial("home.html").replace("@@WORKBENCH@@", partial("workbench.html")).replace("@@PANEL@@", panel())
    (output / "index.html").write_text(shell("", "A desktop for the way I work", "Bryan's personal Niri desktop. Chrome, terminals, coding agents, and small integrations, with a tour and practical setup guides.", home))
    for route, (source, description) in PAGES.items():
        title, body = render_markdown(source)
        target = output / route / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(shell(route, title, description, body))
    (output / ".nojekyll").touch()
    (output / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{SITE}{route}</loc></url>' for route in ["", *PAGES]) + '</urlset>\n')
    if portable:
        for page in output.rglob("*.html"):
            parent = page.parent.relative_to(output).as_posix()
            def relative(match):
                target = match[2][len(BASE):]
                url = urlsplit(target)
                path = posixpath.relpath(url.path or ".", parent)
                if not url.path or url.path.endswith("/"):
                    path += "/"
                return match[1] + '="' + path + ("#" + url.fragment if url.fragment else "") + '"'
            page.write_text(re.sub(r'(href|src)="(' + re.escape(BASE) + r'[^\"]*)"', relative, page.read_text()))
    return validate(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--portable", action="store_true", help="Use relative page links for an independent review snapshot; canonical URLs remain public.")
    args = parser.parse_args()
    print(json.dumps(validate(args.output) if args.validate_only else build(args.output, portable=args.portable), sort_keys=True))
