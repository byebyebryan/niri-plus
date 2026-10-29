import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("controls_public_appearance", ROOT / "components/appearance/render.py")
appearance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(appearance)


class ControlsAppearance(unittest.TestCase):
    def test_control_state_colors_derive_from_selected_identity(self):
        identity = json.loads((ROOT / "design/identity.json").read_text())
        original = json.dumps(identity, sort_keys=True)
        artifacts = appearance.render(identity)
        model = json.loads(artifacts["controls-appearance.json"])
        selected = next(p for p in identity["candidates"] if p["id"] == identity["selected_candidate"])
        self.assertEqual(model["schema_version"], 1)
        self.assertEqual(model["colors"], selected["colors"])
        self.assertEqual(model["derived"], {"current_background": "#353d30", "current_outline": "#86a26f"})
        self.assertEqual(json.dumps(identity, sort_keys=True), original)
        self.assertEqual(model["fonts"]["ui_font"], selected["ui_font"])
        theme = artifacts["niri-plus-controls.rasi"]
        self.assertTrue(theme.startswith(artifacts["neutral-slate.rasi"]))
        self.assertIn("element selected.active", theme)
        self.assertIn("#86a26f", theme)
        self.assertNotIn("color-mix", theme)
        self.assertNotIn("current_background", artifacts["neutral-slate.rasi"])

    def test_state_tints_follow_an_input_identity_change_without_terminal_changes(self):
        identity = json.loads((ROOT / "design/identity.json").read_text())
        before = appearance.render(identity)
        selected = next(p for p in identity["candidates"] if p["id"] == identity["selected_candidate"])
        selected["colors"]["success"] = "#ffffff"
        after = appearance.render(identity)
        self.assertNotEqual(before["controls-appearance.json"], after["controls-appearance.json"])
        self.assertEqual(before["kitty-neutral-slate.conf"], after["kitty-neutral-slate.conf"])


if __name__ == "__main__":
    unittest.main()
