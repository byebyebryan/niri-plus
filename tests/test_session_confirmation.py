"""Session-menu screen routing starts actions through the shared countdown guard."""
import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("session_confirmation", str(ROOT / "components/desktop/bin/desktop-session-menu"))
spec = importlib.util.spec_from_loader(loader.name, loader)
menu = importlib.util.module_from_spec(spec)
loader.exec_module(menu)


class SessionConfirmationTests(unittest.TestCase):
    def test_screen_route_is_opt_in_and_select_starts_the_countdown(self):
        command = menu.screen_command(7, "Example", "shutdown")
        self.assertEqual(Path(command[0]).name, "desktop-suspend")
        self.assertEqual(command[1:], ["menu", "--seconds", "7", "--label", "Example",
                                       "--select", "shutdown"])
        with mock.patch.object(menu.subprocess, "run") as run:
            self.assertEqual(menu.main(["--screen", "--seconds", "7", "--label", "Example", "--select", "shutdown"]), 0)
        run.assert_called_once_with(command, check=True)

    def test_screen_route_rejects_invalid_values(self):
        for args in ((0, "Example", None), (5, "", None), (5, "bad\nlabel", None),
                     (5, "Example", "not-an-action")):
            with self.subTest(args=args), self.assertRaises(ValueError):
                menu.screen_command(*args)

    def test_every_manual_action_routes_through_one_guard_without_another_prompt(self):
        policy = {"seconds": 5, "label": "Example", "lock_on_away": True}
        actions = {"Lock": "lock", "Suspend": "suspend", "Restart": "restart", "Shut down": "shutdown",
                   "Lock and turn off displays": "away"}
        for action, operation in actions.items():
            with self.subTest(action=action):
                run = mock.Mock()
                picker = mock.Mock(side_effect=AssertionError("unexpected second prompt"))
                self.assertTrue(menu.dispatch(action, run=run, picker=picker, confirmation=policy))
                command = run.call_args.args[0]
                self.assertEqual(Path(command[0]).name, "desktop-suspend")
                expected = ["countdown", "--operation", operation, "--seconds", "5", "--label", "Example"]
                if operation == "away":
                    expected.append("--lock")
                self.assertEqual(command[1:], expected)
                self.assertEqual(run.call_count, 1)

    def test_display_only_policy_does_not_add_lock(self):
        run = mock.Mock()
        menu.dispatch("Turn off displays", run=run, confirmation={"seconds": 5, "label": "Example", "lock_on_away": False})
        self.assertNotIn("--lock", run.call_args.args[0])

    def test_unadopted_restart_keeps_cancel_first_confirmation(self):
        run = mock.Mock()
        picker = mock.Mock(return_value="Cancel")
        self.assertFalse(menu.dispatch("Restart", run=run, picker=picker))
        picker.assert_called_once_with(("Cancel", "Restart"), "Confirm restart")
        run.assert_not_called()

    def test_logout_keeps_niri_confirmation_and_cancel_has_no_effect(self):
        run = mock.Mock()
        policy = {"seconds": 5, "label": "Example", "lock_on_away": False}
        self.assertFalse(menu.dispatch(None, run=run, confirmation=policy))
        run.assert_not_called()
        menu.dispatch("Log out", run=run, confirmation=policy)
        self.assertEqual(run.call_args.args[0], ["niri", "msg", "action", "quit"])

    def test_optional_policy_and_invalid_adoption_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary)
            self.assertIsNone(menu.read_confirmation_policy(config))
            path = config / "desktop-session/confirmation.toml"
            path.parent.mkdir()
            for content in ("", "[invalid", 'seconds = true\nlabel = "Example"\nlock_on_away = false',
                            'seconds = 0\nlabel = "Example"\nlock_on_away = false',
                            'seconds = 5\nlabel = ""\nlock_on_away = false',
                            'seconds = 5\nlabel = "Example"\nlock_on_away = "false"'):
                path.write_text(content)
                with self.subTest(content=content), self.assertRaises(SystemExit):
                    menu.read_confirmation_policy(config)
            path.write_text('seconds = 5\nlabel = "Example"\nlock_on_away = false\n')
            self.assertEqual(menu.read_confirmation_policy(config), {"seconds": 5, "label": "Example", "lock_on_away": False})
