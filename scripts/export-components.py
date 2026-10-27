#!/usr/bin/env python3
"""Write or check deterministic public examples exported from first-party components."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parents[1]
METADATA = Path("components/metadata.json")
MANIFEST = Path("examples/manifest.json")
GENERATOR = "scripts/export-components.py"


def read_component(root, relative_path):
    current = Path(root)
    for part in PurePosixPath(relative_path).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"component export source must not traverse symlinks: {relative_path}")
    if not current.is_file():
        raise ValueError(f"missing component export source: {relative_path}")
    return current.read_bytes()


def generated_record(spec, data, version, module):
    record = {
        "path": spec["path"],
        "sha256": hashlib.sha256(data).hexdigest(),
        "kind": "generated first-party component export",
        "module": module,
        "generated": True,
        "generated_by": GENERATOR,
        "generated_from": spec["component"],
        "component_version": version,
        "source": f"Niri Plus {module} component module",
    }
    if "profile" in spec:
        record["profile"] = spec["profile"]
    if "notes" in spec:
        record["notes"] = spec["notes"]
    return record


def render(root=ROOT):
    root = Path(root)
    metadata = json.loads((root / METADATA).read_text(encoding="utf-8"))
    if not isinstance(metadata, dict) or not isinstance(metadata.get("version"), str):
        raise ValueError("components/metadata.json has no component version")
    component_modules = {item["path"]: item["module"] for item in metadata.get("files", [])}
    component_paths = set(component_modules)
    exports = metadata.get("exports")
    if not isinstance(exports, list) or not exports:
        raise ValueError("components/metadata.json exports must be a non-empty list")

    output_files = {}
    records = []
    for spec in exports:
        if not isinstance(spec, dict) or not {"path", "component"} <= set(spec) or set(spec) - {"path", "component", "profile", "notes"}:
            raise ValueError("each export must define path and component, with optional profile/notes")
        destination = spec["path"]
        component = spec["component"]
        if not isinstance(destination, str) or not destination.startswith("examples/") or "\\" in destination:
            raise ValueError(f"invalid example export path: {destination!r}")
        normalized = PurePosixPath(destination)
        if normalized.is_absolute() or normalized.as_posix() != destination or ".." in normalized.parts:
            raise ValueError(f"example export path must be normalized and relative: {destination!r}")
        if destination in output_files:
            raise ValueError(f"duplicate example export path: {destination}")
        if not isinstance(component, str) or component not in component_paths:
            raise ValueError(f"export {destination} refers to undeclared component {component!r}")
        normalized_component = PurePosixPath(component)
        if normalized_component.is_absolute() or normalized_component.as_posix() != component or not component.startswith("components/") or ".." in normalized_component.parts:
            raise ValueError(f"invalid component export source path: {component!r}")
        if "profile" in spec and (not isinstance(spec["profile"], str) or not spec["profile"]):
            raise ValueError(f"invalid export profile for {destination}")
        if "notes" in spec and not isinstance(spec["notes"], str):
            raise ValueError(f"invalid export notes for {destination}")
        data = read_component(root, component)
        output_files[destination] = data
        records.append(generated_record(spec, data, metadata["version"], component_modules[component]))

    manifest_data = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    if not isinstance(manifest_data, dict) or not isinstance(manifest_data.get("files"), list):
        raise ValueError("examples/manifest.json must contain a files list")
    generated_paths = set(output_files)
    retained = [
        record for record in manifest_data["files"]
        if record.get("path") not in generated_paths and record.get("generated_by") != GENERATOR
    ]
    combined = retained + records
    paths = [record.get("path") for record in combined]
    if len(paths) != len(set(paths)):
        raise ValueError("examples/manifest.json contains duplicate paths")
    manifest_data["files"] = sorted(combined, key=lambda record: record["path"])
    output_files[str(MANIFEST)] = (json.dumps(manifest_data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return output_files


def update(root=ROOT, write=False):
    root = Path(root)
    expected = render(root)
    differences = []
    for relative, content in sorted(expected.items()):
        path = root / relative
        if not path.is_file() or path.read_bytes() != content:
            differences.append(relative)
            if write:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
    if differences and not write:
        return differences
    return differences


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="fail if exports or their manifest are stale")
    action.add_argument("--write", action="store_true", help="write component exports and provenance")
    args = parser.parse_args()
    try:
        differences = update(write=args.write)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    if args.check and differences:
        print("stale component exports: " + ", ".join(differences), file=sys.stderr)
        return 1
    print(json.dumps({"mode": "write" if args.write else "check", "changed": differences}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
