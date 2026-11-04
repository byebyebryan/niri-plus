"""Native session-screen ownership, countdown and action mapping, all inert."""
import importlib.machinery
import importlib.util
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader("desktop_suspend_screen", str(ROOT / "components/desktop/bin/desktop-suspend"))
spec = importlib.util.spec_from_loader(loader.name, loader)
suspend = importlib.util.module_from_spec(spec)
loader.exec_module(suspend)


class FakeRunner:
    def __init__(self, outcomes=()):
        self.outcomes = list(outcomes)
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append((list(command), kwargs))
        if self.outcomes:
            outcome = self.outcomes.pop(0)
        else:
            outcome = 0
        if isinstance(outcome, BaseException):
            raise outcome
        if isinstance(outcome, tuple):
            code, stdout, stderr = (outcome + ("", ""))[:3]
        else:
            code, stdout, stderr = outcome, "", ""
        return subprocess.CompletedProcess(command, code, stdout, stderr)


class SessionScreenStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="session-screen-check-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.session = suspend.Session(self.root / "state")
        self.addCleanup(self.session.close)
        self.config = self.root / "config"
        (self.config / "desktop-session").mkdir(parents=True)
        (self.config / "desktop-session/power.toml").write_text("lock_before_suspend = false\n")

    def test_opening_has_no_request_and_dispatch_requires_confirm_and_full_timer(self):
        self.assertTrue(self.session.begin_screen(5, "Example"))
        state = self.session.screen_snapshot()
        self.assertEqual(state["stage"], "choose")
        self.assertIsNone(state["request"])
        self.assertIsNone(state["timer_started_at"])
        self.assertIsNone(self.session.claim_screen("0" * 32))

        intent = suspend.request("shutdown", 5, "Example")
        self.assertTrue(self.session.update_screen(state["revision"], "confirm", intent))
        state = self.session.screen_snapshot()
        self.assertEqual(state["stage"], "confirm")
        self.assertIsNone(self.session.claim_screen(intent["id"]))
        self.assertTrue(self.session.update_screen(state["revision"], "countdown", intent))
        state = self.session.screen_snapshot()
        self.assertIsNone(self.session.claim_screen(intent["id"]))

        clock = {"now": 100.0, "boot": 100.0}
        countdown = suspend.Countdown(5, clock=lambda: clock["now"], boot_clock=lambda: clock["boot"])
        self.assertEqual(countdown.tick(True), 5)
        self.assertTrue(self.session.start_screen_timer(intent["id"], state["revision"], countdown.started))
        for now in (101.0, 102.0, 103.0, 104.0, 104.9):
            clock.update(now=now, boot=now)
            remaining = countdown.tick(True)
            self.assertIsNone(countdown.outcome)
        self.assertEqual(remaining, 1)
        with mock.patch.object(suspend.time, "monotonic", return_value=104.9):
            self.assertIsNone(self.session.claim_screen(intent["id"]))
        clock.update(now=105.0, boot=105.0)
        self.assertEqual(countdown.tick(True), 0)
        self.assertEqual(countdown.outcome, "elapsed")
        with mock.patch.object(suspend.time, "monotonic", return_value=105.0):
            claimed = self.session.claim_screen(intent["id"])
            self.assertEqual(claimed, intent)
            self.assertIsNone(self.session.claim_screen(intent["id"]))

        runner = FakeRunner()
        result = suspend.execute_screen_action(claimed, run=runner, config_home=self.config)
        self.assertEqual(result["status"], "accepted")
        self.assertEqual([call[0] for call in runner.calls], [["systemctl", "poweroff"]])

    def test_cancel_near_deadline_cannot_claim_or_dispatch(self):
        self.session.begin_screen(5, "Example", "restart")
        state = self.session.screen_snapshot()
        intent = state["request"]
        self.assertTrue(self.session.update_screen(state["revision"], "countdown", intent))
        state = self.session.screen_snapshot()
        clock = {"now": 20.0, "boot": 20.0}
        countdown = suspend.Countdown(5, clock=lambda: clock["now"], boot_clock=lambda: clock["boot"])
        countdown.tick(True)
        self.session.start_screen_timer(intent["id"], state["revision"], countdown.started)
        clock.update(now=24.9, boot=24.9)
        self.assertEqual(countdown.tick(True), 1)
        with mock.patch.object(suspend.time, "monotonic", return_value=24.9):
            self.assertIsNone(self.session.claim_screen(intent["id"]))
        self.assertTrue(self.session.cancel())
        clock.update(now=25.0, boot=25.0)
        countdown.tick(True, cancelled=True)
        with mock.patch.object(suspend.time, "monotonic", return_value=25.0):
            self.assertIsNone(self.session.claim_screen(intent["id"]))

    def test_raise_preserves_timer_and_replacement_requires_new_confirmation(self):
        self.session.begin_screen(5, "Original", "shutdown")
        first = self.session.screen_snapshot()
        intent = first["request"]
        self.assertTrue(self.session.update_screen(first["revision"], "countdown", intent))
        state = self.session.screen_snapshot()
        self.assertTrue(self.session.start_screen_timer(intent["id"], state["revision"], time.monotonic()))
        started = self.session.screen_snapshot()["timer_started_at"]

        opener = suspend.Session(self.session.directory)
        self.assertFalse(opener.begin_screen(30, "Changed", wait_seconds=0.1))
        raised = self.session.screen_snapshot()
        self.assertEqual(raised["stage"], "countdown")
        self.assertEqual(raised["request"], intent)
        self.assertEqual(raised["settings"], {"seconds": 5, "label": "Original"})
        self.assertEqual(raised["timer_started_at"], started)
        self.assertEqual(raised["raised"], 1)

        replacement = suspend.Session(self.session.directory)
        self.assertFalse(replacement.begin_screen(7, "Replacement", "restart"))
        changed = self.session.screen_snapshot()
        self.assertEqual(changed["stage"], "confirm")
        self.assertEqual(changed["settings"], {"seconds": 7, "label": "Replacement"})
        self.assertNotEqual(changed["request"]["id"], intent["id"])
        self.assertIsNone(changed["timer_started_at"])
        self.assertIsNone(self.session.claim_screen(intent["id"]))
        self.assertIsNone(self.session.claim_screen(changed["request"]["id"]))

    def test_legacy_pending_owner_is_cancelled_then_grid_acquires_same_invocation(self):
        legacy = suspend.Session(self.session.directory)
        self.assertTrue(legacy.begin(suspend.request("shutdown")))
        new_screen = suspend.Session(self.session.directory)

        def release_on_cancel():
            deadline = time.monotonic() + 2
            while not legacy.cancelled() and time.monotonic() < deadline:
                time.sleep(0.005)
            legacy.close()

        releaser = threading.Thread(target=release_on_cancel, daemon=True)
        releaser.start()
        self.assertTrue(new_screen.begin_screen(wait_seconds=1))
        releaser.join(timeout=1)
        self.assertEqual(new_screen.screen_snapshot()["stage"], "choose")
        self.assertTrue(legacy.cancelled())
        legacy.close()
        new_screen.close()

    def test_committed_legacy_owner_is_not_cancelled_or_replaced(self):
        legacy = suspend.Session(self.session.directory)
        self.assertTrue(legacy.begin())
        pending = suspend.read_json(legacy.pending)
        pending["phase"] = "committing"
        suspend.atomic_json(legacy.pending, pending)
        new_screen = suspend.Session(self.session.directory)
        self.assertFalse(new_screen.begin_screen(wait_seconds=0.1))
        self.assertEqual(new_screen.disposition, "an action is already committed")
        self.assertFalse(legacy.cancelled())
        legacy.close()

    def test_malformed_screen_state_fails_closed(self):
        self.session.begin_screen(5, "Example")
        pending = suspend.read_json(self.session.pending)
        pending["stage"] = "countdown"
        suspend.atomic_json(self.session.pending, pending)
        with self.assertRaises(RuntimeError):
            self.session.screen_snapshot()
        with self.assertRaises(RuntimeError):
            self.session.claim_screen("0" * 32)

    def test_partial_result_retry_gets_a_fresh_confirmation_and_timer(self):
        self.session.begin_screen(1, "Example", "away")
        state = self.session.screen_snapshot()
        intent = state["request"]
        self.assertTrue(self.session.update_screen(state["revision"], "countdown", intent))
        state = self.session.screen_snapshot()
        self.assertTrue(self.session.start_screen_timer(intent["id"], state["revision"], 100.0))
        with mock.patch.object(suspend.time, "monotonic", return_value=101.0):
            claimed = self.session.claim_screen(intent["id"])
        self.assertEqual(claimed, intent)
        result = suspend.execute_screen_action(claimed, run=FakeRunner([(1, "", "fallback applied")]),
                                               config_home=self.config)
        self.assertEqual(result["status"], "partial")
        self.assertTrue(self.session.finish_screen(result))
        failed = self.session.screen_snapshot()
        self.assertEqual(failed["stage"], "result")
        self.assertEqual(failed["result"]["status"], "partial")

        retry = suspend.request("away", 1, "Example")
        self.assertTrue(self.session.update_screen(failed["revision"], "confirm", retry))
        fresh = self.session.screen_snapshot()
        self.assertEqual(fresh["stage"], "confirm")
        self.assertNotEqual(fresh["request"]["id"], intent["id"])
        self.assertIsNone(fresh["timer_started_at"])
        self.assertIsNone(self.session.claim_screen(intent["id"]))

    def test_owner_death_releases_pending_request_without_dispatch(self):
        self.session.begin_screen(5, "Example", "restart")
        old_directory = self.session.directory
        self.session.close()
        replacement = suspend.Session(old_directory)
        self.assertTrue(replacement.begin_screen(5, "Example"))
        self.assertEqual(replacement.screen_snapshot()["stage"], "choose")
        replacement.close()

    def test_same_socket_path_replacement_changes_session_identity(self):
        socket_path = self.root / "niri.sock"
        old_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        old_socket.bind(str(socket_path))
        self.addCleanup(old_socket.close)
        env = {"XDG_RUNTIME_DIR": str(self.root), "NIRI_SOCKET": str(socket_path)}
        old_directory = suspend.state_directory(env)
        owner = suspend.Session(old_directory, socket_path=socket_path, require_socket=True)
        self.addCleanup(owner.close)
        owner.begin_screen(5, "Example", "restart")
        state = owner.screen_snapshot()
        owner.update_screen(state["revision"], "countdown", state["request"])
        state = owner.screen_snapshot()
        owner.start_screen_timer(state["request"]["id"], state["revision"], time.monotonic())

        old_socket.close()
        socket_path.unlink()
        new_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        new_socket.bind(str(socket_path))
        self.addCleanup(new_socket.close)
        new_directory = suspend.state_directory(env)
        self.assertNotEqual(old_directory, new_directory)
        self.assertFalse(owner.session_unchanged())
        self.assertIsNone(owner.claim_screen(state["request"]["id"]))


class ScreenActionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="session-screen-actions-")
        self.addCleanup(self.temp.cleanup)
        self.config = Path(self.temp.name) / "config"
        (self.config / "desktop-session").mkdir(parents=True)
        self.policy = self.config / "desktop-session/power.toml"
        self.policy.write_text("lock_before_suspend = false\n")

    def invoke(self, operation, runner):
        return suspend.execute_screen_action(suspend.request(operation, 5, "Example"),
                                             run=runner, config_home=self.config)

    def test_all_six_fixed_action_mappings_and_logout_is_single_dispatch(self):
        expected = {
            "lock": [["systemctl", "--user", "start", "desktop-lock.service"], ["desktop-away", "away"]],
            "away": [["desktop-away", "away"]],
            "suspend": [["systemctl", "suspend"]],
            "logout": [["niri", "msg", "action", "quit", "--skip-confirmation"]],
            "restart": [["systemctl", "reboot"]],
            "shutdown": [["systemctl", "poweroff"]],
        }
        for operation, commands in expected.items():
            with self.subTest(operation=operation):
                runner = FakeRunner()
                result = self.invoke(operation, runner)
                self.assertEqual(result["status"], "accepted")
                self.assertEqual([call[0] for call in runner.calls], commands)
                if operation == "logout":
                    self.assertEqual(len(runner.calls), 1)

    def test_suspend_rereads_lock_policy_and_preserves_lock_before_sleep(self):
        self.policy.write_text("lock_before_suspend = true\n")
        runner = FakeRunner()
        result = self.invoke("suspend", runner)
        self.assertEqual(result["status"], "accepted")
        self.assertTrue(result["yield_to_locker"])
        self.assertEqual([call[0] for call in runner.calls], [
            ["systemctl", "--user", "start", "desktop-lock.service"], ["systemctl", "suspend"]])
        self.policy.write_text('lock_before_suspend = "true"\n')
        runner = FakeRunner()
        result = self.invoke("suspend", runner)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(runner.calls, [])

    def test_lock_refusal_never_requests_display_off(self):
        runner = FakeRunner([(1, "", "locker failed")])
        result = self.invoke("lock", runner)
        self.assertEqual(result["status"], "refused")
        self.assertFalse(result["yield_to_locker"])
        self.assertEqual([call[0] for call in runner.calls], [["systemctl", "--user", "start", "desktop-lock.service"]])

    def test_lock_timeout_yields_without_display_off_because_lock_may_be_active(self):
        runner = FakeRunner([subprocess.TimeoutExpired("systemctl", 15)])
        result = self.invoke("lock", runner)
        self.assertEqual(result["status"], "partial")
        self.assertTrue(result["yield_to_locker"])
        self.assertEqual(len(runner.calls), 1)

    def test_away_missing_helper_is_refusal_but_fallback_status_is_partial(self):
        missing = FakeRunner([FileNotFoundError("desktop-away missing")])
        result = self.invoke("away", missing)
        self.assertEqual(result["status"], "refused")
        self.assertFalse(result["yield_to_locker"])
        self.assertIn("could not start", result["summary"])

        degraded = FakeRunner([(1, "", "one-shot fallback applied without enforcement")])
        result = self.invoke("away", degraded)
        self.assertEqual(result["status"], "partial")
        self.assertIn("fallback", result["diagnostic"])

    def test_lock_success_plus_away_failure_is_partial_and_yields(self):
        runner = FakeRunner([0, (1, "", "controller unavailable")])
        result = self.invoke("lock", runner)
        self.assertEqual(result["status"], "partial")
        self.assertTrue(result["yield_to_locker"])
        self.assertIn("session is locked", result["summary"])
        self.assertEqual([call[0] for call in runner.calls], [
            ["systemctl", "--user", "start", "desktop-lock.service"], ["desktop-away", "away"]])

    def test_native_refusal_and_timeout_are_reported_truthfully(self):
        refused = FakeRunner([(1, "", "polkit refused reboot")])
        result = self.invoke("restart", refused)
        self.assertEqual(result["status"], "refused")
        self.assertEqual(result["diagnostic"], "polkit refused reboot")

        uncertain = FakeRunner([subprocess.TimeoutExpired("systemctl", 30)])
        result = self.invoke("shutdown", uncertain)
        self.assertEqual(result["status"], "partial")
        self.assertIn("may have been accepted", result["summary"])

    def test_locker_status_fails_closed_when_unclear(self):
        self.assertTrue(suspend.locker_is_active(run=FakeRunner([(0, "active\n", "")]).__call__))
        self.assertFalse(suspend.locker_is_active(run=FakeRunner([(3, "inactive\n", "")]).__call__))
        with self.assertRaises(RuntimeError):
            suspend.locker_is_active(run=FakeRunner([(1, "unknown\n", "")]).__call__)


class SessionScreenGuardTests(unittest.TestCase):
    def test_activation_accepts_fresh_press_without_a_debounce_and_rejects_holds(self):
        keys = suspend.ActivationKeys()
        for key in ("Return", "Space"):
            self.assertTrue(keys.press(key))
            self.assertFalse(keys.press(key))
            self.assertFalse(keys.press(key))
            keys.release(key)
            self.assertTrue(keys.press(key))
            keys.release(key)

    def test_focus_watch_cancels_focus_loss_stall_and_sleep_resume(self):
        now = {"mono": 0.0, "boot": 0.0}
        watch = suspend.ScreenFocusWatch(clock=lambda: now["mono"], boot_clock=lambda: now["boot"])
        self.assertFalse(watch.tick(True))
        now["mono"] = 0.1
        now["boot"] = 0.1
        self.assertTrue(watch.tick(False))

        now.update(mono=0.0, boot=0.0)
        watch = suspend.ScreenFocusWatch(clock=lambda: now["mono"], boot_clock=lambda: now["boot"])
        self.assertFalse(watch.tick(True))
        now.update(mono=3.0, boot=3.0)
        self.assertTrue(watch.tick(True))

        now.update(mono=0.0, boot=0.0)
        watch = suspend.ScreenFocusWatch(clock=lambda: now["mono"], boot_clock=lambda: now["boot"])
        self.assertFalse(watch.tick(True))
        now.update(mono=0.1, boot=30.0)
        self.assertTrue(watch.tick(True))

        now.update(mono=0.0, boot=0.0)
        watch = suspend.ScreenFocusWatch(clock=lambda: now["mono"], boot_clock=lambda: now["boot"])
        self.assertFalse(watch.tick(False))
        now.update(mono=3.0, boot=3.0)
        self.assertTrue(watch.tick(False))


if __name__ == "__main__":
    unittest.main()
