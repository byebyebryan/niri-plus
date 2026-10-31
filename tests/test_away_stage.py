import copy
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


def load_script(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stage = load_script("niri_plus_optional_away_stage_tests", ROOT / "scripts/stage-desktop-away.py")
builder = load_script("niri_plus_away_stage_builder", ROOT / "scripts/build-components.py")


class AwayStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = json.loads(stage.DEFAULT_INPUTS.read_bytes())
        cls.release_tree = tempfile.TemporaryDirectory(prefix="niri-plus-away-release-")
        cls.addClassCleanup(cls.release_tree.cleanup)
        commit = cls.inputs["components"]["source_commit"]
        archived = subprocess.run(["git", "archive", commit, "components"], cwd=ROOT,
                                  check=True, capture_output=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archived)) as archive:
            archive.extractall(cls.release_tree.name, filter="data")
        cls.manifest, cls.payloads = builder.manifest_for(cls.release_tree.name, commit)
        cls.archive = builder.archive_bytes(cls.manifest, cls.payloads)

    def fixture_inputs(self, base, *, archive=None, manifest=None):
        inputs = copy.deepcopy(self.inputs)
        if archive is not None:
            inputs["components"]["archive_sha256"] = hashlib.sha256(archive).hexdigest()
        if manifest is not None:
            manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
            inputs["components"]["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
        path = base / "inputs.json"
        path.write_text(json.dumps(inputs))
        return path

    def run_stage(self, output, inputs_path=stage.DEFAULT_INPUTS, archive=None):
        data = self.archive if archive is None else archive
        with mock.patch.object(stage.verifier.os, "geteuid", return_value=1000):
            return stage.stage_away(output, inputs_path, fetcher=lambda _url, **_kwargs: data)

    def test_default_optional_pin_matches_the_published_release_without_selecting_core(self):
        catalog = json.loads((ROOT / "data/component-releases.json").read_bytes())["releases"]
        published = next(record for record in catalog if record["version"] == "0.5.0")
        self.assertEqual(stage.validate_inputs(self.inputs)["components"], published)
        self.assertEqual(hashlib.sha256(self.archive).hexdigest(), published["archive_sha256"])
        baseline = json.loads((ROOT / "tools/reference/inputs.json").read_bytes())
        self.assertEqual(baseline["components"]["version"], "0.4.1")
        self.assertFalse(any("desktop-away" in path for path in baseline["public_source"]["assets"]))

    def test_stages_only_two_selected_files_with_exact_bytes_modes_and_full_receipt(self):
        with tempfile.TemporaryDirectory(prefix="niri-plus-away-stage-") as temporary:
            output = Path(temporary) / "optional"
            self.run_stage(output)
            selected = {path.relative_to(output).as_posix() for path in (output / "components").rglob("*") if path.is_file()}
            self.assertEqual(selected, set(stage.SELECTED_MODES))
            for name, mode in stage.SELECTED_MODES.items():
                self.assertEqual((output / name).read_bytes(), self.payloads[name])
                self.assertEqual(stat.S_IMODE((output / name).stat().st_mode), mode)
            self.assertEqual((output / "archive.tar.gz").read_bytes(), self.archive)
            self.assertEqual((output / "inputs.json").read_bytes(), stage.DEFAULT_INPUTS.read_bytes())
            self.assertEqual(hashlib.sha256((output / "manifest.json").read_bytes()).hexdigest(),
                             self.inputs["components"]["manifest_sha256"])
            receipt = json.loads((output / "provenance.json").read_bytes())
            self.assertEqual(receipt["validated_file_count"], 46)
            self.assertEqual(receipt["components"], self.inputs["components"])
            self.assertEqual({item["path"] for item in receipt["selected_files"]}, selected)
            self.assertIn("no installation or reference qualification", receipt["status"])
            self.assertFalse((output / "appearance").exists())
            self.assertFalse((output / "source").exists())

    def test_optional_release_retains_all_qualified_core_payload_bytes_and_modes(self):
        baseline = json.loads((ROOT / "tools/reference/inputs.json").read_bytes())["components"]
        with tempfile.TemporaryDirectory(prefix="niri-plus-away-core-parity-") as temporary:
            archived = subprocess.run(["git", "archive", baseline["source_commit"], "components"], cwd=ROOT,
                                      check=True, capture_output=True).stdout
            with tarfile.open(fileobj=io.BytesIO(archived)) as archive:
                archive.extractall(temporary, filter="data")
            manifest, payloads = builder.manifest_for(temporary, baseline["source_commit"])
            self.assertEqual(hashlib.sha256(builder.archive_bytes(manifest, payloads)).hexdigest(),
                             baseline["archive_sha256"])
            self.assertEqual(set(self.payloads) - set(payloads), set(stage.SELECTED_MODES))
            current_records = {item["path"]: item for item in self.manifest["files"]}
            for record in manifest["files"]:
                with self.subTest(path=record["path"]):
                    self.assertEqual(self.payloads[record["path"]], payloads[record["path"]])
                    self.assertEqual(current_records[record["path"]], record)

    def test_rejects_archive_and_manifest_tampering_without_retaining_partial_output(self):
        with tempfile.TemporaryDirectory(prefix="niri-plus-away-corrupt-") as temporary:
            base = Path(temporary)
            with self.assertRaisesRegex(ValueError, "archive SHA-256"):
                self.run_stage(base / "optional", archive=b"corrupt")
            self.assertFalse((base / "optional").exists())
            inputs = copy.deepcopy(self.inputs)
            inputs["components"]["manifest_sha256"] = "0" * 64
            inputs_path = base / "inputs.json"
            inputs_path.write_text(json.dumps(inputs))
            with self.assertRaisesRegex(ValueError, "manifest SHA-256"):
                self.run_stage(base / "optional", inputs_path)
            self.assertFalse((base / "optional").exists())
            self.assertFalse(list(base.glob(".optional.stage-*")))

    def test_validates_unselected_core_payloads_before_staging_away(self):
        payloads = dict(self.payloads)
        payloads["components/shell/init.zsh"] += b"# tampered unselected core\n"
        corrupt = builder.archive_bytes(self.manifest, payloads)
        with tempfile.TemporaryDirectory(prefix="niri-plus-away-core-tamper-") as temporary:
            base = Path(temporary)
            path = self.fixture_inputs(base, archive=corrupt)
            with self.assertRaisesRegex(ValueError, "payload SHA-256 mismatch.*components/shell/init.zsh"):
                self.run_stage(base / "optional", path, corrupt)
            self.assertFalse((base / "optional").exists())
            self.assertFalse(list(base.glob(".optional.stage-*")))

    def test_missing_selected_unit_and_wrong_helper_mode_fail_atomically(self):
        for mutation in ("missing unit", "wrong mode"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(prefix="niri-plus-away-selection-") as temporary:
                base = Path(temporary)
                manifest, payloads = copy.deepcopy(self.manifest), dict(self.payloads)
                if mutation == "missing unit":
                    missing = "components/desktop/systemd/user/desktop-away.service"
                    manifest["files"] = [item for item in manifest["files"] if item["path"] != missing]
                    del payloads[missing]
                else:
                    next(item for item in manifest["files"] if item["path"] == "components/desktop/bin/desktop-away")["mode"] = 0o644
                archive = builder.archive_bytes(manifest, payloads)
                path = self.fixture_inputs(base, archive=archive, manifest=manifest)
                with self.assertRaisesRegex(ValueError, "expected file or mode"):
                    self.run_stage(base / "optional", path, archive)
                self.assertFalse((base / "optional").exists())
                self.assertFalse(list(base.glob(".optional.stage-*")))

    def test_rejects_widened_selection_and_floating_pin(self):
        for name, value, message in (
            ("selected_files", self.inputs["selected_files"] + ["components/shell/init.zsh"], "only the canonical helper and unit"),
            ("schema_version", True, "unsupported away input inventory schema"),
        ):
            with self.subTest(name=name):
                inputs = copy.deepcopy(self.inputs)
                inputs[name] = value
                with self.assertRaisesRegex(ValueError, message):
                    stage.validate_inputs(inputs)
        inputs = copy.deepcopy(self.inputs)
        inputs["components"]["source_commit"] = "main"
        with self.assertRaisesRegex(ValueError, "full 40-character hash"):
            stage.validate_inputs(inputs)

    def test_rejects_existing_output_symlink_ancestor_and_root_before_fetch(self):
        with tempfile.TemporaryDirectory(prefix="niri-plus-away-boundary-") as temporary:
            base = Path(temporary)
            output = base / "existing"
            output.mkdir()
            (output / "keep").write_bytes(b"preimage")
            link = base / "link"
            link.symlink_to(output, target_is_directory=True)
            fetcher = mock.Mock()
            with mock.patch.object(stage.verifier.os, "geteuid", return_value=1000):
                for candidate, message in ((output, "must be new"), (link / "optional", "traverses a symlink")):
                    with self.assertRaisesRegex(ValueError, message):
                        stage.stage_away(candidate, fetcher=fetcher)
            with mock.patch.object(stage.verifier.os, "geteuid", return_value=0):
                with self.assertRaisesRegex(ValueError, "ordinary user"):
                    stage.stage_away(base / "new", fetcher=fetcher)
            fetcher.assert_not_called()
            self.assertEqual((output / "keep").read_bytes(), b"preimage")


if __name__ == "__main__":
    unittest.main()
