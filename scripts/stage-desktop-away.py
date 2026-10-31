#!/usr/bin/env python3
"""Verify a complete immutable bundle and stage only the opt-in away companion.

Writes to a new directory only. Does not install files, manage services, select
the core desktop bundle, or qualify a desktop/reference installation.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUTS = ROOT / "tools/reference/away-inputs.json"
SELECTED_MODES = {
    "components/desktop/bin/desktop-away": 0o755,
    "components/desktop/systemd/user/desktop-away.service": 0o644,
}

_spec = importlib.util.spec_from_file_location(
    "niri_plus_away_archive_verifier", ROOT / "scripts/stage-arch-reference.py"
)
verifier = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verifier)


def validate_inputs(inputs: Any) -> dict[str, Any]:
    if not isinstance(inputs, dict) or set(inputs) != {"schema_version", "components", "selected_files"}:
        raise ValueError("away inputs must define schema_version, components, and selected_files")
    if type(inputs["schema_version"]) is not int or inputs["schema_version"] != 1:
        raise ValueError("unsupported away input inventory schema")
    verifier.validate_component_pin(inputs["components"])
    if inputs["selected_files"] != list(SELECTED_MODES):
        raise ValueError("away selection must contain only the canonical helper and unit, in inventory order")
    return inputs


def stage_away(
    output: Path,
    inputs_path: Path = DEFAULT_INPUTS,
    *,
    fetcher: Callable[..., bytes] = verifier.fetch_https,
) -> dict[str, str]:
    verifier.assert_non_root()
    inputs_bytes = inputs_path.read_bytes()
    inputs = validate_inputs(json.loads(inputs_bytes))
    destination = verifier.output_path(output)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.stage-", dir=destination.parent))
    try:
        archive_bytes = fetcher(inputs["components"]["archive_url"], maximum_bytes=verifier.MAX_COMPONENT_ARCHIVE)
        # Validate every archive member, including all unselected core payloads.
        manifest, payloads = verifier.component_manifest(archive_bytes, inputs["components"])
        records = {item["path"]: item for item in manifest["files"]}
        selected = []
        for relative, mode in SELECTED_MODES.items():
            record = records.get(relative)
            if record is None or record["mode"] != mode:
                raise ValueError(f"away bundle is missing the expected file or mode: {relative}")
            path = staging / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payloads[relative])
            path.chmod(mode)
            selected.append(record)

        # Retain the full verified artifact/manifest separately from the two
        # selected payloads; this is not a partially extracted core bundle.
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
            manifest_bytes = archive.extractfile("manifest.json").read()
        (staging / "archive.tar.gz").write_bytes(archive_bytes)
        (staging / "manifest.json").write_bytes(manifest_bytes)
        (staging / "inputs.json").write_bytes(inputs_bytes)
        provenance = {
            "schema_version": 1,
            "status": "verified optional away inputs; no installation or reference qualification",
            "writes": "new output tree only",
            "stager": {
                "path": "scripts/stage-desktop-away.py",
                "sha256": verifier.sha256(Path(__file__).read_bytes()),
                "archive_verifier_sha256": verifier.sha256((ROOT / "scripts/stage-arch-reference.py").read_bytes()),
            },
            "inputs_sha256": verifier.sha256(inputs_bytes),
            "components": inputs["components"],
            "validated_file_count": len(payloads),
            "selected_files": selected,
        }
        (staging / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        for name in ("archive.tar.gz", "manifest.json", "inputs.json", "provenance.json"):
            (staging / name).chmod(0o644)
        staging.rename(destination)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {"output": str(destination), "provenance": str(destination / "provenance.json")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="new directory for the two verified away files and receipt")
    parser.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS, help="reviewed optional away input inventory JSON")
    args = parser.parse_args(argv)
    try:
        result = stage_away(args.output, args.inputs)
    except (OSError, ValueError, TypeError, KeyError, tarfile.TarError) as error:
        print(f"stage-desktop-away.py: {error}", file=sys.stderr)
        return 1
    print("Verified optional away inputs staged; no installed files or services changed:")
    for name, path in result.items():
        print(f"  {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
