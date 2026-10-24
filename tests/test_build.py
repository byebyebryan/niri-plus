import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("niri_plus_build", ROOT / "scripts/build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BuildContracts(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="niri-plus-check-")
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / "site"

    def test_complete_site_has_checked_links_and_no_planning_material(self):
        result = builder.build(self.output)
        self.assertEqual(result["pages"], 9)
        self.assertGreater(result["local_links"], 200)
        self.assertFalse((self.output / "docs").exists())
        self.assertFalse((self.output / "AGENTS.md").exists())
        self.assertIn("I love terminal life", (self.output / "story/index.html").read_text())
        self.assertIn("Illustrated walkthrough", (self.output / "index.html").read_text())
        for page in self.output.rglob("*.html"):
            self.assertNotIn("https://github.com/byebyebryan/dotfiles", page.read_text())

    def test_broken_local_anchor_is_rejected(self):
        builder.build(self.output)
        page = self.output / "index.html"
        page.write_text(page.read_text().replace("#browser-and-files", "#missing-workflow"))
        with self.assertRaisesRegex(ValueError, "missing anchor"):
            builder.validate(self.output)

    def test_changed_attributed_media_is_rejected(self):
        builder.build(self.output)
        (self.output / "assets/agent-plus.png").write_bytes(b"not the attributed image")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            builder.validate(self.output)

    def test_changed_example_is_rejected(self):
        builder.build(self.output)
        (self.output / "examples/niri/config.kdl").write_text("changed example")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            builder.validate(self.output)

    def test_unexpected_public_file_is_rejected(self):
        builder.build(self.output)
        (self.output / "private-note.txt").write_text("not public")
        with self.assertRaisesRegex(ValueError, "public inventory"):
            builder.validate(self.output)

    def test_nonempty_output_is_preserved(self):
        self.output.mkdir()
        recovery = self.output / "recovery.txt"
        recovery.write_text("keep this")
        with self.assertRaisesRegex(ValueError, "empty"):
            builder.build(self.output)
        self.assertEqual(recovery.read_text(), "keep this")

    def test_personal_notes_have_not_been_embedded_in_examples(self):
        manifest = json.loads((ROOT / "examples/manifest.json").read_text())
        for item in manifest["files"]:
            text = (ROOT / item["path"]).read_text()
            self.assertNotIn("/home/bryan", text)
            self.assertNotIn("tmux-observer-desktop", text)
            self.assertNotIn("honor-xdg-activation-with-invalid-serial", text)


if __name__ == "__main__":
    unittest.main()
