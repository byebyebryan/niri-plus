import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
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


class ArchReferenceStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = json.loads((ROOT / "tools/reference/inputs.json").read_text(encoding="utf-8"))
        cls.component_manifest, cls.component_payloads = builder.manifest_for(ROOT, COMPONENT_COMMIT)
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
            self.assertIn("candidate", provenance["status"])
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


if __name__ == "__main__":
    unittest.main()
