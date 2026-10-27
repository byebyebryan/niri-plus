import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import subprocess
import sys
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
appearance_spec = importlib.util.spec_from_file_location(
    "niri_plus_public_appearance_renderer", ROOT / "components/appearance/render.py"
)
appearance = importlib.util.module_from_spec(appearance_spec)
appearance_spec.loader.exec_module(appearance)
merge_spec = importlib.util.spec_from_file_location(
    "niri_plus_public_ini_merge", ROOT / "components/appearance/ini_merge.py"
)
ini_merge = importlib.util.module_from_spec(merge_spec)
merge_spec.loader.exec_module(ini_merge)


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
                metadata = json.loads((ROOT / "components/metadata.json").read_text())
                self.assertEqual(manifest["schema_version"], 1)
                self.assertEqual(manifest["api_version"], 1)
                self.assertEqual(manifest["version"], metadata["version"])
                self.assertEqual(manifest["source_commit"], TEST_COMMIT)
                self.assertIn("desktop", manifest["modules"])
                self.assertIn("shell", manifest["modules"])
                self.assertIn("appearance", manifest["modules"])
                self.assertIn("prerequisites", manifest["modules"]["desktop"])
                self.assertIn("prerequisites", manifest["modules"]["shell"])
                self.assertIn("prerequisites", manifest["modules"]["appearance"])

                entries = {item["path"]: item for item in manifest["files"]}
                self.assertEqual(set(names[1:]), set(entries))
                declared = {item["path"]: item["module"] for item in metadata["files"]}
                self.assertEqual(set(entries), set(declared))
                for module in manifest["modules"]:
                    self.assertTrue(any(item["module"] == module for item in entries.values()), module)
                for member in members[1:]:
                    entry = entries[member.name]
                    self.assertEqual(entry["module"], declared[member.name])
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
                "appearance_exports": [],
            }
            (source / "components/metadata.json").write_text(json.dumps(metadata))

            result = builder.build_archive(base / "output", TEST_COMMIT, root=source)[0]
            with tarfile.open(result, "r:gz") as archive:
                self.assertEqual([member.name for member in archive.getmembers()], [
                    "manifest.json", "components/desktop/bin/listed"
                ])

    def test_extracted_bundle_renderer_cli_uses_only_its_manifest(self):
        with tempfile.TemporaryDirectory(prefix="niri-plus-renderer-bundle-") as temporary:
            base = Path(temporary)
            bundle = self.archive(base)
            extracted = base / "extracted"
            extracted.mkdir()
            with tarfile.open(bundle, "r:gz") as archive:
                for member in archive.getmembers():
                    relative = Path(member.name)
                    self.assertFalse(relative.is_absolute())
                    self.assertNotIn("..", relative.parts)
                    target = extracted / relative
                    if member.isdir():
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(archive.extractfile(member).read())

            identity = base / "identity.json"
            identity.write_bytes((ROOT / "design/identity.json").read_bytes())
            api = runpy.run_path(str(extracted / "components/appearance/render.py"))
            self.assertTrue(callable(api["render"]))
            self.assertTrue(callable(api["derive_sddm_theme"]))
            output = base / "derived"
            command = [
                sys.executable,
                str(extracted / "components/appearance/render.py"),
                "--identity", str(identity),
                "--output", str(output),
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            receipt = json.loads((output / "manifest.json").read_text())
            self.assertEqual(receipt["renderer_version"], "0.3.1")
            self.assertEqual(receipt["identity_sha256"], hashlib.sha256(identity.read_bytes()).hexdigest())
            self.assertEqual(set(receipt["code_sha256"]), {
                "components/appearance/__init__.py",
                "components/appearance/ini_merge.py",
                "components/appearance/render.py",
                "components/appearance/sddm.py",
            })
            self.assertEqual({item["path"] for item in receipt["files"]}, set(appearance.render(json.loads(identity.read_text()))))
            for record in receipt["files"]:
                data = (output / record["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"])

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
            self.assertEqual(record["module"], "desktop")

        shell_exports = [item for item in metadata["exports"] if item["path"].startswith("examples/terminal/")]
        shell_sources = {item["path"] for item in metadata["files"] if item["module"] == "shell"}
        self.assertEqual({item["component"] for item in shell_exports}, shell_sources)
        for item in shell_exports:
            record = records[item["path"]]
            self.assertEqual(record["module"], "shell")
            self.assertEqual(record["source"], "Niri Plus shell component module")

        appearance_exports = metadata["appearance_exports"]
        self.assertEqual({item["path"] for item in appearance_exports}, {
            "examples/theme/NeutralSlate.colors",
            "examples/theme/gtklock.css",
            "examples/theme/neutral-slate.rasi",
            "examples/theme/niri-neutral-slate.kdl",
            "examples/theme/qt5-palette.conf",
            "examples/theme/qt6-palette.conf",
            "examples/theme/swaync.css",
            "examples/kitty/neutral-slate.conf",
        })
        for item in appearance_exports:
            record = records[item["path"]]
            self.assertTrue(record["generated"])
            self.assertEqual(record["module"], "appearance")
            self.assertEqual(record["generated_by"], "scripts/export-components.py")
            self.assertEqual(record["generated_from"], f"components/appearance/render.py#{item['artifact']}")
            self.assertEqual(record["source"], "Niri Plus appearance component module")
            self.assertEqual(record["identity_sha256"], hashlib.sha256((ROOT / "design/identity.json").read_bytes()).hexdigest())

        helper = next(item for item in metadata["exports"] if item["path"] == "examples/login/derive-theme.py")
        self.assertEqual(helper["component"], "components/appearance/sddm.py")
        self.assertEqual(first[helper["path"]], (ROOT / helper["component"]).read_bytes())
        self.assertEqual(records[helper["path"]]["module"], "appearance")

    def test_appearance_renderer_reproduces_current_public_snapshots(self):
        identity = json.loads((ROOT / "design/identity.json").read_text())
        artifacts = appearance.render(identity)
        snapshots = {
            "NeutralSlate.colors": "examples/theme/NeutralSlate.colors",
            "gtklock.css": "examples/theme/gtklock.css",
            "neutral-slate.rasi": "examples/theme/neutral-slate.rasi",
            "niri-neutral-slate.kdl": "examples/theme/niri-neutral-slate.kdl",
            "qt5-palette.conf": "examples/theme/qt5-palette.conf",
            "qt6-palette.conf": "examples/theme/qt6-palette.conf",
            "swaync.css": "examples/theme/swaync.css",
            "kitty-neutral-slate.conf": "examples/kitty/neutral-slate.conf",
        }
        for artifact, relative in snapshots.items():
            with self.subTest(artifact=artifact):
                self.assertEqual((ROOT / relative).read_bytes(), artifacts[artifact].encode("utf-8"))

        self.assertEqual(
            artifacts["kitty-native-suffix.conf"].splitlines()[0],
            "# Neutral Slate / Balanced+ terminal; independent of desktop surface colors.",
        )
        fonts = json.loads(artifacts["fonts.json"])
        self.assertEqual(fonts["ui_font"], "Noto Sans")
        self.assertEqual(fonts["mono_font"], "MesloLGS Nerd Font")
        roles = json.loads(artifacts["roles.json"])
        self.assertEqual(roles["candidate"], "neutral-slate")
        selected = next(candidate for candidate in identity["candidates"] if candidate["id"] == "neutral-slate")
        self.assertEqual(roles["colors"], selected["colors"])
        compact_identity = {
            "schema_version": 2,
            "status": "selected design",
            "selected_candidate": "neutral-slate",
            "direction": selected,
            "shared": identity["shared"],
            "terminal": identity["terminal"],
        }
        self.assertEqual(appearance.render(compact_identity), artifacts)

    def test_sddm_derivation_returns_marker_free_immutable_core(self):
        identity = json.loads((ROOT / "design/identity.json").read_text())
        with tempfile.TemporaryDirectory(prefix="niri-plus-sddm-source-") as temporary:
            source = Path(temporary) / "upstream"
            source.mkdir()
            (source / "Main.qml").write_text('color: "#1e1e2e"\nerror: "#f38ba8"\n')
            (source / "UserField.qml").write_text("  horizontalAlignment: Text.AlignHCenter\n")
            result = appearance.derive_sddm_theme(source, identity)
            again = appearance.derive_sddm_theme(source, identity)
            self.assertEqual(result, again)
            self.assertEqual(result["name"], "niri-neutral-" + result["sha256"][:12])
            self.assertEqual(len(result["files"]), 3)
            self.assertNotIn(".niri-plus-theme.json", result["files"])
            self.assertIn(b"#202020", result["files"]["Main.qml"])
            self.assertIn(b"placeholderTextColor: \"#999999\"", result["files"]["UserField.qml"])
            self.assertEqual((source / "Main.qml").read_text(), 'color: "#1e1e2e"\nerror: "#f38ba8"\n')

    def test_public_sddm_helper_runs_standalone_outside_checkout(self):
        raw_identity = json.loads((ROOT / "design/identity.json").read_text())
        selected = next(candidate for candidate in raw_identity["candidates"] if candidate["id"] == "neutral-slate")
        compact_identity = {
            "schema_version": 2,
            "status": "selected design",
            "selected_candidate": "neutral-slate",
            "source": "data/identity.json",
            "shared": raw_identity["shared"],
            "direction": selected,
            "terminal": raw_identity["terminal"],
        }
        with tempfile.TemporaryDirectory(prefix="niri-plus-standalone-greeter-") as temporary:
            base = Path(temporary)
            isolated = base / "downloaded"
            isolated.mkdir()
            helper = isolated / "derive-theme.py"
            helper.write_bytes((ROOT / "examples/login/derive-theme.py").read_bytes())
            identity_path = isolated / "identity.json"
            identity_path.write_text(json.dumps(compact_identity))
            source = base / "upstream"
            source.mkdir()
            (source / "Main.qml").write_text('color: "#1e1e2e"\nerror: "#f38ba8"\n')
            (source / "PasswordField.qml").write_text("  horizontalAlignment: Text.AlignHCenter\n")
            output = base / "preview"
            subprocess.run(
                [sys.executable, str(helper), str(source), str(output), "--identity", str(identity_path)],
                check=True,
                capture_output=True,
                text=True,
                cwd=base,
            )
            themes = list(output.iterdir())
            self.assertEqual(len(themes), 1)
            theme = themes[0]
            marker = json.loads((theme / ".niri-plus-theme.json").read_text())
            self.assertEqual(marker["owner"], "niri-plus-example")
            self.assertEqual(theme.name, "niri-neutral-" + marker["sha256"][:12])
            self.assertEqual(len([path for path in theme.rglob("*") if path.is_file()]), 4)
            self.assertIn("Font=Noto Sans\nFontSize=11\n", (theme / "theme.conf.user").read_text())

    def test_ini_merge_api_and_managed_globals_bridge(self):
        source = (
            "# retained\n[General]\nColorScheme=old\nfont=old\n"
            "ColorScheme=duplicate\nunmanaged=keep\n[Other]\nvalue=stay\n"
        )
        managed = {
            "General": {"ColorScheme": "NeutralSlate", "font": "Noto Sans,11"},
            "Colors:View": {"ForegroundNormal": "239,239,236"},
        }
        expected = (
            "# retained\n[General]\nColorScheme=NeutralSlate\nfont=Noto Sans,11\n"
            "unmanaged=keep\n[Other]\nvalue=stay\n\n[Colors:View]\n"
            "ForegroundNormal=239,239,236\n"
        )
        self.assertEqual(ini_merge.merge_ini(source, managed), expected)
        self.assertNotIn("from __future__", (ROOT / "components/appearance/ini_merge.py").read_text())

        bridge = (
            "from pathlib import Path\n"
            f"managed={managed!r}\n"
            f"exec(compile(Path({str(ROOT / 'components/appearance/ini_merge.py')!r}).read_text(), "
            "'components/appearance/ini_merge.py', 'exec'))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", bridge],
            input=source,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout, expected)

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
