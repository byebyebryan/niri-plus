#!/usr/bin/env python3
"""Build a deterministic archive of the explicitly listed Niri Plus modules."""

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile

ROOT = Path(__file__).resolve().parents[1]
METADATA = Path("components/metadata.json")
SOURCE_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")
SUPPORTED_MODES = {0o644, 0o755}


def load_metadata(root=ROOT):
    metadata_path = Path(root) / METADATA
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict) or set(metadata) != {"version", "modules", "files", "exports", "appearance_exports"}:
        raise ValueError("components/metadata.json must define version, modules, files, exports, and appearance_exports")
    if not isinstance(metadata["version"], str) or not VERSION.fullmatch(metadata["version"]):
        raise ValueError("component version must be a numeric major.minor.patch value")
    if not isinstance(metadata["appearance_exports"], list):
        raise ValueError("appearance_exports must be a list")

    modules = metadata["modules"]
    if not isinstance(modules, dict) or not modules:
        raise ValueError("component modules must be a non-empty object")
    for name, definition in modules.items():
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_-]*", name):
            raise ValueError(f"invalid module name: {name!r}")
        if not isinstance(definition, dict) or set(definition) != {"prerequisites"}:
            raise ValueError(f"module {name!r} must define prerequisites")
        prerequisites = definition["prerequisites"]
        if not isinstance(prerequisites, list) or any(not isinstance(item, str) or not item.strip() for item in prerequisites):
            raise ValueError(f"module {name!r} prerequisites must be non-empty strings")

    files = metadata["files"]
    if not isinstance(files, list) or not files:
        raise ValueError("component files must be a non-empty list")
    seen = set()
    for record in files:
        if not isinstance(record, dict) or set(record) != {"path", "module"}:
            raise ValueError("each component file record must define path and module")
        path = record["path"]
        module = record["module"]
        if not isinstance(path, str) or "\\" in path:
            raise ValueError(f"invalid component path: {path!r}")
        relative = PurePosixPath(path)
        if relative.is_absolute() or relative.as_posix() != path or not path.startswith("components/") or ".." in relative.parts:
            raise ValueError(f"component path must be a normalized relative path under components/: {path!r}")
        if path in seen:
            raise ValueError(f"duplicate component path: {path}")
        if module not in modules:
            raise ValueError(f"component {path} refers to unknown module {module!r}")
        if not path.startswith(f"components/{module}/"):
            raise ValueError(f"component path must be under its declared module {module!r}: {path!r}")
        seen.add(path)

    return metadata


def read_input(root, relative_path):
    root = Path(root)
    path = PurePosixPath(relative_path)
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"component input must not traverse symlinks: {relative_path}")
    if not current.is_file():
        raise ValueError(f"missing component input: {relative_path}")
    mode = stat.S_IMODE(current.stat().st_mode)
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"unsupported mode {mode:o} for {relative_path}; use 644 or 755")
    data = current.read_bytes()
    if re.search(rb"(?<![A-Za-z0-9_])/home/[^\s\"'`]+", data):
        raise ValueError(f"component input contains an absolute home path: {relative_path}")
    return data, mode


def manifest_for(root, source_commit):
    if not isinstance(source_commit, str) or not SOURCE_COMMIT.fullmatch(source_commit):
        raise ValueError("--source-commit must be a full lowercase 40-character Git commit")
    metadata = load_metadata(root)
    records = []
    payloads = {}
    for spec in sorted(metadata["files"], key=lambda item: item["path"]):
        data, mode = read_input(root, spec["path"])
        payloads[spec["path"]] = data
        records.append({
            "path": spec["path"],
            "module": spec["module"],
            "sha256": hashlib.sha256(data).hexdigest(),
            "mode": mode,
        })
    manifest = {
        "schema_version": 1,
        "api_version": 1,
        "version": metadata["version"],
        "source_commit": source_commit,
        "modules": metadata["modules"],
        "files": records,
    }
    return manifest, payloads


def archive_bytes(manifest, payloads):
    manifest_data = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        members = [("manifest.json", manifest_data, 0o644)]
        members.extend((path, payloads[path], next(item["mode"] for item in manifest["files"] if item["path"] == path)) for path in sorted(payloads))
        for name, data, mode in members:
            member = tarfile.TarInfo(name)
            member.type = tarfile.REGTYPE
            member.size = len(data)
            member.mode = mode
            member.uid = 0
            member.gid = 0
            member.uname = ""
            member.gname = ""
            member.mtime = 0
            archive.addfile(member, io.BytesIO(data))

    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode="wb", filename="", mtime=0, compresslevel=9) as stream:
        stream.write(tar_stream.getvalue())
    return compressed.getvalue()


def build_archive(output, source_commit, root=ROOT):
    manifest, payloads = manifest_for(root, source_commit)
    output = Path(output).expanduser()
    if output.is_symlink():
        raise ValueError("--output must not be a symlink")
    if output.exists():
        if not output.is_dir() or any(output.iterdir()):
            raise ValueError("--output must be a new or empty directory")
    else:
        output.mkdir(parents=True)

    target = output / f"niri-plus-components-{manifest['version']}.tar.gz"
    data = archive_bytes(manifest, payloads)
    target.write_bytes(data)
    return target, hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="new or empty output directory")
    parser.add_argument("--source-commit", required=True, help="full 40-character source Git commit")
    args = parser.parse_args()
    try:
        archive, digest = build_archive(args.output, args.source_commit)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps({"archive": str(archive), "sha256": digest}, sort_keys=True))


if __name__ == "__main__":
    main()
