import copy
import importlib.util
import json
import math
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

    def test_swaync_sidebar_is_opt_in_and_scoped_to_swaync_and_identity_data(self):
        selected = json.loads((ROOT / "design/identity.json").read_text())
        legacy = copy.deepcopy(selected)
        legacy["shared"].pop("swaync_sidebar")
        before = appearance.render(legacy)
        after = appearance.render(selected)

        changed = {name for name in before if before[name] != after[name]}
        self.assertEqual(changed, {"swaync.css", "theme.json"})
        self.assertNotIn(".notification-group.collapsed.not-expanded { opacity: 1; }", before["swaync.css"])
        self.assertIn(".notification-group.collapsed.not-expanded { opacity: 1; }", after["swaync.css"])
        self.assertEqual(json.loads(after["theme.json"])["shared"]["swaync_sidebar"], {
            "opacity": 0.75,
            "border_color": "#6b747c",
            "card_border_color": "#5d666e",
        })

    def test_swaync_sidebar_alpha_borders_priority_and_focus_contract(self):
        identity = json.loads((ROOT / "design/identity.json").read_text())
        profile = next(item for item in identity["candidates"] if item["id"] == identity["selected_candidate"])
        sidebar = identity["shared"]["swaync_sidebar"]
        colors = profile["colors"]
        css = appearance.render(identity)["swaync.css"]

        self.assertIn(f"--cc-bg: alpha({colors['surface']}, 0.75);", css)
        self.assertIn("--noti-bg-alpha: 0.75;", css)
        self.assertIn(f"--information-bg: alpha({colors['surface']}, 0.75);", css)
        self.assertIn(f"--noti-bg-hover: alpha({colors['raised']}, 0.75);", css)
        self.assertIn(f"--noti-border-color: {sidebar['card_border_color']};", css)
        self.assertIn(f"--information-border-color: {sidebar['card_border_color']};", css)
        self.assertIn(
            f".control-center {{ border: 0; border-left: 1px solid {sidebar['border_color']}; }}",
            css,
        )
        self.assertIn(f".widget-information .information-divider {{ background: {colors['separator']}; }}", css)
        self.assertIn(
            ".control-center .control-center-list .notification { background: rgba(var(--noti-bg), var(--noti-bg-alpha)); }",
            css,
        )
        self.assertIn(
            ".control-center .notification-group.collapsed .notification { background-color: rgba(var(--noti-bg), var(--noti-bg-alpha)); }",
            css,
        )
        self.assertIn(
            ".control-center .notification-group.collapsed:hover .notification { background-color: var(--noti-bg-hover); }",
            css,
        )
        self.assertIn(
            f"background: alpha({colors['surface']}, 0.75);\n  border: 2px solid {colors['error']};",
            css,
        )
        self.assertIn(f"box-shadow: inset 3px 0 0 {colors['accent']};", css)
        self.assertIn(f"button:focus-visible {{ outline: 2px solid {colors['focus']};", css)
        self.assertNotIn("opacity: 0.75;", css)

    def test_swaync_sidebar_identity_contract_rejects_invalid_values(self):
        base = json.loads((ROOT / "design/identity.json").read_text())
        valid = {
            "opacity": 0.75,
            "border_color": "#6b747c",
            "card_border_color": "#5d666e",
        }

        for invalid in (
            None,
            [],
            {"opacity": 0.75, "border_color": "#6b747c"},
            {**valid, "unexpected": True},
        ):
            with self.subTest(sidebar=invalid):
                identity = copy.deepcopy(base)
                identity["shared"]["swaync_sidebar"] = invalid
                with self.assertRaisesRegex(ValueError, "shared.swaync_sidebar"):
                    appearance.render(identity)

        for opacity in (True, False, math.nan, math.inf, -0.01, 1.01, "0.75"):
            with self.subTest(opacity=opacity):
                identity = copy.deepcopy(base)
                identity["shared"]["swaync_sidebar"] = {**valid, "opacity": opacity}
                with self.assertRaisesRegex(ValueError, "opacity must be finite"):
                    appearance.render(identity)

        for key in ("border_color", "card_border_color"):
            for color in ("#12345", "#12345678", "#gg0000", 0, None):
                with self.subTest(key=key, color=color):
                    identity = copy.deepcopy(base)
                    identity["shared"]["swaync_sidebar"] = {**valid, key: color}
                    with self.assertRaisesRegex(ValueError, "six-digit hexadecimal"):
                        appearance.render(identity)

        for opacity in (0, 0.0, 1, 1.0):
            with self.subTest(valid_opacity=opacity):
                identity = copy.deepcopy(base)
                identity["shared"]["swaync_sidebar"] = {**valid, "opacity": opacity}
                appearance.render(identity)


if __name__ == "__main__":
    unittest.main()
