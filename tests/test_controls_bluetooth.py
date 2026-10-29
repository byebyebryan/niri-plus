import copy
from pathlib import Path
import sys
import unittest
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "components/desktop/lib"))
from niri_plus_controls.bluetooth import ADAPTER, BATTERY, DEVICE, BluetoothBackend, BluetoothError
from niri_plus_controls.model import Availability, OperationRequest, ResultKind


class OwnedBluezPeer:
    def __init__(self):
        self.epoch = ":fixture.1"
        self.adapter = "/org/bluez/hci0"
        self.device = self.adapter + "/dev_AA_BB_CC_DD_EE_FF"
        self.data = {
            self.adapter: {ADAPTER: {"Address": "00:11:22:33:44:55", "Alias": "Fixture adapter", "Powered": True}},
            self.device: {DEVICE: {"Address": "AA:BB:CC:DD:EE:FF", "AddressType": "public", "Adapter": self.adapter,
                                    "Alias": "Fixture headphones", "Connected": False, "Paired": True, "Trusted": False},
                          BATTERY: {"Percentage": 82}},
        }
        self.calls = []
        self.jobs = []
        self.fail = False
        self.closed = False

    def owner(self):
        if self.fail:
            raise BluetoothError("Bluetooth service unavailable")
        return self.epoch

    def objects(self):
        return self.owner(), copy.deepcopy(self.data)

    def call(self, owner, path, interface, method):
        assert owner == self.epoch
        self.calls.append((path, interface, method))
        return ()

    def set_power(self, owner, path, desired):
        assert owner == self.epoch
        self.calls.append((path, ADAPTER, "Powered", desired))
        self.data[path][ADAPTER]["Powered"] = desired

    def start(self, owner, path, interface, method):
        self.calls.append((path, interface, method))
        pending = {"done": False, "error": None, "stopped": False}
        self.jobs.append(pending)
        return pending

    def stop_waiting(self, pending):
        pending["stopped"] = True

    def close(self):
        self.closed = True


class BluetoothContracts(unittest.TestCase):
    def setUp(self):
        self.peer = OwnedBluezPeer()
        self.now = 0
        self.backend = BluetoothBackend(peer=self.peer, clock=lambda: self.now, scan_seconds=30)
        self.addCleanup(self.backend.close)

    def target(self, kind):
        return next(t for t in self.backend.snapshot().targets if t.ref.kind == kind)

    def request(self, target, action, **parameters):
        return OperationRequest("fixture", uuid.uuid4().hex, target.ref, action, target.revision, parameters)

    def test_open_is_passive_and_pairing_is_not_connection(self):
        device = self.target("bluetooth-device")
        self.assertFalse(device.active)
        self.assertTrue(device.state["paired"])
        self.assertFalse(device.state["connected"])
        self.assertIsNone(device.state["battery_percent"])
        self.assertEqual(self.peer.calls, [])

    def test_connected_zero_battery_is_real_zero_not_unknown(self):
        self.peer.data[self.peer.device][DEVICE]["Connected"] = True
        self.peer.data[self.peer.device][BATTERY]["Percentage"] = 0
        device = self.target("bluetooth-device")
        self.assertTrue(device.active)
        self.assertEqual(device.state["battery_percent"], 0)

    def test_missing_properties_are_unknown_and_cannot_mutate(self):
        self.peer.data[self.peer.device][DEVICE].pop("Paired")
        target = self.target("bluetooth-device")
        self.assertEqual(target.availability, Availability.UNKNOWN)
        self.assertEqual(self.backend.actions(target.ref), ())
        result = self.backend.execute(self.request(target, "set-device-connection", desired_connected=True))
        self.assertEqual(result.kind, ResultKind.ERROR)
        self.assertEqual(self.peer.calls, [])

    def test_async_acceptance_is_not_connected_success(self):
        target = self.target("bluetooth-device")
        result = self.backend.execute(self.request(target, "set-device-connection", desired_connected=True))
        self.assertEqual(result.kind, ResultKind.PENDING)
        self.assertEqual(self.backend.refresh(result.pending).kind, ResultKind.PENDING)
        self.peer.jobs[0]["done"] = True
        self.peer.data[self.peer.device][DEVICE]["Connected"] = True
        finished = self.backend.refresh(result.pending)
        self.assertEqual(finished.kind, ResultKind.COMPLETE)
        self.assertTrue(finished.target.active)
        self.assertFalse(self.peer.data[self.peer.device][DEVICE]["Trusted"])

    def test_stop_waiting_does_not_disconnect_an_external_connection(self):
        target = self.target("bluetooth-device")
        pending = self.backend.execute(self.request(target, "set-device-connection", desired_connected=True)).pending
        self.peer.data[self.peer.device][DEVICE]["Connected"] = True
        result = self.backend.cancel(pending)
        self.assertEqual(result.kind, ResultKind.CANCELLED)
        self.assertIn("may still", result.message)
        self.assertFalse(any(call[-1] == "Disconnect" for call in self.peer.calls))
        self.assertTrue(self.peer.data[self.peer.device][DEVICE]["Connected"])

    def test_power_off_rejects_changed_connected_scope(self):
        target = self.target("bluetooth-adapter")
        request = self.request(target, "set-adapter-power", desired_on=False, impact=target.state["impact"])
        self.peer.data[self.peer.device][DEVICE]["Connected"] = True
        result = self.backend.execute(request)
        self.assertEqual(result.kind, ResultKind.ERROR)
        self.assertIn("confirmation", result.message)
        self.assertEqual(self.peer.calls, [])

    def test_explicit_power_scope_and_pairing_preservation(self):
        self.peer.data[self.peer.device][DEVICE]["Connected"] = True
        target = self.target("bluetooth-adapter")
        action = self.backend.actions(target.ref)[0]
        self.assertIn("Fixture headphones", action.confirmation)
        result = self.backend.execute(self.request(target, action.action_id, **action.parameters))
        self.assertEqual(result.kind, ResultKind.COMPLETE)
        self.assertTrue(self.peer.data[self.peer.device][DEVICE]["Paired"])
        self.assertFalse(any("RemoveDevice" in call for call in self.peer.calls))

    def test_daemon_or_device_replacement_rejects_old_handles(self):
        target = self.target("bluetooth-device")
        self.peer.epoch = ":fixture.2"
        result = self.backend.execute(self.request(target, "set-device-connection", desired_connected=True))
        self.assertEqual(result.kind, ResultKind.ERROR)
        self.assertEqual(self.peer.calls, [])
        target = self.target("bluetooth-device")
        self.peer.data[self.peer.device][DEVICE]["Address"] = "DIFFERENT"
        result = self.backend.execute(self.request(target, "set-device-connection", desired_connected=True))
        self.assertEqual(result.kind, ResultKind.ERROR)
        self.assertEqual(self.peer.calls, [])

    def test_discovery_is_explicit_coalesced_and_only_owned_session_is_released(self):
        target = self.target("bluetooth-adapter")
        for _ in range(2):
            self.assertEqual(self.backend.execute(self.request(target, "start-discovery")).kind, ResultKind.COMPLETE)
        self.assertEqual(sum(call[-1] == "StartDiscovery" for call in self.peer.calls), 1)
        self.backend.close()
        self.assertEqual(sum(call[-1] == "StopDiscovery" for call in self.peer.calls), 1)
        self.assertTrue(self.peer.closed)

    def test_discovery_close_does_not_send_to_replacement_daemon(self):
        target = self.target("bluetooth-adapter")
        self.backend.execute(self.request(target, "start-discovery"))
        self.peer.epoch = ":replacement"
        self.backend.close()
        self.assertFalse(any(call[-1] == "StopDiscovery" for call in self.peer.calls))

    def test_timeout_stops_observation_without_rollback(self):
        target = self.target("bluetooth-device")
        pending = self.backend.execute(self.request(target, "set-device-connection", desired_connected=True)).pending
        self.now = 30
        result = self.backend.refresh(pending)
        self.assertEqual(result.kind, ResultKind.ERROR)
        self.assertIn("unknown", result.message)
        self.assertTrue(self.peer.jobs[0]["stopped"])
        self.assertFalse(any(call[-1] == "Disconnect" for call in self.peer.calls))

    def test_service_unavailable_does_not_invent_devices_or_start_service(self):
        self.peer.fail = True
        result = self.backend.snapshot()
        self.assertEqual(result.targets, ())
        self.assertIn("unavailable", result.notice)
        self.assertEqual(self.peer.calls, [])


if __name__ == "__main__":
    unittest.main()
