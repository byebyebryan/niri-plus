#!/usr/bin/env python3
"""Stage verified Niri Plus inputs and appearance previews for the Arch guide.

This candidate helper writes only to a new, explicit user-selected directory.
It does not install packages, edit normal configuration paths, or manage services.
"""

from __future__ import annotations

import argparse
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
from typing import Any, Callable
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUTS = ROOT / "tools/reference/inputs.json"
MAX_COMPONENT_ARCHIVE = 32 * 1024 * 1024
MAX_UNPACKED_COMPONENTS = 128 * 1024 * 1024
MAX_SOURCE_FILE = 16 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 256
SUPPORTED_MODES = {0o644, 0o755}
COMPONENT_MODULES = {"desktop", "shell", "appearance"}
REQUIRED_RENDERER_COMPONENTS = (
    "components/appearance/__init__.py",
    "components/appearance/ini_merge.py",
    "components/appearance/render.py",
    "components/appearance/sddm.py",
)
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
GIT_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
COMPONENT_VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_path(value: Any, *, prefix: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError(f"invalid relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or path.as_posix() != value or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"path is not normalized and relative: {value!r}")
    if not value.startswith(prefix):
        raise ValueError(f"path must be under {prefix}: {value!r}")
    return path


def require_hash(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ValueError(f"invalid SHA-256 for {label}")
    return value


def validate_component_pin(components: Any) -> dict[str, Any]:
    """Validate the immutable release tuple shared by input stagers."""
    if not isinstance(components, dict) or set(components) != {
        "version", "api_version", "source_commit", "archive_url", "archive_sha256", "manifest_sha256"
    }:
        raise ValueError("invalid component bundle pin")
    version = components.get("version")
    if not isinstance(version, str) or not COMPONENT_VERSION.fullmatch(version):
        raise ValueError("component version must be numeric x.y.z")
    if type(components.get("api_version")) is not int or components["api_version"] != 1:
        raise ValueError("component API version must be 1")
    if not isinstance(components.get("source_commit"), str) or not GIT_COMMIT.fullmatch(components["source_commit"]):
        raise ValueError("invalid component source commit; expected a full 40-character hash")
    archive_url = components.get("archive_url")
    expected_archive_url = (
        "https://github.com/byebyebryan/niri-plus/releases/download/"
        f"components-v{version}/niri-plus-components-{version}.tar.gz"
    )
    if archive_url != expected_archive_url:
        raise ValueError("component archive URL must match the immutable GitHub release URL for its version")
    require_hash(components.get("archive_sha256"), "component archive")
    require_hash(components.get("manifest_sha256"), "component manifest")
    return components


def validate_inputs(inputs: Any) -> dict[str, Any]:
    if not isinstance(inputs, dict) or set(inputs) != {"schema_version", "components", "identity", "public_source"}:
        raise ValueError("input inventory must define schema_version, components, identity, and public_source")
    if inputs.get("schema_version") != 1:
        raise ValueError("unsupported Arch reference input inventory schema")

    validate_component_pin(inputs["components"])

    identity = inputs["identity"]
    if not isinstance(identity, dict) or set(identity) != {"path", "sha256"}:
        raise ValueError("invalid independent appearance identity pin")
    if identity.get("path") != "design/identity.json":
        raise ValueError("the identity path must be design/identity.json")
    require_hash(identity.get("sha256"), "appearance identity")

    source = inputs["public_source"]
    if not isinstance(source, dict) or set(source) != {"repository", "commit", "examples_manifest_sha256", "assets"}:
        raise ValueError("invalid public example source pin")
    if source.get("repository") != "https://github.com/byebyebryan/niri-plus.git":
        repository = source.get("repository")
        local_repository = isinstance(repository, str) and Path(repository).is_dir()
        if not local_repository:
            raise ValueError("public example source must use the Niri Plus repository")
    if not isinstance(source.get("commit"), str) or not GIT_COMMIT.fullmatch(source["commit"]):
        raise ValueError("invalid public example source commit; expected a full 40-character hash")
    require_hash(source.get("examples_manifest_sha256"), "public examples manifest")
    assets = source.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("public source must list at least one explicit example asset")
    seen: set[str] = set()
    for asset in assets:
        normalized_path(asset, prefix="examples/")
        if asset in seen or asset == "examples/manifest.json":
            raise ValueError(f"duplicate or reserved public example asset: {asset!r}")
        seen.add(asset)
    return inputs


def fetch_https(url: str, *, maximum_bytes: int) -> bytes:
    request = Request(url, headers={"User-Agent": "niri-plus-arch-reference-candidate/1"})
    with urlopen(request, timeout=60) as response:
        if not response.geturl().startswith("https://"):
            raise ValueError("download redirected outside HTTPS")
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > maximum_bytes:
            raise ValueError("download exceeded its size limit")
        data = response.read(maximum_bytes + 1)
    if len(data) > maximum_bytes:
        raise ValueError("download exceeded its size limit")
    return data


def component_manifest(data: bytes, pin: dict[str, Any]) -> tuple[dict[str, Any], dict[str, bytes]]:
    if len(data) > MAX_COMPONENT_ARCHIVE:
        raise ValueError("component archive exceeded the configured size limit")
    if sha256(data) != pin["archive_sha256"]:
        raise ValueError("component archive SHA-256 does not match the published pin")

    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        members = archive.getmembers()
        if not members or len(members) > MAX_ARCHIVE_MEMBERS:
            raise ValueError("component archive has an empty or oversized member list")
        by_name: dict[str, tarfile.TarInfo] = {}
        for member in members:
            normalized_path(member.name, prefix="")
            if member.name in by_name or not member.isfile() or member.issym() or member.islnk():
                raise ValueError(f"unsupported or duplicate component archive member: {member.name}")
            if member.size < 0 or member.size > MAX_UNPACKED_COMPONENTS:
                raise ValueError(f"invalid component member size: {member.name}")
            by_name[member.name] = member

        manifest_member = by_name.get("manifest.json")
        if manifest_member is None:
            raise ValueError("component archive has no manifest.json")
        manifest_stream = archive.extractfile(manifest_member)
        if manifest_stream is None:
            raise ValueError("cannot read component manifest")
        manifest_bytes = manifest_stream.read(MAX_UNPACKED_COMPONENTS + 1)
        if len(manifest_bytes) > MAX_UNPACKED_COMPONENTS:
            raise ValueError("component manifest exceeded the configured size limit")
        if sha256(manifest_bytes) != pin["manifest_sha256"]:
            raise ValueError("component manifest SHA-256 does not match the published pin")
        manifest = json.loads(manifest_bytes)

        if not isinstance(manifest, dict) or (
            manifest.get("schema_version") != 1
            or manifest.get("version") != pin["version"]
            or manifest.get("api_version") != pin["api_version"]
            or manifest.get("source_commit") != pin["source_commit"]
        ):
            raise ValueError("component manifest does not match the published release tuple")
        records = manifest.get("files")
        if not isinstance(records, list) or not records:
            raise ValueError("component manifest must list at least one payload file")

        payloads: dict[str, bytes] = {}
        seen: set[str] = set()
        expected_names = {"manifest.json"}
        total = len(manifest_bytes)
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("component manifest contains a non-object file record")
            path_text = record.get("path", "")
            relative = normalized_path(path_text, prefix="components/")
            mode = record.get("mode")
            module = record.get("module")
            if (
                path_text in seen
                or mode not in SUPPORTED_MODES
                or module not in COMPONENT_MODULES
                or not path_text.startswith(f"components/{module}/")
            ):
                raise ValueError(f"invalid component manifest record: {path_text!r}")
            expected_hash = require_hash(record.get("sha256"), path_text)
            seen.add(path_text)
            expected_names.add(path_text)
            member = by_name.get(path_text)
            if member is None or stat.S_IMODE(member.mode) != mode:
                raise ValueError(f"component archive is missing {path_text} or has an unexpected mode")
            total += member.size
            if total > MAX_UNPACKED_COMPONENTS:
                raise ValueError("component archive expands beyond the configured size limit")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"cannot read component file {path_text}")
            payload = stream.read(member.size + 1)
            if len(payload) != member.size or sha256(payload) != expected_hash:
                raise ValueError(f"component payload SHA-256 mismatch for {path_text}")
            payloads[path_text] = payload

        if set(by_name) != expected_names:
            extras = sorted(set(by_name) - expected_names)
            missing = sorted(expected_names - set(by_name))
            raise ValueError(f"component archive member set differs from manifest; extra={extras}, missing={missing}")
        return manifest, payloads


def write_component_bundle(data: bytes, destination: Path, pin: dict[str, Any]) -> dict[str, Any]:
    manifest, payloads = component_manifest(data, pin)
    destination.mkdir(mode=0o755)
    for relative, payload in payloads.items():
        path = destination.joinpath(*PurePosixPath(relative).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        record = next(item for item in manifest["files"] if item["path"] == relative)
        path.chmod(record["mode"])
    manifest_path = destination / "manifest.json"
    # The original bytes are the hash-pinned source of truth. Preserve them.
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        stream = archive.extractfile("manifest.json")
        if stream is None:
            raise ValueError("component manifest disappeared after validation")
        manifest_bytes = stream.read()
    manifest_path.write_bytes(manifest_bytes)
    manifest_path.chmod(0o644)
    return manifest


def source_repository_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
    })
    return env


def checked_out_source(source: dict[str, Any], work_dir: Path) -> Path:
    checkout = work_dir / "checkout"
    checkout.mkdir(mode=0o700)
    env = source_repository_env()
    git = ["git", "-C", str(checkout)]

    def run(arguments: list[str]) -> str:
        result = subprocess.run(
            [*git, *arguments],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        return result.stdout.strip()

    subprocess.run([*git, "init", "--quiet"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=env)
    subprocess.run([*git, "remote", "add", "origin", source["repository"]], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=env)
    subprocess.run(
        [*git, "fetch", "--quiet", "--depth=1", "origin", source["commit"]],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env=env,
    )
    subprocess.run([*git, "checkout", "--quiet", "--detach", "FETCH_HEAD"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=env)
    if run(["rev-parse", "HEAD"]) != source["commit"]:
        raise ValueError("public source checkout did not resolve to its pinned commit")
    if run(["status", "--porcelain", "--untracked-files=all"]):
        raise ValueError("public source checkout is not clean")
    return checkout


def checked_file(root: Path, relative: str, *, maximum_bytes: int = MAX_SOURCE_FILE) -> tuple[bytes, int]:
    path = root
    for part in PurePosixPath(relative).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f"pinned source asset traverses a symlink: {relative}")
    if not path.is_file():
        raise ValueError(f"pinned source asset is missing: {relative}")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode not in SUPPORTED_MODES:
        raise ValueError(f"unsupported mode {mode:o} for pinned source asset: {relative}")
    data = path.read_bytes()
    if len(data) > maximum_bytes:
        raise ValueError(f"pinned source asset exceeds the size limit: {relative}")
    return data, mode


def validate_examples_manifest(data: bytes, expected_hash: str) -> dict[str, dict[str, Any]]:
    if sha256(data) != expected_hash:
        raise ValueError("public examples manifest SHA-256 does not match the pinned source snapshot")
    manifest = json.loads(data)
    records = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(records, list):
        raise ValueError("public examples manifest has no files list")
    by_path: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("public examples manifest contains an invalid record")
        path = record.get("path")
        normalized_path(path, prefix="")
        if path in by_path:
            raise ValueError(f"duplicate path in public examples manifest: {path}")
        require_hash(record.get("sha256"), f"public example {path}")
        by_path[path] = record
    return by_path


def stage_public_assets(
    source_root: Path,
    destination: Path,
    source_pin: dict[str, Any],
    identity_pin: dict[str, Any],
    component_manifest: dict[str, Any],
) -> tuple[dict[str, Any], bytes, list[dict[str, Any]]]:
    destination.mkdir(mode=0o755)
    example_manifest_bytes, _ = checked_file(source_root, "examples/manifest.json")
    examples_by_path = validate_examples_manifest(example_manifest_bytes, source_pin["examples_manifest_sha256"])
    (destination / "examples").mkdir()
    manifest_target = destination / "examples/manifest.json"
    manifest_target.write_bytes(example_manifest_bytes)
    manifest_target.chmod(0o644)

    component_records = {record["path"]: record for record in component_manifest["files"]}
    asset_receipts: list[dict[str, Any]] = []
    for relative in source_pin["assets"]:
        expected_record = examples_by_path.get(relative)
        if expected_record is None:
            raise ValueError(f"pinned asset is not listed in examples/manifest.json: {relative}")
        payload, mode = checked_file(source_root, relative)
        digest = sha256(payload)
        if digest != expected_record["sha256"]:
            raise ValueError(f"public example hash differs from its pinned manifest: {relative}")

        if expected_record.get("generated") is True:
            if (
                expected_record.get("component_version") != component_manifest["version"]
                or expected_record.get("generated_by") != "scripts/export-components.py"
            ):
                raise ValueError(f"generated example uses an unexpected component version: {relative}")
            component_path = expected_record.get("generated_from")
            component_record = component_records.get(component_path)
            if (
                not isinstance(component_path, str)
                or component_record is None
                or component_record.get("sha256") != digest
            ):
                raise ValueError(f"generated example does not match its component payload: {relative}")

        target = destination.joinpath(*PurePosixPath(relative).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        target.chmod(mode)
        asset_receipts.append({
            "path": relative,
            "sha256": digest,
            "mode": mode,
            "kind": expected_record.get("kind", "unknown"),
            "generated_from": expected_record.get("generated_from"),
        })

    identity_bytes, identity_mode = checked_file(source_root, identity_pin["path"])
    if sha256(identity_bytes) != identity_pin["sha256"]:
        raise ValueError("appearance identity SHA-256 does not match its independent pin")
    identity_value = json.loads(identity_bytes)
    terminal_value = identity_value.get("terminal") if isinstance(identity_value, dict) else None
    terminal_colors = terminal_value.get("colors") if isinstance(terminal_value, dict) else None
    if (
        not isinstance(identity_value, dict)
        or identity_value.get("schema_version") != 2
        or identity_value.get("selected_candidate") != "neutral-slate"
        or not isinstance(terminal_value, dict)
        or terminal_value.get("variant") != "balanced-plus"
        or not isinstance(terminal_colors, dict)
        or terminal_colors.get("background") != "#000000"
    ):
        raise ValueError("independent identity does not select Neutral Slate and pure-black Balanced+")
    identity_target = destination.joinpath(*PurePosixPath(identity_pin["path"]).parts)
    identity_target.parent.mkdir(parents=True, exist_ok=True)
    identity_target.write_bytes(identity_bytes)
    identity_target.chmod(identity_mode)
    return examples_by_path, identity_bytes, asset_receipts


def verify_appearance_output(
    appearance: Path,
    component_manifest: dict[str, Any],
    identity_hash: str,
    component_pin: dict[str, Any],
) -> dict[str, Any]:
    manifest_path = appearance / "manifest.json"
    theme_path = appearance / "theme.json"
    if manifest_path.is_symlink() or theme_path.is_symlink() or not manifest_path.is_file() or not theme_path.is_file():
        raise ValueError("appearance renderer did not produce its manifest and theme preview")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("appearance preview manifest has an invalid shape")
    if (
        manifest.get("schema_version") != 1
        or manifest.get("renderer_version") != component_pin["version"]
        or manifest.get("identity_sha256") != identity_hash
    ):
        raise ValueError("appearance preview provenance does not match the staged component and identity pins")

    expected_components = {record["path"]: record["sha256"] for record in component_manifest["files"]}
    code_hashes = manifest.get("code_sha256")
    if not isinstance(code_hashes, dict):
        raise ValueError("appearance preview does not identify renderer code hashes")
    for relative in REQUIRED_RENDERER_COMPONENTS:
        if code_hashes.get(relative) != expected_components.get(relative):
            raise ValueError(f"appearance preview renderer code hash differs from component bundle: {relative}")

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("appearance preview has no output file inventory")
    expected_files = {"manifest.json"}
    seen: set[str] = set()
    for record in files:
        if not isinstance(record, dict):
            raise ValueError("appearance preview has an invalid output record")
        relative = record.get("path", "")
        normalized_path(relative, prefix="")
        if relative in seen:
            raise ValueError(f"duplicate appearance preview output: {relative}")
        digest = require_hash(record.get("sha256"), f"appearance preview {relative}")
        seen.add(relative)
        expected_files.add(relative)
        target = appearance.joinpath(*PurePosixPath(relative).parts)
        if target.is_symlink() or not target.is_file() or sha256(target.read_bytes()) != digest:
            raise ValueError(f"appearance preview output hash mismatch: {relative}")

    actual_files: set[str] = set()
    for path in appearance.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"appearance preview contains a symlink: {path.relative_to(appearance)}")
        if path.is_file():
            actual_files.add(path.relative_to(appearance).as_posix())
    if actual_files != expected_files:
        raise ValueError("appearance preview file set differs from its manifest")

    theme = json.loads(theme_path.read_text(encoding="utf-8"))
    if not isinstance(theme, dict) or not isinstance(theme.get("profile"), dict) or not isinstance(theme.get("terminal"), dict):
        raise ValueError("appearance preview theme has an invalid shape")
    terminal = theme["terminal"]
    if not isinstance(terminal.get("colors"), dict):
        raise ValueError("appearance preview terminal colors have an invalid shape")
    if (
        theme["profile"].get("id") != "neutral-slate"
        or terminal.get("variant") != "balanced-plus"
        or terminal["colors"].get("background") != "#000000"
    ):
        raise ValueError("appearance preview did not render the selected Neutral Slate/Balanced+ identity")
    return manifest


def render_appearance(bundle: Path, identity: Path, output: Path, component_manifest: dict[str, Any], pin: dict[str, Any]) -> dict[str, Any]:
    command = [
        sys.executable,
        "-B",
        str(bundle / "components/appearance/render.py"),
        "--identity",
        str(identity),
        "--output",
        str(output),
    ]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ValueError(f"appearance renderer failed: {detail or result.returncode}")
    return verify_appearance_output(output, component_manifest, sha256(identity.read_bytes()), pin)


def output_path(raw: Path) -> Path:
    candidate = raw.expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    if ".." in candidate.parts:
        raise ValueError("output path must not use parent-directory components")
    if candidate.name in {"", ".", ".."} or candidate.parent == candidate:
        raise ValueError("choose a new output directory, not a filesystem root")
    parent = candidate.parent
    for ancestor in reversed((parent, *parent.parents)):
        if ancestor.is_symlink():
            raise ValueError(f"output path traverses a symlink: {ancestor}")
        if not ancestor.exists():
            raise ValueError(f"output parent must already exist: {ancestor}")
        if not ancestor.is_dir():
            raise ValueError(f"output parent is not a directory: {ancestor}")
    resolved_parent = parent.resolve(strict=True)
    candidate = resolved_parent / candidate.name
    if candidate.exists() or candidate.is_symlink():
        raise ValueError(f"output directory must be new: {candidate}")
    return candidate


def assert_non_root() -> None:
    if os.geteuid() == 0:
        raise ValueError("run this input stager as an ordinary user, not root")


def stage_reference(
    output: Path,
    inputs_path: Path = DEFAULT_INPUTS,
    *,
    fetcher: Callable[..., bytes] = fetch_https,
) -> dict[str, Any]:
    assert_non_root()
    inputs_bytes = inputs_path.read_bytes()
    inputs = validate_inputs(json.loads(inputs_bytes))
    destination = output_path(output)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.stage-", dir=destination.parent))
    try:
        component_archive = fetcher(inputs["components"]["archive_url"], maximum_bytes=MAX_COMPONENT_ARCHIVE)
        bundle = staging / "bundle"
        components_manifest = write_component_bundle(component_archive, bundle, inputs["components"])

        source_work = staging / ".source-work"
        source_work.mkdir(mode=0o700)
        source_root = checked_out_source(inputs["public_source"], source_work)
        source_out = staging / "source"
        _, identity_bytes, asset_records = stage_public_assets(
            source_root,
            source_out,
            inputs["public_source"],
            inputs["identity"],
            components_manifest,
        )
        shutil.rmtree(source_work)

        appearance_path = staging / "appearance"
        appearance_manifest = render_appearance(
            bundle,
            source_out / "design/identity.json",
            appearance_path,
            components_manifest,
            inputs["components"],
        )

        components_manifest_path = bundle / "manifest.json"
        appearance_manifest_path = appearance_path / "manifest.json"
        try:
            inputs_label = inputs_path.resolve(strict=True).relative_to(ROOT).as_posix()
        except ValueError:
            inputs_label = "external --inputs file"
        provenance = {
            "schema_version": 1,
            "status": "candidate input stage; not a published component release",
            "writes": "new output tree only",
            "stager": {
                "path": "scripts/stage-arch-reference.py",
                "sha256": sha256(Path(__file__).read_bytes()),
            },
            "inputs_manifest": {
                "path": inputs_label,
                "sha256": sha256(inputs_bytes),
            },
            "components": {
                "version": inputs["components"]["version"],
                "api_version": inputs["components"]["api_version"],
                "source_commit": inputs["components"]["source_commit"],
                "archive_url": inputs["components"]["archive_url"],
                "archive_sha256": sha256(component_archive),
                "manifest_sha256": sha256(components_manifest_path.read_bytes()),
                "file_count": len(components_manifest["files"]),
                "files": components_manifest["files"],
            },
            "identity": {
                "path": inputs["identity"]["path"],
                "sha256": sha256(identity_bytes),
                "source_commit": inputs["public_source"]["commit"],
            },
            "public_source": {
                "repository": inputs["public_source"]["repository"],
                "commit": inputs["public_source"]["commit"],
                "examples_manifest_sha256": inputs["public_source"]["examples_manifest_sha256"],
                "assets": asset_records,
            },
            "appearance": {
                "renderer_version": appearance_manifest["renderer_version"],
                "identity_sha256": appearance_manifest["identity_sha256"],
                "manifest_sha256": sha256(appearance_manifest_path.read_bytes()),
                "files": appearance_manifest["files"],
                "code_sha256": appearance_manifest["code_sha256"],
            },
        }
        (staging / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (staging / "provenance.json").chmod(0o644)
        staging.rename(destination)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {
        "output": str(destination),
        "bundle": str(destination / "bundle"),
        "source": str(destination / "source"),
        "appearance": str(destination / "appearance"),
        "provenance": str(destination / "provenance.json"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="new directory for verified inputs and previews")
    parser.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS, help="reviewed input inventory JSON")
    args = parser.parse_args(argv)
    try:
        staged = stage_reference(args.output, args.inputs)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, subprocess.CalledProcessError, tarfile.TarError) as error:
        print(f"stage-arch-reference.py: {error}", file=sys.stderr)
        return 1
    print("Verified Arch reference inputs staged (candidate helper; no packages, services, or user configs changed):")
    for name in ("output", "bundle", "source", "appearance", "provenance"):
        print(f"  {name}: {staged[name]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
