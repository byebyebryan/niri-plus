#!/usr/bin/env python3
"""Isolated source checks for the guarded desktop assembly and local fixture."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen


sys.dont_write_bytecode = True
SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY = SCRIPT_DIR.parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


desktop = load_module("niri_plus_desktop_assembler_check", SCRIPT_DIR / "assemble_desktop.py")
fixture = load_module("niri_plus_sample_server_check", SCRIPT_DIR / "sample_server.py")


class DesktopAssemblyChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="niri-plus-desktop-check-")
        cls.appearance = Path(cls.temporary.name) / "appearance"
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        subprocess.run(
            [
                sys.executable,
                str(REPOSITORY / "components/appearance/render.py"),
                "--identity",
                str(REPOSITORY / "design/identity.json"),
                "--output",
                str(cls.appearance),
            ],
            check=True,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        source_config = (REPOSITORY / "examples/niri/config.kdl").read_text(encoding="utf-8")
        theme = json.loads((cls.appearance / "theme.json").read_text(encoding="utf-8"))
        pilot = desktop.import_pilot_assembler().assemble_niri_config(source_config, theme).encode("utf-8")
        cls.assembled_niri = desktop.assemble_niri(pilot)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_niri_config_restores_dolphin_and_adds_owned_bindings_and_environment(self):
        text = self.assembled_niri.decode("utf-8")
        self.assertEqual(text.count('Mod+E { spawn "dolphin"; }'), 1)
        self.assertEqual(text.count('Mod+N repeat=false { spawn "swaync-client" "-t" "-sw"; }'), 1)
        self.assertEqual(text.count('Mod+Y repeat=false { spawn "rofi-clipboard"; }'), 1)
        self.assertIn('QT_QPA_PLATFORMTHEME "qt5ct:qt6ct"', text)
        self.assertIn('GTK_THEME "adw-gtk3-dark"', text)
        self.assertIn(f'PATH "{desktop.REFERENCE_DESKTOP_PATH}"', text)
        self.assertTrue(desktop.REFERENCE_DESKTOP_PATH.startswith("/home/demo/.local/bin:"))
        self.assertIn('xcursor-theme "breeze_cursors"', text)
        if shutil.which("niri"):
            desktop.validate_niri_config(self.assembled_niri)

    def test_component_manifest_uses_retained_bootstrap_root_layout(self):
        previous_root = desktop.PILOT_ROOT
        try:
            with tempfile.TemporaryDirectory(prefix="niri-plus-component-layout-") as temporary:
                desktop.PILOT_ROOT = Path(temporary)
                expected = {"version": "0.3.1", "api_version": 1, "files": []}
                (desktop.PILOT_ROOT / "manifest.json").write_text(
                    json.dumps(expected), encoding="utf-8"
                )
                self.assertEqual(desktop.load_component_manifest(), expected)
        finally:
            desktop.PILOT_ROOT = previous_root

    def test_receipt_owned_session_links_allow_only_the_exact_leaf_symlink(self):
        previous_home = desktop.HOME
        try:
            with tempfile.TemporaryDirectory(prefix="niri-plus-session-link-guard-") as temporary:
                desktop.HOME = Path(temporary)
                wants = desktop.HOME / ".config/systemd/user/niri.service.wants"
                wants.mkdir(parents=True)
                relative = ".config/systemd/user/niri.service.wants/clipboard-history@image.service"
                path = desktop.HOME / relative
                expected_target = "../clipboard-history@.service"
                path.symlink_to(expected_target)

                with self.assertRaises(desktop.AssemblyError):
                    desktop.relative_target(relative)
                allowed_path = desktop.relative_target(relative, allow_symlink_leaf=True)
                self.assertEqual(
                    desktop.preflight_link(allowed_path, expected_target, allow_existing=True),
                    {"target": expected_target, "preexisting": True},
                )
                with self.assertRaises(desktop.AssemblyError):
                    desktop.preflight_link(allowed_path, "../unowned.service", allow_existing=True)

                outside = Path(temporary) / "outside"
                outside.mkdir()
                (desktop.HOME / ".config/systemd/user/external").symlink_to(
                    outside, target_is_directory=True
                )
                with self.assertRaises(desktop.AssemblyError):
                    desktop.relative_target(
                        ".config/systemd/user/external/clipboard-history@image.service",
                        allow_symlink_leaf=True,
                    )

                managed = desktop.HOME / ".config/managed.conf"
                managed.symlink_to(outside / "managed.conf")
                with self.assertRaises(desktop.AssemblyError):
                    desktop.preflight_targets(
                        {".config/managed.conf": (b"expected managed bytes\n", 0o644)},
                        b"pilot niri bytes\n",
                    )
        finally:
            desktop.HOME = previous_home

    def test_unknown_managed_target_is_refused(self):
        previous_home = desktop.HOME
        try:
            with tempfile.TemporaryDirectory(prefix="niri-plus-target-guard-") as temporary:
                desktop.HOME = Path(temporary)
                target = desktop.HOME / ".config/swaync/config.json"
                target.parent.mkdir(parents=True)
                target.write_text("unrelated user config\n", encoding="utf-8")
                with self.assertRaises(desktop.AssemblyError):
                    desktop.preflight_targets(
                        {".config/swaync/config.json": (b"expected managed bytes\n", 0o644)},
                        b"pilot niri bytes\n",
                    )
                self.assertEqual(target.read_text(encoding="utf-8"), "unrelated user config\n")
        finally:
            desktop.HOME = previous_home

    def test_mime_defaults_name_only_installed_or_assembly_entries(self):
        available_ids = set(desktop.MIME_ASSOCIATIONS.values()) | {
            "niri-plus-audio.desktop",
            "niri-plus-bluetooth.desktop",
            "niri-plus-network.desktop",
            "niri-plus-session.desktop",
        }
        self.assertEqual(len(available_ids), 10)
        self.assertIn("niri-plus-neovim.desktop", available_ids)
        self.assertNotIn("nvim-terminal.desktop", available_ids)

    def test_fixture_download_upload_and_surface_routes(self):
        server = fixture.FixtureServer(("127.0.0.1", 0), fixture.Handler)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(base + "/") as response:
                page = response.read()
                self.assertIn(b"getDisplayMedia", page)
                self.assertIn(b"displaySurface", page)
            with urlopen(base + f"/sample/{fixture.SAMPLE_NAME}") as response:
                self.assertEqual(response.headers.get_content_type(), "text/markdown")
                sample = response.read()
            self.assertEqual(sample, fixture.SAMPLE_BYTES)
            with urlopen(base + f"/assets/{fixture.IMAGE_NAME}") as response:
                self.assertEqual(response.headers.get_content_type(), "image/svg+xml")
                self.assertIn(b"<svg", response.read())

            boundary = "niri-plus-local-check"
            multipart = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{fixture.SAMPLE_NAME}"\r\n'
                "Content-Type: text/markdown\r\n\r\n"
            ).encode("ascii") + sample + f"\r\n--{boundary}--\r\n".encode("ascii")
            request = Request(
                base + "/upload",
                data=multipart,
                headers={
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "Content-Length": str(len(multipart)),
                },
                method="POST",
            )
            with urlopen(request) as response:
                result = json.loads(response.read())
                self.assertEqual(result["sha256"], fixture.SAMPLE_SHA256)
                self.assertIn("uploaded bytes match", result["message"])

            wrong_file = sample + b"changed"
            wrong = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{fixture.SAMPLE_NAME}"\r\n'
                "Content-Type: text/markdown\r\n\r\n"
            ).encode("ascii") + wrong_file + f"\r\n--{boundary}--\r\n".encode("ascii")
            request = Request(
                base + "/upload",
                data=wrong,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as rejected:
                urlopen(request)
            self.assertEqual(rejected.exception.code, 422)
            error_body = rejected.exception.read()
            rejected.exception.close()
            self.assertIn(b"does not match", error_body)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
