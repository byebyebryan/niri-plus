import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import subprocess
import tarfile
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
COMPONENT_COMMIT = "014a14241bd722186ae9248e71162e75cf7af7b1"
EXAMPLE_COMMIT = "b62df460884b5a4d5e8c7eeb05c132a0b26814ae"


def load_script(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stage = load_script("niri_plus_arch_reference_stage", ROOT / "scripts/stage-arch-reference.py")
builder = load_script("niri_plus_component_builder_for_stage_tests", ROOT / "scripts/build-components.py")


def rebuild_archive(data: bytes, *, mutate_name: str | None = None, mutation=None, extra=None) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as source:
        members = []
        for member in source.getmembers():
            stream = source.extractfile(member)
            payload = b"" if stream is None else stream.read()
            if member.name == mutate_name and mutation is not None:
                payload = mutation(payload)
            members.append((member.name, member.mode, payload))
    if extra is not None:
        members.append(extra)

    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name, mode, payload in members:
            member = tarfile.TarInfo(name)
            member.type = tarfile.REGTYPE
            member.mode = mode
            member.uid = 0
            member.gid = 0
            member.mtime = 0
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode="wb", filename="", mtime=0, compresslevel=9) as stream:
        stream.write(tar_stream.getvalue())
    return compressed.getvalue()


def synthetic_component_archive(version: str, source_commit: str, payload_count: int) -> tuple[bytes, bytes]:
    payloads = {
        f"components/appearance/future-{index:02}.py": f"# fixture payload {index}\n".encode()
        for index in range(payload_count)
    }
    records = [
        {
            "path": path,
            "mode": 0o644,
            "module": "appearance",
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
        for path, payload in sorted(payloads.items())
    ]
    manifest_bytes = (
        json.dumps({
            "schema_version": 1,
            "api_version": 1,
            "version": version,
            "source_commit": source_commit,
            "files": records,
        }, ensure_ascii=False, indent=2) + "\n"
    ).encode()
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        for name, payload in [("manifest.json", manifest_bytes), *sorted(payloads.items())]:
            member = tarfile.TarInfo(name)
            member.type = tarfile.REGTYPE
            member.mode = 0o644
            member.uid = 0
            member.gid = 0
            member.mtime = 0
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode="wb", filename="", mtime=0, compresslevel=9) as stream:
        stream.write(tar_stream.getvalue())
    return compressed.getvalue(), manifest_bytes


class ArchReferenceStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = json.loads((ROOT / "tools/reference/history/inputs-0.3.1.json").read_text(encoding="utf-8"))
        # Reproduce the published pin from its actual immutable tree. Current
        # candidate bytes must never be mislabeled with a historic commit.
        cls.release_tree = tempfile.TemporaryDirectory(prefix="niri-plus-release-tree-")
        cls.addClassCleanup(cls.release_tree.cleanup)
        archive = subprocess.run(["git", "archive", COMPONENT_COMMIT, "components"], cwd=ROOT,
                                 check=True, capture_output=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as source:
            source.extractall(cls.release_tree.name, filter="data")
        cls.component_manifest, cls.component_payloads = builder.manifest_for(cls.release_tree.name, COMPONENT_COMMIT)
        cls.component_archive = builder.archive_bytes(cls.component_manifest, cls.component_payloads)
        cls.component_manifest_bytes = (json.dumps(cls.component_manifest, ensure_ascii=False, indent=2) + "\n").encode()

    def test_candidate_inventory_is_the_separate_pinned_public_tuple(self):
        inputs = stage.validate_inputs(self.inputs)
        self.assertEqual(inputs["components"]["version"], "0.3.1")
        self.assertEqual(inputs["components"]["archive_sha256"], hashlib.sha256(self.component_archive).hexdigest())
        self.assertEqual(inputs["public_source"]["commit"], EXAMPLE_COMMIT)
        self.assertEqual(len(inputs["public_source"]["assets"]), len(set(inputs["public_source"]["assets"])))
        self.assertNotIn("examples/notifications/reference.json", inputs["public_source"]["assets"])
        self.assertEqual(inputs["identity"]["sha256"], "6dbb163103e911262b5c1a6b1dd8299863ea790f7a12e7fb264fe9603e8e2455")

        candidate_path = ROOT / "examples/notifications/reference.json"
        candidate_hash = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
        example_manifest = json.loads((ROOT / "examples/manifest.json").read_text(encoding="utf-8"))
        record = next(item for item in example_manifest["files"] if item["path"] == "examples/notifications/reference.json")
        self.assertEqual(record["sha256"], candidate_hash)
        self.assertEqual(record["kind"], "authored Arch reference configuration candidate")

    def test_accepts_future_exact_tuple_shape_without_relabeling_the_current_release(self):
        version = "0.4.1"
        component_commit = "a" * 40
        public_commit = "b" * 40
        archive, manifest_bytes = synthetic_component_archive(version, component_commit, 44)
        future = json.loads(json.dumps(self.inputs))
        future["components"].update({
            "version": version,
            "api_version": 1,
            "source_commit": component_commit,
            "archive_url": (
                "https://github.com/byebyebryan/niri-plus/releases/download/"
                f"components-v{version}/niri-plus-components-{version}.tar.gz"
            ),
            "archive_sha256": hashlib.sha256(archive).hexdigest(),
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        })
        future["public_source"].update({
            "commit": public_commit,
            "examples_manifest_sha256": "c" * 64,
        })

        validated = stage.validate_inputs(future)
        self.assertEqual(validated["components"]["version"], version)
        self.assertEqual(validated["public_source"]["commit"], public_commit)
        self.assertEqual(self.inputs["components"]["version"], "0.3.1")
        with self.assertRaisesRegex(ValueError, "archive SHA-256"):
            stage.component_manifest(self.component_archive, validated["components"])

        manifest, payloads = stage.component_manifest(archive, validated["components"])
        self.assertEqual(manifest["version"], version)
        self.assertEqual(len(payloads), 44)
        self.assertEqual(set(payloads), {record["path"] for record in manifest["files"]})

    def test_validate_inputs_rejects_floating_or_malformed_release_pins(self):
        def reject(change, message):
            candidate = json.loads(json.dumps(self.inputs))
            change(candidate)
            with self.assertRaisesRegex(ValueError, message):
                stage.validate_inputs(candidate)

        for version in ("0.4", "v0.4.1", "0.4.1-rc1", "01.4.1", "0.4.1+local"):
            with self.subTest(version=version):
                reject(lambda inputs: inputs["components"].__setitem__("version", version), "numeric x.y.z")

        for archive_url in (
            "https://github.com/byebyebryan/niri-plus/archive/refs/tags/components-v0.3.1.zip",
            "https://github.com/byebyebryan/niri-plus/releases/download/components-v0.4.1/niri-plus-components-0.4.1.tar.gz",
            "https://example.com/niri-plus-components-0.3.1.tar.gz",
        ):
            with self.subTest(archive_url=archive_url):
                reject(lambda inputs: inputs["components"].__setitem__("archive_url", archive_url), "immutable GitHub release URL")

        for commit in ("a" * 39, "a" * 41, "v0.4.1", "refs/heads/main"):
            with self.subTest(component_commit=commit):
                reject(lambda inputs: inputs["components"].__setitem__("source_commit", commit), "full 40-character hash")
            with self.subTest(public_commit=commit):
                reject(lambda inputs: inputs["public_source"].__setitem__("commit", commit), "full 40-character hash")

        reject(lambda inputs: inputs["components"].__setitem__("api_version", True), "API version must be 1")
        reject(lambda inputs: inputs["components"].__setitem__("archive_sha256", ""), "invalid SHA-256 for component archive")
        reject(lambda inputs: inputs["components"].__setitem__("manifest_sha256", ""), "invalid SHA-256 for component manifest")
        reject(lambda inputs: inputs["public_source"].__setitem__("repository", "https://github.com/example/niri-plus.git"), "public example source must use the Niri Plus repository")

    def test_component_archive_checks_manifest_payloads_and_modes(self):
        manifest, payloads = stage.component_manifest(self.component_archive, self.inputs["components"])
        self.assertEqual(manifest["version"], "0.3.1")
        self.assertEqual(len(payloads), 27)
        self.assertEqual(payloads["components/appearance/render.py"], self.component_payloads["components/appearance/render.py"])

        first_path = next(iter(payloads))
        mutated = rebuild_archive(
            self.component_archive,
            mutate_name=first_path,
            mutation=lambda value: bytes([value[0] ^ 1]) + value[1:],
        )
        pin = dict(self.inputs["components"], archive_sha256=hashlib.sha256(mutated).hexdigest())
        with self.assertRaisesRegex(ValueError, "payload SHA-256 mismatch"):
            stage.component_manifest(mutated, pin)

        unsafe = rebuild_archive(self.component_archive, extra=("../outside", 0o644, b"escape"))
        pin = dict(self.inputs["components"], archive_sha256=hashlib.sha256(unsafe).hexdigest())
        with self.assertRaisesRegex(ValueError, "not normalized and relative"):
            stage.component_manifest(unsafe, pin)
        with self.assertRaisesRegex(ValueError, "not normalized and relative"):
            stage.normalized_path(".", prefix="")

    def test_stages_exact_source_commit_appearance_and_provenance(self):
        with tempfile.TemporaryDirectory(prefix="niri-plus-reference-stage-") as temporary:
            base = Path(temporary)
            inputs_path = base / "inputs.json"
            inputs = json.loads(json.dumps(self.inputs))
            # A local read-only source is used to keep this test offline; the
            # committed production inventory points only to the public GitHub URL.
            inputs["public_source"]["repository"] = str(ROOT)
            inputs_bytes = (json.dumps(inputs, indent=2) + "\n").encode()
            inputs_path.write_bytes(inputs_bytes)
            output = base / "stage"

            def fetcher(url, *, maximum_bytes):
                self.assertEqual(url, inputs["components"]["archive_url"])
                self.assertEqual(maximum_bytes, stage.MAX_COMPONENT_ARCHIVE)
                return self.component_archive

            with mock.patch.object(stage.os, "geteuid", return_value=1000):
                result = stage.stage_reference(output, inputs_path, fetcher=fetcher)

            self.assertTrue((output / "bundle/manifest.json").is_file())
            self.assertTrue((output / "source/design/identity.json").is_file())
            self.assertTrue((output / "source/examples/manifest.json").is_file())
            self.assertTrue((output / "appearance/neutral-slate.rasi").is_file())
            self.assertTrue((output / "appearance/swaync.css").is_file())
            self.assertFalse((output / ".source-work").exists())
            self.assertFalse((output / "source/examples/notifications/reference.json").exists())
            self.assertFalse(any(path.name == ".git" for path in output.rglob(".git")))

            niri = (output / "source/examples/niri/config.kdl").read_text(encoding="utf-8")
            self.assertIn("default-column-width { proportion 0.66667; }", niri)
            self.assertIn('Mod+E { spawn "dolphin"; }', niri)

            provenance = json.loads((output / "provenance.json").read_text(encoding="utf-8"))
            self.assertEqual(provenance["status"], "candidate input stage; not a published component release")
            self.assertEqual(provenance["inputs_manifest"]["path"], "external --inputs file")
            self.assertEqual(provenance["inputs_manifest"]["sha256"], hashlib.sha256(inputs_bytes).hexdigest())
            self.assertEqual(provenance["components"]["archive_sha256"], hashlib.sha256(self.component_archive).hexdigest())
            self.assertEqual(provenance["identity"]["source_commit"], EXAMPLE_COMMIT)
            self.assertEqual(provenance["public_source"]["commit"], EXAMPLE_COMMIT)
            self.assertEqual(provenance["appearance"]["renderer_version"], "0.3.1")
            self.assertEqual(provenance["appearance"]["identity_sha256"], self.inputs["identity"]["sha256"])
            self.assertEqual(result["output"], str(output))
            serialized = json.dumps(provenance)
            self.assertNotIn("niri-plus-vm", serialized)

    def test_failed_stage_leaves_no_output_and_refuses_corrupt_archive(self):
        with tempfile.TemporaryDirectory(prefix="niri-plus-reference-corrupt-") as temporary:
            base = Path(temporary)
            inputs_path = base / "inputs.json"
            inputs = json.loads(json.dumps(self.inputs))
            inputs["public_source"]["repository"] = str(ROOT)
            inputs_path.write_text(json.dumps(inputs), encoding="utf-8")
            output = base / "stage"

            with mock.patch.object(stage.os, "geteuid", return_value=1000):
                with self.assertRaisesRegex(ValueError, "archive SHA-256"):
                    stage.stage_reference(output, inputs_path, fetcher=lambda _url, **_kwargs: b"changed")
            self.assertFalse(output.exists())
            self.assertFalse(list(base.glob(".stage.stage-*")))

    def test_refuses_root_existing_output_and_symlink_ancestor(self):
        with tempfile.TemporaryDirectory(prefix="niri-plus-reference-boundary-") as temporary:
            base = Path(temporary)
            with mock.patch.object(stage.os, "geteuid", return_value=0):
                with self.assertRaisesRegex(ValueError, "ordinary user"):
                    stage.stage_reference(base / "never-created", base / "missing-inputs.json")

            existing = base / "existing"
            existing.mkdir()
            with self.assertRaisesRegex(ValueError, "must be new"):
                stage.output_path(existing)

            real = base / "real"
            real.mkdir()
            link = base / "link"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "traverses a symlink"):
                stage.output_path(link / "stage")

            with self.assertRaisesRegex(ValueError, "parent-directory"):
                stage.output_path(base / ".." / "outside")


class CurrentPublishedReferenceTests(unittest.TestCase):
    def test_published_041_bytes_and_complete_direct_controls_stage(self):
        inputs = json.loads((ROOT / "tools/reference/inputs.json").read_text())
        with tempfile.TemporaryDirectory(prefix="niri-plus-current-reference-") as temporary:
            base = Path(temporary)
            code_tree = base / "code"
            code_tree.mkdir()
            commit = inputs["components"]["source_commit"]
            archived = subprocess.run(["git", "archive", commit, "components"], cwd=ROOT,
                                      check=True, capture_output=True).stdout
            with tarfile.open(fileobj=io.BytesIO(archived)) as source:
                source.extractall(code_tree, filter="data")
            manifest, payloads = builder.manifest_for(code_tree, commit)
            archive = builder.archive_bytes(manifest, payloads)
            self.assertEqual(hashlib.sha256(archive).hexdigest(), inputs["components"]["archive_sha256"])
            checked, files = stage.component_manifest(archive, inputs["components"])
            self.assertEqual((checked["version"], len(files)), ("0.4.1", 44))
            # Read the actual public-example commit through an offline clone.
            inputs["public_source"]["repository"] = str(ROOT)
            inputs_path = base / "inputs.json"
            inputs_path.write_text(json.dumps(inputs))
            output = base / "staged"
            with mock.patch.object(stage.os, "geteuid", return_value=1000):
                stage.stage_reference(output, inputs_path, fetcher=lambda _url, **_kwargs: archive)
            library = output / "bundle/components/desktop/lib/niri_plus_controls"
            self.assertEqual(len(list(library.glob("*.py"))), 13)
            for name in ("desktop-network-menu", "desktop-audio-menu", "desktop-bluetooth-menu", "desktop-controls"):
                self.assertTrue((output / "bundle/components/desktop/bin" / name).is_file())
            roles = json.loads((output / "appearance/roles.json").read_text())
            self.assertEqual(roles["colors"]["workspace_background"], "#000000")
            self.assertEqual(roles["colors"]["overview_background"], "#111213")
            for name in ("network", "audio", "bluetooth"):
                self.assertFalse((output / f"source/examples/desktop/niri-plus-{name}.desktop").exists())
            self.assertTrue((output / "source/examples/desktop/niri-plus-session.desktop").is_file())


if __name__ == "__main__":
    unittest.main()
