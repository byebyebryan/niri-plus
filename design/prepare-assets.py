#!/usr/bin/env python3
"""Prepare licensed review fonts/icons from the installed Arch packages."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
FONTS = [
    ("inter", "/usr/share/fonts/inter/InterVariable.ttf", "/usr/share/licenses/inter-font/LICENSE.txt", "Inter Variable", "inter-font"),
    ("noto", "/usr/share/fonts/noto/NotoSans-Regular.ttf", "/usr/share/licenses/noto-fonts/LICENSE", "Noto Sans", "noto-fonts"),
    ("noto-medium", "/usr/share/fonts/noto/NotoSans-Medium.ttf", "/usr/share/licenses/noto-fonts/LICENSE", "Noto Sans Medium", "noto-fonts"),
    ("noto-semibold", "/usr/share/fonts/noto/NotoSans-SemiBold.ttf", "/usr/share/licenses/noto-fonts/LICENSE", "Noto Sans Semibold", "noto-fonts"),
    ("meslo", "/usr/share/fonts/TTF/MesloLGSNerdFont-Regular.ttf", "/usr/share/licenses/ttf-meslo-nerd/LICENSE.txt", "MesloLGS Nerd Font", "ttf-meslo-nerd"),
    ("jetbrains", "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf", "/usr/share/licenses/ttf-jetbrains-mono-nerd/OFL.txt", "JetBrainsMono Nerd Font", "ttf-jetbrains-mono-nerd"),
    ("source-han", "/usr/share/fonts/adobe-source-han-sans/SourceHanSansCN-Regular.otf", "/usr/share/licenses/adobe-source-han-sans-cn-fonts/LICENSE.txt", "Source Han Sans CN", "adobe-source-han-sans-cn-fonts"),
]
ICONS = {
    "files": "/usr/share/icons/breeze-dark/apps/22/system-file-manager.svg",
    "wifi": "/usr/share/icons/breeze-dark/devices/22/network-wireless.svg",
    "audio": "/usr/share/icons/breeze-dark/status/22/audio-volume-high.svg",
    "lock": "/usr/share/icons/breeze-dark/actions/22/system-lock-screen.svg",
    "power": "/usr/share/icons/breeze-dark/actions/22/system-shutdown.svg",
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    (ASSETS / "fonts").mkdir(parents=True, exist_ok=True)
    (ASSETS / "licenses").mkdir(exist_ok=True)
    (ASSETS / "icons").mkdir(exist_ok=True)
    records = []
    for slug, source, license_path, family, package in FONTS:
        target = ASSETS / "fonts" / (slug + ".woff2")
        if not target.exists() or target.stat().st_mtime < Path(source).stat().st_mtime:
            with tempfile.TemporaryDirectory(prefix="niri-font-") as temporary:
                copy = Path(temporary) / Path(source).name
                shutil.copyfile(source, copy)
                subprocess.run(["woff2_compress", str(copy)], check=True, capture_output=True)
                shutil.copyfile(copy.with_suffix(".woff2"), target)
        shutil.copyfile(license_path, ASSETS / "licenses" / (slug + ".txt"))
        records.append({"path": target.relative_to(ROOT).as_posix(), "sha256": digest(target), "family": family, "package": subprocess.check_output(["pacman", "-Q", package], text=True).strip(), "source_sha256": digest(source), "transformation": "WOFF2 packaging, preserving the source glyph set", "license": "assets/licenses/" + slug + ".txt"})
    for slug, source in ICONS.items():
        target = ASSETS / "icons" / (slug + ".svg")
        shutil.copyfile(source, target)
        records.append({"path": target.relative_to(ROOT).as_posix(), "sha256": digest(target), "source": "KDE Breeze Dark " + Path(source).name, "package": "breeze-icons 6.31.0-1", "license": "LGPL-3.0-or-later / LGPL-2.1-only; see bundled texts"})
    for name in ["LGPL-3.0-or-later", "LGPL-2.1-only"]:
        url = "https://raw.githubusercontent.com/spdx/license-list-data/main/text/" + name + ".txt"
        with urlopen(url, timeout=20) as response:
            (ASSETS / "licenses" / (name + ".txt")).write_bytes(response.read())
    (ASSETS / "provenance.json").write_text(json.dumps({"date": "2026-10-24", "files": records, "icon_source": "https://invent.kde.org/frameworks/breeze-icons", "icon_attribution": "KDE Breeze contributors; installed package version and file hashes recorded above", "license_text_source": "https://github.com/spdx/license-list-data", "native_images": "See native/native-provenance.json; all other screens are HTML/CSS design mockups."}, indent=2) + "\n")
    print(json.dumps({"fonts": len(FONTS), "icons": len(ICONS)}))


if __name__ == "__main__":
    main()
