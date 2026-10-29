#!/usr/bin/env python3
"""Build Niri Plus from readable Markdown and reviewed static assets."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
from fractions import Fraction
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
from string import Template
import sys
from urllib.parse import unquote, urljoin, urlsplit

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from components.appearance.render import render as render_appearance

SITE = "https://dev.byebyebryan.com/niri-plus/"
BASE = urlsplit(SITE).path
PAGES = {
    "design/": ("docs/design.md", "Neutral Slate: appearance, behavior, palette, typography, and setup for the Niri Plus desktop."),
    "design/contrast/": ("docs/design/contrast.md", "Compare a clearer warm desktop and a separate pure-black terminal palette with the current Neutral Slate design."),
    "story/": ("docs/story.md", "The personal story behind a desktop shaped around Chrome, terminals, and coding agents."),
    "tour/": ("docs/tour.md", "Explore browser, terminal, notification, clipboard, and remote-host workflows."),
    "architecture/": ("docs/architecture.md", "How Niri, SwayNC, Rofi, Kitty, and small session services fit together."),
    "components/": ("docs/components.md", "Canonical Niri Plus component sources, public exports, consumer boundaries, and release status."),
    "setup/": ("docs/setup.md", "A concise overview of the Arch reference desktop, what it includes, and the choices to make."),
    "setup/agent/": ("docs/setup-agent.md", "Ordered Arch setup instructions for agents: inputs, commands, stage gates, verification and recovery."),
    "recipes/notifications/": ("docs/recipes/notifications.md", "SwayNC, the custom system panel, and notification integration under Niri."),
    "recipes/clipboard/": ("docs/recipes/clipboard.md", "Text and image clipboard history with Cliphist, Rofi, and session-scoped collectors."),
    "recipes/session/": ("docs/recipes/session.md", "Choose manual locking, idle behavior, and clear session service ownership."),
    "recipes/appearance/": ("docs/recipes/appearance.md", "Scoped Neutral Slate appearance fragments for Niri, Rofi, SwayNC, Gtklock, Qt, and KDE."),
    "recipes/terminal/": ("docs/recipes/terminal.md", "Kitty, Zsh, Powerlevel10k, history, completion, and the terminal-centered workflow."),
    "recipes/desktop-utilities/": ("docs/recipes/desktop-utilities.md", "Portable Network, Bluetooth, Audio, and Session entry points for a Niri desktop."),
    "recipes/rofi-controls/": ("docs/recipes/rofi-controls.md", "Direct Rofi Network, Audio and Bluetooth controls: opt-in release, agent setup and acceptance boundaries."),
    "recipes/displays/": ("docs/recipes/displays.md", "Kanshi display profiles, logical scaling, docking and recovery under Niri."),
    "recipes/login/": ("docs/recipes/login.md", "SDDM session entry and a separately derived Neutral Slate login theme."),
    "recipes/hardware-feedback/": ("docs/recipes/hardware-feedback.md", "Transient volume, microphone and laptop-backlight feedback with the managed helpers."),
    "recipes/input/": ("docs/recipes/input.md", "Fcitx5, keyboard/input ownership, CJK text and fractional-scale candidate windows."),
    "recipes/files/": ("docs/recipes/files.md", "Default applications, browser file interaction and removable-media ownership."),
    "reference/": ("docs/reference.md", "Search the keyboard reference, explore source versions, and download portable examples."),
}
SOURCES = {source: route for route, (source, _) in PAGES.items()}
ASSETS = {"style.css", "site.js", "contrast.css", "contrast.js", "favicon.svg", "social.png", "agent-plus.png", "panel.png", "panel-ethernet.png", "provenance.json", "LICENSES.txt", "arch-reference/themed-greeter-after-reboot.png", "arch-reference/gtklock-replay-neutral-slate.png", "arch-reference/chrome-ime-replay-fractional-preedit.png"}
DEMO_ASSETS = {
    f"assets/demo-{scene}.{suffix}"
    for scene in ("overview", "browser-files", "terminal", "information")
    for suffix in ("mp4", "png")
}
SWAYNC_DEMO_ASSETS = {
    "assets/demo-overview.mp4",
    "assets/demo-overview.png",
    "assets/demo-information.mp4",
    "assets/demo-information.png",
}
SWAYNC_PIN = {
    "package": "swaync-bryan",
    "version": "0.12.6-15",
    "recipe_revision": "cd1038d1c824f256ecb5a448d78df9f71b64850a",
    "recipe_archive_sha256": "297852ede6f49cd9a2e75204d734807529e84b2dd0b01f6fc8789da4b53d9ff0",
    "source_revision": "4114c9cd56f086e166253880d0c96c6c5212e4aa",
    "source_archive_sha256": "8b69e2f47692a0dc53b00c5e9cf8c9df62c1295e5e7ee36acf16e40359f6bc83",
}
DEMO_ASSET_LICENSES = {
    path: "GPL-3.0-only" if path in SWAYNC_DEMO_ASSETS else "MIT"
    for path in DEMO_ASSETS
}
FONT_ASSETS = {f"assets/{directory}/{font}.{suffix}" for font in ["noto", "noto-medium", "noto-semibold", "meslo", "source-han"] for directory, suffix in [("fonts", "woff2"), ("licenses", "txt")]}
GENERATED = {"data/identity.json", "data/contrast-study.json", "assets/identity.css", "assets/fonts/provenance.json", "examples/kitty/neutral-slate.conf", "setup/agent.md"}
PUBLIC_TOOLS = {"scripts/check-terminal.py", "scripts/check-desktop.py"}
PUBLIC_LOCAL_DOCS = {
    "LICENSE",
    "docs/planning/arch-installation-receipt.md",
    "docs/planning/components-0.3.1-receipt.md",
    "docs/planning/desktop-demonstration-receipt.md",
    "tools/vm/desktop/wlr-compat/README.md",
    "design/rofi-controls/index.html",
    "docs/planning/rofi-controls-implementation-receipt.md",
}
DEMO_CLIPS = {
    "overview": {
        "video": "assets/demo-overview.mp4",
        "poster": "assets/demo-overview.png",
        "id": "demo-overview",
        "title": "The native desktop, in motion",
        "description": "A 62-second staged Arch guest composite follows browser and file work, a short reused terminal scene, and on-demand information and clipboard tools.",
        "steps": [
            "See the full browser/files scene followed by a 12-second excerpt from the earlier terminal pilot.",
            "Open the SwayNC panel and clipboard picker in the staged Niri guest.",
            "Use the focused recordings below for the full task sequences.",
        ],
        "setup": [("Install the Arch reference desktop", "setup-agent.md#3-install-the-first-session-packages")],
    },
    "browser-files": {
        "video": "assets/demo-browser-files.mp4",
        "poster": "assets/demo-browser-files.png",
        "id": "demo-browser-files",
        "title": "Browser and files",
        "description": "Chrome downloads a public sample; Dolphin opens it and an SVG; the native GTK chooser returns the original file to the upload sample page.",
        "steps": [
            "Download the public Markdown sample and SVG in Chrome.",
            "Open the Markdown file through Dolphin with the guest Neovim default, and open the SVG in Gwenview.",
            "Choose the original Markdown sample in Chrome's GTK file chooser and verify the returned bytes.",
        ],
        "setup": [("Browser, MIME, and file-dialog recipe", "recipes/files.md")],
    },
    "terminal": {
        "video": "assets/demo-terminal.mp4",
        "poster": "assets/demo-terminal.png",
        "id": "demo-terminal",
        "title": "Kitty and Zsh beside a browser",
        "description": "The exact-byte reused pilot capture keeps a local Chrome sample page beside Kitty while Zsh runs a guest-guarded sample check.",
        "steps": [
            "Keep the local sample page and Kitty project side by side.",
            "Move focus between Niri columns, then run the guest-guarded check in Zsh.",
            "Scroll the local page with Page Down and Page Up, then return focus to Kitty.",
        ],
        "setup": [("Kitty and Zsh setup", "recipes/terminal.md")],
    },
    "information": {
        "video": "assets/demo-information.mp4",
        "poster": "assets/demo-information.png",
        "id": "demo-information",
        "title": "Information and clipboard, on demand",
        "description": "SwayNC displays the guest's available CPU, RAM and Ethernet information; Rofi restores public text and image samples and exercises Delete, Cancel and confirmed Clear all.",
        "steps": [
            "Open SwayNC with Mod+N and inspect the CPU, RAM and Ethernet values available in this guest.",
            "Open clipboard history with Mod+Y and restore the exact public text and image samples.",
            "Delete one selected item, Cancel a clear to preserve history, then confirm Clear all.",
        ],
        "setup": [
            ("Notification panel setup", "recipes/notifications.md"),
            ("Clipboard history setup", "recipes/clipboard.md"),
        ],
    },
}


def component_releases():
    """Read the reviewed immutable tuples independently of the latest release."""
    catalog = json.loads((ROOT / "data/component-releases.json").read_text())
    if catalog.get("schema_version") != 1 or not isinstance(catalog.get("releases"), list):
        raise ValueError("invalid component release catalog")
    releases = {}
    for record in catalog["releases"]:
        if not isinstance(record, dict):
            raise ValueError("invalid component release record")
        version = record.get("version")
        if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version) or version in releases:
            raise ValueError("invalid or duplicate component release version")
        if record.get("api_version") != 1 or not re.fullmatch(r"[0-9a-f]{40}", str(record.get("source_commit", ""))):
            raise ValueError("invalid component release source/API")
        for field in ("archive_sha256", "manifest_sha256"):
            if not re.fullmatch(r"[0-9a-f]{64}", str(record.get(field, ""))):
                raise ValueError("invalid component release digest")
        expected_url = f"https://github.com/byebyebryan/niri-plus/releases/download/components-v{version}/niri-plus-components-{version}.tar.gz"
        if record.get("archive_url") != expected_url:
            raise ValueError("component release URL differs from its immutable version")
        releases[version] = record
    return releases


def validate_capture_versions(versions):
    """Bind media to its actual release and a retained identity source."""
    if not isinstance(versions, dict):
        raise ValueError("desktop demos must record exact source_versions")
    component_pin = versions.get("components")
    if not isinstance(component_pin, dict):
        raise ValueError("desktop demo component pin is missing")
    released = component_releases().get(component_pin.get("version"))
    fields = ("version", "source_commit", "archive_sha256", "manifest_sha256")
    if released is None or any(component_pin.get(key) != released[key] for key in fields):
        raise ValueError("desktop demo component pin differs from a reviewed immutable release")
    for optional in ("api_version", "archive_url"):
        if optional in component_pin and component_pin[optional] != released[optional]:
            raise ValueError("desktop demo component pin differs from a reviewed immutable release")
    identity_pin = versions.get("identity")
    source_path = identity_pin.get("path") if isinstance(identity_pin, dict) else None
    if not isinstance(source_path, str):
        raise ValueError("desktop demo identity source path is missing")
    relative = PurePosixPath(source_path)
    allowed = source_path == "design/identity.json" or (
        relative.parts[:2] == ("design", "history") and relative.suffix == ".json"
    )
    identity_source = ROOT / source_path
    if (not allowed or relative.is_absolute() or ".." in relative.parts
            or relative.as_posix() != source_path or identity_source.is_symlink()
            or not identity_source.is_file()
            or not identity_source.resolve().is_relative_to((ROOT / "design").resolve())):
        raise ValueError("desktop demo identity source path is not a retained design input")
    identity_hash = hashlib.sha256(identity_source.read_bytes()).hexdigest()
    if identity_pin.get("sha256") != identity_hash:
        raise ValueError("desktop demo identity hash differs from its recorded source")
    return versions


def validate_desktop_demo_manifest(provenance, *, require_complete=False):
    """Validate public capture metadata before copying native demo assets."""
    demos = provenance.get("desktop_demos")
    if not isinstance(demos, dict):
        raise ValueError("desktop demo provenance is missing desktop_demos")
    capture_label = demos.get("capture_label")
    if not isinstance(capture_label, str) or "staged" not in capture_label.lower() or "arch" not in capture_label.lower():
        raise ValueError("desktop demos must carry a staged Arch capture label")
    validate_capture_versions(demos.get("source_versions"))
    clips = demos.get("clips")
    if not isinstance(clips, list) or not clips or any(not isinstance(item, dict) or not isinstance(item.get("id"), str) for item in clips):
        raise ValueError("desktop demo provenance must define clip records")
    clip_ids = [item["id"] for item in clips]
    if len(clip_ids) != len(set(clip_ids)) or set(clip_ids) - set(DEMO_CLIPS):
        raise ValueError("desktop demo provenance has duplicate or unknown clips")
    if require_complete and set(clip_ids) != set(DEMO_CLIPS):
        raise ValueError("desktop demo provenance must define exactly the four site clips")
    file_records = provenance.get("files")
    if not isinstance(file_records, list):
        raise ValueError("asset provenance files must be a list")
    records_by_path = {}
    for item in file_records:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            continue
        path = item["path"]
        if path in records_by_path:
            raise ValueError(f"duplicate asset provenance: {path}")
        records_by_path[path] = item
    for clip in clips:
        if not isinstance(clip, dict):
            raise ValueError("desktop demo clip records must be objects")
        if "source_versions" in clip:
            validate_capture_versions(clip["source_versions"])
        expected = DEMO_CLIPS[clip["id"]]
        if clip.get("video") != expected["video"] or clip.get("poster") != expected["poster"]:
            raise ValueError(f"desktop demo paths differ from the site contract: {clip['id']}")
        if clip.get("width") != 1920 or clip.get("height") != 1080:
            raise ValueError(f"desktop demo must record 1920x1080 dimensions: {clip['id']}")
        duration = clip.get("duration_seconds")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0:
            raise ValueError(f"desktop demo must record its measured duration: {clip['id']}")
        frame_count = clip.get("frame_count")
        if not isinstance(frame_count, int) or isinstance(frame_count, bool) or frame_count <= 0:
            raise ValueError(f"desktop demo must record its decoded frame count: {clip['id']}")
        frame_rate = clip.get("average_frame_rate")
        try:
            measured_frame_rate = Fraction(str(frame_rate))
        except (ValueError, ZeroDivisionError):
            measured_frame_rate = Fraction(0)
        if measured_frame_rate <= 0:
            raise ValueError(f"desktop demo must record its measured average frame rate: {clip['id']}")
        if not isinstance(clip.get("video_codec"), str) or not clip["video_codec"].strip():
            raise ValueError(f"desktop demo must record its video codec: {clip['id']}")
        if not isinstance(clip.get("pixel_format"), str) or not clip["pixel_format"].strip():
            raise ValueError(f"desktop demo must record its pixel format: {clip['id']}")
        if clip["id"] in {"overview", "information"}:
            swaync_pin = clip.get("additional_source_versions", {}).get("swaync")
            if not isinstance(swaync_pin, dict) or any(swaync_pin.get(key) != value for key, value in SWAYNC_PIN.items()):
                raise ValueError(f"SwayNC-containing clip must record the exact fork and recipe source tuple: {clip['id']}")
        capture_date = clip.get("capture_date")
        try:
            date.fromisoformat(capture_date)
        except (TypeError, ValueError):
            raise ValueError(f"desktop demo must record its capture date: {clip['id']}") from None
        source_capture_hash = clip.get("source_capture_sha256")
        source_captures = clip.get("source_captures")
        if source_capture_hash is not None:
            if not isinstance(source_capture_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", source_capture_hash):
                raise ValueError(f"desktop demo source_capture_sha256 must be a SHA-256 hash or null: {clip['id']}")
        elif not isinstance(source_captures, list) or not source_captures:
            raise ValueError(f"desktop demo must identify its raw source capture(s): {clip['id']}")
        reuse_reason = clip.get("reuse_reason")
        if reuse_reason is not None and (not isinstance(reuse_reason, str) or not reuse_reason.strip()):
            raise ValueError(f"desktop demo reuse_reason must be null or explanatory text: {clip['id']}")
        if clip.get("audio") != "none":
            raise ValueError(f"desktop demo must be silent: {clip['id']}")
        fixture_label = clip.get("fixture_label")
        if not isinstance(fixture_label, str) or not fixture_label.strip():
            raise ValueError(f"desktop demo must identify its sample/fixture content: {clip['id']}")
        notes = clip.get("processing_notes")
        if not isinstance(notes, list) or not notes or any(not isinstance(note, str) or not note.strip() for note in notes):
            raise ValueError(f"desktop demo must record its processing notes: {clip['id']}")
        human_review = clip.get("human_review")
        if not isinstance(human_review, str) or not human_review.strip():
            raise ValueError(f"desktop demo must record its human-review status: {clip['id']}")
        for review_name in ("agent_review", "automated_review"):
            review_status = clip.get(review_name)
            if not isinstance(review_status, str) or not review_status.strip():
                raise ValueError(f"desktop demo must record its {review_name} status: {clip['id']}")
    required_paths = {path for clip in clips for path in (clip["video"], clip["poster"])}
    missing = required_paths - records_by_path.keys()
    if missing:
        raise ValueError(f"desktop demo assets lack provenance hashes: {', '.join(sorted(missing))}")
    for path in required_paths:
        record = records_by_path[path]
        asset_hash = record.get("sha256")
        if not isinstance(asset_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", asset_hash):
            raise ValueError(f"desktop demo asset needs a SHA-256 hash: {path}")
        if record.get("license") != DEMO_ASSET_LICENSES[path]:
            raise ValueError(f"desktop demo asset license must be {DEMO_ASSET_LICENSES[path]}: {path}")
        if not isinstance(record.get("source"), str) or not record["source"].strip():
            raise ValueError(f"desktop demo asset must identify its source: {path}")
        if not isinstance(record.get("description"), str) or not record["description"].strip():
            raise ValueError(f"desktop demo asset must describe its content: {path}")
    for clip in clips:
        poster_source = clip.get("poster_source")
        poster_record = records_by_path[clip["poster"]]
        source_path = poster_source.get("path") if isinstance(poster_source, dict) else None
        source_record = records_by_path.get(source_path)
        if (
            not isinstance(poster_source, dict)
            or source_path not in DEMO_ASSETS
            or not source_path.endswith(".png")
            or not source_record
            or poster_source.get("sha256") != source_record.get("sha256")
            or source_record.get("sha256") != poster_record.get("sha256")
        ):
            raise ValueError(f"desktop demo must identify the exact poster source and hash: {clip['id']}")
    if require_complete and required_paths != DEMO_ASSETS:
        raise ValueError("desktop demo source and poster inventory must match the explicit site inventory")
    for clip in clips:
        clip_record = records_by_path[clip["video"]]
        source_capture_hash = clip.get("source_capture_sha256")
        if source_capture_hash is not None:
            if source_capture_hash != clip_record["sha256"]:
                raise ValueError(f"desktop demo focused capture must be byte-identical to its recorded source: {clip['id']}")
        else:
            for source in clip["source_captures"]:
                if not isinstance(source, dict):
                    raise ValueError(f"desktop demo source capture records must be objects: {clip['id']}")
                source_path = source.get("path")
                source_hash = source.get("sha256")
                trim = source.get("trim_range_seconds")
                if source_path not in DEMO_ASSETS or not source_path.endswith(".mp4"):
                    raise ValueError(f"desktop demo composite source must be an inventoried MP4: {clip['id']}")
                if source_path not in records_by_path or records_by_path[source_path].get("sha256") != source_hash:
                    raise ValueError(f"desktop demo composite source hash differs from asset provenance: {clip['id']}")
                if not isinstance(trim, list) or len(trim) != 2 or any(not isinstance(value, (int, float)) for value in trim) or trim[0] < 0 or trim[1] <= trim[0]:
                    raise ValueError(f"desktop demo composite source must record a valid trim range: {clip['id']}")
    separate_checks = demos.get("separate_guest_checks")
    if not isinstance(separate_checks, list):
        raise ValueError("desktop demos must distinguish separately tested guest checks")
    sharing = next((item for item in separate_checks if isinstance(item, dict) and item.get("id") == "wlr-whole-monitor-sharing"), None)
    if not sharing or sharing.get("recorded_in_clips") is not False:
        raise ValueError("whole-monitor sharing evidence must remain separate from the recordings")
    if not isinstance(sharing.get("scope"), str) or "guest" not in sharing["scope"].lower() or "not a fleet/default" not in sharing["scope"].lower():
        raise ValueError("whole-monitor sharing evidence must retain its guest-only compatibility scope")
    return demos


def desktop_demo_provenance():
    return validate_desktop_demo_manifest(json.loads((ROOT / "assets/provenance.json").read_text()))


def validate_desktop_demo_sources():
    """Verify the staged public media against its manifest before the build."""
    missing = [path for path in sorted(DEMO_ASSETS) if not (ROOT / path).is_file()]
    if missing:
        raise ValueError(f"desktop demo assets are not staged yet: {', '.join(missing)}")
    provenance = json.loads((ROOT / "assets/provenance.json").read_text())
    validate_desktop_demo_manifest(provenance, require_complete=True)
    records = {item["path"]: item for item in provenance["files"]}
    for path in sorted(DEMO_ASSETS):
        source = ROOT / path
        payload = source.read_bytes()
        if hashlib.sha256(payload).hexdigest() != records[path]["sha256"]:
            raise ValueError(f"desktop demo source hash mismatch: {path}")
        if path.endswith(".png"):
            header = payload[:24]
            if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
                raise ValueError(f"desktop demo poster is not a PNG: {path}")
            width = int.from_bytes(header[16:20], "big")
            height = int.from_bytes(header[20:24], "big")
            if (width, height) != (1920, 1080):
                raise ValueError(f"desktop demo poster must be 1920x1080: {path}")
        elif len(payload) < 12 or payload[4:8] != b"ftyp":
            raise ValueError(f"desktop demo video is not an MP4 file: {path}")
    return provenance


def working_identity(source_path="design/identity.json"):
    source = ROOT / source_path
    identity = json.loads(source.read_text())
    direction = next(c for c in identity["candidates"] if c["id"] == identity["working_direction"])
    if identity["selected_candidate"] != direction["id"] or identity["status"] != "selected":
        raise ValueError("public identity must project the selected candidate")
    return {"schema_version": identity["schema_version"], "status": "selected design", "selected_candidate": identity["selected_candidate"], "source": source_path, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "theme_scope": identity["theme_scope"], "shared": identity["shared"], "direction": direction, "terminal": identity["terminal"]}


def kitty_fragment(identity):
    return render_appearance(_appearance_identity(identity))["kitty-neutral-slate.conf"]


def identity_css(identity):
    return render_appearance(_appearance_identity(identity))["identity.css"]


def _appearance_identity(identity):
    if "candidates" in identity:
        return identity
    return {
        "schema_version": identity["schema_version"],
        "status": "selected",
        "selected_candidate": identity["selected_candidate"],
        "candidates": [identity["direction"]],
        "shared": identity["shared"],
        "terminal": identity["terminal"],
    }


def identity_palette():
    identity = working_identity()
    colors = identity["direction"]["colors"]
    names = [("workspace_background", "Workspace background"), ("overview_background", "Overview background"), ("canvas", "UI canvas"), ("surface", "Surface"), ("raised", "Raised surface"), ("input", "Input"), ("border", "Control border"), ("separator", "Quiet separator"), ("text", "Main text"), ("secondary", "Secondary text"), ("muted", "Muted text"), ("accent", "Accent"), ("accent_ink", "Text on accent"), ("focus", "Focus"), ("selection", "Selection"), ("selection_text", "Text on selection"), ("success", "Success"), ("warning", "Warning"), ("error", "Error"), ("visited_link", "Visited link"), ("secure_surface", "Login / lock surface"), ("secure_input", "Login / lock input"), ("secure_button", "Login / lock button")]
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
    provenance = json.loads((ROOT / "assets/provenance.json").read_text())["desktop_demos"]
    captures = [provenance["source_versions"], *(clip["source_versions"] for clip in provenance["clips"] if "source_versions" in clip)]
    retained_identities = {item["identity"]["path"] for item in captures}
    return {"assets/" + x for x in ASSETS} | DEMO_ASSETS | PUBLIC_LOCAL_DOCS | {"data/setup.json", "data/history/setup-20261026.json", "data/history/components-0.3.1.json", "data/components.json", "data/component-releases.json", "examples/manifest.json"} | retained_identities | examples | FONT_ASSETS | GENERATED


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
    if resolved.startswith("design/") and resolved.removeprefix("design/") in FONT_ASSETS:
        return BASE + resolved.removeprefix("design/") + suffix
    if resolved in SOURCES:
        return BASE + SOURCES[resolved] + suffix
    if resolved in public_files():
        return BASE + resolved + suffix
    raise ValueError(f"{source}: unregistered local link {target}")


def public_markdown(source, output_name, *, repository_links=False):
    """Preserve Markdown and commands while resolving links for its public URL."""
    lines = (ROOT / source).read_text().splitlines(keepends=True)
    parser = MarkdownIt("commonmark").enable("table")
    for token in parser.parse("".join(lines)):
        if token.type != "inline" or token.map is None:
            continue
        start, end = token.map
        content = "".join(lines[start:end])
        for child in token.children or []:
            if child.type != "link_open":
                continue
            target = child.attrGet("href")
            try:
                resolved = link(source, target)
            except ValueError:
                if not repository_links:
                    raise
                url = urlsplit(target)
                path = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(url.path)))
                original = (ROOT / path).resolve()
                if not original.is_relative_to(ROOT.resolve()) or not original.is_file():
                    raise ValueError(f"{source}: missing repository reference {target}")
                suffix = ("?" + url.query if url.query else "") + ("#" + url.fragment if url.fragment else "")
                resolved = "https://github.com/byebyebryan/niri-plus/blob/main/" + path + suffix
            if resolved.startswith(BASE):
                url = urlsplit(resolved[len(BASE):])
                resolved = posixpath.relpath(url.path or ".", posixpath.dirname(output_name) or ".")
                if not url.path or url.path.endswith("/"):
                    resolved += "/"
                resolved += ("?" + url.query if url.query else "") + ("#" + url.fragment if url.fragment else "")
            content = content.replace("](" + target + ")", "](" + resolved + ")")
        # Inline maps keep their original line count; fenced command bodies stay untouched.
        lines[start:end] = content.splitlines(keepends=True)
    return "".join(lines)


def agent_markdown():
    return public_markdown("docs/setup-agent.md", "setup/agent.md")


def partial(name):
    return (ROOT / "site" / name).read_text().replace("@@BASE@@", BASE)


def demo(name):
    clip = DEMO_CLIPS[name]
    provenance = desktop_demo_provenance()
    record = next(item for item in provenance["clips"] if item["id"] == name)
    versions = record.get("source_versions", provenance["source_versions"])
    video = link("docs/tour.md", "../" + clip["video"])
    poster = link("docs/tour.md", "../" + clip["poster"])
    capture_label = escape(provenance["capture_label"])
    codec = "H.264" if record["video_codec"].lower() == "h264" else record["video_codec"]
    file_records = {item["path"]: item for item in json.loads((ROOT / "assets/provenance.json").read_text())["files"]}
    video_hash = file_records[clip["video"]]["sha256"]
    poster_hash = file_records[clip["poster"]]["sha256"]
    if record.get("source_capture_sha256"):
        source_details = f'<li>Raw source capture SHA-256: <code>{escape(record["source_capture_sha256"])}</code>.</li>'
    else:
        source_details = "".join(
            f'<li><code>{escape(source["path"])}</code>, source SHA-256 <code>{escape(source["sha256"])}</code>, seconds {source["trim_range_seconds"][0]}–{source["trim_range_seconds"][1]}.</li>'
            for source in record["source_captures"]
        )
    steps = "".join(f"<li>{escape(step)}</li>" for step in clip["steps"])
    processing_notes = "".join(f"<li>{escape(note)}</li>" for note in record["processing_notes"])
    receipt_path = provenance["capture_receipt_path"].removeprefix("docs/")
    receipt_link = link("docs/tour.md", receipt_path)
    setup_links = " · ".join(
        f'<a href="{escape(link("docs/tour.md", target), quote=True)}">{escape(label)}</a>'
        for label, target in clip["setup"]
    )
    return f'''<figure class="native-demo" id="{clip['id']}" data-native-demo="{name}">
  <video class="native-demo-video" controls preload="none" playsinline width="{record['width']}" height="{record['height']}" poster="{poster}" aria-label="{escape(clip['title'], quote=True)} video" aria-describedby="{clip['id']}-summary">
    <source src="{video}" type="video/mp4">
    <a class="native-demo-fallback" href="{video}"><img src="{poster}" width="{record['width']}" height="{record['height']}" alt="{escape(clip['title'], quote=True)} poster; open the video file to play the native desktop recording">Open or download the video.</a>
  </video>
  <figcaption class="native-demo-caption" id="{clip['id']}-summary">
    <p class="eyebrow">{capture_label}</p>
    <h3>{escape(clip['title'])}</h3>
    <p>{escape(clip['description'])}</p>
    <p class="native-demo-fixture">Sample content and guest readings: {escape(record['fixture_label'])}</p>
    <p class="native-demo-duration">{record['duration_seconds']} seconds · Captured {escape(record['capture_date'])} · Components {escape(versions['components']['version'])}</p>
    <ol class="native-demo-steps">{steps}</ol>
    <p class="native-demo-links"><span>Setup:</span> {setup_links} <span class="native-demo-provenance">· <a class="native-demo-download" href="{escape(video, quote=True)}">Open or download MP4</a> · <a href="{BASE}assets/provenance.json">Media provenance</a> · <a href="{escape(receipt_link, quote=True)}">Capture receipt</a></span></p>
    <details class="native-demo-details">
      <summary>Capture details</summary>
      <p>Captured {escape(record['capture_date'])}{' · exact-byte reused pilot scene' if record.get('reuse_reason') else ''}. Silent {escape(codec)}/{escape(record['pixel_format'])}, {record['width']}×{record['height']}, {record['frame_count']} decoded frames at {escape(str(record['average_frame_rate']))} fps.</p>
      <p>Output SHA-256: <code>{escape(video_hash)}</code>. Poster SHA-256: <code>{escape(poster_hash)}</code>.</p>
      {f'<p>Reuse reason: {escape(record["reuse_reason"])}</p>' if record.get('reuse_reason') else ''}
      <ul>{source_details}</ul>
      <p>Processing notes:</p>
      <ul>{processing_notes}</ul>
      <p>Review status: agent {escape(record['agent_review'])}; automated {escape(record['automated_review'])}; human {escape(record['human_review'])}.</p>
    </details>
  </figcaption>
</figure>'''


def panel():
    return f'''<figure class="panel-shot"><div class="media-label"><span>Native SwayNC fork</span><span>Actual rendering ↗</span></div><a class="panel-frame" href="{BASE}assets/panel.png" aria-label="Open the full isolated SwayNC screenshot" style="display:block"><img src="{BASE}assets/panel.png" alt="System, Network, and Bluetooth cards in the actual SwayNC fork" width="1280" height="800" loading="lazy"></a><figcaption>Actual fork in an isolated session, using its default theme. Sample wireless/GPU values; local CPU/RAM. Battery hides on this hardware. <a href="{BASE}assets/provenance.json">Media source</a>.</figcaption></figure>'''


def snapshot():
    data = json.loads((ROOT / "data/setup.json").read_text())
    fork = data["swaync"]
    deployment = data["deployment"]
    hosts = ", ".join(deployment["rollout_order"])
    summary = deployment.get("summary", "Scoped delivery passed; normal-use visual and device checks remain.")
    return f'''<div class="snapshot"><div><span class="eyebrow">Managed desktop / {escape(data['date'])}</span><strong>Neutral Slate · {escape(hosts)}</strong><p>{escape(summary)}</p></div><dl><div><dt>Components</dt><dd>{escape(data['component_version'])} · <code>{data['producer_revision'][:10]}</code></dd></div><div><dt>Consumer</dt><dd><code>{data['consumer_revision'][:10]}</code></dd></div><div><dt>SwayNC fork</dt><dd>{escape(fork['package'])} {escape(fork['version'])}</dd></div></dl><a href="{BASE}data/setup.json">Full delivery record ↗</a></div>'''


def render_markdown(source):
    text = (ROOT / source).read_text()
    parser = MarkdownIt("commonmark", {"html": False}).enable("table")
    enhancements = {}
    pattern = re.compile(r"^<!-- niri-plus:([a-z-]+) -->\n(.*?)\n<!-- /niri-plus:\1 -->$", re.M | re.S)

    def slot(match):
        name, fallback = match.groups()
        if name not in {"workbench", "architecture", "keys", "snapshot", "panel", "overview", "gallery", "palette", "typography", "contrast", *(f"demo-{clip}" for clip in DEMO_CLIPS)} or name in enhancements.values():
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
    if source == "docs/setup.md":
        body = body.replace(f'<a href="{BASE}setup/agent/">Set up with an agent</a>',
                            f'<a class="button" href="{BASE}setup/agent/">Set up with an agent</a>', 1)
    replacements = {"workbench": partial("workbench.html"), "architecture": partial("architecture.html"), "snapshot": snapshot(), "panel": panel(), "overview": partial("identity-overview.html"), "gallery": identity_gallery(), "palette": identity_palette(), "typography": identity_typography(), "contrast": contrast_html()}
    replacements.update({f"demo-{name}": demo(name) for name in DEMO_CLIPS})
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
    audience = {"docs/story.md": "Personal story", "docs/setup.md": "Setup overview", "docs/setup-agent.md": "Agent instructions"}.get(source, "Desktop guide")
    next_route, next_label = ("setup/agent/", "Set up with an agent") if source == "docs/setup.md" else ("setup/", "Setup overview")
    body = f'<div class="wrap document-layout"><aside class="on-this-page" aria-label="On this page"><span class="aside-label">{"The story" if source == "docs/story.md" else "On this page"}</span>{toc}</aside><article class="prose"><p class="eyebrow">Niri Plus / {audience}</p>{body}<div class="article-end"><a href="{BASE}{next_route}">{next_label} →</a><a href="https://github.com/byebyebryan/niri-plus/blob/main/{source}">Read on GitHub ↗</a></div></article></div>'
    return title, body


def shell(route, title, description, body):
    navigation = []
    for target, label in [("story/", "Story"), ("tour/", "Tour"), ("design/", "Design"), ("setup/", "Setup"), ("reference/", "Reference")]:
        current = "page" if route == target else "location" if target == "setup/" and route.startswith("setup/") else None
        selected = f' aria-current="{current}"' if current else ""
        navigation.append(f'<a href="{BASE}{target}"{selected}>{label}</a>')
    navigation = ''.join(navigation)
    page_assets = f'<link rel="stylesheet" href="{BASE}assets/contrast.css"><script defer src="{BASE}assets/contrast.js"></script>' if route == "design/contrast/" else ""
    if route == "setup/agent/":
        page_assets += f'<link rel="alternate" type="text/markdown" href="{BASE}setup/agent.md">'
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
        for attribute in ("src", "href", "poster"):
            if attrs.get(attribute):
                self.links.append(attrs[attribute])
        if tag == "img" and not attrs.get("alt"):
            raise ValueError("image is missing alt text")


def validate(output):
    validate_desktop_demo_sources()
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
    if (output / "setup/agent.md").read_text() != agent_markdown():
        raise ValueError("agent Markdown differs from its detailed source")
    for name in sorted(PUBLIC_LOCAL_DOCS):
        if not name.endswith(".md"):
            continue
        text = (output / name).read_text()
        if text != public_markdown(name, name, repository_links=True):
            raise ValueError(f"public Markdown differs from source: {name}")
        for token in MarkdownIt("commonmark").enable("table").parse(text):
            for child in token.children or []:
                if child.type != "link_open":
                    continue
                url = urlsplit(urljoin(SITE + name, child.attrGet("href")))
                if url.netloc != urlsplit(SITE).netloc or not url.path.startswith(BASE):
                    continue
                dest = unquote(url.path[len(BASE):])
                dest += "index.html" if not dest or dest.endswith("/") else ""
                if dest not in actual:
                    raise ValueError(f"{name}: missing Markdown target {url.geturl()}")
                if url.fragment and dest in pages and unquote(url.fragment) not in pages[dest].ids:
                    raise ValueError(f"{name}: missing Markdown anchor {url.geturl()}")
                links += 1
    return {"pages": len(pages), "files": len(actual), "local_links": links}


def portable_links(content, parent):
    """Rewrite public-path media and navigation attributes for review snapshots."""
    def relative(match):
        target = match[2][len(BASE):]
        url = urlsplit(target)
        path = posixpath.relpath(url.path or ".", parent)
        if not url.path or url.path.endswith("/"):
            path += "/"
        suffix = ("?" + url.query if url.query else "") + ("#" + url.fragment if url.fragment else "")
        return match[1] + '="' + path + suffix + '"'

    return re.sub(r'(href|src|poster)="(' + re.escape(BASE) + r'[^\"]*)"', relative, content)


def build(output, portable=False):
    output = output.absolute()
    if output.is_symlink() or output.resolve() in {ROOT, ROOT.parent}:
        raise ValueError("unsafe output path")
    if output.resolve().is_relative_to(ROOT) and output.resolve() != ROOT / "dist":
        raise ValueError("only dist may be used as an in-checkout output")
    if output.exists() and any(output.iterdir()):
        raise ValueError("output must be empty; choose a new directory")
    validate_desktop_demo_sources()
    output.mkdir(parents=True, exist_ok=True)
    identity = working_identity()
    fonts = json.loads((ROOT / "design/assets/provenance.json").read_text())
    examples = json.loads((ROOT / "examples/manifest.json").read_text())
    generated = {"data/identity.json": json.dumps(identity, indent=2) + "\n", "data/contrast-study.json": json.dumps(contrast_study(), indent=2) + "\n", "assets/identity.css": identity_css(identity), "examples/kitty/neutral-slate.conf": kitty_fragment(identity), "examples/manifest.json": json.dumps(examples, indent=2) + "\n", "assets/fonts/provenance.json": json.dumps({"files": [item for item in fonts["files"] if item["path"] in FONT_ASSETS]}, indent=2) + "\n"}
    generated["setup/agent.md"] = agent_markdown()
    for name in public_files():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if name in generated:
            target.write_text(generated[name])
            continue
        if name in PUBLIC_LOCAL_DOCS and name.endswith(".md"):
            target.write_text(public_markdown(name, name, repository_links=True))
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
            page.write_text(portable_links(page.read_text(), parent))
    return validate(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--portable", action="store_true", help="Use relative page links for an independent review snapshot; canonical URLs remain public.")
    args = parser.parse_args()
    print(json.dumps(validate(args.output) if args.validate_only else build(args.output, portable=args.portable), sort_keys=True))
