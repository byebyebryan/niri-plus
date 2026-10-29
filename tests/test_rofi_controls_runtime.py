import json
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "components/desktop/lib"
import sys
sys.path.insert(0, str(LIB))

from niri_plus_controls.runtime import MAX_SECRET_BYTES, _password_prompt


class PasswordPromptBufferTests(unittest.TestCase):
    def make_rofi(self, directory: Path, output: bytes) -> tuple[Path, Path]:
        executable = directory / "fake-rofi"
        argv_path = directory / "argv.json"
        source = (
            "#!/usr/bin/python3\n"
            "import json, os, sys\n"
            f"open({str(argv_path)!r}, 'w').write(json.dumps(sys.argv[1:]))\n"
            f"sys.stdout.buffer.write({output!r})\n"
            "sys.stdout.buffer.flush()\n"
        )
        executable.write_text(source)
        executable.chmod(0o700)
        return executable, argv_path

    def test_password_dmenu_preserves_whitespace_and_strips_only_line_ending(self):
        with tempfile.TemporaryDirectory(prefix="controls-password-buffer-") as tmp:
            root = Path(tmp)
            executable, argv_path = self.make_rofi(root, b"  pass with trailing spaces  \r\n")
            result = _password_prompt(
                str(executable), "Wi-Fi password", root / "theme.rasi",
                no_config=True, env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")},
            )
            self.assertEqual(result, bytearray(b"  pass with trailing spaces  "))
            self.assertIsNotNone(result)
            argv = json.loads(argv_path.read_text())
            self.assertIn("-password", argv)
            self.assertIn("-disable-history", argv)
            self.assertIn("-dmenu", argv)
            self.assertNotIn(b"pass with trailing spaces", argv_path.read_bytes())
            result[:] = b"\0" * len(result)

    def test_oversized_password_is_rejected_without_returning_material(self):
        with tempfile.TemporaryDirectory(prefix="controls-password-overflow-") as tmp:
            root = Path(tmp)
            executable, _ = self.make_rofi(root, b"x" * (MAX_SECRET_BYTES + 1))
            result = _password_prompt(
                str(executable), "Wi-Fi password", root / "theme.rasi",
                no_config=True, env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")},
            )
            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
