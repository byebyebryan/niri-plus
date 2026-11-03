"""Fail-closed suspend decisions and serialized cancellation, without a desktop."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("desktop_suspend", str(ROOT / "components/desktop/bin/desktop-suspend"))
spec = importlib.util.spec_from_loader(loader.name, loader)
suspend = importlib.util.module_from_spec(spec)
loader.exec_module(suspend)


class CountdownTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.boot = 100.0
        self.timer = suspend.Countdown(5, clock=lambda: self.now, boot_clock=lambda: self.boot)

    def advance(self, seconds):
        self.now += seconds
        self.boot += seconds

    def test_five_seconds_start_only_after_focus(self):
        self.advance(1)
        self.assertEqual(self.timer.tick(False), 5)
        self.advance(1)
        self.assertEqual(self.timer.tick(True), 5)
        for remaining in (4, 3, 2, 1):
            self.advance(1)
            self.assertEqual(self.timer.tick(True), remaining)
            self.assertIsNone(self.timer.outcome)
        self.advance(1)
        self.assertEqual(self.timer.tick(True), 0)
        self.assertEqual(self.timer.outcome, "elapsed")

    def test_unfocused_startup_and_focus_loss_cancel(self):
        self.advance(3)
        self.timer.tick(False)
        self.assertEqual(self.timer.outcome, "cancelled")
        self.setUp()
        self.timer.tick(True)
        self.advance(1)
        self.timer.tick(False)
        self.assertEqual(self.timer.outcome, "cancelled")

    def test_explicit_cancel_at_deadline_wins(self):
        self.timer.tick(True)
        for _ in range(4):
            self.advance(1)
            self.timer.tick(True)
        self.advance(1)
        self.timer.tick(True, cancelled=True)
        self.assertEqual(self.timer.outcome, "cancelled")

    def test_frozen_ui_and_external_sleep_cancel(self):
        self.timer.tick(True)
        self.advance(6)
        self.timer.tick(True)
        self.assertEqual(self.timer.outcome, "cancelled")
        self.setUp()
        self.timer.tick(True)
        self.advance(0.1)
        self.boot += 60
        self.timer.tick(True)
        self.assertEqual(self.timer.outcome, "cancelled")


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="suspend-check-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.session = suspend.Session(self.root / "session")
        self.addCleanup(self.session.close)
        self.config = self.root / "config"
        (self.config / "desktop-session").mkdir(parents=True)
        self.policy = self.config / "desktop-session/power.toml"
        self.policy.write_text("lock_before_suspend = false\n")

    def test_duplicate_cannot_replace_or_restart_owner(self):
        self.assertTrue(self.session.begin())
        pending = self.session.pending.read_bytes()
        other = suspend.Session(self.session.directory)
        self.assertFalse(other.begin())
        other.close()
        self.assertEqual(self.session.pending.read_bytes(), pending)
        self.assertFalse(self.session.cancelled())

    def test_cancel_during_startup_prevents_commit(self):
        self.session.begin()
        self.assertTrue(suspend.Session(self.session.directory).cancel())
        run = mock.Mock()
        self.assertFalse(self.session.commit(run=run, config_home=self.config))
        run.assert_not_called()

    def test_cli_cancel_targets_active_instance(self):
        env = dict(os.environ, XDG_RUNTIME_DIR=str(self.root), NIRI_SOCKET="/isolated/session.sock")
        directory = suspend.state_directory(env)
        owner = suspend.Session(directory)
        try:
            owner.begin()
            result = subprocess.run(["/usr/bin/python3", str(loader.path), "cancel"], env=env,
                                    capture_output=True, text=True, timeout=3)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(owner.cancelled())
        finally:
            owner.close()

    def test_away_cancels_before_lock_and_blank(self):
        self.session.begin()
        calls = []

        def run(args, **_kwargs):
            self.assertTrue(self.session.cancelled())
            calls.append(args)

        suspend.away(suspend.Session(self.session.directory), True, run=run)
        self.assertEqual(calls, [["systemctl", "--user", "start", "desktop-lock.service"], ["desktop-away", "away"]])
        self.assertFalse(self.session.commit(run=run, config_home=self.config))

    def test_away_failure_does_not_skip_lock(self):
        self.session.begin()
        run = mock.Mock(side_effect=subprocess.CalledProcessError(1, "systemctl"))
        with self.assertRaises(subprocess.CalledProcessError):
            suspend.away(suspend.Session(self.session.directory), True, run=run)
        self.assertEqual(run.call_count, 1)
        self.assertTrue(self.session.cancelled())

    def test_commit_uses_captured_lock_policy(self):
        for lock in (False, True):
            with self.subTest(lock=lock):
                self.policy.write_text(f"lock_before_suspend = {str(lock).lower()}\n")
                self.session.begin()
                run = mock.Mock()
                self.assertTrue(self.session.commit(run=run, config_home=self.config))
                args = [call.args[0] for call in run.call_args_list]
                expected = [["systemctl", "suspend"]]
                if lock:
                    expected.insert(0, ["systemctl", "--user", "start", "desktop-lock.service"])
                self.assertEqual(args, expected)
                self.session.close()

    def test_invalid_or_missing_policy_never_suspends(self):
        self.session.begin()
        run = mock.Mock()
        for content in ('lock_before_suspend = "false"', "other = true", "[invalid"):
            self.policy.write_text(content)
            with self.assertRaises((ValueError, KeyError)):
                self.session.commit(run=run, config_home=self.config)
        self.policy.unlink()
        with self.assertRaises(OSError):
            self.session.commit(run=run, config_home=self.config)
        run.assert_not_called()

    def test_stale_cancel_does_not_cancel_next_instance(self):
        self.session.begin()
        self.session.cancel()
        self.session.close()
        self.assertTrue(self.session.begin())
        self.assertFalse(self.session.cancelled())

    def test_sessions_are_separate_and_private(self):
        env = {"XDG_RUNTIME_DIR": str(self.root), "NIRI_SOCKET": "/session/a.sock"}
        first = suspend.state_directory(env)
        second = suspend.state_directory(dict(env, NIRI_SOCKET="/session/b.sock"))
        self.assertNotEqual(first, second)
        self.assertEqual(first.stat().st_mode & 0o777, 0o700)
        unsafe = self.root / "unsafe"
        unsafe.mkdir(mode=0o755)
        with self.assertRaises(RuntimeError):
            suspend.private_directory(unsafe)


if __name__ == "__main__":
    unittest.main()
