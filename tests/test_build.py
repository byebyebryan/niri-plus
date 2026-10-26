import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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
        self.assertEqual(result["pages"], 14)
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

    def test_identity_is_one_theme_from_the_reviewed_source(self):
        builder.build(self.output)
        identity = json.loads((self.output / "data/identity.json").read_text())
        self.assertEqual(identity["selected_candidate"], "neutral-slate")
        self.assertEqual(identity["direction"]["id"], "neutral-slate")
        self.assertEqual(identity["direction"]["ui_font"], "Noto Sans")
        self.assertEqual(identity["direction"]["mono_font"], "MesloLGS Nerd Font")
        self.assertEqual(identity["theme_scope"]["supported_target_count"], 1)
        self.assertNotIn("candidates", identity)
        self.assertEqual(len(identity["terminal"]["ansi"]), 16)
        self.assertEqual(len(identity["terminal"]["ansi_names"]), 16)
        self.assertEqual(len(identity["terminal"]["ansi_roles"]), 16)
        fragment = (self.output / "examples/kitty/neutral-slate.conf").read_text()
        self.assertIn("background #202326", fragment)
        self.assertIn("cursor #a6ceff", fragment)
        self.assertIn("selection_background #2b425b", fragment)
        self.assertIn("color1 #e5a09b", fragment)
        self.assertIn("color2 #b8c9a4", fragment)
        self.assertIn("color3 #ddbb80", fragment)
        self.assertIn("color4 #83b8f5", fragment)
        self.assertIn("color12 #a6ceff", fragment)
        self.assertNotIn("font_family", fragment)
        design = (self.output / "design/index.html").read_text()
        self.assertIn("Noto Sans", design)
        self.assertIn("MesloLGS Nerd Font", design)
        self.assertIn("bright supplemental violet", design)
        self.assertEqual(design.count('class="ansi-slot"'), 16)
        self.assertEqual(design.count('data-surface-panel='), 4)
        self.assertNotIn("Slate Blue", design)
        self.assertNotIn("Inter Variable", design)
        self.assertFalse((self.output / "assets/fonts/inter.woff2").exists())
        self.assertTrue((self.output / "assets/fonts/noto.woff2").is_file())
        self.assertTrue((self.output / "assets/fonts/noto-medium.woff2").is_file())
        self.assertTrue((self.output / "assets/fonts/noto-semibold.woff2").is_file())
        (self.output / "assets/identity.css").write_text(":root{--bg:red}")
        with self.assertRaisesRegex(ValueError, "generated appearance"):
            builder.validate(self.output)

    def test_native_theme_examples_are_bound_to_the_canonical_identity(self):
        manifest = json.loads((ROOT / "examples/manifest.json").read_text())
        records = [item for item in manifest["files"] if item["path"].startswith("examples/theme/")]
        self.assertEqual(len(records), 7)
        identity = json.loads((ROOT / "design/identity.json").read_text())
        digest = hashlib.sha256((ROOT / "design/identity.json").read_bytes()).hexdigest()
        self.assertEqual({item["identity_sha256"] for item in records}, {digest})
        self.assertIn("not a deployed artifact", " ".join(item.get("notes", "") for item in records))
        stale = [dict(item) for item in records]
        stale[0]["identity_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "stale identity association"):
            builder.validate_identity_associations(stale)
        self.assertEqual(identity["selected_candidate"], "neutral-slate")
        builder.build(self.output)
        public_manifest = json.loads((self.output / "examples/manifest.json").read_text())
        self.assertEqual(len([item for item in public_manifest["files"] if item["path"].startswith("examples/theme/")]), 7)

    def test_contrast_study_keeps_the_selected_identity_and_isolates_black_only(self):
        builder.build(self.output)
        study = json.loads((self.output / "data/contrast-study.json").read_text())
        identity = json.loads((self.output / "data/identity.json").read_text())
        self.assertEqual(study["status"], "proposal")
        self.assertEqual(study["baseline_sha256"], identity["source_sha256"])
        current = study["baseline"]["terminal"]
        black, balanced, vivid = study["terminal_variants"]
        self.assertEqual({key for key in current if current[key] != black[key]}, {"id", "name", "background"})
        self.assertEqual(black["background"], "#000000")
        self.assertEqual(vivid["background"], "#000000")
        self.assertEqual(vivid["foreground"], current["foreground"])
        self.assertEqual(len(vivid["ansi"]), 16)
        self.assertEqual(balanced["background"], "#000000")
        self.assertEqual(balanced["foreground"], current["foreground"])
        self.assertEqual(len(balanced["ansi"]), 16)
        for slot in range(1, 7):
            self.assertGreaterEqual(builder.contrast_ratio(balanced["ansi"][slot], "#000000"), 4.5)
            self.assertGreater(builder.contrast_ratio(balanced["ansi"][slot], balanced["ansi"][slot + 8]), builder.contrast_ratio(current["ansi"][slot], current["ansi"][slot + 8]))
        self.assertEqual(identity["direction"]["colors"]["surface"], "#202326")
        self.assertNotIn("crisper-slate", (self.output / "assets/identity.css").read_text())
        fragment = (self.output / "examples/kitty/neutral-slate.conf").read_text()
        self.assertIn("background #202326", fragment)
        study["terminal_variants"][0]["background"] = "#111111"
        (self.output / "data/contrast-study.json").write_text(json.dumps(study))
        with self.assertRaisesRegex(ValueError, "contrast study differs"):
            builder.validate(self.output)

    def test_contrast_study_rejects_a_changed_selected_baseline(self):
        identity = builder.working_identity()
        identity["source_sha256"] = "0" * 64
        with patch.object(builder, "working_identity", return_value=identity):
            with self.assertRaisesRegex(ValueError, "reviewed baseline"):
                builder.contrast_study()

    def test_portable_review_keeps_links_valid_without_the_project_mount(self):
        builder.build(self.output, portable=True)
        text = (self.output / "design/index.html").read_text()
        self.assertIn('href="../assets/identity.css"', text)
        self.assertIn('href="../recipes/terminal/"', text)
        self.assertIn('href="../recipes/appearance/"', text)
        self.assertIn('href="https://dev.byebyebryan.com/niri-plus/design/"', text)

    def test_terminal_and_utility_recipes_export_pinned_sources_and_isolated_check(self):
        builder.build(self.output)
        terminal = (self.output / "recipes/terminal/index.html").read_text()
        utilities = (self.output / "recipes/desktop-utilities/index.html").read_text()
        self.assertIn("zsh-neutral-slate", terminal)
        self.assertIn("does not edit", terminal)
        self.assertIn("UDisks2", utilities)
        self.assertIn("desktop-lock.service", utilities)
        for relative in (
            "examples/terminal/fetch.py",
            "examples/terminal/pins.json",
            "examples/terminal/THIRD_PARTY_NOTICES.md",
            "examples/desktop/desktop-session-menu",
            "examples/desktop/niri-plus-network.desktop",
            "examples/desktop/power.toml.example",
            "scripts/check-terminal.py",
        ):
            self.assertTrue((self.output / relative).is_file(), relative)
        manifest = json.loads((self.output / "examples/manifest.json").read_text())
        self.assertEqual(len([item for item in manifest["files"] if item["path"].startswith("examples/terminal/")]), 6)
        self.assertIn("scripts/check-terminal.py", {item["path"] for item in manifest["files"]})

    def test_old_slate_blue_terminal_example_remains_a_historical_file(self):
        builder.build(self.output)
        historical = (self.output / "examples/kitty/slate-blue.conf").read_text()
        self.assertIn("Slate Blue - appearance proposal, not deployed", historical)
        self.assertIn("background #202326", historical)
        self.assertIn("color4 #83b8f5", historical)

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
