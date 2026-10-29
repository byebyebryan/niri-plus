import json
from pathlib import Path
import subprocess
import sys
import unittest
import uuid

LIB = Path(__file__).resolve().parents[1] / "components/desktop/lib"
sys.path.insert(0, str(LIB))
from niri_plus_controls.audio import AudioBackend, NORMAL_VOLUME
from niri_plus_controls.model import OperationRequest, ResultKind


def device(name, index, percent=45, *, muted=False, available=True):
    value = round(NORMAL_VOLUME * percent / 100)
    return {
        "name": name, "description": name, "index": index, "mute": muted,
        "state": "SUSPENDED", "properties": {"object.serial": str(index + 100)},
        "volume": {"front-left": {"value": value}, "front-right": {"value": value}},
        "active_port": "port", "ports": [{"name": "port", "availability": "available" if available else "not available"}],
    }


class PrivatePactl:
    """An injected native-command peer; never executes an installed command."""

    def __init__(self):
        self.info = {"server_name": "fixture Pulse server", "server_string": "private-fixture", "cookie": "123",
                     "default_sink_name": "speakers", "default_source_name": "microphone"}
        self.sinks = [device("speakers", 1), device("headphones", 2, 30), device("hdmi", 3, available=False)]
        self.sources = [device("microphone", 4, 65, muted=True)]
        self.mutations = []
        self.fail = False

    def __call__(self, command, **kwargs):
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert kwargs["timeout"] == 4
        operation, *args = command[2:]
        if self.fail:
            return subprocess.CompletedProcess(command, 1, "", "fixture unavailable")
        if operation == "info":
            data = self.info
        elif operation == "list":
            data = self.sinks if args == ["sinks"] else self.sources
        else:
            self.mutations.append(command[2:])
            name, *values = args
            records = self.sinks if "sink" in operation else self.sources
            row = next(r for r in records if r["name"] == name)
            if operation.startswith("set-default-"):
                self.info["default_sink_name" if "sink" in operation else "default_source_name"] = name
            elif operation.endswith("-volume"):
                for channel, value in zip(row["volume"].values(), values):
                    channel["value"] = int(value)
            elif operation.endswith("-mute"):
                row["mute"] = values[0] == "1"
            else:
                raise AssertionError(operation)
            data = None
        return subprocess.CompletedProcess(command, 0, json.dumps(data), "")


class AudioContracts(unittest.TestCase):
    def setUp(self):
        self.peer = PrivatePactl()
        self.backend = AudioBackend(runner=self.peer, pactl="fixture-pactl")

    def target(self, name):
        return next(t for t in self.backend.snapshot().targets if t.title == name)

    def request(self, target, action, **parameters):
        return OperationRequest("fixture-invocation", uuid.uuid4().hex, target.ref, action, target.revision, parameters)

    def test_repeated_volume_uses_fresh_values_and_keeps_microphone_muted(self):
        target = self.target("microphone")
        observed = []
        for _ in range(3):
            result = self.backend.execute(self.request(target, "volume-up"))
            self.assertEqual(result.kind, ResultKind.COMPLETE)
            observed.append(result.target.state["volume_percent"])
            self.assertTrue(result.target.state["muted"])
        self.assertEqual(observed, [70, 75, 80])

    def test_volume_preserves_balance(self):
        self.peer.sinks[0]["volume"]["front-left"]["value"] = 32768
        self.peer.sinks[0]["volume"]["front-right"]["value"] = 16384
        target = self.target("speakers")
        result = self.backend.execute(self.request(target, "volume-up"))
        self.assertEqual(result.target.state["volume_percent"], 55)
        values = [c["value"] for c in self.peer.sinks[0]["volume"].values()]
        self.assertLessEqual(abs(values[0] - 2 * values[1]), 1)

    def test_changed_volume_is_observed_before_adjusting(self):
        target = self.target("speakers")
        for channel in self.peer.sinks[0]["volume"].values():
            channel["value"] = round(NORMAL_VOLUME * .75)
        result = self.backend.execute(self.request(target, "volume-up"))
        self.assertEqual(result.target.state["volume_percent"], 80)

    def test_default_changes_only_one_direction_and_does_not_move_streams(self):
        target = self.target("headphones")
        result = self.backend.execute(self.request(target, "set-default", direction="output"))
        self.assertTrue(result.target.state["is_default"])
        self.assertEqual(self.peer.info["default_source_name"], "microphone")
        self.assertEqual(self.peer.mutations, [["set-default-sink", "headphones"]])
        self.assertFalse(self.target("speakers").state["is_default"])

    def test_mute_uses_explicit_intent_instead_of_inverting_external_state(self):
        target = self.target("microphone")
        self.peer.sources[0]["mute"] = False
        result = self.backend.execute(self.request(target, "mute", desired_muted=False))
        self.assertFalse(result.target.state["muted"])
        self.assertEqual(self.peer.mutations[-1], ["set-source-mute", "microphone", "0"])

    def test_old_server_or_reused_node_identity_cannot_operate(self):
        target = self.target("speakers")
        self.peer.info["cookie"] = "different-server"
        self.assertEqual(self.backend.execute(self.request(target, "volume-up")).kind, ResultKind.ERROR)
        self.assertEqual(self.peer.mutations, [])
        target = self.target("speakers")
        self.peer.sinks[0]["properties"]["object.serial"] = "replacement"
        self.assertEqual(self.backend.execute(self.request(target, "volume-up")).kind, ResultKind.ERROR)
        self.assertEqual(self.peer.mutations, [])

    def test_unavailable_and_unknown_volume_do_not_mutate(self):
        target = self.target("hdmi")
        self.assertEqual(self.backend.actions(target.ref), ())
        self.assertEqual(self.backend.execute(self.request(target, "volume-up")).kind, ResultKind.ERROR)
        self.peer.sinks[0].pop("volume")
        target = self.target("speakers")
        self.assertIsNone(target.state["volume_percent"])
        self.assertEqual(self.backend.execute(self.request(target, "volume-up")).kind, ResultKind.ERROR)
        self.assertEqual(self.peer.mutations, [])

    def test_duplicate_request_is_not_applied_twice(self):
        target = self.target("speakers")
        request = self.request(target, "volume-up")
        first = self.backend.execute(request)
        self.assertEqual(first, self.backend.execute(request))
        self.assertEqual(len(self.peer.mutations), 1)

    def test_volume_limit_and_gradual_reduction_of_preexisting_amplification(self):
        for channel in self.peer.sinks[0]["volume"].values():
            channel["value"] = round(NORMAL_VOLUME * 1.5)
        target = self.target("speakers")
        up = self.backend.execute(self.request(target, "volume-up"))
        self.assertEqual(up.target.state["volume_percent"], 150)
        down = self.backend.execute(self.request(target, "volume-down"))
        self.assertEqual(down.target.state["volume_percent"], 145)

    def test_server_unavailable_is_explicit_and_does_not_invent_values(self):
        self.peer.fail = True
        snapshot = self.backend.snapshot()
        self.assertEqual(snapshot.targets, ())
        self.assertIn("rejected", snapshot.notice)
        self.assertEqual(self.peer.mutations, [])


if __name__ == "__main__":
    unittest.main()
