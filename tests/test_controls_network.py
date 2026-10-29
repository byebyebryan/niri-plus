"""Private injected NetworkManager peers for the native Wi-Fi adapter."""

from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import time
import unittest
from unittest import mock
import uuid


LIB = Path(__file__).resolve().parents[1] / "components/desktop/lib"
sys.path.insert(0, str(LIB))

try:
    import gi
    gi.require_version('NM', '1.0')
    gi.require_version('Secret', '1')
    from gi.repository import GLib, NM
except (ImportError, ValueError) as error:
    raise unittest.SkipTest("Native GI bindings unavailable; run the explicit system-Python controls gate") from error

from niri_plus_controls.model import ActionKind, OperationRequest, ResultKind, Utility
from niri_plus_controls.network import NetworkBackend
from niri_plus_controls.nm_bus import NMUnavailable, load_nm_modules


class FastRuntime:
    """A deterministic GLib adapter for injected native method tests."""

    def __init__(self):
        self.closed = False
        self.context = load_nm_modules().GLib.MainContext.new()

    def push(self):
        pass

    def pop(self):
        pass

    def iterate_for(self, _milliseconds):
        pass

    def run_async(self, start, finish, **_kwargs):
        result = []
        start(lambda _source, value, _data=None: result.append(finish(value)))
        if len(result) != 1:
            raise AssertionError("Injected asynchronous operation did not complete")
        return result[0]

    def close(self):
        self.closed = True


class FakeProfile:
    def __init__(self, connection, path, *, has_802_1x=False):
        self.connection = connection
        self.path = path
        self.client = None
        self.delete_calls = 0
        self.has_802_1x = has_802_1x

    def get_path(self):
        return self.path

    def to_dbus(self, flags):
        return self.connection.to_dbus(flags)

    def delete_async(self, _cancellable, callback, user_data):
        self.delete_calls += 1
        if self.client is not None:
            self.client.profiles = [profile for profile in self.client.profiles if profile is not self]
        callback(self, object(), user_data)

    @staticmethod
    def delete_finish(_result):
        return True

    def get_setting_802_1x(self):
        if self.has_802_1x:
            return object()
        return self.connection.get_setting_802_1x()

    def __getattr__(self, name):
        return getattr(self.connection, name)


class FakeAP:
    def __init__(self, path, ssid, bssid, *, security="open", strength=75, cipher_bits=0, extra_flags=0, valid_profiles=None):
        self.path = path
        self.ssid = bytes(ssid)
        self.bssid = bssid
        self.strength = strength
        self.security = security
        self.cipher_bits = int(cipher_bits)
        self.extra_flags = int(extra_flags)
        self.valid_profiles = None if valid_profiles is None else set(valid_profiles)

    def get_path(self):
        return self.path

    def get_ssid(self):
        return self.ssid

    def get_bssid(self):
        return self.bssid

    def get_strength(self):
        return self.strength

    def get_flags(self):
        return (1 if self.security == "wep" else 0) | self.extra_flags

    def get_wpa_flags(self):
        return (256 | self.cipher_bits) if self.security in {"wpa-psk", "wpa1-psk"} else self.extra_flags

    def get_rsn_flags(self):
        return ({"wpa-psk": 256, "sae": 1024}.get(self.security, 0) | self.cipher_bits) | self.extra_flags

    def connection_valid(self, profile):
        if self.valid_profiles is None:
            return True
        return profile.get_uuid() in self.valid_profiles


class FakeIPAddress:
    def __init__(self, address):
        self.address = address

    def get_address(self):
        return self.address


class FakeIPConfig:
    def __init__(self, addresses):
        self.addresses = [FakeIPAddress(value) for value in addresses]

    def get_addresses(self):
        return list(self.addresses)


class FakeDevice:
    def __init__(
        self, path, interface, aps=(), *, managed=True, state=30, hold_scan=False,
        device_type=2, carrier=True, available_connections=None, ipv4=(), ipv6=(),
    ):
        self.path = path
        self.interface = interface
        self.aps = list(aps)
        self.managed = managed
        self.state = state
        self.device_type = int(device_type)
        self.carrier = carrier
        self.available_connections = None if available_connections is None else list(available_connections)
        self.ipv4 = tuple(ipv4)
        self.ipv6 = tuple(ipv6)
        self.last_scan = -1
        self.scan_requests = 0
        self.hold_scan = hold_scan
        self.pending_scan = None

    def get_path(self):
        return self.path

    def get_device_type(self):
        return self.device_type

    def get_iface(self):
        return self.interface

    def get_managed(self):
        return self.managed

    def get_state(self):
        return self.state

    def get_access_points(self):
        return list(self.aps)

    def get_available_connections(self):
        return list(self.available_connections or ())

    def get_carrier(self):
        return self.carrier

    def get_ip4_config(self):
        return FakeIPConfig(self.ipv4) if self.ipv4 else None

    def get_ip6_config(self):
        return FakeIPConfig(self.ipv6) if self.ipv6 else None

    def get_last_scan(self):
        return self.last_scan

    def request_scan_async(self, _cancellable, callback, user_data):
        self.scan_requests += 1
        if self.hold_scan:
            self.pending_scan = (callback, user_data)
        else:
            self.complete_scan(callback, user_data)

    def complete_scan(self, callback=None, user_data=None):
        self.last_scan = load_nm_modules().NM.utils_get_timestamp_msec()
        if callback is None and self.pending_scan is not None:
            callback, user_data = self.pending_scan
            self.pending_scan = None
        if callback is not None:
            callback(self, object(), user_data)

    @staticmethod
    def request_scan_finish(_result):
        return True


class FakeActive:
    def __init__(self, path, profile, device, *, state=2, reason=0, specific_object=""):
        self.path = path
        self.profile = profile
        self.device = device
        self.state = state
        self.reason = reason
        self.specific_object = specific_object

    def get_path(self):
        return self.path

    def get_connection(self):
        return self.profile

    def get_devices(self):
        return [self.device]

    def get_specific_object_path(self):
        return self.specific_object

    def get_state(self):
        return self.state

    def get_state_reason(self):
        return self.reason


def make_profile(
    name="Home Wi-Fi", ssid=b"home", *, profile_uuid=None, path=None, interface="",
    security="wpa-psk", flags=0, password=None, hidden=False, mode=None, secondaries=(), has_802_1x=False,
):
    connection = NM.SimpleConnection.new()
    setting_connection = NM.SettingConnection.new()
    setting_connection.set_property("id", name)
    setting_connection.set_property("uuid", profile_uuid or str(uuid.uuid4()))
    setting_connection.set_property("type", "802-11-wireless")
    setting_connection.set_property("autoconnect", False)
    if interface:
        setting_connection.set_property("interface-name", interface)
    if secondaries:
        setting_connection.set_property("secondaries", list(secondaries))
    connection.add_setting(setting_connection)
    wireless = NM.SettingWireless.new()
    wireless.set_property("ssid", GLib.Bytes.new(bytes(ssid)))
    if mode is not None:
        wireless.set_property("mode", mode)
    else:
        wireless.set_property("mode", "infrastructure")
    wireless.set_property("hidden", hidden)
    connection.add_setting(wireless)
    connection.add_setting(NM.SettingIP4Config.new())
    connection.add_setting(NM.SettingIP6Config.new())
    if security:
        security_setting = NM.SettingWirelessSecurity.new()
        security_setting.set_property("key-mgmt", security)
        security_setting.set_property("psk-flags", flags)
        if password:
            security_setting.set_property("psk", password)
        connection.add_setting(security_setting)
    return FakeProfile(connection, path or f"/org/freedesktop/NetworkManager/Settings/{uuid.uuid4().hex[:8]}", has_802_1x=has_802_1x)


def make_ethernet_profile(
    name="Wired connection", *, profile_uuid=None, path=None, interface="", secondaries=(), has_802_1x=False,
):
    connection = NM.SimpleConnection.new()
    setting_connection = NM.SettingConnection.new()
    setting_connection.set_property("id", name)
    setting_connection.set_property("uuid", profile_uuid or str(uuid.uuid4()))
    setting_connection.set_property("type", "802-3-ethernet")
    setting_connection.set_property("autoconnect", True)
    if interface:
        setting_connection.set_property("interface-name", interface)
    if secondaries:
        setting_connection.set_property("secondaries", list(secondaries))
    connection.add_setting(setting_connection)
    connection.add_setting(NM.SettingWired.new())
    connection.add_setting(NM.SettingIP4Config.new())
    connection.add_setting(NM.SettingIP6Config.new())
    return FakeProfile(
        connection,
        path or f"/org/freedesktop/NetworkManager/Settings/{uuid.uuid4().hex[:8]}",
        has_802_1x=has_802_1x,
    )


def make_vpn_profile(name="Office VPN", *, profile_uuid=None, path=None):
    connection = NM.SimpleConnection.new()
    setting_connection = NM.SettingConnection.new()
    setting_connection.set_property("id", name)
    setting_connection.set_property("uuid", profile_uuid or str(uuid.uuid4()))
    setting_connection.set_property("type", "vpn")
    connection.add_setting(setting_connection)
    return FakeProfile(connection, path or f"/org/freedesktop/NetworkManager/Settings/{uuid.uuid4().hex[:8]}")


class FakeClient:
    def __init__(self, devices=(), profiles=(), actives=(), *, wifi=True, hardware=True, active_state=2, active_reason=0, connectivity=0):
        self.owner = ":1.25"
        self.devices = list(devices)
        self.profiles = list(profiles)
        self.actives = list(actives)
        self.wifi = wifi
        self.hardware = hardware
        self.active_state = active_state
        self.active_reason = active_reason
        self.connectivity = connectivity
        self.activation_calls = []
        self.deactivation_calls = []
        self.add_calls = []
        self._active_serial = 0
        self._last_active = None
        for device in self.devices:
            if device.available_connections is not None:
                continue
            expected = "802-11-wireless" if device.device_type == 2 else "802-3-ethernet" if device.device_type == 1 else ""
            device.available_connections = [
                profile for profile in self.profiles
                if profile.get_setting_connection().get_connection_type() == expected
                and (not profile.get_setting_connection().get_interface_name() or profile.get_setting_connection().get_interface_name() == device.interface)
            ]

    def get_dbus_name_owner(self):
        return self.owner

    def get_devices(self):
        return list(self.devices)

    def get_connections(self):
        return list(self.profiles)

    def get_active_connections(self):
        return list(self.actives)

    def get_connectivity(self):
        return self.connectivity

    def wireless_get_enabled(self):
        return self.wifi

    def wireless_hardware_get_enabled(self):
        return self.hardware

    def wireless_set_enabled(self, value):
        self.wifi = bool(value)

    def _new_active(self, profile, device, specific_object=""):
        self._active_serial += 1
        active = FakeActive(
            f"/org/freedesktop/NetworkManager/ActiveConnection/{self._active_serial}",
            profile, device, state=self.active_state, reason=self.active_reason, specific_object=specific_object,
        )
        self.actives.append(active)
        self._last_active = active
        return active

    def activate_connection_async(self, profile, device, specific_object, _cancellable, callback, user_data):
        self.activation_calls.append((profile, device, specific_object))
        self._new_active(profile, device, specific_object or "")
        callback(self, object(), user_data)

    def activate_connection_finish(self, _result):
        return self._last_active

    def add_and_activate_connection2(self, connection, device, specific_object, options, _cancellable, callback, user_data):
        path = f"/org/freedesktop/NetworkManager/Settings/created-{len(self.add_calls) + 1}"
        profile = FakeProfile(connection, path)
        profile.client = self
        self.profiles.append(profile)
        self.add_calls.append((connection, device, specific_object, options, profile))
        self._new_active(profile, device, specific_object or "")
        callback(self, object(), user_data)

    def add_and_activate_connection2_finish(self, _result):
        return self._last_active, GLib.Variant("a{sv}", {})

    def deactivate_connection_async(self, active, _cancellable, callback, user_data):
        self.deactivation_calls.append(active)
        active.state = 4
        self.actives = [item for item in self.actives if item is not active]
        callback(self, object(), user_data)

    @staticmethod
    def deactivate_connection_finish(_result):
        return True


class MemoryStore:
    def __init__(self):
        self.values = {}
        self.stores = []
        self.deletes = []

    def lookup(self, connection_uuid, setting_name, setting_key):
        return self.values.get((connection_uuid, setting_name, setting_key))

    def store(self, connection_uuid, setting_name, setting_key, secret):
        key = (connection_uuid, setting_name, setting_key)
        self.values[key] = secret
        self.stores.append(key)

    def delete(self, connection_uuid, setting_name, setting_key):
        key = (connection_uuid, setting_name, setting_key)
        self.values.pop(key, None)
        self.deletes.append(key)


class FakeAgent:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.registered = False
        self.closed = False
        self.primed = []
        self.completed = []
        self.cancelled = []

    def register(self, **_kwargs):
        self.registered = True

    def prime_secret(self, secret, *, secret_flags):
        self.primed.append((secret, secret_flags))

    def complete_secret(self, pending, secret):
        self.completed.append((pending, secret))

    def cancel_pending(self, pending):
        self.cancelled.append(pending)
        return True

    def close(self):
        self.closed = True

    def iterate_for(self, _milliseconds):
        pass


class RegistrationFailureAgent(FakeAgent):
    def register(self, **_kwargs):
        raise NMUnavailable("fixture manager rejected registration")


class NetworkBackendContracts(unittest.TestCase):
    def make_backend(self, client, **kwargs):
        return NetworkBackend(
            client=client, runtime=FastRuntime(), secret_store=MemoryStore(),
            username="fixture-user", timeout=0.3, **kwargs,
        )

    @staticmethod
    def request(target, action, parameters=None, *, revision=None):
        return OperationRequest(
            "fixture-invocation", uuid.uuid4().hex, target.ref, action,
            revision or target.revision, parameters or {},
        )

    @staticmethod
    def target(backend, *, kind, title_contains=None):
        snapshot = backend.snapshot(Utility.NETWORK)
        return next(
            target for target in snapshot.targets
            if target.ref.kind == kind and (title_contains is None or title_contains in target.title)
        )

    def test_raw_ssid_identity_survives_duplicate_unsafe_display_values(self):
        ap0 = FakeAP("/ap/one", b"lab\nroom", "00:00:00:00:00:01")
        ap1 = FakeAP("/ap/two", b"lab\x00room", "00:00:00:00:00:02")
        raw_format_chars = "lab\u2028room\u202e".encode()
        ap2 = FakeAP("/ap/three", raw_format_chars, "00:00:00:00:00:03")
        client = FakeClient([
            FakeDevice("/dev/w0", "wlan0", [ap0]),
            FakeDevice("/dev/w1", "wlan1", [ap1]),
            FakeDevice("/dev/w2", "wlan2", [ap2]),
        ])
        backend = self.make_backend(client)
        try:
            targets = [t for t in backend.snapshot().targets if t.ref.kind == "wifi-ap"]
            self.assertEqual(len(targets), 3)
            self.assertEqual(len({target.ref for target in targets}), 3)
            self.assertEqual({t.title.split(" · ", 1)[0] for t in targets}, {"lab room"})
            self.assertEqual({t.state["ssid_hex"] for t in targets}, {b"lab\nroom".hex(), b"lab\x00room".hex(), raw_format_chars.hex()})
            self.assertTrue(all(t.state["new_wifi"] is True and t.state["saved"] is False for t in targets))
            self.assertTrue(all("\x00" not in t.title and "\n" not in t.title for t in targets))
            self.assertTrue(all(len(set(t.title.split(" · ", 1)[0])) > 1 for t in targets))
        finally:
            backend.close()

    def test_saved_profiles_are_pinned_to_exact_adapter_and_profile(self):
        ssid = b"shared"
        profile_a = make_profile("Shared A", ssid, profile_uuid="uuid-a", interface="wlan0")
        profile_b = make_profile("Shared B", ssid, profile_uuid="uuid-b", interface="wlan1")
        ap_a = FakeAP("/ap/a", ssid, "00:00:00:00:00:11", security="wpa-psk")
        ap_b = FakeAP("/ap/b", ssid, "00:00:00:00:00:12", security="wpa-psk")
        device_a = FakeDevice("/dev/w0", "wlan0", [ap_a])
        device_b = FakeDevice("/dev/w1", "wlan1", [ap_b])
        client = FakeClient([device_a, device_b], [profile_a, profile_b])
        backend = self.make_backend(client)
        try:
            snapshot = backend.snapshot()
            saved = [t for t in snapshot.targets if t.ref.kind == "wifi-profile"]
            self.assertEqual({t.state["uuid"] for t in saved}, {"uuid-a", "uuid-b"})
            self.assertEqual({t.state["device_path"] for t in saved}, {"/dev/w0", "/dev/w1"})
            self.assertTrue(all(t.state["saved"] and not t.state["new_wifi"] for t in saved))
            ap_target = next(t for t in snapshot.targets if t.ref.kind == "wifi-ap" and t.state["interface"] == "wlan1")
            action = next(a for a in backend.actions(ap_target.ref) if a.action_id == "connect")
            self.assertNotIn("persistence_choice_required", action.parameters)
            self.assertEqual(action.parameters["profile_uuid"], "uuid-b")
            self.assertEqual(action.parameters["device_path"], "/dev/w1")
            # The scan row is pinned to wlan1; select its single matching profile,
            # even when another profile with the same SSID exists on another adapter.
            result = backend.execute(self.request(ap_target, action.action_id, action.parameters))
            self.assertEqual(result.kind, ResultKind.COMPLETE)
            self.assertEqual(client.activation_calls[0][0].get_uuid(), "uuid-b")
            self.assertEqual(client.activation_calls[0][1].get_path(), "/dev/w1")
        finally:
            backend.close()

    def test_multiple_matching_profiles_require_selecting_an_exact_saved_row(self):
        ssid = b"shared"
        profiles = [make_profile("First", ssid, profile_uuid="uuid-first"), make_profile("Second", ssid, profile_uuid="uuid-second")]
        ap = FakeAP("/ap/one", ssid, "00:00:00:00:00:22", security="wpa-psk")
        client = FakeClient([FakeDevice("/dev/w0", "wlan0", [ap])], profiles)
        backend = self.make_backend(client)
        try:
            ap_target = self.target(backend, kind="wifi-ap")
            connect = next(a for a in backend.actions(ap_target.ref) if a.action_id == "connect")
            self.assertFalse(connect.enabled)
            self.assertIn("exact profile row", connect.disabled_reason)
            saved = [t for t in backend.snapshot().targets if t.ref.kind == "wifi-profile"]
            self.assertEqual({t.state["uuid"] for t in saved}, {"uuid-first", "uuid-second"})
            self.assertTrue(all(any(a.action_id == "connect" for a in backend.actions(t.ref)) for t in saved))
        finally:
            backend.close()

    def test_global_radio_confirmation_names_managed_scope_and_revalidates_it(self):
        ap = FakeAP("/ap/one", b"home", "00:00:00:00:00:31", security="wpa-psk")
        d0 = FakeDevice("/dev/w0", "wlan0", [ap])
        d1 = FakeDevice("/dev/w1", "wlan1")
        profile = make_profile("Current Wi-Fi", b"home", profile_uuid="active-wifi")
        active = FakeActive("/active/1", profile, d0, state=2)
        client = FakeClient([d0, d1], [profile], [active])
        backend = self.make_backend(client)
        try:
            radio = self.target(backend, kind="wifi-radio")
            action = backend.actions(radio.ref)[0]
            self.assertEqual(action.action_id, "set-wifi-radio")
            self.assertEqual(action.kind, ActionKind.CONFIRM)
            self.assertFalse(action.parameters["desired_on"])
            self.assertIn("wlan0", action.confirmation)
            self.assertIn("wlan1", action.confirmation)
            self.assertIn("Current Wi-Fi", action.confirmation)
            self.assertIn("Ethernet and Bluetooth remain unchanged", action.confirmation)
            stale = self.request(radio, action.action_id, action.parameters)
            changed_profile = make_profile("Replacement Wi-Fi", b"other", profile_uuid="replacement")
            client.profiles.append(changed_profile)
            client.actives.append(FakeActive("/active/2", changed_profile, d1, state=2))
            result = backend.execute(stale)
            self.assertEqual(result.kind, ResultKind.ERROR)
            self.assertTrue(client.wifi)
            current_radio = self.target(backend, kind="wifi-radio")
            current_action = backend.actions(current_radio.ref)[0]
            result = backend.execute(self.request(current_radio, current_action.action_id, current_action.parameters))
            self.assertEqual(result.kind, ResultKind.COMPLETE)
            self.assertFalse(client.wifi)
        finally:
            backend.close()

    def test_radio_on_is_explicit_and_unmanaged_adapters_are_not_in_the_confirmed_scope(self):
        managed = FakeDevice("/dev/w0", "wlan0")
        unmanaged = FakeDevice("/dev/w1", "wlan1", managed=False)
        client = FakeClient([managed, unmanaged], wifi=False)
        backend = self.make_backend(client)
        try:
            radio = self.target(backend, kind="wifi-radio")
            action = backend.actions(radio.ref)[0]
            self.assertEqual(action.action_id, "set-wifi-radio")
            self.assertEqual(action.kind, ActionKind.OPERATION)
            self.assertTrue(action.parameters["desired_on"])
            self.assertEqual(radio.state["interfaces"], "wlan0")
            result = backend.execute(self.request(radio, action.action_id, action.parameters))
            self.assertEqual(result.kind, ResultKind.COMPLETE)
            self.assertTrue(client.wifi)
        finally:
            backend.close()

    def test_daemon_replacement_changes_opaque_target_epoch_and_rejects_pending_handles(self):
        profile = make_profile("Home", b"home", profile_uuid="profile-home")
        device = FakeDevice("/dev/w0", "wlan0")
        client = FakeClient([device], [profile], active_state=1)
        backend = self.make_backend(client)
        try:
            old_target = next(t for t in backend.snapshot().targets if t.ref.kind == "wifi-profile")
            action = next(a for a in backend.actions(old_target.ref) if a.action_id == "connect")
            result = backend.execute(self.request(old_target, "connect", action.parameters))
            self.assertEqual(result.kind, ResultKind.PENDING)
            self.assertIsNotNone(result.pending)
            client.owner = ":1.88"
            new_snapshot = backend.snapshot()
            self.assertNotEqual(old_target.ref, next(t.ref for t in new_snapshot.targets if t.ref.kind == "wifi-profile"))
            stale_target_result = backend.execute(self.request(old_target, "connect", action.parameters))
            self.assertEqual(stale_target_result.kind, ResultKind.ERROR)
            self.assertEqual(backend.refresh(result.pending).kind, ResultKind.ERROR)
            self.assertEqual(backend.cancel(result.pending).kind, ResultKind.ERROR)
            self.assertEqual(client.deactivation_calls, [])
        finally:
            backend.close()

    def test_accepted_connection_is_pending_until_native_active_state_is_activated(self):
        profile = make_profile("Home", b"home", profile_uuid="profile-home")
        device = FakeDevice("/dev/w0", "wlan0")
        client = FakeClient([device], [profile], active_state=1)
        backend = self.make_backend(client)
        try:
            target = self.target(backend, kind="wifi-profile")
            action = next(a for a in backend.actions(target.ref) if a.action_id == "connect")
            accepted = backend.execute(self.request(target, "connect", action.parameters))
            self.assertEqual(accepted.kind, ResultKind.PENDING)
            active = client.actives[0]
            active.state = 2
            observed = backend.refresh(accepted.pending)
            self.assertEqual(observed.kind, ResultKind.COMPLETE)
            self.assertIn("Observed", observed.message)
        finally:
            backend.close()

    def test_explicit_cancel_deactivates_only_the_exact_active_connection(self):
        profile = make_profile("Home", b"home", profile_uuid="profile-home")
        device = FakeDevice("/dev/w0", "wlan0")
        client = FakeClient([device], [profile], active_state=1)
        backend = self.make_backend(client)
        try:
            target = self.target(backend, kind="wifi-profile")
            action = next(a for a in backend.actions(target.ref) if a.action_id == "connect")
            accepted = backend.execute(self.request(target, "connect", action.parameters))
            self.assertEqual(accepted.kind, ResultKind.PENDING)
            accepted_active = client.actives[0]
            result = backend.cancel(accepted.pending)
            self.assertEqual(result.kind, ResultKind.CANCELLED)
            self.assertEqual(len(client.deactivation_calls), 1)
            self.assertIs(client.deactivation_calls[0], accepted_active)
            self.assertEqual(client.actives, [])
        finally:
            backend.close()

    def test_external_replacement_race_never_disconnects_a_new_active_connection(self):
        profile = make_profile("Home", b"home", profile_uuid="profile-home")
        device = FakeDevice("/dev/w0", "wlan0")
        client = FakeClient([device], [profile], active_state=1)
        backend = self.make_backend(client)
        try:
            target = self.target(backend, kind="wifi-profile")
            action = next(a for a in backend.actions(target.ref) if a.action_id == "connect")
            accepted = backend.execute(self.request(target, "connect", action.parameters))
            self.assertEqual(accepted.kind, ResultKind.PENDING)
            original = client.actives[0]
            replacement = FakeActive("/active/replacement", profile, device, state=2)
            client.actives = [replacement]
            result = backend.cancel(accepted.pending)
            self.assertEqual(result.kind, ResultKind.ERROR)
            self.assertIn("no replacement", result.message)
            self.assertEqual(client.deactivation_calls, [])
            self.assertEqual(client.actives, [replacement])
            self.assertNotEqual(original.get_path(), replacement.get_path())
        finally:
            backend.close()

    def test_close_keeps_an_accepted_connection_and_uses_only_bounded_monitoring(self):
        profile = make_profile("Home", b"home", profile_uuid="profile-home")
        device = FakeDevice("/dev/w0", "wlan0")
        client = FakeClient([device], [profile], active_state=1)
        backend = self.make_backend(client)
        runtime = backend._runtime
        target = self.target(backend, kind="wifi-profile")
        action = next(a for a in backend.actions(target.ref) if a.action_id == "connect")
        accepted = backend.execute(self.request(target, "connect", action.parameters))
        self.assertEqual(accepted.kind, ResultKind.PENDING)
        active = client.actives[0]
        active.state = 2
        backend.close()
        deadline = time.monotonic() + 1.0
        while not runtime.closed and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(runtime.closed, "closed backend monitor should end after native activation settles")
        self.assertEqual(client.deactivation_calls, [])
        self.assertEqual(client.actives, [active])

    def test_cancel_and_close_reject_unsubmitted_credential_staging(self):
        ap = FakeAP("/ap/new", b"Cafe", "00:00:00:00:00:45", security="wpa-psk")
        device = FakeDevice("/dev/w0", "wlan0", [ap])
        for close_first in (False, True):
            with self.subTest(close_first=close_first):
                client = FakeClient([device])
                backend = self.make_backend(client)
                target = self.target(backend, kind="wifi-ap")
                action = next(a for a in backend.actions(target.ref) if a.action_id == "connect")
                parameters = dict(action.parameters)
                parameters.pop("persistence_choice_required")
                parameters["persistence"] = "remember"
                prompt = backend.execute(self.request(target, "connect", parameters))
                self.assertEqual(prompt.kind, ResultKind.NEEDS_SECRET)
                if close_first:
                    backend.close()
                    rejected = backend.provide_secret(prompt.pending, io.BytesIO(b"never-submit-this"))
                    self.assertEqual(rejected.kind, ResultKind.ERROR)
                    self.assertIn("closed", rejected.message)
                else:
                    canceled = backend.cancel(prompt.pending)
                    self.assertEqual(canceled.kind, ResultKind.CANCELLED)
                    rejected = backend.provide_secret(prompt.pending, io.BytesIO(b"never-submit-this"))
                    self.assertEqual(rejected.kind, ResultKind.ERROR)
                    self.assertEqual(backend.refresh(prompt.pending).kind, ResultKind.ERROR)
                    backend.close()
                self.assertEqual(client.add_calls, [])

    def test_new_remember_and_once_profiles_use_nm_owned_flags_and_per_user_policy(self):
        for persistence, expected_persist, expected_autoconnect in (
            ("remember", "disk", True), ("once", "volatile", False),
        ):
            with self.subTest(persistence=persistence):
                ap = FakeAP("/ap/new", b"Cafe", "00:00:00:00:00:44", security="wpa-psk")
                device = FakeDevice("/dev/w0", "wlan0", [ap])
                client = FakeClient([device])
                backend = self.make_backend(client)
                try:
                    target = self.target(backend, kind="wifi-ap")
                    action = next(a for a in backend.actions(target.ref) if a.action_id == "connect")
                    params = dict(action.parameters)
                    params.pop("persistence_choice_required")
                    params["persistence"] = persistence
                    prompt = backend.execute(self.request(target, "connect", params))
                    self.assertEqual(prompt.kind, ResultKind.NEEDS_SECRET)
                    self.assertIn("NetworkManager", prompt.message)
                    self.assertNotIn("wireless-security", json.dumps(target.state))
                    secret = b"test-network-passphrase"
                    completed = backend.provide_secret(prompt.pending, io.BytesIO(secret))
                    self.assertEqual(completed.kind, ResultKind.COMPLETE)
                    self.assertEqual(len(client.add_calls), 1)
                    connection, selected_device, specific, options, profile = client.add_calls[0]
                    setting_connection = connection.get_setting_connection()
                    security = connection.get_setting_wireless_security()
                    self.assertEqual(setting_connection.get_property("permissions"), ["user:fixture-user:"])
                    self.assertEqual(setting_connection.get_autoconnect(), expected_autoconnect)
                    self.assertEqual(security.get_psk_flags(), 0)
                    self.assertEqual(security.get_psk(), secret.decode())
                    self.assertEqual(selected_device.get_path(), "/dev/w0")
                    self.assertEqual(specific, "/ap/new")
                    self.assertEqual(options.lookup_value("persist", GLib.VariantType.new("s")).unpack(), expected_persist)
                    self.assertNotIn(secret.decode(), json.dumps(completed.target.state))
                    self.assertNotIn(secret.decode(), json.dumps(completed.target.facts, default=lambda item: item.value))
                    self.assertEqual(profile.get_uuid(), setting_connection.get_uuid())
                finally:
                    backend.close()

    def test_saved_profile_rejects_persistence_changes_and_preserves_secret_flags(self):
        profile = make_profile("Agent owned", b"home", profile_uuid="agent-profile", flags=1)
        device = FakeDevice("/dev/w0", "wlan0")
        client = FakeClient([device], [profile])
        backend = self.make_backend(client, agent_factory=FakeAgent)
        try:
            target = self.target(backend, kind="wifi-profile")
            action = next(a for a in backend.actions(target.ref) if a.action_id == "connect")
            self.assertEqual(action.action_id, "connect")
            self.assertNotIn("persistence", action.parameters)
            params = dict(action.parameters)
            params["persistence"] = "once"
            result = backend.execute(self.request(target, "connect", params))
            self.assertEqual(result.kind, ResultKind.ERROR)
            self.assertEqual(profile.get_setting_wireless_security().get_psk_flags(), 1)
            self.assertEqual(client.activation_calls, [])
        finally:
            backend.close()

    def test_wrong_password_requires_one_explicit_retry_action(self):
        profile = make_profile("Home", b"home", profile_uuid="profile-home", flags=1)
        device = FakeDevice("/dev/w0", "wlan0")
        client = FakeClient([device], [profile], active_state=4, active_reason=10)
        backend = self.make_backend(client, agent_factory=FakeAgent)
        try:
            target = self.target(backend, kind="wifi-profile")
            action = next(a for a in backend.actions(target.ref) if a.action_id == "connect")
            result = backend.execute(self.request(target, "connect", action.parameters))
            self.assertEqual(result.kind, ResultKind.ERROR)
            self.assertIn("Retry explicitly", result.message)
            retry = next(a for a in backend.actions(target.ref) if a.action_id == "connect")
            self.assertEqual(retry.label, "Retry with a new password")
            self.assertTrue(retry.parameters["reentry"])
            client.active_state = 2
            prompt = backend.execute(self.request(target, "connect", retry.parameters))
            self.assertEqual(prompt.kind, ResultKind.NEEDS_SECRET)
            completed = backend.provide_secret(prompt.pending, io.BytesIO(b"new-password"))
            self.assertEqual(completed.kind, ResultKind.COMPLETE)
            self.assertEqual(profile.get_setting_wireless_security().get_psk_flags(), 1)
            self.assertEqual(client.activation_calls[-1][0].get_uuid(), "profile-home")
            agent = next(op.agent for op in backend._operations.values() if op.pending == prompt.pending)
            self.assertEqual(agent.primed, [("new-password", 1)])
        finally:
            backend.close()

    def test_open_and_wpa3_new_profiles_use_explicit_safe_profile_policy(self):
        # Open profiles need no prompt; WPA3 receives one scoped password and
        # leaves storage to the new NetworkManager-owned profile.
        open_ap = FakeAP("/ap/open", b"Guest", "00:00:00:00:00:51", security="open")
        open_device = FakeDevice("/dev/open", "wlan0", [open_ap])
        open_client = FakeClient([open_device])
        open_backend = self.make_backend(open_client)
        try:
            target = self.target(open_backend, kind="wifi-ap", title_contains="Guest")
            action = next(a for a in open_backend.actions(target.ref) if a.action_id == "connect")
            parameters = dict(action.parameters)
            parameters.pop("persistence_choice_required")
            parameters["persistence"] = "once"
            result = open_backend.execute(self.request(target, "connect", parameters))
            self.assertEqual(result.kind, ResultKind.COMPLETE)
            connection, _device, _ap, options, _profile = open_client.add_calls[0]
            self.assertIsNone(connection.get_setting_wireless_security())
            self.assertEqual(connection.get_setting_connection().get_property("permissions"), ["user:fixture-user:"])
            self.assertFalse(connection.get_setting_connection().get_autoconnect())
            self.assertEqual(options.lookup_value("persist", GLib.VariantType.new("s")).unpack(), "volatile")
        finally:
            open_backend.close()

        sae_ap = FakeAP("/ap/sae", b"Private", "00:00:00:00:00:52", security="sae")
        sae_device = FakeDevice("/dev/sae", "wlan1", [sae_ap])
        sae_client = FakeClient([sae_device])
        sae_backend = self.make_backend(sae_client)
        try:
            target = self.target(sae_backend, kind="wifi-ap", title_contains="Private")
            action = next(a for a in sae_backend.actions(target.ref) if a.action_id == "connect")
            parameters = dict(action.parameters)
            parameters.pop("persistence_choice_required")
            parameters["persistence"] = "remember"
            prompt = sae_backend.execute(self.request(target, "connect", parameters))
            self.assertEqual(prompt.kind, ResultKind.NEEDS_SECRET)
            result = sae_backend.provide_secret(prompt.pending, io.BytesIO(b"sae-password"))
            self.assertEqual(result.kind, ResultKind.COMPLETE)
            connection = sae_client.add_calls[0][0]
            security = connection.get_setting_wireless_security()
            self.assertEqual(security.get_key_mgmt(), "sae")
            self.assertEqual(security.get_psk_flags(), 0)
            self.assertEqual(security.get_psk(), "sae-password")
            self.assertTrue(connection.get_setting_connection().get_autoconnect())
        finally:
            sae_backend.close()

    def test_missing_secret_agent_fails_without_submitting_saved_profile(self):
        profile = make_profile("Agent owned", b"home", profile_uuid="agent-profile", flags=1)
        device = FakeDevice("/dev/w0", "wlan0")
        client = FakeClient([device], [profile])
        backend = self.make_backend(client, agent_factory=RegistrationFailureAgent)
        try:
            target = self.target(backend, kind="wifi-profile")
            action = next(a for a in backend.actions(target.ref) if a.action_id == "connect")
            result = backend.execute(self.request(target, "connect", action.parameters))
            self.assertEqual(result.kind, ResultKind.ERROR)
            self.assertIn("secret agent", result.message)
            self.assertEqual(client.activation_calls, [])
            self.assertEqual(profile.get_setting_wireless_security().get_psk_flags(), 1)
        finally:
            backend.close()

    def test_scan_requests_coalesce_and_recent_scans_are_throttled(self):
        device = FakeDevice("/dev/w0", "wlan0", hold_scan=True)
        client = FakeClient([device])
        backend = self.make_backend(client)
        try:
            target = self.target(backend, kind="wifi-device")
            action = next(a for a in backend.actions(target.ref) if a.action_id == "rescan")
            first = backend.execute(self.request(target, "rescan", action.parameters))
            self.assertEqual(first.kind, ResultKind.PENDING)
            second = backend.execute(self.request(target, "rescan", action.parameters))
            self.assertEqual(second.kind, ResultKind.PENDING)
            self.assertEqual(second.pending, first.pending)
            self.assertEqual(device.scan_requests, 1)
            device.complete_scan()
            settled = backend.refresh(first.pending)
            self.assertEqual(settled.kind, ResultKind.COMPLETE)
            recent = backend.execute(self.request(target, "rescan", action.parameters))
            self.assertEqual(recent.kind, ResultKind.COMPLETE)
            self.assertEqual(device.scan_requests, 1)
        finally:
            backend.close()

    def test_scan_throttle_uses_native_boottime_milliseconds(self):
        # The independent GLib clock is deliberately both a different unit and
        # suspend offset. It must never be compared with NM's LastScan value.
        clock_ms = 5_000_000
        for age_ms, expected_requests in ((500, 0), (2000, 1), (2500, 1), (None, 1)):
            with self.subTest(age_ms=age_ms):
                device = FakeDevice("/dev/w0", "wlan0")
                device.last_scan = -1 if age_ms is None else clock_ms - age_ms
                backend = self.make_backend(FakeClient([device]))
                try:
                    target = self.target(backend, kind="wifi-device")
                    action = next(a for a in backend.actions(target.ref) if a.action_id == "rescan")
                    with mock.patch.object(NM, "utils_get_timestamp_msec", return_value=clock_ms), \
                            mock.patch.object(GLib, "get_monotonic_time", return_value=123_456_000):
                        result = backend.execute(self.request(target, "rescan", action.parameters))
                    self.assertIn(result.kind, {ResultKind.COMPLETE, ResultKind.PENDING})
                    self.assertEqual(device.scan_requests, expected_requests)
                finally:
                    backend.close()

    def test_sae_saved_profile_matches_native_compatible_transition_ap(self):
        profile = make_profile("WPA3 saved", b"transition", profile_uuid="sae-saved", security="sae")
        transition = FakeAP("/ap/transition", b"transition", "00:00:00:00:00:91",
                            security="wpa-psk", extra_flags=1024, valid_profiles=["sae-saved"])
        device = FakeDevice("/dev/w0", "wlan0", [transition], available_connections=[profile])
        client = FakeClient([device], [profile])
        backend = self.make_backend(client)
        try:
            target = self.target(backend, kind="wifi-ap")
            self.assertEqual(target.state["security"], "wpa-psk")
            self.assertTrue(target.state["saved"])
            action = next(a for a in backend.actions(target.ref) if a.action_id == "connect")
            self.assertEqual(action.parameters["profile_uuid"], "sae-saved")
            self.assertNotIn("persistence_choice_required", action.parameters)
            result = backend.execute(self.request(target, "connect", action.parameters))
            self.assertEqual(result.kind, ResultKind.COMPLETE)
            self.assertEqual(client.activation_calls[0][0].get_uuid(), "sae-saved")
            self.assertEqual(client.add_calls, [])
            self.assertEqual(next(iter(backend._operations.values())).security, "sae")

            transition.valid_profiles.clear()
            current = self.target(backend, kind="wifi-ap")
            self.assertFalse(current.state["saved"], "A coarse security-family match cannot override NM's compatibility rejection")
        finally:
            backend.close()

    def test_volatile_profile_cleanup_is_owned_and_fails_closed_on_modification(self):
        ap = FakeAP("/ap/new", b"Temporary", "00:00:00:00:00:61", security="wpa-psk")
        device = FakeDevice("/dev/w0", "wlan0", [ap])

        failed_client = FakeClient([device], active_state=4, active_reason=10)
        failed_backend = self.make_backend(failed_client)
        try:
            target = self.target(failed_backend, kind="wifi-ap")
            action = next(a for a in failed_backend.actions(target.ref) if a.action_id == "connect")
            parameters = dict(action.parameters)
            parameters.pop("persistence_choice_required")
            parameters["persistence"] = "once"
            prompt = failed_backend.execute(self.request(target, "connect", parameters))
            result = failed_backend.provide_secret(prompt.pending, io.BytesIO(b"temporary-pass"))
            self.assertEqual(result.kind, ResultKind.ERROR)
            profile = failed_client.add_calls[0][4]
            self.assertEqual(profile.delete_calls, 1)
            self.assertNotIn(profile, failed_client.profiles)
        finally:
            failed_backend.close()

        pending_client = FakeClient([device], active_state=1)
        pending_backend = self.make_backend(pending_client)
        try:
            target = self.target(pending_backend, kind="wifi-ap")
            action = next(a for a in pending_backend.actions(target.ref) if a.action_id == "connect")
            parameters = dict(action.parameters)
            parameters.pop("persistence_choice_required")
            parameters["persistence"] = "once"
            prompt = pending_backend.execute(self.request(target, "connect", parameters))
            accepted = pending_backend.provide_secret(prompt.pending, io.BytesIO(b"temporary-pass"))
            self.assertEqual(accepted.kind, ResultKind.PENDING)
            profile = pending_client.add_calls[0][4]
            profile.get_setting_connection().set_property("id", "Changed by another actor")
            canceled = pending_backend.cancel(accepted.pending)
            self.assertEqual(canceled.kind, ResultKind.CANCELLED)
            self.assertEqual(profile.delete_calls, 0)
            self.assertIn(profile, pending_client.profiles)
        finally:
            pending_backend.close()

    def test_hidden_wep_and_hotspot_profiles_are_advanced(self):
        profiles = [
            make_profile("Hidden", b"hidden", profile_uuid="hidden", hidden=True),
            make_profile("WEP", b"wep", profile_uuid="wep", security="none"),
            make_profile("Hotspot", b"hotspot", profile_uuid="hotspot", security=None, mode="ap"),
        ]
        client = FakeClient([FakeDevice("/dev/w0", "wlan0")], profiles)
        backend = self.make_backend(client)
        try:
            targets = [t for t in backend.snapshot().targets if t.ref.kind == "wifi-profile"]
            self.assertEqual(len(targets), 3)
            for target in targets:
                self.assertEqual(target.state["security"], "advanced")
                action = backend.actions(target.ref)[0]
                self.assertEqual(action.action_id, "advanced-settings")
                self.assertFalse(action.enabled)
        finally:
            backend.close()

    def test_legacy_wpa_access_point_is_not_offered_as_wpa2(self):
        ap = FakeAP("/ap/wpa1", b"Legacy", "00:00:00:00:00:71", security="wpa1-psk")
        backend = self.make_backend(FakeClient([FakeDevice("/dev/w0", "wlan0", [ap])]))
        try:
            target = self.target(backend, kind="wifi-ap")
            self.assertEqual(target.state["security"], "advanced")
            action = backend.actions(target.ref)[0]
            self.assertEqual(action.action_id, "advanced-settings")
            self.assertFalse(action.enabled)
        finally:
            backend.close()

    def test_actual_cipher_bits_do_not_hide_a_supported_personal_network(self):
        flags = getattr(NM, "80211ApSecurityFlags")
        cipher_bits = int(flags.PAIR_CCMP | flags.GROUP_CCMP)
        ap = FakeAP("/ap/secure", b"Secure", "00:00:00:00:00:81", security="wpa-psk", cipher_bits=cipher_bits)
        backend = self.make_backend(FakeClient([FakeDevice("/dev/w0", "wlan0", [ap])]))
        try:
            target = self.target(backend, kind="wifi-ap")
            self.assertEqual(target.state["security"], "wpa-psk")
            action = backend.actions(target.ref)[0]
            self.assertEqual(action.action_id, "connect")
            self.assertTrue(action.enabled)
        finally:
            backend.close()

    def test_same_ssid_bssids_have_one_stable_row_and_activation_uses_freshest(self):
        profile = make_profile("Shared profile", b"shared", profile_uuid="shared-profile")
        weaker = FakeAP("/ap/weaker", b"shared", "00:00:00:00:00:82", security="wpa-psk", strength=48)
        stronger = FakeAP("/ap/stronger", b"shared", "00:00:00:00:00:83", security="wpa-psk", strength=82)
        device = FakeDevice("/dev/w0", "wlan0", [weaker, stronger])
        client = FakeClient([device], [profile])
        backend = self.make_backend(client)
        try:
            before = self.target(backend, kind="wifi-ap")
            self.assertEqual(before.state["bssid"], stronger.bssid)
            self.assertEqual(len([t for t in backend.snapshot().targets if t.ref.kind == "wifi-ap"]), 1)
            action = next(action for action in backend.actions(before.ref) if action.action_id == "connect")
            self.assertNotIn("ap_path", action.parameters)

            weaker.strength = 95
            stronger.strength = 20
            after = self.target(backend, kind="wifi-ap")
            self.assertEqual(after.ref, before.ref)
            self.assertEqual(after.state["bssid"], weaker.bssid)
            result = backend.execute(self.request(before, action.action_id, action.parameters))
            self.assertEqual(result.kind, ResultKind.COMPLETE)
            self.assertEqual(client.activation_calls[0][2], "/ap/weaker")
        finally:
            backend.close()

    def test_incompatible_unknown_security_classes_keep_separate_rows(self):
        wep = FakeAP("/ap/wep", b"Same name", "00:00:00:00:00:84", security="wep")
        unknown = FakeAP("/ap/unknown", b"Same name", "00:00:00:00:00:85", extra_flags=0x10000)
        backend = self.make_backend(FakeClient([FakeDevice("/dev/w0", "wlan0", [wep, unknown])]))
        try:
            targets = [target for target in backend.snapshot().targets if target.ref.kind == "wifi-ap"]
            self.assertEqual(len(targets), 2)
            self.assertEqual({target.state["security"] for target in targets}, {"advanced"})
            self.assertEqual(len({target.ref for target in targets}), 2)
            self.assertEqual(len({target.state["security_group"] for target in targets}), 2)
        finally:
            backend.close()

    def test_unavailable_saved_wifi_profile_has_no_connect_action(self):
        profile = make_profile("Unavailable saved", b"missing", profile_uuid="missing-profile")
        ap = FakeAP("/ap/missing", b"missing", "00:00:00:00:00:86", security="wpa-psk", valid_profiles=[])
        device = FakeDevice("/dev/w0", "wlan0", [ap], available_connections=[])
        backend = self.make_backend(FakeClient([device], [profile]))
        try:
            target = self.target(backend, kind="wifi-profile")
            self.assertEqual(target.availability.value, "unavailable")
            self.assertIn("unavailable", target.status.casefold())
            self.assertEqual(backend.actions(target.ref), ())
        finally:
            backend.close()

    def test_connecting_profile_is_not_marked_current_and_disconnect_names_exact_target(self):
        profile = make_profile("Meeting Wi-Fi", b"meeting", profile_uuid="meeting-profile")
        device = FakeDevice("/dev/w0", "wlan0")
        active = FakeActive("/active/connecting", profile, device, state=1)
        backend = self.make_backend(FakeClient([device], [profile], [active]))
        try:
            target = self.target(backend, kind="wifi-profile")
            self.assertEqual(target.status, "Connecting")
            self.assertFalse(target.active)
            self.assertFalse(target.state["connected"])
            action = backend.actions(target.ref)[0]
            self.assertEqual(action.action_id, "disconnect")
            self.assertIn("Meeting Wi-Fi", action.confirmation)
            self.assertIn("wlan0", action.confirmation)
        finally:
            backend.close()

    def test_wired_inventory_and_saved_profile_operations_are_scoped(self):
        wired = make_ethernet_profile("Office wired", profile_uuid="office-wired", interface="enp2s0")
        eth0 = FakeDevice(
            "/dev/eth0", "enp2s0", device_type=1, state=100, carrier=True,
            ipv4=("192.0.2.15",), ipv6=("2001:db8::15",),
        )
        eth1 = FakeDevice("/dev/eth1", "enp3s0", device_type=1, state=30, carrier=False)
        wifi = FakeDevice("/dev/wifi", "wlan0", state=30)
        client = FakeClient([eth0, eth1, wifi], [wired], connectivity=4)
        backend = self.make_backend(client)
        try:
            snapshot = backend.snapshot()
            devices = [target for target in snapshot.targets if target.ref.kind == "ethernet-device"]
            self.assertEqual({target.state["interface"] for target in devices}, {"enp2s0", "enp3s0"})
            device_target = next(target for target in devices if target.state["interface"] == "enp2s0")
            self.assertEqual(device_target.status, "Disconnected")
            self.assertFalse(device_target.active)
            profile_target = self.target(backend, kind="ethernet-profile")
            action = next(action for action in backend.actions(profile_target.ref) if action.action_id == "connect")
            connected = backend.execute(self.request(profile_target, action.action_id, action.parameters))
            self.assertEqual(connected.kind, ResultKind.COMPLETE)
            self.assertEqual(client.activation_calls[0][0].get_uuid(), "office-wired")
            self.assertEqual(client.activation_calls[0][1].get_path(), "/dev/eth0")
            self.assertIsNone(client.activation_calls[0][2])
            self.assertEqual(client.add_calls, [], "wired menu operations must never create a new profile")

            current = self.target(backend, kind="ethernet-profile")
            self.assertEqual(current.status, "Connected")
            self.assertTrue(current.active)
            self.assertTrue(current.state["connected"])
            fact_values = {fact.label: fact.value for fact in current.facts}
            self.assertEqual(fact_values["IPv4 addresses"], "192.0.2.15")
            self.assertEqual(fact_values["IPv6 addresses"], "2001:db8::15")
            self.assertEqual(fact_values["NetworkManager connectivity check"], "Full")

            disconnect = backend.actions(current.ref)[0]
            self.assertEqual(disconnect.action_id, "disconnect")
            self.assertIn("Office wired", disconnect.confirmation)
            self.assertIn("enp2s0", disconnect.confirmation)
            request = self.request(current, disconnect.action_id, disconnect.parameters)
            replacement = FakeActive("/active/replacement", wired, eth0, state=2)
            client.actives = [replacement]
            stale = backend.execute(request)
            self.assertEqual(stale.kind, ResultKind.ERROR)
            self.assertEqual(client.deactivation_calls, [])
            self.assertEqual(client.actives, [replacement])

            current = self.target(backend, kind="ethernet-profile")
            disconnect = backend.actions(current.ref)[0]
            result = backend.execute(self.request(current, disconnect.action_id, disconnect.parameters))
            self.assertEqual(result.kind, ResultKind.COMPLETE)
            self.assertEqual(client.deactivation_calls, [replacement])

            ethernet_active = FakeActive("/active/ethernet-live", wired, eth0, state=2)
            client.actives = [ethernet_active]
            radio = self.target(backend, kind="wifi-radio")
            radio_action = backend.actions(radio.ref)[0]
            self.assertIn("Ethernet and Bluetooth remain unchanged", radio_action.confirmation)
            result = backend.execute(self.request(radio, radio_action.action_id, radio_action.parameters))
            self.assertEqual(result.kind, ResultKind.COMPLETE)
            self.assertFalse(client.wifi)
            self.assertEqual(client.actives, [ethernet_active])
        finally:
            backend.close()

    def test_secondary_eap_and_vpn_profiles_are_visible_as_advanced(self):
        secondary = make_profile("Primary with VPN", b"primary", profile_uuid="primary-vpn", secondaries=("vpn-uuid",))
        eap = make_profile("Enterprise Wi-Fi", b"enterprise", profile_uuid="enterprise", security="wpa-eap")
        vpn = make_vpn_profile(profile_uuid="vpn-uuid")
        wired_eap = make_ethernet_profile("Wired 802.1X", profile_uuid="wired-eap", has_802_1x=True)
        wifi = FakeDevice("/dev/wifi", "wlan0", [FakeAP("/ap/primary", b"primary", "00:00:00:00:00:87")])
        eth = FakeDevice("/dev/eth", "enp2s0", device_type=1, carrier=True)
        backend = self.make_backend(FakeClient([wifi, eth], [secondary, eap, vpn, wired_eap]))
        try:
            targets = backend.snapshot().targets
            wifi_advanced = [target for target in targets if target.ref.kind == "wifi-profile" and target.state["security"] == "advanced"]
            ethernet_advanced = [target for target in targets if target.ref.kind == "ethernet-profile" and target.state["security"] == "advanced"]
            vpn_targets = [target for target in targets if target.ref.kind == "network-profile"]
            self.assertEqual({target.state["uuid"] for target in wifi_advanced}, {"primary-vpn", "enterprise"})
            self.assertEqual({target.state["uuid"] for target in ethernet_advanced}, {"wired-eap"})
            self.assertEqual({target.state["uuid"] for target in vpn_targets}, {"vpn-uuid"})
            for target in (*wifi_advanced, *ethernet_advanced, *vpn_targets):
                actions = backend.actions(target.ref)
                self.assertEqual(actions[0].action_id, "advanced-settings")
                self.assertFalse(actions[0].enabled)
                self.assertFalse(any(action.action_id == "connect" and action.enabled for action in actions))
        finally:
            backend.close()


if __name__ == "__main__":
    unittest.main()
