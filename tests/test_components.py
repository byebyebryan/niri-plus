import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_script(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_script("niri_plus_component_builder", "build-components.py")
exporter = load_script("niri_plus_component_exporter", "export-components.py")
TEST_COMMIT = "a" * 40


class ComponentContracts(unittest.TestCase):
    def archive(self, directory, name="archive"):
        return builder.build_archive(Path(directory) / name, TEST_COMMIT)[0]

    def test_archive_is_deterministic_and_manifest_hashes_every_member(self):
        with tempfile.TemporaryDirectory(prefix="niri-plus-components-") as temporary:
            root = Path(temporary)
            first = self.archive(root, "first")
            second = self.archive(root, "second")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertLess(first.stat().st_size, 100_000)

            with tarfile.open(first, "r:gz") as archive:
                members = archive.getmembers()
                names = [member.name for member in members]
                self.assertEqual(names[0], "manifest.json")
                self.assertEqual(names[1:], sorted(names[1:]))
                self.assertTrue(all(member.isfile() for member in members))
                self.assertTrue(all(member.uid == member.gid == member.mtime == 0 for member in members))
                manifest = json.load(archive.extractfile("manifest.json"))
                self.assertEqual(manifest["schema_version"], 1)
                self.assertEqual(manifest["api_version"], 1)
                self.assertEqual(manifest["version"], "0.1.0")
                self.assertEqual(manifest["source_commit"], TEST_COMMIT)
                self.assertIn("prerequisites", manifest["modules"]["desktop"])

                entries = {item["path"]: item for item in manifest["files"]}
                self.assertEqual(set(names[1:]), set(entries))
                self.assertEqual(len(entries), 16)
                for member in members[1:]:
                    entry = entries[member.name]
                    data = archive.extractfile(member).read()
                    self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])
                    self.assertEqual(member.mode, entry["mode"])
                    self.assertIn(entry["mode"], (420, 493))
                    self.assertNotIn(b"/home/", data)
                    self.assertNotIn(b".codex", data)

    def test_builder_includes_only_explicit_inputs(self):
        with tempfile.TemporaryDirectory(prefix="niri-plus-explicit-inputs-") as temporary:
            base = Path(temporary)
            source = base / "source"
            listed = source / "components/desktop/bin/listed"
            listed.parent.mkdir(parents=True)
            listed.write_text("listed\n")
            (listed.parent / "untracked-cache").write_text("must not be packaged\n")
            metadata = {
                "version": "0.1.0",
                "modules": {"desktop": {"prerequisites": ["fixture"]}},
                "files": [{"path": "components/desktop/bin/listed", "module": "desktop"}],
                "exports": [],
            }
            (source / "components/metadata.json").write_text(json.dumps(metadata))

            result = builder.build_archive(base / "output", TEST_COMMIT, root=source)[0]
            with tarfile.open(result, "r:gz") as archive:
                self.assertEqual([member.name for member in archive.getmembers()], [
                    "manifest.json", "components/desktop/bin/listed"
                ])

    def test_bad_commit_and_nonempty_output_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="niri-plus-components-errors-") as temporary:
            output = Path(temporary) / "output"
            with self.assertRaisesRegex(ValueError, "full lowercase 40-character"):
                builder.build_archive(output, "not-a-commit")
            output.mkdir()
            (output / "keep").write_text("preserve\n")
            with self.assertRaisesRegex(ValueError, "new or empty directory"):
                builder.build_archive(output, TEST_COMMIT)
            self.assertEqual((output / "keep").read_text(), "preserve\n")

    def test_generated_exports_are_repeatable_and_use_one_readiness_source(self):
        first = exporter.render(ROOT)
        second = exporter.render(ROOT)
        self.assertEqual(first, second)
        self.assertEqual(exporter.update(ROOT, write=False), [])

        metadata = json.loads((ROOT / "components/metadata.json").read_text())
        ready = [item for item in metadata["exports"] if item["path"].endswith("desktop-session-ready")]
        self.assertEqual(len(ready), 2)
        self.assertEqual({item["component"] for item in ready}, {"components/desktop/bin/desktop-session-ready"})
        self.assertEqual(first[ready[0]["path"]], first[ready[1]["path"]])

        manifest = json.loads(first["examples/manifest.json"])
        records = {item["path"]: item for item in manifest["files"]}
        for item in ready:
            record = records[item["path"]]
            self.assertTrue(record["generated"])
            self.assertEqual(record["generated_by"], "scripts/export-components.py")
            self.assertEqual(record["generated_from"], "components/desktop/bin/desktop-session-ready")

    def test_portable_unit_urls_are_preserved_as_authored_profiles(self):
        generated = exporter.render(ROOT)
        self.assertNotIn("examples/session/desktop-lock.service", generated)
        self.assertNotIn("examples/clipboard/clipboard-history@.service", generated)
        self.assertIn("examples/session/profiles/minimal-niri/desktop-lock.service", generated)
        self.assertIn("examples/clipboard/profiles/minimal-niri/clipboard-history@.service", generated)
        self.assertIn("ExecStart=/usr/bin/gtklock --daemonize\n", generated["examples/session/profiles/minimal-niri/desktop-lock.service"].decode())
        self.assertIn("cliphist store\n", generated["examples/clipboard/profiles/minimal-niri/clipboard-history@.service"].decode())


if __name__ == "__main__":
    unittest.main()
