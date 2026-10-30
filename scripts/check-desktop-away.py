#!/usr/bin/env python3
"""Exercise away-mode decisions and an isolated daemon with a fake compositor."""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "components/desktop/bin/desktop-away"
loader = importlib.machinery.SourceFileLoader("desktop_away", str(HELPER))
spec = importlib.util.spec_from_loader(loader.name, loader)
away = importlib.util.module_from_spec(spec)
loader.exec_module(away)


class LatchTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.calls = []
        self.latch = away.Latch(self.calls.append, lambda: self.now)

    def test_regular_mode_never_overrides_an_application(self):
        self.latch.enforce({"DP-1": "On"})
        self.assertEqual(self.calls, [])

    def test_away_corrects_a_wake_and_stops_after_input(self):
        self.latch.enter()
        self.now += 1
        self.latch.enforce({"DP-1": "On"})
        self.latch.input(102, 1, 30, 1, "keyboard")
        self.latch.enforce({"DP-1": "On"})
        self.assertEqual(self.calls, [False, False, True])
        self.assertFalse(self.latch.away)
        self.assertEqual(self.latch.reblank_count, 1)

    def test_off_and_disconnected_outputs_do_not_cause_a_wake(self):
        self.latch.enter()
        self.latch.enforce({"DP-1": "Off"})
        self.assertEqual(self.calls, [False])
        self.latch.enforce({})
        self.assertEqual(self.calls, [False, False])
        self.assertTrue(self.latch.away)

    def test_shortcut_releases_repeats_and_jack_events_do_not_resume(self):
        self.latch.enter()
        for kind, code, value in [(1, 25, 0), (1, 25, 2), (5, 6, 1), (0, 3, 0), (2, 0, 0)]:
            self.latch.input(101, kind, code, value, "keyboard")
        self.assertTrue(self.latch.away)

    def test_queued_input_from_before_the_shortcut_does_not_resume(self):
        self.latch.enter()
        self.latch.input(99.9, 1, 25, 1, "keyboard")
        self.assertTrue(self.latch.away)
        self.latch.input(100.1, 1, 30, 1, "keyboard")
        self.assertFalse(self.latch.away)

    def test_pointer_movement_and_scroll_resume(self):
        for code in (0, 1, 8, 11):
            self.latch.enter()
            self.latch.input(101, 2, code, -1, "mouse")
            self.assertFalse(self.latch.away)

    def test_failed_enter_does_not_arm(self):
        self.latch.command = mock.Mock(side_effect=OSError("offline"))
        with self.assertRaises(OSError):
            self.latch.enter()
        self.assertFalse(self.latch.away)

    def test_repeated_manual_off_rearms_the_timestamp(self):
        self.latch.enter()
        self.now = 110
        self.latch.enter()
        self.latch.input(105, 1, 30, 1, "keyboard")
        self.assertTrue(self.latch.away)

    def test_correction_is_rate_limited(self):
        self.latch.enter()
        for _ in range(5):
            self.latch.enforce({"DP-1": "On"})
        self.assertEqual(self.calls, [False, False])


class InputTests(unittest.TestCase):
    def test_unpadded_machine_words(self):
        self.assertEqual(away.bitmap("1 2"), (1 << away.WORD_BITS) | 2)
        self.assertEqual(away.bitmap(""), 0)

    def test_real_bluetooth_uhid_is_accepted(self):
        self.assertTrue(away.qualifies(5, 1 << 30, 0, 0, "/sys/devices/virtual/misc/uhid/device"))

    def test_synthetic_devices_cannot_release_away(self):
        for bus, path in [(6, "/sys/devices/input/device"), (3, "/sys/devices/virtual/input/input99/device")]:
            self.assertFalse(away.qualifies(bus, 1 << 30, 3, 0, path))

    def test_audio_and_controller_switches_are_excluded(self):
        self.assertFalse(away.qualifies(3, 1 << 115, 0, 0, "/sys/devices/usb/input/device"))
        self.assertFalse(away.qualifies(3, 1 << 304, 3, 3, "/sys/devices/usb/input/device"))

    def test_mouse_and_touchpad_are_accepted(self):
        self.assertTrue(away.qualifies(3, 1 << 272, 3, 0, "/sys/devices/usb/input/device"))
        self.assertTrue(away.qualifies(0x18, 1 << 330, 0, 3, "/sys/devices/pci/input/device"))

    def test_event_overrun_and_partial_reads(self):
        reader = away.InputReader.__new__(away.InputReader)
        reader.watch = 99
        calls = []
        reader.callback = lambda *args: calls.append(args)
        reader.devices = {12: {"name": "test", "buffer": b"", "overrun": False}}
        packed = b"".join(away.EVENT.pack(101, 0, *event) for event in
                          [(0, 3, 0), (1, 30, 1), (0, 0, 0), (1, 31, 1)])
        with mock.patch.object(away.os, "read", side_effect=[packed[:-3], packed[-3:]]):
            reader.ready(12)
            reader.ready(12)
        self.assertEqual([(x[1], x[2], x[3]) for x in calls], [(1, 31, 1)])


class ControlTests(unittest.TestCase):
    def test_bad_request_does_not_change_state(self):
        daemon = away.Daemon(Path("/unused"))
        daemon.inputs = types.SimpleNamespace(devices={})
        server, client = socket.socketpair()
        with mock.patch.object(away, "display_state", return_value={}):
            worker = threading.Thread(target=daemon.handle, args=(server,))
            worker.start()
            client.sendall(b'{"action":"suspend"}\n')
            result = json.loads(client.recv(4096))
            worker.join(2)
        client.close()
        daemon.selector.close()
        self.assertFalse(result["ok"])
        self.assertFalse(daemon.latch.away)

    def test_isolated_daemon_recovers_from_a_wake_and_restores_on_stop(self):
        with tempfile.TemporaryDirectory(prefix="desktop-away-check-") as temporary:
            base = Path(temporary)
            state = base / "display"
            state.write_text("On")
            script = '''import importlib.machinery,importlib.util,sys
from pathlib import Path
loader=importlib.machinery.SourceFileLoader("test_away",sys.argv[1])
spec=importlib.util.spec_from_loader(loader.name,loader)
m=importlib.util.module_from_spec(spec);loader.exec_module(m)
state=Path(sys.argv[2]);m.input_nodes=lambda: {}
m.display_state=lambda: {"fake-DP":state.read_text()}
m.power=lambda on: state.write_text("On" if on else "Off")
m.sys.exit(m.main())
'''
            env = dict(os.environ, XDG_RUNTIME_DIR=str(base), NIRI_SOCKET="/fake/niri.sock")
            command = [sys.executable, "-c", script, str(HELPER), str(state), "run"]
            # main's argv is set separately from the loader's file arguments.
            script = script.replace('m.sys.exit(m.main())', 'm.sys.argv=[sys.argv[1],"run"];m.sys.exit(m.main())')
            command[2] = script
            child = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            directory = base / "desktop-away"

            def request(action):
                with socket.socket(socket.AF_UNIX) as client:
                    client.settimeout(2)
                    client.connect(str(directory / "control.sock"))
                    client.sendall(json.dumps({"action": action}).encode() + b"\n")
                    return json.loads(client.recv(4096))

            def until(predicate):
                end = time.monotonic() + 3
                while time.monotonic() < end:
                    if predicate():
                        return
                    time.sleep(0.02)
                self.fail("isolated daemon did not converge")

            try:
                until(lambda: (directory / "control.sock").exists())
                self.assertFalse(request("status")["away"])
                self.assertTrue(request("away")["away"])
                self.assertEqual(state.read_text(), "Off")
                state.write_text("On")
                until(lambda: state.read_text() == "Off")
                self.assertGreaterEqual(request("status")["reblank_count"], 1)
                duplicate = subprocess.run(command, env=env, capture_output=True, text=True, timeout=3)
                self.assertNotEqual(duplicate.returncode, 0)
                self.assertTrue(request("status")["away"])
                self.assertFalse(request("resume")["away"])
                self.assertEqual(state.read_text(), "On")
                self.assertTrue(request("away")["away"])
            finally:
                child.send_signal(signal.SIGTERM)
                out, err = child.communicate(timeout=5)
            self.assertEqual(child.returncode, 0, out + err)
            self.assertEqual(state.read_text(), "On")
            self.assertFalse((directory / "control.sock").exists())


if __name__ == "__main__":
    unittest.main()
