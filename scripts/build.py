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
    "story/": ("docs/story.md", "The personal story behind a desktop shaped around Chrome, terminals, and coding agents."),
    "tour/": ("docs/tour.md", "Explore browser, terminal, notification, clipboard, and remote-host workflows."),
    "architecture/": ("docs/architecture.md", "How Niri, SwayNC, Rofi, Kitty, and small session services fit together."),
    "setup/": ("docs/setup.md", "Assemble the parts you want with portable examples and focused Arch Linux recipes."),
    "recipes/notifications/": ("docs/recipes/notifications.md", "SwayNC, the custom system panel, and notification integration under Niri."),
    "recipes/clipboard/": ("docs/recipes/clipboard.md", "Text and image clipboard history with Cliphist, Rofi, and session-scoped collectors."),
    "recipes/session/": ("docs/recipes/session.md", "Choose manual locking, idle behavior, and clear session service ownership."),
    "reference/": ("docs/reference.md", "Search the keyboard reference, explore source versions, and download portable examples."),
}
SOURCES = {source: route for route, (source, _) in PAGES.items()}
ASSETS = {"style.css", "site.js", "favicon.svg", "social.png", "agent-plus.png", "panel.png", "panel-ethernet.png", "provenance.json", "LICENSES.txt"}


def public_files():
    manifest = json.loads((ROOT / "examples/manifest.json").read_text())
    examples = {item["path"] for item in manifest["files"]}
    for name in examples:
        if not name.startswith("examples/") or ".." in Path(name).parts:
            raise ValueError(f"invalid example path: {name}")
    return {"assets/" + x for x in ASSETS} | {"data/setup.json", "examples/manifest.json"} | examples


def link(source, target):
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or target.startswith(("#", "/")):
        return target
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(parsed.path)))
    suffix = ("?" + parsed.query if parsed.query else "") + ("#" + parsed.fragment if parsed.fragment else "")
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
    return f'''<div class="snapshot"><div><span class="eyebrow">Source snapshot / {escape(data['date'])}</span><strong>Minimal Niri · SwayNC · Gtklock</strong><p>Selected on three managed machines. Public recipes are adapted examples.</p></div><dl><div><dt>SwayNC fork</dt><dd>{escape(fork['package'])} {escape(fork['version'])}</dd></div><div><dt>Private configuration</dt><dd><code>{data['chezmoi_revision'][:10]}</code></dd></div></dl><a href="{BASE}data/setup.json">Full source record ↗</a></div>'''


def render_markdown(source):
    text = (ROOT / source).read_text()
    parser = MarkdownIt("commonmark", {"html": False}).enable("table")
    enhancements = {}
    pattern = re.compile(r"^<!-- niri-plus:([a-z]+) -->\n(.*?)\n<!-- /niri-plus:\1 -->$", re.M | re.S)

    def slot(match):
        name, fallback = match.groups()
        if name not in {"workbench", "architecture", "keys", "snapshot", "panel"} or name in enhancements.values():
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
    replacements = {"workbench": partial("workbench.html"), "architecture": partial("architecture.html"), "snapshot": snapshot(), "panel": panel()}
    for key, name in enhancements.items():
        if name != "keys":
            body = body.replace(f"<p>{key}</p>", replacements[name])
    if "keys" in enhancements.values():
        control = '<div class="key-search" hidden data-key-search><label for="key-filter">Find a key or task</label><input id="key-filter" type="search" placeholder="Try clipboard, Mod, or window…" autocomplete="off"><p class="key-count" aria-live="polite" data-key-count></p></div>'
        body = body.replace('<h2 id="keyboard-reference">Keyboard reference</h2>', '<h2 id="keyboard-reference">Keyboard reference</h2>' + control, 1)
    title = (ROOT / source).read_text().splitlines()[0].removeprefix("# ")
    toc = ''.join(f'<a href="#{a}">{escape(t)}</a>' for a, t in headings)
    if source == "docs/story.md":
        toc = '<p class="eyebrow">A personal setup</p><p>Browser interaction.<br>Terminal work.<br>Agents in the everyday.</p><a href="' + BASE + 'tour/">See the desktop →</a>'
    body = f'<div class="wrap document-layout"><aside class="on-this-page" aria-label="On this page"><span class="aside-label">{"The story" if source == "docs/story.md" else "On this page"}</span>{toc}</aside><article class="prose"><p class="eyebrow">Niri Plus / {"Personal story" if source == "docs/story.md" else "Desktop guide"}</p>{body}<div class="article-end"><a href="{BASE}setup/">Setup guide →</a><a href="https://github.com/byebyebryan/niri-plus/blob/main/{source}">Read on GitHub ↗</a></div></article></div>'
    return title, body


def shell(route, title, description, body):
    navigation = ''.join(f'<a href="{BASE}{r}"' + (' aria-current="page"' if route == r else '') + f'>{label}</a>' for r, label in [("story/", "Story"), ("tour/", "Tour"), ("setup/", "Setup"), ("reference/", "Reference")])
    return Template((ROOT / "site/layout.html").read_text()).substitute(title=escape(title), description=escape(description, quote=True), canonical=SITE + route, site=SITE, base=BASE, navigation=navigation, body=body)


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
    for source in ["assets/provenance.json", "examples/manifest.json"]:
        for item in json.loads((ROOT / source).read_text())["files"]:
            path = output / item["path"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
                raise ValueError(f"hash mismatch: {item['path']}")
    return {"pages": len(pages), "files": len(actual), "local_links": links}


def build(output):
    output = output.absolute()
    if output.is_symlink() or output.resolve() in {ROOT, ROOT.parent}:
        raise ValueError("unsafe output path")
    if output.resolve().is_relative_to(ROOT) and output.resolve() != ROOT / "dist":
        raise ValueError("only dist may be used as an in-checkout output")
    if output.exists() and any(output.iterdir()):
        raise ValueError("output must be empty; choose a new directory")
    output.mkdir(parents=True, exist_ok=True)
    for name in public_files():
        source = ROOT / name
        if name in {"assets/style.css", "assets/site.js", "assets/favicon.svg"}:
            source = ROOT / "site" / Path(name).name
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
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
    return validate(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    print(json.dumps(validate(args.output) if args.validate_only else build(args.output), sort_keys=True))
