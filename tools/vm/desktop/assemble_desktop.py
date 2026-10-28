#!/usr/bin/env python3
"""Add the pinned desktop workflow to the retained Niri Plus Arch pilot."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from typing import Any
from urllib.request import Request, urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
VM_TOOLS = SCRIPT_DIR.parent
HOME = Path.home().resolve()
PILOT_ROOT = HOME / ".local/share/niri-plus-vm"
ASSEMBLY_ROOT = PILOT_ROOT / "desktop"
RECEIPT_PATH = ASSEMBLY_ROOT / "assembly-receipt.json"
RECOVERY_ROOT = HOME / ".local/state/niri-plus-vm/desktop-recovery"
PILOT_PINS_PATH = VM_TOOLS / "pins.json"
SWAYNC_PINS_PATH = SCRIPT_DIR / "swaync-pins.json"
MAX_RECIPE_ARCHIVE = 32 * 1024 * 1024
REFERENCE_DESKTOP_PATH = (
    "/home/demo/.local/bin:"
    "/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/bin/site_perl:"
    "/usr/bin/vendor_perl:/usr/bin/core_perl"
)

PACKAGE_NAMES = (
    "adw-gtk-theme",
    "ark",
    "base-devel",
    "bluez",
    "bluez-utils",
    "breeze",
    "breeze-cursors",
    "breeze-icons",
    "cliphist",
    "desktop-file-utils",
    "dconf",
    "dolphin",
    "gtk4",
    "gtk4-layer-shell",
    "gwenview",
    "granite7",
    "glib2",
    "gtk3",
    "gsettings-desktop-schemas",
    "json-glib",
    "libadwaita",
    "libgee",
    "libnotify",
    "libpulse",
    "mpv",
    "neovim",
    "networkmanager",
    "pavucontrol",
    "pipewire",
    "pipewire-pulse",
    "qt5-wayland",
    "qt5ct",
    "qt6-wayland",
    "qt6ct",
    "shared-mime-info",
    "udisks2",
    "wl-clipboard",
    "wireplumber",
    "xdg-desktop-portal",
    "xdg-desktop-portal-gtk",
    "xdg-desktop-portal-wlr",
)

RUNTIME_BUILD_DEPENDENCIES = (
    "gtk4",
    "gtk4-layer-shell",
    "libadwaita",
    "glib2",
    "libgee",
    "json-glib",
    "libpulse",
    "granite7",
)

MIME_ASSOCIATIONS = {
    "x-scheme-handler/http": "google-chrome.desktop",
    "x-scheme-handler/https": "google-chrome.desktop",
    "text/html": "google-chrome.desktop",
    "application/xhtml+xml": "google-chrome.desktop",
    "application/pdf": "google-chrome.desktop",
    "inode/directory": "org.kde.dolphin.desktop",
    "image/png": "org.kde.gwenview.desktop",
    "image/jpeg": "org.kde.gwenview.desktop",
    "image/webp": "org.kde.gwenview.desktop",
    "image/gif": "org.kde.gwenview.desktop",
    "image/avif": "org.kde.gwenview.desktop",
    "image/heif": "org.kde.gwenview.desktop",
    "image/bmp": "org.kde.gwenview.desktop",
    "image/tiff": "org.kde.gwenview.desktop",
    "image/svg+xml": "org.kde.gwenview.desktop",
    "video/mp4": "mpv.desktop",
    "video/x-matroska": "mpv.desktop",
    "video/webm": "mpv.desktop",
    "video/quicktime": "mpv.desktop",
    "video/x-msvideo": "mpv.desktop",
    "video/mpeg": "mpv.desktop",
    "audio/mpeg": "mpv.desktop",
    "audio/flac": "mpv.desktop",
    "audio/ogg": "mpv.desktop",
    "audio/opus": "mpv.desktop",
    "audio/x-wav": "mpv.desktop",
    "audio/aac": "mpv.desktop",
    "audio/mp4": "mpv.desktop",
    "application/zip": "org.kde.ark.desktop",
    "application/x-tar": "org.kde.ark.desktop",
    "application/x-7z-compressed": "org.kde.ark.desktop",
    "application/vnd.rar": "org.kde.ark.desktop",
    "application/x-rar-compressed": "org.kde.ark.desktop",
    "application/gzip": "org.kde.ark.desktop",
    "application/x-bzip2": "org.kde.ark.desktop",
    "application/x-xz": "org.kde.ark.desktop",
    "application/zstd": "org.kde.ark.desktop",
    "text/plain": "niri-plus-neovim.desktop",
    "text/markdown": "niri-plus-neovim.desktop",
    "application/json": "niri-plus-neovim.desktop",
    "text/csv": "niri-plus-neovim.desktop",
    "text/x-python": "niri-plus-neovim.desktop",
    "text/x-shellscript": "niri-plus-neovim.desktop",
}


class AssemblyError(RuntimeError):
    pass


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=check,
    )


def require_guest() -> None:
    result = subprocess.run([str(VM_TOOLS / "guest-guard.sh")], text=True, capture_output=True)
    if result.returncode:
        sys.stderr.write(result.stderr or result.stdout)
        raise SystemExit(result.returncode)


def require_arch_demo() -> None:
    if os.geteuid() == 0 or os.environ.get("USER") != "demo":
        raise AssemblyError("run the desktop assembler as the ordinary demo user, not root")
    if HOME != Path("/home/demo") or Path(os.environ.get("HOME", "")).resolve() != HOME:
        raise AssemblyError("the desktop assembler is scoped to the retained demo account")
    release = {}
    for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            release[key] = value.strip().strip('"')
    if release.get("ID") != "arch" or os.uname().machine != "x86_64":
        raise AssemblyError("expected x86_64 Arch Linux")
    if os.environ.get("XDG_CONFIG_HOME", str(HOME / ".config")) != str(HOME / ".config"):
        raise AssemblyError("the retained pilot uses the ordinary ~/.config path")
    if os.environ.get("XDG_DATA_HOME", str(HOME / ".local/share")) != str(HOME / ".local/share"):
        raise AssemblyError("the retained pilot uses the ordinary ~/.local/share path")


def require_active_session() -> None:
    for unit in ("niri.service", "graphical-session.target"):
        state = run(["systemctl", "--user", "is-active", unit], capture=True, check=False)
        if state.returncode or state.stdout.strip() != "active":
            detail = (state.stdout or state.stderr).strip()
            raise AssemblyError(f"{unit} must be active in the demo graphical session ({detail or 'inactive'})")


def user_service_state(unit: str) -> str:
    result = run(["systemctl", "--user", "is-active", unit], capture=True, check=False)
    if result.returncode == 0:
        return result.stdout.strip()
    detail = result.stdout.strip()
    if detail in {"inactive", "failed", "activating", "deactivating"}:
        return detail
    if "could not be found" in result.stderr.lower() or "not found" in result.stderr.lower():
        return "not-found"
    raise AssemblyError(f"cannot inspect user service {unit}: {(result.stderr or detail).strip()}")


def normalized_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or ".." in path.parts or "." in path.parts:
        raise AssemblyError(f"unsafe managed path: {value!r}")
    return path


def ensure_no_symlink_ancestors(path: Path, *, allow_symlink_leaf: bool = False) -> None:
    if not path.is_absolute() or not path.is_relative_to(HOME):
        raise AssemblyError(f"managed path escapes demo home: {path}")
    if path.is_symlink() and not allow_symlink_leaf:
        raise AssemblyError(f"managed path is a symlink: {path}")
    if not (allow_symlink_leaf and path.is_symlink()) and not path.resolve(strict=False).is_relative_to(HOME):
        raise AssemblyError(f"managed path escapes demo home: {path}")
    current = HOME
    for component in path.relative_to(HOME).parts[:-1]:
        current /= component
        if current.is_symlink():
            raise AssemblyError(f"managed parent is a symlink: {current}")
        if current.exists() and not current.is_dir():
            raise AssemblyError(f"managed parent is not a directory: {current}")


def load_pilot_pins() -> dict[str, Any]:
    try:
        pins = json.loads(PILOT_PINS_PATH.read_text(encoding="utf-8"))
        if pins.get("schema_version") != 1 or pins.get("components", {}).get("version") != "0.3.1":
            raise AssemblyError("unsupported retained pilot input tuple")
        return pins
    except (OSError, json.JSONDecodeError) as error:
        raise AssemblyError(f"cannot read retained pilot pins: {error}") from error


def load_swaync_pins() -> dict[str, Any]:
    try:
        pins = json.loads(SWAYNC_PINS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AssemblyError(f"cannot read the SwayNC pin record: {error}") from error
    if pins.get("schema_version") != 1:
        raise AssemblyError("unsupported SwayNC pin schema")
    for field in (
        "recipe_revision",
        "recipe_archive_sha256",
        "source_revision",
        "source_archive_sha256",
    ):
        value = pins.get(field, "")
        if not re.fullmatch(r"[0-9a-f]{40}" if field.endswith("revision") else r"[0-9a-f]{64}", value):
            raise AssemblyError(f"invalid SwayNC pin: {field}")
    if pins.get("package") != "swaync-bryan" or pins.get("version") != "0.12.6-15":
        raise AssemblyError("SwayNC package pin does not match the accepted fork release")
    return pins


def import_pilot_assembler():
    module_path = VM_TOOLS / "bootstrap_guest.py"
    spec = importlib.util.spec_from_file_location("niri_plus_vm_bootstrap", module_path)
    if spec is None or spec.loader is None:
        raise AssemblyError("cannot load the retained pilot config assembler")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_pilot(pins: dict[str, Any]) -> tuple[dict[str, Any], bytes, bytes, bytes]:
    if PILOT_ROOT.is_symlink() or not PILOT_ROOT.is_dir():
        raise AssemblyError(f"retained pilot tree is missing or unsafe: {PILOT_ROOT}")
    receipt_path = PILOT_ROOT / "setup-receipt.json"
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise AssemblyError("the retained pilot setup receipt is missing or unsafe")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise AssemblyError("the retained pilot receipt is invalid JSON") from error

    public_inputs = receipt.get("public_inputs", {})
    if public_inputs.get("components") != pins.get("components"):
        raise AssemblyError("retained pilot receipt uses a different component bundle pin")
    if public_inputs.get("identity") != pins.get("identity"):
        raise AssemblyError("retained pilot receipt uses a different appearance identity")
    if public_inputs.get("public_source", {}).get("commit") != pins.get("public_source", {}).get("commit"):
        raise AssemblyError("retained pilot receipt uses a different public source commit")
    if receipt.get("guest", {}).get("hostname") != "niri-plus-arch":
        raise AssemblyError("retained pilot receipt names a different guest")

    # The setup receipt is the authority for the frozen public inputs. Reject
    # altered files instead of silently rendering from a changed pilot tree.
    for item in receipt.get("files", []):
        relative = normalized_relative(item.get("path", ""))
        path = PILOT_ROOT.joinpath(*relative.parts)
        if path.is_symlink():
            if item.get("type") != "symlink" or os.readlink(path) != item.get("target"):
                raise AssemblyError(f"retained pilot symlink changed: {path}")
        elif not path.is_file() or item.get("type") != "file":
            raise AssemblyError(f"retained pilot input is missing or has changed type: {path}")
        elif sha256(path.read_bytes()) != item.get("sha256"):
            raise AssemblyError(f"retained pilot input hash changed: {path}")
        elif stat.S_IMODE(path.stat().st_mode) != item.get("mode"):
            raise AssemblyError(f"retained pilot input mode changed: {path}")

    appearance_manifest_path = PILOT_ROOT / "appearance/manifest.json"
    component_manifest = load_component_manifest()
    appearance_manifest = json.loads(appearance_manifest_path.read_text(encoding="utf-8"))
    if component_manifest.get("version") != "0.3.1" or component_manifest.get("api_version") != 1:
        raise AssemblyError("retained desktop component manifest has an unexpected version")
    if appearance_manifest.get("renderer_version") != "0.3.1":
        raise AssemblyError("retained appearance was rendered by a different component version")
    if appearance_manifest.get("identity_sha256") != pins["identity"]["sha256"]:
        raise AssemblyError("retained appearance uses a different identity hash")

    component_records = {record["path"]: record for record in component_manifest.get("files", [])}
    needed_components = (
        "components/desktop/bin/desktop-session-menu",
        "components/desktop/bin/desktop-session-ready",
        "components/desktop/bin/rofi-clipboard",
        "components/desktop/config/cliphist/config",
        "components/desktop/share/applications/niri-plus-audio.desktop",
        "components/desktop/share/applications/niri-plus-bluetooth.desktop",
        "components/desktop/share/applications/niri-plus-network.desktop",
        "components/desktop/share/applications/niri-plus-session.desktop",
        "components/desktop/systemd/user/clipboard-history@.service",
    )
    for relative in needed_components:
        record = component_records.get(relative)
        path = PILOT_ROOT / relative
        if record is None or not path.is_file() or path.is_symlink() or sha256(path.read_bytes()) != record.get("sha256"):
            raise AssemblyError(f"required public desktop component is missing or changed: {relative}")
    appearance_records = {record["path"]: record for record in appearance_manifest.get("files", [])}
    swaync_style_record = appearance_records.get("swaync.css")
    swaync_style_path = PILOT_ROOT / "appearance/swaync.css"
    if (
        swaync_style_record is None
        or not swaync_style_path.is_file()
        or swaync_style_path.is_symlink()
        or sha256(swaync_style_path.read_bytes()) != swaync_style_record.get("sha256")
    ):
        raise AssemblyError("selected SwayNC appearance is missing or changed")

    source_config = PILOT_ROOT / "source-assets/examples/niri/config.kdl"
    source_portal = PILOT_ROOT / "source-assets/examples/portals/niri-portals.conf"
    base_config = source_config.read_text(encoding="utf-8")
    theme = json.loads((PILOT_ROOT / "appearance/theme.json").read_text(encoding="utf-8"))
    pilot_module = import_pilot_assembler()
    pilot_niri = pilot_module.assemble_niri_config(base_config, theme).encode("utf-8")
    expected_pilot_digest = receipt.get("managed_home_targets", {}).get(".config/niri/config.kdl")
    if expected_pilot_digest != sha256(pilot_niri):
        raise AssemblyError("retained pilot receipt does not match its generated Niri config")

    portal_bytes = source_portal.read_bytes()
    portal_target = HOME / ".config/xdg-desktop-portal/niri-portals.conf"
    ensure_no_symlink_ancestors(portal_target)
    portal_digest = receipt.get("managed_home_targets", {}).get(".config/xdg-desktop-portal/niri-portals.conf")
    if (
        not portal_target.is_file()
        or portal_target.is_symlink()
        or portal_target.read_bytes() != portal_bytes
        or portal_digest != sha256(portal_bytes)
        or b"org.freedesktop.impl.portal.FileChooser=gtk;" not in portal_bytes
        or b"org.freedesktop.impl.portal.ScreenCast=wlr;" not in portal_bytes
    ):
        raise AssemblyError("GTK/WLR portal routing drifted from the admitted pilot configuration")
    return receipt, pilot_niri, portal_bytes, swaync_style_path.read_bytes()


def validate_niri_config(payload: bytes) -> None:
    with tempfile.NamedTemporaryFile(prefix="niri-plus-desktop-", suffix=".kdl", delete=False) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    try:
        run(["niri", "validate", "--config", str(temporary)], capture=True)
    finally:
        temporary.unlink(missing_ok=True)


def assemble_niri(pilot_niri: bytes) -> bytes:
    text = pilot_niri.decode("utf-8")
    anchor = '    Mod+D { spawn "rofi" "-show" "drun"; }\n'
    if text.count(anchor) != 1:
        raise AssemblyError("the admitted pilot Niri launcher binding has changed")
    for key in ("Mod+E", "Mod+N", "Mod+Y"):
        if re.search(rf"(?m)^\s*{re.escape(key)}(?:\s|\{{)", text):
            raise AssemblyError(f"the admitted pilot Niri config unexpectedly defines {key}")
    additions = (
        anchor
        + '    Mod+E { spawn "dolphin"; }\n'
        + '    Mod+N repeat=false { spawn "swaync-client" "-t" "-sw"; }\n'
        + '    Mod+Y repeat=false { spawn "rofi-clipboard"; }\n'
    )
    text = text.replace(anchor, additions, 1)
    appearance_anchor = "prefer-no-csd\n"
    if text.count(appearance_anchor) != 1 or "\nenvironment {" in text or "\ncursor {" in text:
        raise AssemblyError("the admitted pilot Niri top-level appearance section has changed")
    appearance = (
        appearance_anchor
        + "environment {\n"
        + '    QT_QPA_PLATFORMTHEME "qt5ct:qt6ct"\n'
        + '    GTK_THEME "adw-gtk3-dark"\n'
        + f'    PATH "{REFERENCE_DESKTOP_PATH}"\n'
        + "}\n"
        + "cursor {\n"
        + '    xcursor-theme "breeze_cursors"\n'
        + "    xcursor-size 24\n"
        + "}\n"
    )
    return text.replace(appearance_anchor, appearance, 1).encode("utf-8")


def mimeapps_bytes() -> bytes:
    rows = ["[Default Applications]"]
    rows.extend(f"{mime}={application}" for mime, application in MIME_ASSOCIATIONS.items())
    return ("\n".join(rows) + "\n").encode("utf-8")


def gtk_settings_bytes() -> bytes:
    return (
        "[Settings]\n"
        "gtk-theme-name=adw-gtk3-dark\n"
        "gtk-icon-theme-name=breeze-dark\n"
        "gtk-cursor-theme-name=breeze_cursors\n"
        "gtk-cursor-theme-size=24\n"
        "gtk-font-name=Noto Sans 11\n"
    ).encode("utf-8")


def qt_config_bytes(version: int, palette_path: Path, *, fonts: dict[str, Any]) -> bytes:
    style = "Fusion" if version == 5 else "Breeze"
    general_font = f"{fonts['ui_font']},{fonts['ui_pt']},-1,5,50,0,0,0,0,0"
    fixed_font = f"{fonts['mono_font']},{fonts['terminal_pt']},-1,5,50,0,0,0,0,0"
    return (
        "[Appearance]\n"
        f"color_scheme_path={palette_path}\n"
        "custom_palette=true\n"
        "icon_theme=breeze-dark\n"
        f"style={style}\n"
        "\n"
        "[Fonts]\n"
        f'fixed="{fixed_font}"\n'
        f'general="{general_font}"\n'
    ).encode("utf-8")


def kdeglobals_bytes() -> bytes:
    path = PILOT_ROOT / "appearance/kdeglobals-managed.json"
    if path.is_symlink() or not path.is_file():
        raise AssemblyError("generated KDE appearance values are missing")
    managed = json.loads(path.read_text(encoding="utf-8"))
    rows: list[str] = []
    for section, values in managed.items():
        rows.append(f"[{section}]")
        for key, value in values.items():
            if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                raise AssemblyError(f"unsupported generated KDE value for {section}/{key}")
            rows.append(f"{key}={value}")
        rows.append("")
    return ("\n".join(rows)).encode("utf-8")


def niri_ready_dropin() -> bytes:
    return (
        "[Unit]\n"
        "After=graphical-session.target\n"
        "PartOf=graphical-session.target\n"
        "Requisite=graphical-session.target\n"
    ).encode("utf-8")


def load_component_manifest() -> dict[str, Any]:
    path = PILOT_ROOT / "manifest.json"
    if path.is_symlink() or not path.is_file():
        raise AssemblyError(f"retained public component manifest is missing or unsafe: {path}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise AssemblyError(f"retained public component manifest is invalid JSON: {path}") from error
    if not isinstance(manifest, dict):
        raise AssemblyError(f"retained public component manifest has an invalid shape: {path}")
    return manifest


def component_files() -> dict[str, tuple[bytes, int]]:
    manifest = load_component_manifest()
    records = {item["path"]: item for item in manifest.get("files", [])}
    mapping = {
        "components/desktop/bin/desktop-session-menu": ".local/bin/desktop-session-menu",
        "components/desktop/bin/desktop-session-ready": ".local/bin/desktop-session-ready",
        "components/desktop/bin/rofi-clipboard": ".local/bin/rofi-clipboard",
        "components/desktop/config/cliphist/config": ".config/cliphist/config",
        "components/desktop/share/applications/niri-plus-audio.desktop": ".local/share/applications/niri-plus-audio.desktop",
        "components/desktop/share/applications/niri-plus-bluetooth.desktop": ".local/share/applications/niri-plus-bluetooth.desktop",
        "components/desktop/share/applications/niri-plus-network.desktop": ".local/share/applications/niri-plus-network.desktop",
        "components/desktop/share/applications/niri-plus-session.desktop": ".local/share/applications/niri-plus-session.desktop",
        "components/desktop/systemd/user/clipboard-history@.service": ".config/systemd/user/clipboard-history@.service",
    }
    results: dict[str, tuple[bytes, int]] = {}
    for source_relative, target_relative in mapping.items():
        source_path = PILOT_ROOT / source_relative
        record = records.get(source_relative)
        if record is None:
            raise AssemblyError(f"public component manifest omitted {source_relative}")
        payload = source_path.read_bytes()
        if sha256(payload) != record["sha256"]:
            raise AssemblyError(f"public component changed after pilot verification: {source_relative}")
        results[target_relative] = (payload, record["mode"])
    return results


def appearance_file(name: str) -> bytes:
    manifest = json.loads((PILOT_ROOT / "appearance/manifest.json").read_text(encoding="utf-8"))
    records = {item["path"]: item for item in manifest.get("files", [])}
    record = records.get(name)
    path = PILOT_ROOT / "appearance" / name
    if record is None or path.is_symlink() or not path.is_file():
        raise AssemblyError(f"selected appearance output is missing: {name}")
    payload = path.read_bytes()
    if sha256(payload) != record.get("sha256"):
        raise AssemblyError(f"selected appearance output hash changed: {name}")
    return payload


def planned_targets(pilot_niri: bytes, style: bytes) -> dict[str, tuple[bytes, int]]:
    targets = component_files()
    fonts = json.loads((PILOT_ROOT / "appearance/fonts.json").read_text(encoding="utf-8"))
    targets.update({
        ".config/niri/config.kdl": (assemble_niri(pilot_niri), 0o644),
        ".config/mimeapps.list": (mimeapps_bytes(), 0o644),
        ".config/gtk-3.0/settings.ini": (gtk_settings_bytes(), 0o644),
        ".config/qt5ct/qt5ct.conf": (
            qt_config_bytes(5, HOME / ".config/qt5ct/colors/NeutralSlate.conf", fonts=fonts), 0o644
        ),
        ".config/qt5ct/colors/NeutralSlate.conf": (appearance_file("qt5-palette.conf"), 0o644),
        ".config/qt6ct/qt6ct.conf": (
            qt_config_bytes(6, HOME / ".config/qt6ct/colors/NeutralSlate.conf", fonts=fonts), 0o644
        ),
        ".config/qt6ct/colors/NeutralSlate.conf": (appearance_file("qt6-palette.conf"), 0o644),
        ".config/kdeglobals": (kdeglobals_bytes(), 0o644),
        ".config/swaync/config.json": ((SCRIPT_DIR / "swaync-config.json").read_bytes(), 0o644),
        ".config/swaync/style.css": (style, 0o644),
        ".config/systemd/user/swaync.service.d/niri-plus-session.conf": (niri_ready_dropin(), 0o644),
        ".local/share/color-schemes/NeutralSlate.colors": (appearance_file("NeutralSlate.colors"), 0o644),
        ".local/share/applications/niri-plus-neovim.desktop": ((SCRIPT_DIR / "niri-plus-neovim.desktop").read_bytes(), 0o644),
        ".local/share/niri-plus-vm/desktop/sample_server.py": ((SCRIPT_DIR / "sample_server.py").read_bytes(), 0o755),
        ".local/share/niri-plus-vm/desktop/sample-site/index.html": ((SCRIPT_DIR / "sample-site/index.html").read_bytes(), 0o644),
        ".local/share/niri-plus-vm/desktop/swaync-pins.json": (SWAYNC_PINS_PATH.read_bytes(), 0o644),
    })
    return targets


def load_recipe_archive(pins: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    url = (
        f"{pins['repository']}/archive/{pins['recipe_revision']}.tar.gz"
    )
    request = Request(url, headers={"User-Agent": "niri-plus-vm-desktop/1"})
    with urlopen(request, timeout=60) as response:
        if not response.geturl().startswith("https://"):
            raise AssemblyError("SwayNC recipe archive redirected outside HTTPS")
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_RECIPE_ARCHIVE:
            raise AssemblyError("SwayNC recipe archive exceeded the size limit")
        archive_bytes = response.read(MAX_RECIPE_ARCHIVE + 1)
    if len(archive_bytes) > MAX_RECIPE_ARCHIVE:
        raise AssemblyError("SwayNC recipe archive exceeded the size limit")
    actual_digest = sha256(archive_bytes)
    if actual_digest != pins["recipe_archive_sha256"]:
        raise AssemblyError("SwayNC recipe archive checksum did not match its pin")

    expected_member = f"SwayNotificationCenter-{pins['recipe_revision']}/packaging/arch/PKGBUILD"
    try:
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
            member = archive.getmember(expected_member)
            if not member.isfile() or member.issym() or member.islnk() or member.size > 256 * 1024:
                raise AssemblyError("pinned SwayNC PKGBUILD is not a regular bounded file")
            stream = archive.extractfile(member)
            if stream is None:
                raise AssemblyError("cannot read the pinned SwayNC PKGBUILD")
            recipe_bytes = stream.read()
    except (tarfile.TarError, KeyError) as error:
        raise AssemblyError(f"cannot extract pinned SwayNC PKGBUILD: {error}") from error

    recipe_text = recipe_bytes.decode("utf-8")
    expected_lines = (
        f"pkgname={pins['package']}",
        "pkgver=0.12.6",
        "pkgrel=15",
        f"_commit={pins['source_revision']}",
        f"sha256sums=('{pins['source_archive_sha256']}')",
    )
    for expected in expected_lines:
        if expected not in recipe_text:
            raise AssemblyError(f"pinned SwayNC recipe is missing expected declaration: {expected}")
    return recipe_bytes, {
        "url": url,
        "revision": pins["recipe_revision"],
        "archive_sha256": actual_digest,
        "pkgbuild_sha256": sha256(recipe_bytes),
        "source_revision": pins["source_revision"],
        "source_archive_sha256": pins["source_archive_sha256"],
    }


def installed_package_version(package: str) -> str | None:
    result = run(["pacman", "-Q", package], capture=True, check=False)
    if result.returncode:
        if "was not found" in result.stderr or "not found" in result.stderr:
            return None
        if "no package" in result.stderr:
            return None
        return None
    parts = result.stdout.strip().split(maxsplit=1)
    return parts[1] if len(parts) == 2 else None


def package_versions(names: tuple[str, ...] = PACKAGE_NAMES + ("swaync-bryan",)) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in names:
        value = installed_package_version(name)
        if value is None:
            raise AssemblyError(f"required package is missing after setup: {name}")
        result[name] = value
    return result


def require_no_pending_upgrade() -> None:
    result = run(["pacman", "-Qu"], capture=True, check=False)
    if result.returncode not in (0, 1):
        raise AssemblyError(f"cannot inspect the Arch upgrade state: {result.stderr.strip()}")
    if result.stdout.strip():
        first = result.stdout.strip().splitlines()[0]
        raise AssemblyError(
            "the guest has pending Arch package upgrades; finish a separately reviewed full upgrade before this incremental assembly "
            f"(first pending package: {first})"
        )


def build_and_install_swaync(pins: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
    recipe_bytes, recipe_receipt = load_recipe_archive(pins)
    with tempfile.TemporaryDirectory(prefix="niri-plus-swaync-") as temporary_text:
        work = Path(temporary_text)
        build = work / "build"
        output = work / "packages"
        build.mkdir(mode=0o700)
        output.mkdir(mode=0o700)
        (build / "PKGBUILD").write_bytes(recipe_bytes)
        environment = os.environ.copy()
        environment["PKGDEST"] = str(output)
        print("Building the verified public SwayNC fork as demo.", flush=True)
        run(["makepkg", "--syncdeps", "--rmdeps", "--noconfirm", "--cleanbuild"], cwd=build, env=environment)
        candidates = sorted(output.glob(f"{pins['package']}-{pins['version']}-*.pkg.tar.*"))
        if len(candidates) != 1 or candidates[0].is_symlink():
            raise AssemblyError(f"expected one runtime {pins['package']} package, found {len(candidates)}")
        package_path = candidates[0]
        info = run(["pacman", "-Qip", str(package_path)], capture=True).stdout
        fields = {}
        for line in info.splitlines():
            if ":" in line:
                name, value = line.split(":", 1)
                fields[name.strip()] = value.strip()
        if fields.get("Name") != pins["package"] or fields.get("Version") != pins["version"]:
            raise AssemblyError("built package metadata does not match the pinned runtime package")
        package_digest = sha256(package_path.read_bytes())
        run(["sudo", "pacman", "-U", "--noconfirm", str(package_path)])
        actual_version = installed_package_version(pins["package"])
        if actual_version != pins["version"]:
            raise AssemblyError(f"installed SwayNC version is {actual_version}, expected {pins['version']}")
        return {**recipe_receipt, "package_sha256": package_digest, "installed_version": actual_version}, recipe_bytes


def atomic_write_new_or_exact(path: Path, payload: bytes, mode: int) -> None:
    ensure_no_symlink_ancestors(path)
    if path.exists():
        if not path.is_file() or path.is_symlink() or path.read_bytes() != payload:
            raise AssemblyError(f"file changed after preflight; refusing to overwrite: {path}")
        if stat.S_IMODE(path.stat().st_mode) != mode:
            raise AssemblyError(f"managed file mode changed after preflight: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=f".{path.name}.niri-plus-", dir=path.parent, delete=False) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    try:
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_replace_preimage(path: Path, payload: bytes, mode: int) -> None:
    ensure_no_symlink_ancestors(path)
    if not path.is_file() or path.is_symlink():
        raise AssemblyError(f"recorded file preimage disappeared before replacement: {path}")
    with tempfile.NamedTemporaryFile(prefix=f".{path.name}.niri-plus-", dir=path.parent, delete=False) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    try:
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def save_json_atomic(path: Path, value: dict[str, Any], mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise AssemblyError(f"refusing a symlink receipt path: {path}")
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with tempfile.NamedTemporaryFile(prefix=f".{path.name}.niri-plus-", dir=path.parent, delete=False) as stream:
        stream.write(data)
        temporary = Path(stream.name)
    try:
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def relative_target(relative: str, *, allow_symlink_leaf: bool = False) -> Path:
    parsed = normalized_relative(relative)
    result = HOME.joinpath(*parsed.parts)
    ensure_no_symlink_ancestors(result, allow_symlink_leaf=allow_symlink_leaf)
    return result


def preflight_targets(targets: dict[str, tuple[bytes, int]], pilot_niri: bytes) -> dict[str, dict[str, Any]]:
    states: dict[str, dict[str, Any]] = {}
    for relative, (expected, mode) in targets.items():
        path = relative_target(relative)
        if path.exists():
            if path.is_symlink() or not path.is_file():
                raise AssemblyError(f"refusing non-regular target: {path}")
            actual = path.read_bytes()
            actual_mode = stat.S_IMODE(path.stat().st_mode)
            if relative == ".config/niri/config.kdl" and actual == pilot_niri and actual_mode == 0o644:
                states[relative] = {"kind": "file", "mode": actual_mode, "sha256": sha256(actual), "admitted_pilot_preimage": True}
            else:
                raise AssemblyError(f"refusing to replace an unrecognized existing target: {path}")
        else:
            states[relative] = {"kind": "absent"}
    return states


def preflight_recovery_backups(target_states: dict[str, dict[str, Any]]) -> None:
    if RECOVERY_ROOT.is_symlink():
        raise AssemblyError(f"desktop recovery root is a symlink: {RECOVERY_ROOT}")
    if RECOVERY_ROOT.exists() and (
        not RECOVERY_ROOT.is_dir() or stat.S_IMODE(RECOVERY_ROOT.stat().st_mode) != 0o700
    ):
        raise AssemblyError("desktop recovery directory exists with unexpected type or permissions")
    for relative, state in target_states.items():
        if state.get("kind") != "file":
            continue
        backup = RECOVERY_ROOT / (sha256(relative.encode("utf-8")) + ".preimage")
        ensure_no_symlink_ancestors(backup)
        if backup.exists():
            target = relative_target(relative)
            if backup.is_symlink() or not backup.is_file() or stat.S_IMODE(backup.stat().st_mode) != 0o600:
                raise AssemblyError(f"desktop preimage backup path is occupied unsafely: {backup}")
            if backup.read_bytes() != target.read_bytes():
                raise AssemblyError(f"desktop preimage backup conflicts with the admitted pilot state: {backup}")


def preflight_session_links_before_packages() -> None:
    links = (
        (".config/systemd/user/niri.service.wants/clipboard-history@text.service", "../clipboard-history@.service"),
        (".config/systemd/user/niri.service.wants/clipboard-history@image.service", "../clipboard-history@.service"),
    )
    for relative, target in links:
        preflight_link(relative_target(relative, allow_symlink_leaf=True), target, allow_existing=False)
    swaync_link = relative_target(".config/systemd/user/niri.service.wants/swaync.service")
    if swaync_link.exists() or swaync_link.is_symlink():
        raise AssemblyError(f"SwayNC session link already exists without this assembly receipt: {swaync_link}")


def preflight_link(path: Path, expected_target: str, *, allow_existing: bool) -> dict[str, Any]:
    ensure_no_symlink_ancestors(path, allow_symlink_leaf=True)
    if not path.exists() and not path.is_symlink():
        return {"target": expected_target, "preexisting": False}
    if path.is_symlink() and os.readlink(path) == expected_target and allow_existing:
        return {"target": expected_target, "preexisting": True}
    raise AssemblyError(f"refusing an existing session link with unknown ownership: {path}")


def symlink_atomic(path: Path, target: str, *, allow_exact: bool) -> bool:
    ensure_no_symlink_ancestors(path, allow_symlink_leaf=True)
    if path.is_symlink():
        if allow_exact and os.readlink(path) == target:
            return False
        raise AssemblyError(f"session link changed after preflight: {path}")
    if path.exists():
        raise AssemblyError(f"session link target is occupied: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(target, path)
    return True


def verify_systemd_unit(payload: bytes, name: str) -> None:
    with tempfile.TemporaryDirectory(prefix="niri-plus-unit-verify-") as temp_text:
        temp = Path(temp_text) / name
        temp.write_bytes(payload)
        run(["systemd-analyze", "--user", "verify", str(temp)], capture=True)


def swaync_unit_path() -> Path:
    result = run(["systemctl", "--user", "show", "--property=FragmentPath", "--value", "swaync.service"], capture=True)
    value = result.stdout.strip()
    path = Path(value)
    if not value or not path.is_absolute() or not path.is_file() or path.is_symlink():
        raise AssemblyError("the pinned SwayNC package did not provide a regular swaync.service")
    if not path.is_relative_to(Path("/usr/lib/systemd/user")) and not path.is_relative_to(Path("/usr/local/lib/systemd/user")):
        raise AssemblyError(f"SwayNC service resolves outside the packaged user-unit paths: {path}")
    return path


def load_existing_receipt(targets: dict[str, tuple[bytes, int]], pins: dict[str, Any]) -> dict[str, Any] | None:
    ensure_no_symlink_ancestors(RECEIPT_PATH)
    if not RECEIPT_PATH.exists():
        if RECEIPT_PATH.is_symlink():
            raise AssemblyError("desktop assembly receipt path is a symlink")
        return None
    if RECEIPT_PATH.is_symlink() or not RECEIPT_PATH.is_file():
        raise AssemblyError("desktop assembly receipt is not a regular file")
    try:
        receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise AssemblyError("desktop assembly receipt is invalid JSON") from error
    if receipt.get("schema_version") != 1 or receipt.get("state") not in {"prepared", "complete"}:
        raise AssemblyError("unsupported desktop assembly receipt")
    if receipt.get("swaync_pins") != pins:
        raise AssemblyError("desktop assembly receipt uses a different SwayNC pin tuple")
    recorded_targets = receipt.get("targets", {})
    if set(recorded_targets) != set(targets):
        raise AssemblyError("desktop assembly receipt target inventory does not match this tool")
    for relative, (expected, mode) in targets.items():
        item = recorded_targets[relative]
        if item.get("sha256") != sha256(expected) or item.get("mode") != mode:
            raise AssemblyError(f"desktop assembly receipt target differs from the current input: {relative}")
        path = relative_target(relative)
        preimage = item.get("preimage", {})
        if preimage.get("kind") == "file":
            backup_relative = normalized_relative(preimage.get("backup", ""))
            backup = HOME.joinpath(*backup_relative.parts)
            if (
                backup.is_symlink()
                or not backup.is_file()
                or stat.S_IMODE(backup.stat().st_mode) != 0o600
                or sha256(backup.read_bytes()) != preimage.get("sha256")
            ):
                raise AssemblyError(f"recorded target preimage backup is missing or changed: {backup}")
        if path.exists():
            if path.is_symlink() or not path.is_file():
                raise AssemblyError(f"managed target changed type after assembly: {path}")
            actual = path.read_bytes()
            actual_mode = stat.S_IMODE(path.stat().st_mode)
            if actual != expected or actual_mode != mode:
                backup_relative = preimage.get("backup")
                backup = HOME / backup_relative if backup_relative else None
                if (
                    receipt.get("state") != "prepared"
                    or preimage.get("kind") != "file"
                    or backup is None
                    or backup.is_symlink()
                    or not backup.is_file()
                    or actual != backup.read_bytes()
                    or actual_mode != preimage.get("mode")
                    or sha256(actual) != preimage.get("sha256")
                ):
                    raise AssemblyError(f"managed target drifted after the prepared assembly: {path}")
        else:
            if receipt.get("state") != "prepared" or preimage.get("kind") != "absent":
                raise AssemblyError(f"admitted preimage disappeared after assembly began: {path}")
    if receipt.get("state") == "complete":
        for relative, item in receipt.get("session_links", {}).items():
            path = relative_target(relative, allow_symlink_leaf=True)
            if item.get("preexisting"):
                continue
            if not path.is_symlink() or os.readlink(path) != item.get("target"):
                raise AssemblyError(f"owned session link changed after assembly: {path}")
    verify_gsettings_snapshot(receipt)
    return receipt


GTK_SCHEMA = "org.gnome.desktop.interface"
GSETTINGS_VALUES = {
    "color-scheme": ("'prefer-dark'", "'prefer-dark'"),
    "gtk-theme": ("'adw-gtk3-dark'", "'adw-gtk3-dark'"),
    "icon-theme": ("'breeze-dark'", "'breeze-dark'"),
    "font-name": ("'Noto Sans 11'", "'Noto Sans 11'"),
    "monospace-font-name": ("'MesloLGS Nerd Font 11'", "'MesloLGS Nerd Font 11'"),
    "cursor-theme": ("'breeze_cursors'", "'breeze_cursors'"),
    "cursor-size": ("24", "24"),
}


def gsettings_snapshot() -> dict[str, dict[str, str]]:
    keys = run(["gsettings", "list-keys", GTK_SCHEMA], capture=True).stdout.splitlines()
    snapshot = {}
    for key, (variant, _expected) in GSETTINGS_VALUES.items():
        if key not in keys:
            raise AssemblyError(f"installed GSettings schema lacks {GTK_SCHEMA}/{key}")
        value = run(["gsettings", "get", GTK_SCHEMA, key], capture=True).stdout.strip()
        snapshot[key] = {"before": value, "expected": variant}
    return snapshot


def verify_gsettings_snapshot(receipt: dict[str, Any]) -> None:
    saved = receipt.get("gsettings", {})
    if set(saved) != set(GSETTINGS_VALUES):
        raise AssemblyError("desktop receipt GSettings inventory differs from this tool")
    for key, state in saved.items():
        current = run(["gsettings", "get", GTK_SCHEMA, key], capture=True).stdout.strip()
        expected = state.get("expected")
        before = state.get("before")
        if current != expected and not (receipt.get("state") == "prepared" and current == before):
            raise AssemblyError(f"GSettings key drifted after assembly began: {GTK_SCHEMA}/{key}")


def apply_gsettings(receipt: dict[str, Any]) -> None:
    verify_gsettings_snapshot(receipt)
    for key, state in receipt["gsettings"].items():
        current = run(["gsettings", "get", GTK_SCHEMA, key], capture=True).stdout.strip()
        if current != state["expected"]:
            run(["gsettings", "set", GTK_SCHEMA, key, state["expected"]], capture=True)


def load_or_capture_gsettings(existing_receipt: dict[str, Any] | None) -> dict[str, dict[str, str]]:
    if existing_receipt is not None:
        verify_gsettings_snapshot(existing_receipt)
        return existing_receipt["gsettings"]
    return gsettings_snapshot()


def ensure_recovery_preimages(target_states: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if RECOVERY_ROOT.is_symlink():
        raise AssemblyError(f"desktop recovery root is a symlink: {RECOVERY_ROOT}")
    if RECOVERY_ROOT.exists():
        if not RECOVERY_ROOT.is_dir() or stat.S_IMODE(RECOVERY_ROOT.stat().st_mode) != 0o700:
            raise AssemblyError("desktop recovery directory exists with unexpected type or permissions")
    else:
        RECOVERY_ROOT.mkdir(parents=True, mode=0o700)
        RECOVERY_ROOT.chmod(0o700)
    result: dict[str, dict[str, Any]] = {}
    for relative, state in target_states.items():
        if state["kind"] == "absent":
            result[relative] = {"kind": "absent"}
            continue
        path = relative_target(relative)
        original = path.read_bytes()
        backup_name = sha256(relative.encode("utf-8")) + ".preimage"
        backup = RECOVERY_ROOT / backup_name
        if backup.exists() or backup.is_symlink():
            if backup.is_symlink() or not backup.is_file() or backup.read_bytes() != original:
                raise AssemblyError(f"desktop preimage backup path is already occupied: {backup}")
        else:
            descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(original)
        result[relative] = {
            "kind": "file",
            "mode": state["mode"],
            "sha256": sha256(original),
            "backup": str(backup.relative_to(HOME)),
            "admitted_pilot_preimage": bool(state.get("admitted_pilot_preimage")),
        }
    return result


def create_receipt(
    pins: dict[str, Any],
    target_states: dict[str, dict[str, Any]],
    swaync_recipe_receipt: dict[str, Any],
    links: dict[str, dict[str, Any]],
    gsettings: dict[str, dict[str, str]],
) -> dict[str, Any]:
    preimages = ensure_recovery_preimages(target_states)
    targets = {}
    for relative, state in target_states.items():
        payload_hash = None
        mode = None
        if state["kind"] != "absent":
            path = relative_target(relative)
            payload_hash = state["sha256"] if state.get("already_expected") else None
            mode = state["mode"]
        targets[relative] = {
            "sha256": None,
            "mode": None,
            "preimage": preimages[relative],
        }
    # The expected payload map is filled below by the caller after preimages
    # are secured and before the first home target is written.
    return {
        "schema_version": 1,
        "state": "prepared",
        "guest": {"hostname": "niri-plus-arch", "account": "demo", "architecture": "x86_64", "distribution": "Arch Linux"},
        "swaync_pins": pins,
        "swaync_recipe": swaync_recipe_receipt,
        "targets": targets,
        "session_links": links,
        "gsettings": gsettings,
        "networking": "NetworkManager package installed only; service/connection ownership remains external to this tool.",
    }


def expected_receipt_targets(receipt: dict[str, Any], targets: dict[str, tuple[bytes, int]]) -> None:
    for relative, (payload, mode) in targets.items():
        receipt["targets"][relative]["sha256"] = sha256(payload)
        receipt["targets"][relative]["mode"] = mode


def verify_target_preimage(item: dict[str, Any], relative: str) -> bool:
    path = relative_target(relative)
    if not path.exists():
        return item.get("preimage", {}).get("kind") == "absent"
    if path.is_symlink() or not path.is_file():
        raise AssemblyError(f"managed target changed type: {path}")
    data = path.read_bytes()
    return (
        item.get("preimage", {}).get("kind") == "file"
        and sha256(data) == item["preimage"].get("sha256")
        and stat.S_IMODE(path.stat().st_mode) == item["preimage"].get("mode")
    )


def apply_targets(receipt: dict[str, Any], targets: dict[str, tuple[bytes, int]]) -> None:
    for relative, (payload, mode) in targets.items():
        path = relative_target(relative)
        item = receipt["targets"][relative]
        if path.exists():
            if path.is_file() and not path.is_symlink() and path.read_bytes() == payload and stat.S_IMODE(path.stat().st_mode) == mode:
                continue
            if not verify_target_preimage(item, relative):
                raise AssemblyError(f"target is neither its recorded preimage nor the expected output: {path}")
            atomic_replace_preimage(path, payload, mode)
        else:
            atomic_write_new_or_exact(path, payload, mode)


def create_session_links(receipt: dict[str, Any], service_path: Path) -> None:
    wants = HOME / ".config/systemd/user/niri.service.wants"
    links = receipt["session_links"]
    for instance in ("text", "image"):
        relative = f".config/systemd/user/niri.service.wants/clipboard-history@{instance}.service"
        item = links[relative]
        created = symlink_atomic(relative_target(relative, allow_symlink_leaf=True), item["target"], allow_exact=True)
        item["created_by_assembly"] = created or not item.get("preexisting", False)
    swaync_relative = ".config/systemd/user/niri.service.wants/swaync.service"
    swaync_item = links[swaync_relative]
    desired_target = str(service_path)
    if swaync_item.get("target") != desired_target:
        if swaync_item.get("preexisting"):
            raise AssemblyError("existing SwayNC session link no longer matches its packaged unit")
        swaync_item["target"] = desired_target
    created = symlink_atomic(
        relative_target(swaync_relative, allow_symlink_leaf=True), desired_target, allow_exact=True
    )
    swaync_item["created_by_assembly"] = created or not swaync_item.get("preexisting", False)
    save_json_atomic(RECEIPT_PATH, receipt)


def stage_recovery_and_receipt(
    pins: dict[str, Any],
    targets: dict[str, tuple[bytes, int]],
    target_states: dict[str, dict[str, Any]],
    links: dict[str, dict[str, Any]],
    swaync_recipe_receipt: dict[str, Any],
    gsettings: dict[str, dict[str, str]],
) -> dict[str, Any]:
    if RECEIPT_PATH.exists():
        if RECEIPT_PATH.is_symlink() or not RECEIPT_PATH.is_file():
            raise AssemblyError("desktop assembly receipt path is occupied")
        receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
        if receipt.get("schema_version") != 1 or receipt.get("swaync_pins") != pins:
            raise AssemblyError("existing desktop assembly receipt does not match this input tuple")
        if receipt.get("gsettings") != gsettings:
            raise AssemblyError("recorded GSettings preimages differ from the current assembly")
        expected_receipt_targets(receipt, targets)
        return receipt
    if ASSEMBLY_ROOT.is_symlink() or (ASSEMBLY_ROOT.exists() and not ASSEMBLY_ROOT.is_dir()):
        raise AssemblyError(f"desktop assembly state path is unsafe: {ASSEMBLY_ROOT}")
    receipt = create_receipt(pins, target_states, swaync_recipe_receipt, links, gsettings)
    expected_receipt_targets(receipt, targets)
    ASSEMBLY_ROOT.mkdir(parents=True, exist_ok=True)
    save_json_atomic(RECEIPT_PATH, receipt)
    return receipt


def session_links_preflight(service_path: Path, existing_receipt: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    root = HOME / ".config/systemd/user/niri.service.wants"
    expected = {
        ".config/systemd/user/niri.service.wants/clipboard-history@text.service": "../clipboard-history@.service",
        ".config/systemd/user/niri.service.wants/clipboard-history@image.service": "../clipboard-history@.service",
        ".config/systemd/user/niri.service.wants/swaync.service": str(service_path),
    }
    result = {}
    for relative, target in expected.items():
        old = existing_receipt.get("session_links", {}).get(relative) if existing_receipt else None
        if old and old.get("target") != target:
            raise AssemblyError(f"recorded session link target changed: {relative}")
        path = relative_target(relative, allow_symlink_leaf=True)
        if path.is_symlink() and existing_receipt is None:
            raise AssemblyError(f"a session link already exists without this tool's ownership receipt: {path}")
        if old and not path.is_symlink() and (
            bool(old.get("preexisting"))
            or (existing_receipt.get("state") == "complete" and bool(old.get("created_by_assembly")))
        ):
            raise AssemblyError(f"recorded session link disappeared after assembly: {path}")
        item = preflight_link(path, target, allow_existing=existing_receipt is not None)
        if old:
            item["preexisting"] = bool(old.get("preexisting"))
        result[relative] = item
    return result


def system_service_state(unit: str) -> str:
    result = run(["systemctl", "is-active", unit], capture=True, check=False)
    if result.returncode == 0:
        return result.stdout.strip()
    value = result.stdout.strip()
    if value in {"inactive", "failed", "activating", "deactivating"}:
        return value
    if "could not be found" in result.stderr.lower() or "not found" in result.stderr.lower():
        return "not-found"
    raise AssemblyError(f"cannot inspect system service {unit}: {(result.stderr or value).strip()}")


def native_provider_snapshot() -> dict[str, str]:
    return {
        "bluetooth.service": system_service_state("bluetooth.service"),
        "pipewire.socket": user_service_state("pipewire.socket"),
        "pipewire-pulse.socket": user_service_state("pipewire-pulse.socket"),
        "wireplumber.service": user_service_state("wireplumber.service"),
    }


def activate_native_services(before: dict[str, str]) -> dict[str, str]:
    if before.get("bluetooth.service") != "active":
        run(["sudo", "systemctl", "enable", "--now", "bluetooth.service"])
    for unit in ("pipewire.socket", "pipewire-pulse.socket", "wireplumber.service"):
        if user_service_state(unit) != "active":
            run(["systemctl", "--user", "start", unit])
    return {
        "bluetooth.service": system_service_state("bluetooth.service"),
        "pipewire.socket": user_service_state("pipewire.socket"),
        "pipewire-pulse.socket": user_service_state("pipewire-pulse.socket"),
        "wireplumber.service": user_service_state("wireplumber.service"),
    }


def verify_effective_mime_defaults() -> None:
    for mime, expected in MIME_ASSOCIATIONS.items():
        result = run(["xdg-mime", "query", "default", mime], capture=True)
        if result.stdout.strip() != expected:
            raise AssemblyError(f"effective MIME default for {mime} is {result.stdout.strip()!r}, expected {expected!r}")


def verify_desktop_entries() -> None:
    identifiers = set(MIME_ASSOCIATIONS.values()) | {
        "niri-plus-audio.desktop",
        "niri-plus-bluetooth.desktop",
        "niri-plus-network.desktop",
        "niri-plus-session.desktop",
    }
    local_applications = HOME / ".local/share/applications"
    for identifier in sorted(identifiers):
        local = local_applications / identifier
        system = Path("/usr/share/applications") / identifier
        if not ((local.is_file() and not local.is_symlink()) or (system.is_file() and not system.is_symlink())):
            raise AssemblyError(f"MIME or launcher desktop ID is not installed: {identifier}")
    for identifier in ("niri-plus-audio.desktop", "niri-plus-bluetooth.desktop", "niri-plus-network.desktop", "niri-plus-session.desktop", "niri-plus-neovim.desktop"):
        path = local_applications / identifier
        run(["desktop-file-validate", str(path)], capture=True)


def install_packages() -> None:
    print("Installing desktop application, portal, clipboard, and SwayNC runtime packages.", flush=True)
    run(["sudo", "pacman", "-S", "--needed", "--noconfirm", *PACKAGE_NAMES])
    missing = [name for name in PACKAGE_NAMES if installed_package_version(name) is None]
    if missing:
        raise AssemblyError("package transaction did not install: " + ", ".join(missing))
    runtime_missing = [name for name in RUNTIME_BUILD_DEPENDENCIES if installed_package_version(name) is None]
    if runtime_missing:
        raise AssemblyError("SwayNC runtime dependencies must be preinstalled before makepkg: " + ", ".join(runtime_missing))


def main() -> int:
    # Identity is checked before package, network, service, or home mutations.
    require_guest()
    require_arch_demo()
    require_active_session()
    pins = load_pilot_pins()
    swaync_pins = load_swaync_pins()
    pilot_receipt, pilot_niri, _portal_bytes, swaync_style = verify_pilot(pins)
    targets = planned_targets(pilot_niri, swaync_style)
    validate_niri_config(targets[".config/niri/config.kdl"][0])
    existing_receipt = load_existing_receipt(targets, swaync_pins)
    if existing_receipt is None:
        target_states = preflight_targets(targets, pilot_niri)
        preflight_recovery_backups(target_states)
        preflight_session_links_before_packages()
        if ASSEMBLY_ROOT.exists():
            if ASSEMBLY_ROOT.is_symlink() or not ASSEMBLY_ROOT.is_dir() or any(ASSEMBLY_ROOT.iterdir()):
                raise AssemblyError("desktop assembly state directory exists without a recognized receipt")
        if user_service_state("swaync.service") == "active":
            raise AssemblyError("SwayNC is already running; stop and review it before the first fork handover")
        for unit in ("clipboard-history@text.service", "clipboard-history@image.service"):
            if user_service_state(unit) == "active":
                raise AssemblyError(f"{unit} is already active; inspect its owner before adding the pilot collector")
        provider_before = native_provider_snapshot()
    else:
        target_states = {}
        provider_before = existing_receipt.get("native_provider_before", {})

    if (PILOT_ROOT / "desktop/assembly-receipt.json").exists() and existing_receipt is None:
        raise AssemblyError("unexpected desktop state exists without a valid assembly receipt")

    require_no_pending_upgrade()
    sudo = run(["sudo", "-v"], capture=False, check=False)
    if sudo.returncode:
        raise AssemblyError("sudo authorization failed")
    install_packages()

    # Installing the fork replaces upstream SwayNC atomically. Its runtime
    # dependencies are already installed, so makepkg removes only build deps.
    if existing_receipt is not None:
        installed = installed_package_version(swaync_pins["package"])
        if installed != swaync_pins["version"]:
            raise AssemblyError("the completed desktop receipt no longer matches the installed SwayNC fork")
        swaync_package_receipt = existing_receipt.get("swaync_recipe", {})
        recipe_bytes_path = ASSEMBLY_ROOT / "swaync/PKGBUILD"
        if recipe_bytes_path.is_file() and not recipe_bytes_path.is_symlink():
            recipe_bytes = recipe_bytes_path.read_bytes()
        elif existing_receipt.get("state") == "prepared":
            recipe_bytes, recovered_recipe_receipt = load_recipe_archive(swaync_pins)
            if recovered_recipe_receipt.get("pkgbuild_sha256") != swaync_package_receipt.get("pkgbuild_sha256"):
                raise AssemblyError("recovered pinned SwayNC recipe differs from its prepared receipt")
        else:
            raise AssemblyError("the completed recipe receipt copy is missing or unsafe")
        if sha256(recipe_bytes) != swaync_package_receipt.get("pkgbuild_sha256"):
            raise AssemblyError("the recipe receipt copy changed")
    else:
        swaync_package_receipt, recipe_bytes = build_and_install_swaync(swaync_pins)

    run(["systemctl", "--user", "daemon-reload"])
    service_path = swaync_unit_path()
    links = session_links_preflight(service_path, existing_receipt)
    gsettings = load_or_capture_gsettings(existing_receipt)
    # Save exact preimages and the expected result before the first user-file
    # mutation. A failed application can resume from this prepared receipt.
    receipt = stage_recovery_and_receipt(
        swaync_pins, targets, target_states, links, swaync_package_receipt, gsettings
    )
    receipt["swaync_recipe"] = swaync_package_receipt
    receipt["native_provider_before"] = provider_before
    expected_receipt_targets(receipt, targets)
    receipt["package_versions"] = package_versions()
    save_json_atomic(RECEIPT_PATH, receipt)

    # Keep the public build recipe next to its receipt for local inspection.
    recipe_target_relative = ".local/share/niri-plus-vm/desktop/swaync/PKGBUILD"
    recipe_target = relative_target(recipe_target_relative)
    if recipe_target.exists():
        if recipe_target.is_symlink() or not recipe_target.is_file() or recipe_target.read_bytes() != recipe_bytes:
            raise AssemblyError("an unrelated SwayNC recipe copy already occupies the evidence path")
    else:
        atomic_write_new_or_exact(recipe_target, recipe_bytes, 0o644)
    receipt["swaync_recipe_copy"] = {
        "path": recipe_target_relative,
        "sha256": sha256(recipe_bytes),
    }
    save_json_atomic(RECEIPT_PATH, receipt)

    apply_targets(receipt, targets)
    apply_gsettings(receipt)
    create_session_links(receipt, service_path)
    run(["systemd-analyze", "--user", "verify", str(HOME / ".config/systemd/user/clipboard-history@.service")], capture=True)
    run(["systemctl", "--user", "daemon-reload"])
    run(["update-desktop-database", str(HOME / ".local/share/applications")], capture=True)
    verify_desktop_entries()
    verify_effective_mime_defaults()

    # SwayNC and clipboard collectors are tied to Niri. BlueZ, PipeWire and
    # WirePlumber remain their native providers; NetworkManager ownership is
    # explicitly outside this tool.
    for unit in ("swaync.service", "clipboard-history@text.service", "clipboard-history@image.service"):
        if user_service_state(unit) != "active":
            run(["systemctl", "--user", "start", unit])
    receipt["native_provider_services"] = activate_native_services(provider_before)
    receipt["package_versions"] = package_versions()
    receipt["state"] = "complete"
    receipt["verified_mime_defaults"] = MIME_ASSOCIATIONS
    receipt["services"] = {
        unit: user_service_state(unit)
        for unit in ("swaync.service", "clipboard-history@text.service", "clipboard-history@image.service")
    }
    receipt["pilot_setup_receipt_sha256"] = sha256((PILOT_ROOT / "setup-receipt.json").read_bytes())
    save_json_atomic(RECEIPT_PATH, receipt)

    print(f"Incremental desktop assembly complete: {RECEIPT_PATH}")
    print("Open Mod+N for SwayNC, Mod+Y for clipboard history, and Mod+E for Dolphin.")
    print("Start the local browser fixture with: python ~/.local/share/niri-plus-vm/desktop/sample_server.py")
    print("NetworkManager was installed only; its connection handover remains separately owned.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, AssemblyError, json.JSONDecodeError, subprocess.CalledProcessError, tarfile.TarError) as error:
        print(f"assemble_desktop.py: {error}", file=sys.stderr)
        raise SystemExit(1)
