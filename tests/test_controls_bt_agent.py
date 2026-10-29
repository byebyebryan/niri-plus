"""Pure callback contracts for the invocation-owned BlueZ pairing agent."""

from __future__ import annotations

import io
import secrets
import sys
import unittest
from pathlib import Path

try:
    import gi
    gi.require_version('Gio', '2.0')
    gi.require_version('GLib', '2.0')
    from gi.repository import Gio, GLib
except (ImportError, ValueError) as error:
    raise unittest.SkipTest("Native GI bindings unavailable; run the explicit system-Python controls gate") from error


LIB = Path(__file__).resolve().parents[1] / "components/desktop/lib"
sys.path.insert(0, str(LIB))

from niri_plus_controls.bt_agent import AGENT_INTERFACE, PairingAgent


class FakeConnection:
    def __init__(self):
        self.registered = {}
        self.unregistered = []
        self.next_id = 1

    def register_object(self, path, interface, callback, _get_property, _set_property):
        registration_id = self.next_id
        self.next_id += 1
        self.registered[registration_id] = (path, interface, callback)
        return registration_id

    def unregister_object(self, registration_id):
        self.unregistered.append(registration_id)
        self.registered.pop(registration_id, None)


class FakePeer:
    Gio = Gio
    GLib = GLib

    def __init__(self):
        self.context = GLib.MainContext.new()
        self.connection = FakeConnection()
        self.service_owner = ":1.7"
        self.calls = []

    def _connection(self):
        return self.connection

    def owner(self):
        return self.service_owner

    def call(self, owner, path, interface, method, signature="()", values=()):
        self.calls.append((owner, path, interface, method, signature, values))


class FakeInvocation:
    def __init__(self):
        self.value = None
        self.errors = []

    def return_value(self, value):
        self.value = value

    def return_dbus_error(self, name, message):
        self.errors.append((name, message))


class PairingAgentContracts(unittest.TestCase):
    def setUp(self):
        self.peer = FakePeer()
        self.agent = PairingAgent(self.peer, ":1.7", "/org/bluez/hci0/dev_00_11_22_33_44_55")
        self.agent.register()

    def tearDown(self):
        self.agent.close()

    def invoke(self, sender, method, signature, values):
        invocation = FakeInvocation()
        self.agent._method(
            None, sender, self.agent.path, AGENT_INTERFACE, method,
            GLib.Variant(signature, values), invocation,
        )
        return invocation

    def test_agent_registration_is_temporary_and_never_default(self):
        self.assertEqual(len(self.peer.calls), 1)
        owner, path, interface, method, signature, values = self.peer.calls[0]
        self.assertEqual((owner, path, interface, method, signature),
                         (":1.7", "/org/bluez", "org.bluez.AgentManager1", "RegisterAgent", "(os)"))
        self.assertEqual(values, (self.agent.path, "KeyboardDisplay"))
        self.assertFalse(any(call[3] == "RequestDefaultAgent" for call in self.peer.calls))
        self.assertTrue(self.agent._registered)
        self.assertEqual(len(self.peer.connection.registered), 1)

    def test_request_pin_preserves_printable_whitespace_only_in_the_reply(self):
        pin = f" {secrets.token_hex(2)} "
        invocation = self.invoke(":1.7", "RequestPinCode", "(o)", (self.agent.device_path,))
        self.assertIsNone(invocation.value)
        self.assertEqual(self.agent.challenge[0], "RequestPinCode")
        self.assertNotIn(pin, self.agent.challenge[2])
        self.agent.provide_secret(io.BytesIO(pin.encode("ascii")))
        self.assertEqual(invocation.value.get_type_string(), "(s)")
        self.assertEqual(invocation.value.unpack(), (pin,))
        self.assertNotIn(pin, repr(self.agent.__dict__))
        self.assertIsNone(self.agent.challenge)

    def test_request_passkey_is_bounded_numeric_and_keeps_secret_out_of_agent_state(self):
        passkey = f"{secrets.randbelow(1_000_000):06d}"
        invocation = self.invoke(":1.7", "RequestPasskey", "(o)", (self.agent.device_path,))
        self.agent.provide_secret(io.BytesIO(passkey.encode("ascii")))
        self.assertEqual(invocation.value.get_type_string(), "(u)")
        self.assertEqual(invocation.value.unpack(), (int(passkey),))
        self.assertNotIn(passkey, repr(self.agent.__dict__))

    def test_confirmation_code_and_keyboard_progress_are_formatted_explicitly(self):
        confirmation = self.invoke(":1.7", "RequestConfirmation", "(ou)", (self.agent.device_path, 42))
        self.assertIn("000042", self.agent.challenge[2])
        self.agent.confirm(True)
        self.assertEqual(confirmation.value.get_type_string(), "()")
        self.assertEqual(confirmation.value.unpack(), ())

        display = self.invoke(":1.7", "DisplayPasskey", "(ouq)", (self.agent.device_path, 42, 2))
        self.assertIn("000042", self.agent.display)
        self.assertIn("2/6 digits entered", self.agent.display)
        self.assertEqual(display.value.get_type_string(), "()")

    def test_wrong_agent_owner_and_wrong_device_are_rejected(self):
        wrong_owner = self.invoke(":1.99", "RequestAuthorization", "(o)", (self.agent.device_path,))
        self.assertEqual(wrong_owner.errors[0][0], "org.bluez.Error.Rejected")
        wrong_device = self.invoke(":1.7", "RequestAuthorization", "(o)", ("/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF",))
        self.assertEqual(wrong_device.errors[0][0], "org.bluez.Error.Rejected")
        self.assertIsNone(self.agent.challenge)

    def test_cancel_and_close_reject_only_the_owned_challenge(self):
        invocation = self.invoke(":1.7", "RequestAuthorization", "(o)", (self.agent.device_path,))
        self.assertIsNotNone(self.agent.challenge)
        canceled = self.invoke(":1.7", "Cancel", "()", ())
        self.assertEqual(canceled.value.get_type_string(), "()")
        self.assertEqual(invocation.errors[0][0], "org.bluez.Error.Canceled")
        self.assertIsNone(self.agent.challenge)

        second = self.invoke(":1.7", "RequestAuthorization", "(o)", (self.agent.device_path,))
        self.agent.close()
        self.assertEqual(second.errors[0][0], "org.bluez.Error.Canceled")
        self.assertTrue(any(call[3] == "UnregisterAgent" for call in self.peer.calls))
        self.assertEqual(len(self.peer.connection.unregistered), 1)

    def test_close_after_service_replacement_does_not_unregister_from_new_owner(self):
        self.peer.service_owner = ":1.88"
        self.peer.calls.clear()
        self.agent.close()
        self.assertEqual(self.peer.calls, [])
        self.assertEqual(len(self.peer.connection.unregistered), 1)


if __name__ == "__main__":
    unittest.main()
