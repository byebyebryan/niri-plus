import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "components/desktop/bin/niri-close-all"
loader = importlib.machinery.SourceFileLoader("niri_plus_close_all", str(HELPER))
spec = importlib.util.spec_from_loader(loader.name, loader)
close = importlib.util.module_from_spec(spec)
loader.exec_module(close)


class CloseAllTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="niri-close-all-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.endpoint = self.root / "niri.sock"
        self.server = socket.socket(socket.AF_UNIX)
        self.server.bind(str(self.endpoint))
        self.addCleanup(self.server.close)
        self.env = dict(os.environ, NIRI_SOCKET=str(self.endpoint))
        self.errors = io.StringIO()

    def run_helper(self, runner, **kwargs):
        return close.close_all(environment=self.env, run=runner, errors=self.errors, **kwargs)

    def test_snapshot_spans_workspaces_floating_and_unknown_metadata_without_focus_actions(self):
        windows = [{"id": 4, "workspace_id": 1, "is_focused": True},
                   {"id": 9, "workspace_id": 50, "is_floating": True},
                   {"id": 0, "workspace_id": None, "app_id": None, "future_field": True},
                   {"id": 2 ** 64 - 1, "workspace_id": 100}]
        calls = []
        def run(command, **kwargs):
            calls.append(command)
            self.assertEqual(kwargs["env"]["NIRI_SOCKET"], str(self.endpoint))
            self.assertEqual(kwargs["timeout"], 5)
            return subprocess.CompletedProcess(command, 0, json.dumps(windows) if len(calls) == 1 else "Handled")
        result = self.run_helper(run)
        self.assertEqual(calls, [["niri", "msg", "--json", "windows"], *[
            ["niri", "msg", "action", "close-window", "--id", str(i)] for i in [4, 9, 0, 2 ** 64 - 1]]])
        self.assertEqual(result["requested_ids"], [4, 9, 0, 2 ** 64 - 1])
        self.assertEqual(result["scope"], "all-workspaces-and-outputs")

    def test_new_save_dialogs_and_windows_are_not_resnapshotted_or_closed(self):
        windows, calls = [{"id": 7}, {"id": 8}, {"id": 7}], []
        def run(command, **kwargs):
            calls.append(command)
            if len(calls) == 1:
                return subprocess.CompletedProcess(command, 0, json.dumps(windows))
            # Closing an app opens a save dialog. The app refuses to disappear.
            windows.append({"id": 999})
            return subprocess.CompletedProcess(command, 0, "Handled")
        result = self.run_helper(run)
        self.assertEqual(len(calls), 3)
        self.assertEqual(result["snapshot_ids"], [7, 8])
        self.assertEqual(result["requested_ids"], [7, 8])
        self.assertNotIn(999, result["requested_ids"])

    def test_empty_snapshot_sends_no_actions(self):
        calls = []
        def run(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, "[]")
        result = self.run_helper(run)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["snapshot_ids"], [])

    def test_invalid_snapshot_is_rejected_in_full_before_any_action(self):
        for bad in [{}, None, [None], [{"id": 1}, {}], [{"id": True}], [{"id": -1}],
                    [{"id": 2 ** 64}], [{"id": "2"}], [{"id": 2.0}]]:
            with self.subTest(bad=bad):
                calls = []
                def run(command, **kwargs):
                    calls.append(command)
                    return subprocess.CompletedProcess(command, 0, json.dumps(bad))
                with self.assertRaises(ValueError):
                    self.run_helper(run)
                self.assertEqual(len(calls), 1)

    def test_invalid_json_and_snapshot_failure_send_no_actions(self):
        for status, value in [(0, "not json"), (1, '[{"id": 1}]')]:
            calls = []
            def run(command, **kwargs):
                calls.append(command)
                return subprocess.CompletedProcess(command, status, value)
            with self.assertRaises((ValueError, RuntimeError)):
                self.run_helper(run)
            self.assertEqual(len(calls), 1)

    def test_failed_or_timed_out_request_is_not_retried_and_other_ids_are_attempted(self):
        for failure in ["refused", "timeout", "missing"]:
            with self.subTest(failure=failure):
                calls = []
                def run(command, **kwargs):
                    calls.append(command)
                    if len(calls) == 1:
                        return subprocess.CompletedProcess(command, 0, '[{"id": 1},{"id": 2}]')
                    if command[-1] == "1":
                        if failure == "timeout": raise subprocess.TimeoutExpired(command, 5)
                        if failure == "missing": raise FileNotFoundError("fixture missing CLI")
                        return subprocess.CompletedProcess(command, 1, "")
                    return subprocess.CompletedProcess(command, 0, "Handled")
                result = self.run_helper(run)
                self.assertEqual(len(calls), 3)
                self.assertEqual(result["failed_ids"], [1])
                self.assertEqual(result["requested_ids"], [2])

    def test_compositor_socket_replacement_stops_before_remaining_ids(self):
        calls = []
        replacement = socket.socket(socket.AF_UNIX)
        self.addCleanup(replacement.close)
        def run(command, **kwargs):
            calls.append(command)
            if len(calls) == 1:
                return subprocess.CompletedProcess(command, 0, '[{"id": 3},{"id": 4}]')
            self.endpoint.unlink()
            replacement.bind(str(self.endpoint))
            return subprocess.CompletedProcess(command, 0, "Handled")
        result = self.run_helper(run)
        self.assertEqual(len(calls), 2)
        self.assertEqual(result["requested_ids"], [3])
        self.assertEqual(result["not_attempted_ids"], [4])

    def test_missing_non_socket_and_symlink_endpoints_send_no_requests(self):
        regular = self.root / "regular"
        regular.write_text("fixture")
        linked = self.root / "link.sock"
        linked.symlink_to(self.endpoint)
        for endpoint in [None, "relative.sock", str(regular), str(linked), str(self.root / "absent")]:
            with self.subTest(endpoint=endpoint):
                env = dict(self.env)
                env.pop("NIRI_SOCKET")
                if endpoint is not None: env["NIRI_SOCKET"] = endpoint
                def run(*args, **kwargs):
                    self.fail("invalid session endpoint invoked a command")
                with self.assertRaises((RuntimeError, OSError)):
                    close.close_all(environment=env, run=run)

    def test_dry_run_uses_one_snapshot_and_no_close_requests(self):
        calls = []
        def run(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, '[{"id": 11}]')
        result = self.run_helper(run, dry_run=True)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["snapshot_ids"], [11])
        self.assertEqual(result["requested_ids"], [])
        self.assertTrue(result["dry_run"])

    def test_real_cli_uses_private_command_stub_and_exit_statuses(self):
        bindir = self.root / "bin"
        bindir.mkdir()
        log = self.root / "requests.jsonl"
        stub = bindir / "niri"
        stub.write_text('''#!/usr/bin/env python3
import json, os, sys
with open(os.environ["CLOSE_ALL_TEST_LOG"], "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1:] == ["msg", "--json", "windows"]:
    print('[{"id": 10}, {"id": 20}]')
else:
    assert sys.argv[1:5] == ["msg", "action", "close-window", "--id"]
    if sys.argv[-1] == os.environ.get("CLOSE_ALL_TEST_FAIL"):
        raise SystemExit(1)
''')
        stub.chmod(0o755)
        env = dict(self.env, PATH=str(bindir) + os.pathsep + os.environ["PATH"], CLOSE_ALL_TEST_LOG=str(log))
        for args, failure, expected_status, count in [([], "", 0, 3),
                (["--dry-run"], "", 0, 1), ([], "10", 1, 3), (["--help"], "", 0, 0),
                (["--unknown-option"], "", 2, 0)]:
            with self.subTest(args=args, failure=failure):
                log.unlink(missing_ok=True)
                process = subprocess.run([sys.executable, str(HELPER), *args],
                    env=dict(env, CLOSE_ALL_TEST_FAIL=failure), capture_output=True, text=True, timeout=10)
                self.assertEqual(process.returncode, expected_status, process.stderr)
                calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
                self.assertEqual(len(calls), count)
                if count:
                    result = json.loads(process.stdout)
                    self.assertEqual(result["failed_ids"], [10] if failure else [])

    def test_opt_in_binding_leaves_the_starter_and_mod_q_unchanged(self):
        profile = (ROOT / "components/desktop/config/niri/close-all.kdl").read_text()
        self.assertIn('Mod+Shift+Q repeat=false hotkey-overlay-title="Close all windows (all workspaces and outputs)"', profile)
        starter = (ROOT / "examples/niri/config.kdl").read_text()
        self.assertIn("Mod+Q { close-window; }", starter)
        self.assertNotIn("Mod+Shift+Q", starter)


if __name__ == "__main__":
    unittest.main()
