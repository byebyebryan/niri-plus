#!/usr/bin/env python3
"""Fetch the pinned terminal plugins into a new, user-selected directory."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tarfile
import tempfile
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
MAX_ARCHIVE_BYTES = 32 * 1024 * 1024
MAX_UNPACKED_BYTES = 128 * 1024 * 1024
LOCAL_FILES = (
    "init.zsh",
    "zshrc",
    "p10k.zsh",
    "p10k-custom-segments.zsh",
    "pins.json",
    "THIRD_PARTY_NOTICES.md",
    "fetch.py",
)


def safe_destination(raw: str, home: Path | None = None) -> Path:
    home = (Path.home() if home is None else home).resolve()
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    if candidate.is_symlink():
        raise ValueError("destination must not be a symlink")
    destination = candidate.resolve(strict=False)
    if destination in {Path("/"), home} or not destination.is_relative_to(home):
        raise ValueError("choose a new destination below your home directory")
    if candidate.exists() or destination.exists():
        raise ValueError("destination already exists; choose a new, empty path")
    return destination


def read_pins() -> list[dict[str, str]]:
    pins = json.loads((ROOT / "pins.json").read_text())
    if pins.get("schema_version") != 1:
        raise ValueError("unsupported pins.json schema")
    projects = pins.get("plugins")
    if not isinstance(projects, list) or len(projects) != 4:
        raise ValueError("expected exactly four pinned plugin archives")
    seen = set()
    for project in projects:
        commit = project.get("commit", "")
        digest = project.get("sha256", "")
        url = project.get("archive_url", "")
        if len(commit) != 40 or any(ch not in "0123456789abcdef" for ch in commit):
            raise ValueError(f"invalid immutable commit for {project.get('name')}")
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError(f"invalid sha256 for {project.get('name')}")
        if not url.startswith("https://codeload.github.com/") or not url.endswith("/" + commit):
            raise ValueError(f"invalid immutable archive URL for {project.get('name')}")
        directory = project.get("install_directory", "")
        if not directory or directory in {".", ".."} or "/" in directory or directory in seen:
            raise ValueError("invalid or duplicate plugin install directory")
        seen.add(directory)
    return projects


def download(url: str, destination: Path) -> str:
    request = Request(url, headers={"User-Agent": "niri-plus-terminal-fetch/1"})
    digest = hashlib.sha256()
    total = 0
    with urlopen(request, timeout=30) as response, destination.open("xb") as output:
        final_url = response.geturl()
        if not final_url.startswith("https://"):
            raise ValueError("archive redirect left HTTPS")
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_ARCHIVE_BYTES:
            raise ValueError("archive exceeds the configured size limit")
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_ARCHIVE_BYTES:
                raise ValueError("archive exceeds the configured size limit")
            digest.update(chunk)
            output.write(chunk)
    return digest.hexdigest()


def extract_verified(archive: Path, project: dict[str, str], destination: Path) -> None:
    unpacked = 0
    root = project["archive_root"]
    with tarfile.open(archive, "r:gz") as source:
        members = source.getmembers()
        if not members:
            raise ValueError(f"empty archive for {project['name']}")
        checked: list[tuple[tarfile.TarInfo, Path]] = []
        symlink_paths: set[Path] = set()
        for member in members:
            name = member.name
            if member.isdir() and name.endswith("/"):
                name = name.rstrip("/")
            path = PurePosixPath(name)
            if path.is_absolute() or "\\" in name or any(part in {"", ".", ".."} for part in name.split("/")):
                raise ValueError(f"unsafe archive member: {name}")
            parts = path.parts
            if not parts or parts[0] != root:
                raise ValueError(f"unexpected archive root for {project['name']}")
            if not (member.isdir() or member.isfile() or member.issym()):
                raise ValueError(f"unsupported archive member type: {name}")
            if member.size < 0:
                raise ValueError(f"invalid archive member size: {name}")
            if member.issym():
                link = PurePosixPath(member.linkname)
                if link.is_absolute() or "\\" in member.linkname:
                    raise ValueError(f"unsafe archive symlink: {name}")
                resolved_parts = list(Path(*parts[1:]).parent.parts)
                for component in member.linkname.split("/"):
                    if component in {"", "."}:
                        continue
                    if component == "..":
                        if not resolved_parts:
                            raise ValueError(f"archive symlink escapes its root: {name}")
                        resolved_parts.pop()
                    else:
                        resolved_parts.append(component)
                if not resolved_parts:
                    raise ValueError(f"archive symlink resolves to its root: {name}")
                symlink_paths.add(Path(*parts[1:]))
            unpacked += member.size
            if unpacked > MAX_UNPACKED_BYTES:
                raise ValueError("archive expands beyond the configured size limit")
            relative = Path(*parts[1:])
            checked.append((member, relative))

        for _, relative in checked:
            if any(parent in symlink_paths for parent in relative.parents if parent != Path(".")):
                raise ValueError(f"archive path traverses an internal symlink: {relative}")

        for member, relative in checked:
            if not relative.parts:
                continue
            target = destination / relative
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if member.issym():
                os.symlink(member.linkname, target)
                continue
            stream = source.extractfile(member)
            if stream is None:
                raise ValueError(f"unable to read archive member: {member.name}")
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            descriptor = os.open(target, flags, member.mode & 0o777)
            with os.fdopen(descriptor, "wb") as output, stream:
                shutil.copyfileobj(stream, output)


def dependency_receipt(stage: Path, projects: list[dict[str, str]]) -> dict[str, object]:
    pins_bytes = (ROOT / "pins.json").read_bytes()
    files: list[dict[str, object]] = []
    for path in sorted(stage.rglob("*"), key=lambda item: item.relative_to(stage).as_posix()):
        relative = path.relative_to(stage).as_posix()
        if path.is_dir() and not path.is_symlink():
            continue
        if path.is_symlink():
            link_target = os.readlink(path)
            files.append(
                {
                    "path": relative,
                    "type": "symlink",
                    "target": link_target,
                    "sha256": hashlib.sha256(os.fsencode(link_target)).hexdigest(),
                }
            )
        elif path.is_file():
            files.append(
                {
                    "path": relative,
                    "type": "file",
                    "mode": stat.S_IMODE(path.stat().st_mode),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
        else:
            raise ValueError(f"unsupported dependency payload: {relative}")

    plugins = [
        {
            "name": project["name"],
            "commit": project["commit"],
            "archive_sha256": project["sha256"],
            "install_directory": project["install_directory"],
            "entrypoint": project["entrypoint"],
        }
        for project in sorted(projects, key=lambda item: item["name"])
    ]
    return {
        "schema_version": 1,
        "pins_sha256": hashlib.sha256(pins_bytes).hexdigest(),
        "plugins": plugins,
        "files": files,
    }


def install(
    destination: Path,
    *,
    projects: list[dict[str, str]] | None = None,
    dependencies_only: bool = False,
) -> Path:
    projects = read_pins() if projects is None else projects
    if dependencies_only:
        names = {project.get("name") for project in projects}
        if len(projects) != 4 or len(names) != 4 or "powerlevel10k" not in names:
            raise ValueError("dependency-only mode requires all four pinned trees, including Powerlevel10k")
    destination = safe_destination(str(destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".niri-plus-terminal-fetch-", dir=destination.parent))
    created_destination = False
    try:
        if dependencies_only:
            shutil.copyfile(ROOT / "pins.json", stage / "pins.json")
            shutil.copyfile(ROOT / "THIRD_PARTY_NOTICES.md", stage / "THIRD_PARTY_NOTICES.md")
        else:
            for name in LOCAL_FILES:
                shutil.copyfile(ROOT / name, stage / name)

        for project in projects:
            archive = stage / f"{project['name']}.tar.gz"
            actual = download(project["archive_url"], archive)
            if not hmac.compare_digest(actual, project["sha256"]):
                raise ValueError(f"SHA-256 mismatch for {project['name']}")
            target = stage / "plugins" / project["install_directory"]
            target.mkdir(parents=True, exist_ok=False)
            extract_verified(archive, project, target)
            archive.unlink()
            if not (target / project["entrypoint"]).is_file():
                raise ValueError(f"missing plugin entrypoint for {project['name']}")

        if dependencies_only:
            receipt = dependency_receipt(stage, projects)
            (stage / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

        # Create the selected leaf exclusively. A previous installation is
        # never merged, replaced, or deleted.
        destination.mkdir(mode=0o700)
        created_destination = True
        for source in stage.iterdir():
            target = destination / source.name
            if source.is_dir():
                shutil.copytree(source, target, symlinks=True)
            else:
                shutil.copy2(source, target)
        destination.chmod(0o755)
        created_destination = False
        return destination
    finally:
        shutil.rmtree(stage, ignore_errors=True)
        if created_destination:
            shutil.rmtree(destination, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", help="new directory below your home directory")
    parser.add_argument(
        "--dependencies-only",
        action="store_true",
        help="install only verified plugins, pins, notices, and a SHA-256 receipt",
    )
    args = parser.parse_args(argv)
    try:
        installed = install(Path(args.destination), dependencies_only=args.dependencies_only)
    except (OSError, ValueError, tarfile.TarError) as error:
        print(f"fetch.py: {error}", file=sys.stderr)
        return 1
    if args.dependencies_only:
        print(f"Installed the pinned dependency tree at {installed}")
        print(f"Receipt: {installed / 'receipt.json'}")
        print("No shell startup or configuration files were copied.")
    else:
        print(f"Installed the pinned Zsh bundle at {installed}")
        print("No shell startup file was changed. Review the recipe before sourcing zshrc.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
