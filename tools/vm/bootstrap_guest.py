#!/usr/bin/env python3
"""Stage the pinned Niri Plus pilot in the verified Arch capture guest."""

from __future__ import annotations

import hashlib
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
PIN_FILE = SCRIPT_DIR / "pins.json"
MAX_COMPONENT_ARCHIVE = 32 * 1024 * 1024
COMPONENT_MODULES = {"desktop", "shell", "appearance"}
ARCH_BASH_PROFILE = (SCRIPT_DIR / "session/arch-skel.bash_profile").read_bytes()
ARCH_BASH_PROFILE_SHA256 = "e149407c2bee17779caec70a7edd3d0000d172e7e4347429b80cb4d55bcec9c2"
LEGACY_LAB_BASH_PROFILE = (
    b"# Lab-only console start for the retained Niri Plus reference guest.\n"
    b'if [[ "$(tty 2>/dev/null || true)" == /dev/tty1 && -z "${WAYLAND_DISPLAY:-}" ]]; then\n'
    b"    exec niri-session\n"
    b"fi\n\n"
    b"[[ -f ~/.bashrc ]] && . ~/.bashrc\n"
)
PACKAGE_NAMES = (
    "dbus", "ffmpeg", "fontconfig", "git", "grim", "kitty", "mesa",
    "mesa-utils", "niri", "noto-fonts", "noto-fonts-emoji", "python",
    "rofi", "ttf-meslo-nerd", "xdg-desktop-portal-gtk", "xdg-desktop-portal-wlr",
    "jack2", "wf-recorder", "wtype",
    "xwayland-satellite", "zsh", "google-chrome",
)
BOOTSTRAP_TOOLS = (
    "README.md", "bootstrap-guest.sh", "bootstrap_guest.py", "capture_scene.py",
    "disable-demo-session.sh", "guest-guard.sh", "pins.json",
)
SAMPLE_FILES = (
    (Path("sample/site/index.html"), Path("site/index.html")),
    (Path("sample/project/status.py"), Path("project/status.py")),
)


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(command: list[str], *, cwd: Path | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def require_guest() -> None:
    guard = SCRIPT_DIR / "guest-guard.sh"
    result = subprocess.run([str(guard)], text=True, capture_output=True)
    if result.returncode:
        sys.stderr.write(result.stderr or result.stdout)
        raise SystemExit(result.returncode)


def load_pins() -> dict[str, Any]:
    pins = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    if pins.get("schema_version") != 1:
        raise ValueError("unsupported tools/vm/pins.json schema")
    if pins["components"].get("version") != "0.3.1":
        raise ValueError("the pilot requires the published Niri Plus 0.3.1 component bundle")
    return pins


def fetch_https(url: str, *, maximum_bytes: int) -> bytes:
    request = Request(url, headers={"User-Agent": "niri-plus-vm-pilot/1"})
    with urlopen(request, timeout=60) as response:
        final_url = response.geturl()
        if not final_url.startswith("https://"):
            raise ValueError("download redirected outside HTTPS")
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > maximum_bytes:
            raise ValueError("download exceeded its size limit")
        data = response.read(maximum_bytes + 1)
    if len(data) > maximum_bytes:
        raise ValueError("download exceeded its size limit")
    return data


def normalized_archive_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or "\\" in name or path.as_posix() != name or ".." in path.parts or "." in path.parts:
        raise ValueError(f"unsafe component archive path: {name!r}")
    return path


def extract_component_bundle(archive_bytes: bytes, destination: Path, pins: dict[str, Any]) -> dict[str, Any]:
    component_pin = pins["components"]
    if digest_bytes(archive_bytes) != component_pin["archive_sha256"]:
        raise ValueError("component archive SHA-256 does not match the recorded publication pin")

    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
        members = archive.getmembers()
        by_name: dict[str, tarfile.TarInfo] = {}
        for member in members:
            path = normalized_archive_path(member.name)
            if member.name in by_name or not member.isfile() or member.issym() or member.islnk():
                raise ValueError(f"unsupported or duplicate component archive member: {member.name}")
            by_name[member.name] = member

        manifest_member = by_name.get("manifest.json")
        if manifest_member is None:
            raise ValueError("component archive has no manifest.json")
        manifest_stream = archive.extractfile(manifest_member)
        if manifest_stream is None:
            raise ValueError("cannot read component manifest")
        manifest_bytes = manifest_stream.read()
        if digest_bytes(manifest_bytes) != component_pin["manifest_sha256"]:
            raise ValueError("component manifest SHA-256 does not match the publication record")
        manifest = json.loads(manifest_bytes)
        if (
            manifest.get("version") != component_pin["version"]
            or manifest.get("api_version") != component_pin["api_version"]
            or manifest.get("source_commit") != component_pin["source_commit"]
        ):
            raise ValueError("component manifest does not match the pinned release tuple")

        records = manifest.get("files")
        if not isinstance(records, list) or len(records) != 27:
            raise ValueError("component manifest does not contain the expected 27 payload files")
        expected_names = {"manifest.json"}
        seen_paths: set[str] = set()
        for record in records:
            path_text = record.get("path", "")
            path = normalized_archive_path(path_text)
            if path_text in seen_paths or not path_text.startswith("components/"):
                raise ValueError(f"invalid or duplicate component path: {path_text!r}")
            seen_paths.add(path_text)
            expected_names.add(path_text)
            mode = record.get("mode")
            if mode not in {0o644, 0o755} or record.get("module") not in COMPONENT_MODULES:
                raise ValueError(f"invalid mode or module in component manifest for {path_text}")
            member = by_name.get(path_text)
            if member is None:
                raise ValueError(f"component archive is missing {path_text}")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"cannot read component file {path_text}")
            payload = stream.read()
            if digest_bytes(payload) != record.get("sha256"):
                raise ValueError(f"component payload SHA-256 mismatch for {path_text}")
            target = destination.joinpath(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            target.chmod(mode)

        if set(by_name) != expected_names:
            extra = sorted(set(by_name) - expected_names)
            raise ValueError(f"component archive has unlisted members: {extra}")
        manifest_path = destination / "manifest.json"
        manifest_path.write_bytes(manifest_bytes)
        manifest_path.chmod(0o644)
        return manifest


def git_output(repository: Path, *arguments: str) -> str:
    result = run(["git", "-C", str(repository), *arguments], capture=True)
    return result.stdout.strip()


def fetch_public_assets(source_directory: Path, pins: dict[str, Any]) -> dict[str, str]:
    source_pin = pins["public_source"]
    repository = source_directory / "checkout"
    repository.mkdir(parents=True, exist_ok=False)
    run(["git", "init", "--quiet", str(repository)])
    run(["git", "-C", str(repository), "remote", "add", "origin", source_pin["repository"]])
    run(["git", "-C", str(repository), "fetch", "--quiet", "--depth=1", "origin", source_pin["commit"]])
    run(["git", "-C", str(repository), "checkout", "--quiet", "--detach", "FETCH_HEAD"])
    actual_commit = git_output(repository, "rev-parse", "HEAD")
    if actual_commit != source_pin["commit"]:
        raise ValueError(f"public checkout returned {actual_commit}, expected {source_pin['commit']}")
    if git_output(repository, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("public source checkout is not clean")

    asset_hashes: dict[str, str] = {}
    for relative_text in source_pin["assets"]:
        relative = normalized_archive_path(relative_text)
        source = repository.joinpath(*relative.parts)
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"public source asset is missing or symlinked: {relative_text}")
        payload = source.read_bytes()
        target = source_directory.joinpath(*relative.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        asset_hashes[relative_text] = digest_bytes(payload)
    return asset_hashes


def checked_replace(text: str, old: str, new: str, description: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"expected one {description} in the pinned Niri starter; found {count}")
    return text.replace(old, new, 1)


def assemble_niri_config(base_config: str, rendered_theme: dict[str, Any]) -> str:
    colors = rendered_theme.get("colors", {})
    if rendered_theme.get("profile", {}).get("id") != "neutral-slate":
        raise ValueError("appearance renderer did not select Neutral Slate")
    if rendered_theme.get("terminal", {}).get("colors", {}).get("background") != "#000000":
        raise ValueError("appearance renderer did not select the pure-black terminal")

    config = checked_replace(base_config, 'background-color "#000000"', f'background-color "{colors["canvas"]}"', "canvas setting")
    config = checked_replace(config, 'active-color "#7fc8ff"', f'active-color "{colors["focus"]}"', "active focus color")
    config = checked_replace(config, 'inactive-color "#505050"', f'inactive-color "{colors["border"]}"', "inactive focus color")
    config = checked_replace(config, "default-column-width { proportion 0.66667; }", "default-column-width { proportion 0.5; }", "default column width")
    config = checked_replace(config, '    Mod+E { spawn "dolphin"; }\n', "", "out-of-scope Dolphin binding")
    return config


def file_inventory(root: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if path.is_symlink():
            target = os.readlink(path)
            records.append({
                "path": path.relative_to(root).as_posix(),
                "type": "symlink",
                "target": target,
                "sha256": digest_bytes(os.fsencode(target)),
            })
        elif path.is_file():
            records.append({
                "path": path.relative_to(root).as_posix(),
                "type": "file",
                "mode": stat.S_IMODE(path.stat().st_mode),
                "sha256": digest_bytes(path.read_bytes()),
            })
    return records


def ensure_no_symlink_ancestors(path: Path, home: Path) -> None:
    resolved_home = home.resolve()
    if path.is_symlink() or not path.resolve(strict=False).is_relative_to(resolved_home):
        raise ValueError(f"managed path escapes the demo home or is a symlink: {path}")
    current = resolved_home
    for part in path.relative_to(resolved_home).parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"managed path traverses a symlink: {current}")
        if current.exists() and not current.is_dir():
            raise ValueError(f"managed parent is not a directory: {current}")


def expected_home_files(home: Path, root: Path, staged: Path) -> dict[Path, bytes]:
    base_config = (staged / "source-assets/examples/niri/config.kdl").read_text(encoding="utf-8")
    theme = json.loads((staged / "appearance/theme.json").read_text(encoding="utf-8"))
    niri_config = assemble_niri_config(base_config, theme)
    kitty_config = (
        "# Guest pilot: appearance from the independently pinned schema-2 identity.\n"
        "font_family MesloLGS Nerd Font Mono\n"
        "font_size 11.0\n"
        "shell /usr/bin/zsh --login\n"
        f"include {root}/appearance/kitty-neutral-slate.conf\n"
    )
    rofi_config = '@theme "niri-plus-neutral-slate.rasi"\n'
    zshrc = f'source "{root}/components/shell/zshrc"\n'
    bash_profile = (SCRIPT_DIR / "session/demo.bash_profile").read_bytes()
    return {
        home / ".config/niri/config.kdl": niri_config.encode("utf-8"),
        home / ".config/kitty/kitty.conf": kitty_config.encode("utf-8"),
        home / ".config/rofi/config.rasi": rofi_config.encode("utf-8"),
        home / ".config/rofi/niri-plus-neutral-slate.rasi": (staged / "appearance/neutral-slate.rasi").read_bytes(),
        home / ".config/xdg-desktop-portal/niri-portals.conf": (staged / "source-assets/examples/portals/niri-portals.conf").read_bytes(),
        home / ".zshrc": zshrc.encode("utf-8"),
        home / ".bash_profile": bash_profile,
    }


def preflight_home_files(home_files: dict[Path, bytes], home: Path) -> None:
    for path, expected in home_files.items():
        ensure_no_symlink_ancestors(path, home)
        if path.exists():
            if not path.is_file():
                raise ValueError(f"refusing to replace an existing user file: {path}")
            actual = path.read_bytes()
            if path == home / ".bash_profile":
                if actual not in {expected, ARCH_BASH_PROFILE, LEGACY_LAB_BASH_PROFILE} or stat.S_IMODE(path.stat().st_mode) != 0o644:
                    raise ValueError(f"refusing to replace an unknown or modified login profile: {path}")
            elif actual != expected:
                raise ValueError(f"refusing to replace an existing user file: {path}")
    niri_bytes = home_files[home / ".config/niri/config.kdl"]
    with tempfile.NamedTemporaryFile(prefix="niri-plus-config-", suffix=".kdl", delete=False) as temporary:
        temporary.write(niri_bytes)
        temporary_config = Path(temporary.name)
    try:
        run(["niri", "validate", "--config", str(temporary_config)])
    finally:
        temporary_config.unlink(missing_ok=True)


def write_new_file(path: Path, data: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, mode)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)


def ensure_bash_profile_recovery(home: Path, managed_profile: bytes) -> dict[str, Any]:
    if digest_bytes(ARCH_BASH_PROFILE) != ARCH_BASH_PROFILE_SHA256:
        raise ValueError("the recorded Arch skeleton profile fixture has changed")
    profile = home / ".bash_profile"
    recovery_directory = home / ".local/state/niri-plus-vm/recovery"
    state_path = recovery_directory / "bash_profile.state.json"
    backup_path = recovery_directory / "bash_profile.preimage"
    ensure_no_symlink_ancestors(state_path, home)
    ensure_no_symlink_ancestors(backup_path, home)

    if state_path.exists():
        if state_path.is_symlink() or not state_path.is_file():
            raise ValueError(f"refusing an unsafe Bash profile recovery record: {state_path}")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("schema_version") != 1 or state.get("state") not in {"absent", "arch-skel"}:
            raise ValueError("unsupported Bash profile recovery record")
        if state["state"] == "arch-skel":
            if (
                state.get("sha256") != ARCH_BASH_PROFILE_SHA256
                or state.get("mode") != 0o644
                or not backup_path.is_file()
                or backup_path.is_symlink()
                or backup_path.read_bytes() != ARCH_BASH_PROFILE
                or stat.S_IMODE(backup_path.stat().st_mode) != 0o600
            ):
                raise ValueError("the preserved Arch skeleton profile preimage is missing or changed")
        elif backup_path.exists():
            raise ValueError("an absent-profile recovery record unexpectedly has a preimage file")
        if profile.exists():
            if profile.is_symlink() or stat.S_IMODE(profile.stat().st_mode) != 0o644:
                raise ValueError("the managed Bash profile has unexpected type or mode")
            actual = profile.read_bytes()
            if actual not in {managed_profile, LEGACY_LAB_BASH_PROFILE} and not (state["state"] == "arch-skel" and actual == ARCH_BASH_PROFILE):
                raise ValueError("the managed Bash profile changed after setup")
        elif state["state"] != "absent":
            raise ValueError("the original Bash profile disappeared after setup")
        return {
            "state": state["state"],
            "sha256": state.get("sha256"),
            "mode": state.get("mode"),
            "backup_path": "~/.local/state/niri-plus-vm/recovery/bash_profile.preimage" if state["state"] == "arch-skel" else None,
        }

    if backup_path.exists():
        raise ValueError("a Bash profile preimage exists without its recovery record")
    if not profile.exists():
        state = {"schema_version": 1, "state": "absent"}
        record = {"state": "absent", "sha256": None, "mode": None, "backup_path": None}
    else:
        if profile.is_symlink() or stat.S_IMODE(profile.stat().st_mode) != 0o644 or profile.read_bytes() != ARCH_BASH_PROFILE:
            raise ValueError("only the exact 57-byte Arch skeleton .bash_profile is an accepted preimage")
        state = {
            "schema_version": 1,
            "state": "arch-skel",
            "sha256": ARCH_BASH_PROFILE_SHA256,
            "mode": 0o644,
        }
        record = {
            "state": "arch-skel",
            "sha256": ARCH_BASH_PROFILE_SHA256,
            "mode": 0o644,
            "backup_path": "~/.local/state/niri-plus-vm/recovery/bash_profile.preimage",
        }

    if recovery_directory.exists():
        if (
            recovery_directory.is_symlink()
            or not recovery_directory.is_dir()
            or recovery_directory.stat().st_uid != os.getuid()
            or stat.S_IMODE(recovery_directory.stat().st_mode) != 0o700
        ):
            raise ValueError("Bash profile recovery directory exists with unexpected ownership or permissions")
    else:
        recovery_directory.mkdir(parents=True, mode=0o700)
        recovery_directory.chmod(0o700)
    if state["state"] == "arch-skel":
        write_new_file(backup_path, ARCH_BASH_PROFILE, 0o600)
    write_new_file(state_path, (json.dumps(state, sort_keys=True) + "\n").encode("utf-8"), 0o600)
    return record


def apply_home_files(home_files: dict[Path, bytes]) -> None:
    for path, expected in home_files.items():
        if path.name == ".bash_profile":
            if path.exists():
                actual = path.read_bytes()
                if actual in {ARCH_BASH_PROFILE, LEGACY_LAB_BASH_PROFILE}:
                    with tempfile.NamedTemporaryFile(prefix=".bash_profile.niri-plus-", dir=path.parent, delete=False) as temporary:
                        temporary.write(expected)
                        replacement = Path(temporary.name)
                    replacement.chmod(0o644)
                    os.replace(replacement, path)
                elif actual != expected:
                    raise ValueError(f"Bash profile changed after preflight: {path}")
            else:
                write_new_file(path, expected)
        elif not path.exists():
            write_new_file(path, expected)
        elif not path.is_file() or path.read_bytes() != expected:
            raise ValueError(f"managed file changed after preflight: {path}")


def install_getty_dropin() -> bool:
    source = SCRIPT_DIR / "session/getty@tty1.service.d/20-niri-plus-demo.conf"
    target = Path("/etc/systemd/system/getty@tty1.service.d/20-niri-plus-demo.conf")
    if target.is_symlink():
        raise ValueError(f"refusing to replace a symlink: {target}")
    expected = source.read_bytes()
    changed = False
    if target.exists():
        if not target.is_file() or target.read_bytes() != expected:
            raise ValueError(f"refusing to replace an existing systemd drop-in: {target}")
    else:
        with tempfile.NamedTemporaryFile(prefix="niri-plus-getty-", delete=False) as temporary:
            temporary.write(expected)
            temporary_path = Path(temporary.name)
        try:
            run(["sudo", "install", "-D", "-o", "root", "-g", "root", "-m", "0644", str(temporary_path), str(target)])
            changed = True
        finally:
            temporary_path.unlink(missing_ok=True)
    if changed:
        run(["sudo", "systemctl", "daemon-reload"])
        run(["sudo", "systemctl", "reset-failed", "getty@tty1.service"])
        run(["sudo", "systemctl", "restart", "getty@tty1.service"])
    return changed


def aur_source_receipt(pins: dict[str, Any]) -> dict[str, Any]:
    chrome = pins["google_chrome_aur"]
    with tempfile.TemporaryDirectory(prefix="niri-plus-google-chrome-") as temporary:
        repository = Path(temporary) / "aur"
        repository.mkdir()
        run(["git", "init", "--quiet", str(repository)])
        run(["git", "-C", str(repository), "remote", "add", "origin", chrome["repository"]])
        run(["git", "-C", str(repository), "fetch", "--quiet", "--depth=1", "origin", chrome["commit"]])
        run(["git", "-C", str(repository), "checkout", "--quiet", "--detach", "FETCH_HEAD"])
        actual_commit = git_output(repository, "rev-parse", "HEAD")
        if actual_commit != chrome["commit"]:
            raise ValueError(f"Chrome AUR checkout returned {actual_commit}, expected {chrome['commit']}")
        if git_output(repository, "status", "--porcelain", "--untracked-files=all"):
            raise ValueError("Chrome AUR checkout is not clean")

        build_file = repository / "PKGBUILD"
        source_info = repository / ".SRCINFO"
        build_bytes = build_file.read_bytes()
        version_match = re.search(rb"(?m)^pkgver=([^\r\n]+)$", build_bytes)
        if version_match is None or version_match.group(1).decode("ascii") != chrome["version"]:
            raise ValueError("pinned Chrome AUR recipe does not declare the recorded version")
        source_bytes = source_info.read_bytes()

        installed_version = ""
        installed = subprocess.run(["pacman", "-Q", "google-chrome"], text=True, capture_output=True)
        if installed.returncode == 0:
            installed_version = run(["google-chrome-stable", "--version"], capture=True).stdout.strip()
        action = "already-installed-exact-version"
        if chrome["version"] not in installed_version:
            if os.geteuid() == 0:
                raise ValueError("makepkg must run as the ordinary demo user, not root")
            print("Building Google Chrome from the pinned public AUR recipe.", flush=True)
            run(["makepkg", "--syncdeps", "--install", "--noconfirm", "--cleanbuild"], cwd=repository)
            installed_version = run(["google-chrome-stable", "--version"], capture=True).stdout.strip()
            action = "built-from-pinned-aur-recipe"
        if chrome["version"] not in installed_version:
            raise ValueError(f"installed Chrome version is not {chrome['version']}: {installed_version}")

        return {
            "repository": chrome["repository"],
            "commit": actual_commit,
            "pkgbuild_sha256": digest_bytes(build_bytes),
            "srcinfo_sha256": digest_bytes(source_bytes),
            "version": chrome["version"],
            "installed_version": installed_version,
            "install_action": action,
            "upstream_google_deb_checksum": "verified by the pinned PKGBUILD during makepkg",
        }


def package_versions() -> dict[str, str]:
    result = {}
    for package in PACKAGE_NAMES:
        output = run(["pacman", "-Q", package], capture=True).stdout.strip()
        name, version = output.split(maxsplit=1)
        result[name] = version
    return result


def font_match(name: str) -> str:
    return run(["fc-match", "--format", "%{family} | %{file}\n", name], capture=True).stdout.strip()


def stage_guest(pins: dict[str, Any], chrome_receipt: dict[str, Any]) -> Path:
    home = Path.home().resolve()
    if os.geteuid() == 0 or os.environ.get("USER") != "demo":
        raise ValueError("run the bootstrap as the ordinary demo user")
    if Path(os.environ.get("HOME", "")).resolve() != home:
        raise ValueError("HOME does not resolve to the current demo account")

    application_root = home / ".local/share/niri-plus-vm"
    if application_root.is_symlink():
        raise ValueError(f"refusing to use a symlink: {application_root}")
    home_files: dict[Path, bytes]

    if application_root.exists():
        receipt_path = application_root / "setup-receipt.json"
        if not receipt_path.is_file():
            raise ValueError(f"existing pilot directory has no receipt: {application_root}")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("public_inputs", {}).get("components") != pins["components"]:
            raise ValueError("existing pilot directory uses a different component pin; preserve or remove it manually")
        inventory = receipt.get("files", [])
        for item in inventory:
            relative = normalized_archive_path(item["path"])
            path = application_root.joinpath(*relative.parts)
            if item.get("type") != "file" or path.is_symlink() or not path.is_file() or digest_bytes(path.read_bytes()) != item.get("sha256"):
                raise ValueError(f"existing pilot input changed: {path}")
        home_files = expected_home_files(home, application_root, application_root)
        preflight_home_files(home_files, home)
        profile_preimage = ensure_bash_profile_recovery(home, home_files[home / ".bash_profile"])
        if receipt.get("home_preimages", {}).get(".bash_profile") != profile_preimage:
            raise ValueError("existing Bash profile recovery state differs from the setup receipt")
        session_profile = application_root / "tools/session/demo.bash_profile"
        expected_session_profile = (SCRIPT_DIR / "session/demo.bash_profile").read_bytes()
        if session_profile.is_symlink() or not session_profile.is_file():
            raise ValueError("existing pilot session profile is missing or unsafe")
        if session_profile.read_bytes() == LEGACY_LAB_BASH_PROFILE:
            records = [item for item in receipt.get("files", []) if item.get("path") == "tools/session/demo.bash_profile"]
            if len(records) != 1:
                raise ValueError("existing setup receipt has no unique session profile inventory entry")
            with tempfile.NamedTemporaryFile(prefix=".demo.bash_profile.niri-plus-", dir=session_profile.parent, delete=False) as temporary:
                temporary.write(expected_session_profile)
                replacement = Path(temporary.name)
            replacement.chmod(0o644)
            os.replace(replacement, session_profile)
            records[0]["sha256"] = digest_bytes(expected_session_profile)
            receipt.setdefault("managed_home_targets", {})[".bash_profile"] = digest_bytes(home_files[home / ".bash_profile"])
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", prefix=".setup-receipt.niri-plus-", dir=application_root, delete=False) as temporary:
                json.dump(receipt, temporary, ensure_ascii=False, indent=2, sort_keys=True)
                temporary.write("\n")
                receipt_replacement = Path(temporary.name)
            receipt_replacement.chmod(0o644)
            os.replace(receipt_replacement, receipt_path)
        elif session_profile.read_bytes() != expected_session_profile:
            raise ValueError("existing pilot session profile is not the known lab preimage")
        profile_changed = (home / ".bash_profile").read_bytes() != home_files[home / ".bash_profile"] if (home / ".bash_profile").exists() else False
        apply_home_files(home_files)
        getty_changed = install_getty_dropin()
        if profile_changed and not getty_changed:
            run(["sudo", "systemctl", "reset-failed", "getty@tty1.service"])
            run(["sudo", "systemctl", "restart", "getty@tty1.service"])
        print(f"Verified existing pilot setup at {application_root}")
        return application_root

    share_directory = application_root.parent
    share_directory.mkdir(parents=True, exist_ok=True)
    if share_directory.is_symlink():
        raise ValueError(f"refusing to use a symlink: {share_directory}")
    stage = Path(tempfile.mkdtemp(prefix=".niri-plus-vm-stage-", dir=share_directory))
    try:
        archive_data = fetch_https(pins["components"]["archive_url"], maximum_bytes=MAX_COMPONENT_ARCHIVE)
        component_manifest = extract_component_bundle(archive_data, stage, pins)

        source_assets = stage / "source-assets"
        source_assets.mkdir(parents=True, exist_ok=True)
        source_hashes = fetch_public_assets(stage / "public-source", pins)
        # Keep only the pinned source assets after checking the public checkout.
        shutil.move(str(stage / "public-source" / "design"), str(source_assets / "design"))
        shutil.move(str(stage / "public-source" / "examples"), str(source_assets / "examples"))
        shutil.rmtree(stage / "public-source")

        identity_path = stage / pins["identity"]["source_path"]
        identity_bytes = (source_assets / pins["identity"]["source_path"]).read_bytes()
        if digest_bytes(identity_bytes) != pins["identity"]["sha256"]:
            raise ValueError("identity SHA-256 does not match its independent pin")
        identity_path.parent.mkdir(parents=True, exist_ok=True)
        identity_path.write_bytes(identity_bytes)

        component_archive_receipt = {
            "archive_sha256": digest_bytes(archive_data),
            "manifest_sha256": digest_bytes((stage / "manifest.json").read_bytes()),
            "version": component_manifest["version"],
            "api_version": component_manifest["api_version"],
            "source_commit": component_manifest["source_commit"],
            "manifest_file_count": len(component_manifest["files"]),
        }
        pins["components"]["archive_sha256"] = component_archive_receipt["archive_sha256"]

        appearance_directory = stage / "appearance"
        run([
            sys.executable,
            str(stage / "components/appearance/render.py"),
            "--identity", str(identity_path),
            "--output", str(appearance_directory),
        ])
        appearance_manifest = json.loads((appearance_directory / "manifest.json").read_text(encoding="utf-8"))
        if appearance_manifest.get("renderer_version") != pins["components"]["version"]:
            raise ValueError("appearance output was rendered by a different component version")
        if appearance_manifest.get("identity_sha256") != pins["identity"]["sha256"]:
            raise ValueError("appearance output did not use the independently pinned identity")
        rendered_theme = json.loads((appearance_directory / "theme.json").read_text(encoding="utf-8"))
        if rendered_theme.get("profile", {}).get("id") != "neutral-slate":
            raise ValueError("renderer selected an unexpected desktop profile")
        if rendered_theme.get("terminal", {}).get("variant") != "balanced-plus":
            raise ValueError("renderer selected an unexpected terminal profile")
        if rendered_theme.get("terminal", {}).get("colors", {}).get("background") != "#000000":
            raise ValueError("renderer did not produce the pure-black terminal background")

        shell_component = stage / "components/shell"
        plugin_stage = stage / "plugin-stage"
        run([sys.executable, str(shell_component / "fetch.py"), "--dependencies-only", str(plugin_stage)])
        shutil.copytree(plugin_stage / "plugins", shell_component / "plugins")
        shutil.copy2(plugin_stage / "receipt.json", shell_component / "plugins-receipt.json")
        shutil.rmtree(plugin_stage)

        for source_relative, destination_relative in SAMPLE_FILES:
            source = SCRIPT_DIR / source_relative
            target = stage / destination_relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        tools_directory = stage / "tools"
        tools_directory.mkdir(parents=True, exist_ok=True)
        for name in BOOTSTRAP_TOOLS:
            source = SCRIPT_DIR / name
            if source.is_file():
                shutil.copy2(source, tools_directory / name)
        shutil.copytree(SCRIPT_DIR / "session", tools_directory / "session")

        home_files = expected_home_files(home, application_root, stage)
        preflight_home_files(home_files, home)
        profile_preimage = ensure_bash_profile_recovery(home, home_files[home / ".bash_profile"])
        fonts = {
            "Noto Sans": font_match("Noto Sans"),
            "MesloLGS Nerd Font Mono": font_match("MesloLGS Nerd Font Mono"),
        }
        if "Noto Sans" not in fonts["Noto Sans"]:
            raise ValueError(f"Noto Sans did not resolve to an installed font: {fonts['Noto Sans']}")
        if "MesloLGS Nerd Font Mono" not in fonts["MesloLGS Nerd Font Mono"]:
            raise ValueError(f"Meslo did not resolve to an installed font: {fonts['MesloLGS Nerd Font Mono']}")
        public_inputs = {
            "components": pins["components"],
            "component_archive": component_archive_receipt,
            "identity": pins["identity"],
            "identity_source_commit": pins["public_source"]["commit"],
            "public_source": {
                "repository": pins["public_source"]["repository"],
                "commit": pins["public_source"]["commit"],
                "asset_sha256": source_hashes,
                "identity_sha256": pins["identity"]["sha256"],
            },
            "google_chrome_aur": chrome_receipt,
            "shell_plugins": json.loads((shell_component / "plugins-receipt.json").read_text(encoding="utf-8")),
        }
        receipt = {
            "schema_version": 1,
            "created_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "guest": {
                "hostname": "niri-plus-arch",
                "os_release": "Arch Linux x86_64; package versions recorded below",
                "session_harness": "guest tty1 getty autologin for demo starts niri-session; lab-only, not login acceptance",
            },
            "public_inputs": public_inputs,
            "installed_packages": package_versions(),
            "fonts": fonts,
            "home_preimages": {".bash_profile": profile_preimage},
            "managed_home_targets": {str(path.relative_to(home)): digest_bytes(data) for path, data in home_files.items()},
            "assembly_changes": [
                "Rendered Niri and Kitty appearance from the 0.3.1 component renderer and independently SHA-verified identity.",
                "Set the Niri starter's default column width to one half for the browser/terminal pilot frame.",
                "Removed the starter's Dolphin binding because Dolphin is outside this pilot's installed application set.",
                "Kept Rofi's application-launch binding and installed its generated Neutral Slate theme.",
                "Selected the pinned GTK default/file chooser and WLR monitor-sharing portal backends for Niri.",
            ],
            "files": file_inventory(stage),
        }
        (stage / "setup-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        if application_root.exists():
            raise ValueError(f"pilot destination appeared during setup: {application_root}")
        stage.rename(application_root)
        apply_home_files(home_files)
        install_getty_dropin()
        return application_root
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def main() -> int:
    require_guest()
    if os.geteuid() == 0 or os.environ.get("USER") != "demo":
        raise ValueError("run as the ordinary demo user, not root")
    pins = load_pins()
    chrome_receipt = aur_source_receipt(pins)
    application_root = stage_guest(pins, chrome_receipt)
    print(f"Guest pilot staged at {application_root}")
    print("The tty1 lab autologin will start niri-session; open the guest viewer and wait for Niri before capture.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, tarfile.TarError, subprocess.CalledProcessError) as error:
        print(f"bootstrap_guest.py: {error}", file=sys.stderr)
        raise SystemExit(1)
