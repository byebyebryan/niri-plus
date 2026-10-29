"""Secret-agent callback and private D-Bus lifecycle tests."""

from __future__ import annotations

import io
from pathlib import Path
import subprocess
import sys
import threading
import time
import unittest
import uuid


LIB = Path(__file__).resolve().parents[1] / "components/desktop/lib"
sys.path.insert(0, str(LIB))

try:
    import gi
    gi.require_version('Gio', '2.0')
    gi.require_version('NM', '1.0')
    gi.require_version('Secret', '1')
    from gi.repository import Gio, GLib, NM
except (ImportError, ValueError) as error:
    raise unittest.SkipTest("Native GI bindings unavailable; run the explicit system-Python controls gate") from error

from niri_plus_controls.model import PendingRef, TargetRef
from niri_plus_controls.nm_agent import (
    LibsecretStore,
    NetworkSecretAgent,
    SecretRequest,
    SecretStoreError,
    WIFI_PSK_KEY,
    WIFI_SECURITY_SETTING,
)
from niri_plus_controls.nm_bus import dedicated_bus_connection


FIXTURE = Path(__file__).resolve().parent / "fixtures/controls_nm/agent_manager_peer.py"
BUS_NAME = "org.freedesktop.NetworkManager"
AGENT_PATH = "/org/freedesktop/NetworkManager/SecretAgent"
PROBE_PATH = "/org/niri_plus/ControlsTestProbe"
PROBE_INTERFACE = "org.niri_plus.ControlsTestProbe"


class PrivateNetworkManagerPeer:
    """A private dbus-daemon and a separate AgentManager process."""

    def __init__(self):
        self.bus = subprocess.Popen(
            ["dbus-daemon", "--session", "--nofork", "--print-address=1", "--print-pid=1"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        assert self.bus.stdout is not None
        self.address = self.bus.stdout.readline().strip()
        self.bus_pid = self.bus.stdout.readline().strip()
        if not self.address:
            raise RuntimeError("private D-Bus did not publish an address")
        self.manager = subprocess.Popen(
            [sys.executable, str(FIXTURE), self.address],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        assert self.manager.stdout is not None
        ready = self.manager.stdout.readline().strip()
        if ready != "ready":
            raise RuntimeError("private AgentManager peer did not start")

    def connect(self):
        return dedicated_bus_connection(address=self.address)

    def status(self):
        connection = self.connect()
        try:
            result = connection.call_sync(
                BUS_NAME, PROBE_PATH, PROBE_INTERFACE, "GetStatus", None,
                GLib.VariantType.new("(suuu)"), Gio.DBusCallFlags.NONE, 1500, None,
            )
            return result.unpack()
        finally:
            connection.close_sync(None)

    def close(self):
        for process in (self.manager, self.bus):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()


class MemoryStore:
    def __init__(self):
        self.values = {}
        self.calls = []
        self.fail_lookup = False
        self.fail_store = False
        self.fail_delete = False

    def lookup(self, connection_uuid, setting_name, setting_key):
        self.calls.append(("lookup", connection_uuid, setting_name, setting_key))
        if self.fail_lookup:
            raise SecretStoreError("fixture store unavailable")
        return self.values.get((connection_uuid, setting_name, setting_key))

    def store(self, connection_uuid, setting_name, setting_key, secret):
        self.calls.append(("store", connection_uuid, setting_name, setting_key))
        if self.fail_store:
            raise SecretStoreError("fixture store unavailable")
        self.values[(connection_uuid, setting_name, setting_key)] = secret

    def delete(self, connection_uuid, setting_name, setting_key):
        self.calls.append(("delete", connection_uuid, setting_name, setting_key))
        if self.fail_delete:
            raise SecretStoreError("fixture store unavailable")
        self.values.pop((connection_uuid, setting_name, setting_key), None)


class FakeSchema:
    @staticmethod
    def new(name, flags, attributes):
        return {"name": name, "flags": flags, "attributes": attributes}


class FakeSecretModule:
    class SchemaFlags:
        DONT_MATCH_NAME = 7

    class SchemaAttributeType:
        STRING = 1

    Schema = FakeSchema

    def __init__(self):
        self.calls = []

    def password_lookup_sync(self, schema, attrs, cancellable):
        self.calls.append(("lookup", schema, attrs, cancellable))
        return "fixture-value"

    def password_store_sync(self, schema, attrs, collection, label, password, cancellable):
        self.calls.append(("store", schema, attrs, collection, label, password, cancellable))
        return True

    def password_clear_sync(self, schema, attrs, cancellable):
        self.calls.append(("delete", schema, attrs, cancellable))
        return True


def connection(uuid_value: str, secret_flags: int = 1, *, password: str | None = None):
    value = NM.SimpleConnection.new()
    setting_connection = NM.SettingConnection.new()
    setting_connection.set_property("id", "Fixture Wi-Fi")
    setting_connection.set_property("uuid", uuid_value)
    setting_connection.set_property("type", "802-11-wireless")
    value.add_setting(setting_connection)
    wireless = NM.SettingWireless.new()
    wireless.set_property("ssid", GLib.Bytes.new(b"fixture"))
    wireless.set_property("mode", "infrastructure")
    value.add_setting(wireless)
    security = NM.SettingWirelessSecurity.new()
    security.set_property("key-mgmt", "wpa-psk")
    security.set_property("psk-flags", secret_flags)
    if password is not None:
        security.set_property("psk", password)
    value.add_setting(security)
    return value


def extract_psk(serialized):
    settings = serialized.unpack() if hasattr(serialized, "unpack") else serialized
    return settings[WIFI_SECURITY_SETTING][WIFI_PSK_KEY]


class NetworkSecretAgentContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.peer = PrivateNetworkManagerPeer()

    @classmethod
    def tearDownClass(cls):
        cls.peer.close()

    def setUp(self):
        self.uuid = str(uuid.uuid4())
        self.path = f"/org/freedesktop/NetworkManager/Settings/{uuid.uuid4().hex}"
        self.store = MemoryStore()
        self.connections = []
        self.agents = []

    def tearDown(self):
        for agent in self.agents:
            agent.close()
        for connection in self.connections:
            try:
                connection.close_sync(None)
            except Exception:
                pass

    def make_agent(self, *, expected_uuid=None, expected_path=None, store=None, request_secret=None):
        bus_connection = self.peer.connect()
        self.connections.append(bus_connection)
        agent = NetworkSecretAgent(
            identifier=f"org.niri_plus.rofi.test.{uuid.uuid4().hex}",
            dbus_connection=bus_connection,
            secret_store=store or self.store,
            expected_uuid=expected_uuid or self.uuid,
            expected_connection_path=expected_path or self.path,
            request_secret=request_secret or (lambda _request: PendingRef("pending-test", TargetRef("wifi-profile", "target-test"), 1)),
            context=GLib.MainContext.new(),
        )
        self.agents.append(agent)
        return agent

    def invoke_get(self, agent, conn, conn_path, flags, *, callback):
        agent.do_get_secrets(
            conn, conn_path, WIFI_SECURITY_SETTING, [], flags, callback, None,
        )

    def test_libsecret_store_uses_networkmanager_schema_and_exact_attributes(self):
        secret = FakeSecretModule()
        store = LibsecretStore(secret_module=secret)
        self.assertEqual(store._schema["name"], "org.freedesktop.NetworkManager.Connection")
        self.assertEqual(store._schema["flags"], secret.SchemaFlags.DONT_MATCH_NAME)
        expected_types = {
            "connection-uuid": secret.SchemaAttributeType.STRING,
            "setting-name": secret.SchemaAttributeType.STRING,
            "setting-key": secret.SchemaAttributeType.STRING,
        }
        self.assertEqual(store._schema["attributes"], expected_types)
        self.assertEqual(store.lookup(self.uuid, WIFI_SECURITY_SETTING, WIFI_PSK_KEY), "fixture-value")
        store.store(self.uuid, WIFI_SECURITY_SETTING, WIFI_PSK_KEY, "fixture-password")
        store.delete(self.uuid, WIFI_SECURITY_SETTING, WIFI_PSK_KEY)
        self.assertEqual(secret.calls[0][2], {
            "connection-uuid": self.uuid,
            "setting-name": WIFI_SECURITY_SETTING,
            "setting-key": WIFI_PSK_KEY,
        })
        self.assertEqual(secret.calls[1][2], secret.calls[0][2])
        self.assertEqual(secret.calls[2][2], secret.calls[0][2])

    def test_private_agent_objects_keep_unique_ids_connections_and_glib_contexts(self):
        agent = self.make_agent()
        agent.initialize(timeout=1.5)
        self.assertEqual(agent.get_dbus_connection().get_unique_name(), self.connections[-1].get_unique_name())
        self.assertEqual(agent.get_main_context(), agent._context)
        self.assertFalse(agent.get_registered())

        second_connection = self.peer.connect()
        self.connections.append(second_connection)
        second = NetworkSecretAgent(
            identifier=f"org.niri_plus.rofi.test.{uuid.uuid4().hex}",
            dbus_connection=second_connection, secret_store=self.store,
            expected_uuid=self.uuid, expected_connection_path=self.path,
            request_secret=lambda _request: PendingRef("second", TargetRef("wifi-profile", "target-test"), 1),
            context=GLib.MainContext.new(),
        )
        self.agents.append(second)
        second.initialize(timeout=1.5)
        self.assertEqual(second.get_dbus_connection().get_unique_name(), second_connection.get_unique_name())
        self.assertFalse(second.get_registered())
        self.assertNotEqual(agent.get_property("identifier"), second.get_property("identifier"))
        self.assertEqual(self.peer.status(), ("", 0, 0, 0))

    def test_private_dbus_export_rejects_unauthenticated_getsecrets_peer(self):
        requests = []
        agent = self.make_agent(request_secret=lambda request: requests.append(request) or PendingRef("remote-request", TargetRef("wifi-profile", "target-test"), 3))
        agent.initialize(timeout=1.5)
        request_connection = self.peer.connect()
        conn = connection(self.uuid, int(NM.SettingSecretFlags.NOT_SAVED))
        serialized = conn.to_dbus(NM.ConnectionSerializationFlags.WITH_NON_SECRET)
        parameters = GLib.Variant.new_tuple(
            serialized,
            GLib.Variant("o", self.path),
            GLib.Variant("s", WIFI_SECURITY_SETTING),
            GLib.Variant("as", []),
            GLib.Variant("u", int(NM.SecretAgentGetSecretsFlags.ALLOW_INTERACTION)),
        )
        call_result = []

        def call_untrusted_peer():
            try:
                call_result.append(request_connection.call_sync(
                    agent.get_dbus_connection().get_unique_name(), AGENT_PATH,
                    "org.freedesktop.NetworkManager.SecretAgent", "GetSecrets", parameters,
                    GLib.VariantType.new("(a{sa{sv}})"), Gio.DBusCallFlags.NONE, 1500, None,
                ))
            except Exception as error:
                call_result.append(error)

        thread = threading.Thread(target=call_untrusted_peer, daemon=True)
        thread.start()
        deadline = time.monotonic() + 1.5
        while thread.is_alive() and time.monotonic() < deadline:
            agent.iterate_for(5)
        thread.join(timeout=0.2)
        try:
            self.assertFalse(thread.is_alive())
            self.assertTrue(call_result and isinstance(call_result[0], GLib.Error), repr(call_result))
            self.assertIn("PermissionDenied", str(call_result[0]))
            self.assertEqual(requests, [], "unregistered D-Bus peers cannot provoke credential prompts")
            self.assertEqual(self.peer.status()[3], 0)
        finally:
            request_connection.close_sync(None)

    def test_agent_owned_cached_secret_and_request_new_bypass(self):
        key = (self.uuid, WIFI_SECURITY_SETTING, WIFI_PSK_KEY)
        self.store.values[key] = "cached-password"
        prompts = []
        pending = PendingRef("pending-cached", TargetRef("wifi-profile", "target-test"), 1)
        agent = self.make_agent(request_secret=lambda request: prompts.append(request) or pending)
        conn = connection(self.uuid, int(NM.SettingSecretFlags.AGENT_OWNED))
        responses = []
        self.invoke_get(agent, conn, self.path, 0, callback=lambda *args: responses.append(args))
        self.assertEqual(extract_psk(responses[0][2]), "cached-password")
        self.assertEqual(prompts, [])

        request_new = int(NM.SecretAgentGetSecretsFlags.REQUEST_NEW | NM.SecretAgentGetSecretsFlags.ALLOW_INTERACTION)
        self.invoke_get(agent, conn, self.path, request_new, callback=lambda *args: responses.append(args))
        self.assertEqual(len(prompts), 1)
        self.assertEqual(prompts[0].request_new, True)
        self.assertEqual(len(responses), 1, "request_new must wait for this explicit credential input")
        agent.complete_secret(pending, "replacement-password")
        self.assertEqual(len(responses), 2)
        self.assertEqual(extract_psk(responses[1][2]), "replacement-password")
        self.assertEqual(self.store.values[key], "replacement-password")
        self.assertEqual([call[0] for call in self.store.calls], ["lookup", "store"])

    def test_agent_owned_input_is_persisted_before_getsecrets_callback(self):
        agent = self.make_agent()
        agent.prime_secret("remember-before-callback", secret_flags=int(NM.SettingSecretFlags.AGENT_OWNED))
        key = (self.uuid, WIFI_SECURITY_SETTING, WIFI_PSK_KEY)
        observed_store_state = []
        conn = connection(self.uuid, int(NM.SettingSecretFlags.AGENT_OWNED))
        self.invoke_get(
            agent, conn, self.path, 0,
            callback=lambda *_args: observed_store_state.append(key in self.store.values),
        )
        self.assertEqual(observed_store_state, [True])
        self.assertEqual(self.store.values[key], "remember-before-callback")
        self.assertEqual([call[0] for call in self.store.calls], ["store"])

    def test_flags_zero_and_not_saved_never_write_to_secret_service(self):
        for flags in (0, int(NM.SettingSecretFlags.NOT_SAVED)):
            with self.subTest(flags=flags):
                store = MemoryStore()
                pending = PendingRef(f"pending-{flags}", TargetRef("wifi-profile", "target-test"), 1)
                agent = self.make_agent(store=store, request_secret=lambda _request: pending)
                conn = connection(self.uuid, flags)
                responses = []
                self.invoke_get(
                    agent, conn, self.path, int(NM.SecretAgentGetSecretsFlags.ALLOW_INTERACTION),
                    callback=lambda *args: responses.append(args),
                )
                self.assertEqual(responses, [])
                agent.complete_secret(pending, "attempt-only-password")
                self.assertEqual(extract_psk(responses[0][2]), "attempt-only-password")
                self.assertEqual(store.calls, [])

    def test_agent_owned_store_failure_fails_callback_without_returning_password(self):
        store = MemoryStore()
        store.fail_store = True
        pending = PendingRef("pending-store-failure", TargetRef("wifi-profile", "target-test"), 1)
        agent = self.make_agent(store=store, request_secret=lambda _request: pending)
        conn = connection(self.uuid, int(NM.SettingSecretFlags.AGENT_OWNED))
        responses = []
        self.invoke_get(
            agent, conn, self.path, int(NM.SecretAgentGetSecretsFlags.ALLOW_INTERACTION),
            callback=lambda *args: responses.append(args),
        )
        with self.assertRaises(SecretStoreError):
            agent.complete_secret(pending, "must-not-be-returned")
        self.assertEqual(len(responses), 1)
        self.assertIsNone(responses[0][2])
        self.assertIsNotNone(responses[0][3])
        self.assertNotIn("must-not-be-returned", str(responses[0][3]))

    def test_cancel_and_unrelated_requests_do_not_interfere_with_competing_agents(self):
        pending = PendingRef("pending-cancel", TargetRef("wifi-profile", "target-test"), 1)
        prompts = []
        agent = self.make_agent(request_secret=lambda request: prompts.append(request) or pending)
        conn = connection(self.uuid, int(NM.SettingSecretFlags.NOT_SAVED))
        responses = []
        allow = int(NM.SecretAgentGetSecretsFlags.ALLOW_INTERACTION)
        self.invoke_get(agent, conn, self.path, allow, callback=lambda *args: responses.append(args))
        self.assertEqual(len(prompts), 1)

        other = connection(str(uuid.uuid4()), int(NM.SettingSecretFlags.NOT_SAVED))
        self.invoke_get(agent, other, self.path, allow, callback=lambda *args: responses.append(args))
        self.assertEqual(len(prompts), 1)
        self.assertEqual(len(responses), 1)
        self.assertIsNotNone(responses[0][3])
        self.assertTrue(agent.has_pending_secret)

        agent.do_cancel_get_secrets(self.path, WIFI_SECURITY_SETTING)
        self.assertFalse(agent.has_pending_secret)
        self.assertEqual(len(responses), 2)
        self.assertIsNotNone(responses[1][3])
        self.assertEqual(self.store.calls, [])

    def test_save_and_delete_callbacks_persist_only_agent_owned_exact_profile(self):
        agent = self.make_agent()
        conn = connection(self.uuid, int(NM.SettingSecretFlags.AGENT_OWNED), password="store-this-password")
        save_results = []
        agent.do_save_secrets(conn, self.path, lambda *args: save_results.append(args), None)
        key = (self.uuid, WIFI_SECURITY_SETTING, WIFI_PSK_KEY)
        self.assertEqual(self.store.values[key], "store-this-password")
        self.assertIsNone(save_results[0][2])

        delete_results = []
        agent.do_delete_secrets(conn, self.path, lambda *args: delete_results.append(args), None)
        self.assertNotIn(key, self.store.values)
        self.assertIsNone(delete_results[0][2])

        other_results = []
        agent.do_save_secrets(conn, self.path + "/other", lambda *args: other_results.append(args), None)
        self.assertIsNotNone(other_results[0][2])
        self.assertEqual(len(self.store.calls), 2)

    def test_save_failure_is_not_acknowledged_as_success(self):
        store = MemoryStore()
        store.fail_store = True
        agent = self.make_agent(store=store)
        conn = connection(self.uuid, int(NM.SettingSecretFlags.AGENT_OWNED), password="must-not-be-logged")
        responses = []
        agent.do_save_secrets(conn, self.path, lambda *args: responses.append(args), None)
        self.assertEqual(len(responses), 1)
        self.assertIsNotNone(responses[0][2])
        self.assertNotIn("must-not-be-logged", str(responses[0][2]))

    def test_save_without_a_secret_and_delete_store_failure_are_not_acknowledged(self):
        agent = self.make_agent()
        conn_without_secret = connection(self.uuid, int(NM.SettingSecretFlags.AGENT_OWNED))
        save_results = []
        agent.do_save_secrets(conn_without_secret, self.path, lambda *args: save_results.append(args), None)
        self.assertIsNotNone(save_results[0][2])

        self.store.fail_delete = True
        conn = connection(self.uuid, int(NM.SettingSecretFlags.AGENT_OWNED), password="delete-this-value")
        delete_results = []
        agent.do_delete_secrets(conn, self.path, lambda *args: delete_results.append(args), None)
        self.assertIsNotNone(delete_results[0][2])
        self.assertNotIn("delete-this-value", str(delete_results[0][2]))


if __name__ == "__main__":
    unittest.main()
