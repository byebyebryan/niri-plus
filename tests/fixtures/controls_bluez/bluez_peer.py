"""Synthetic org.bluez service used only on an owned private D-Bus daemon."""

from __future__ import annotations

import threading

import gi

gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gio, GLib


BLUEZ = "org.bluez"
OBJECT_MANAGER = "org.freedesktop.DBus.ObjectManager"
AGENT_MANAGER = "org.bluez.AgentManager1"
AGENT = "org.bluez.Agent1"
ADAPTER = "org.bluez.Adapter1"
DEVICE = "org.bluez.Device1"
BATTERY = "org.bluez.Battery1"

OBJECT_MANAGER_XML = """<node><interface name="org.freedesktop.DBus.ObjectManager">
  <method name="GetManagedObjects"><arg type="a{oa{sa{sv}}}" direction="out"/></method>
</interface></node>"""
AGENT_MANAGER_XML = """<node><interface name="org.bluez.AgentManager1">
  <method name="RegisterAgent"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
  <method name="UnregisterAgent"><arg type="o" direction="in"/></method>
  <method name="RequestDefaultAgent"><arg type="o" direction="in"/></method>
</interface></node>"""
ADAPTER_XML = """<node><interface name="org.bluez.Adapter1">
  <method name="StartDiscovery"/><method name="StopDiscovery"/>
  <method name="RemoveDevice"><arg type="o" direction="in"/></method>
  <property name="Address" type="s" access="read"/>
  <property name="Alias" type="s" access="read"/>
  <property name="Name" type="s" access="read"/>
  <property name="Powered" type="b" access="readwrite"/>
  <property name="Discovering" type="b" access="read"/>
</interface></node>"""
DEVICE_XML = """<node><interface name="org.bluez.Device1">
  <method name="Connect"/><method name="Disconnect"/><method name="Pair"/><method name="CancelPairing"/>
  <property name="Adapter" type="o" access="read"/>
  <property name="Address" type="s" access="read"/>
  <property name="AddressType" type="s" access="read"/>
  <property name="Alias" type="s" access="read"/>
  <property name="Name" type="s" access="read"/>
  <property name="Paired" type="b" access="read"/>
  <property name="Connected" type="b" access="read"/>
  <property name="Trusted" type="b" access="readwrite"/>
</interface></node>"""
BATTERY_XML = """<node><interface name="org.bluez.Battery1">
  <property name="Percentage" type="y" access="read"/>
</interface></node>"""


def _variant(signature: str, value):
    return GLib.Variant(signature, value)


class BluezPeer:
    """In-memory ObjectManager/Adapter1/Device1 peer with observable booleans."""

    adapter_path = "/org/bluez/hci0"

    def __init__(self, address: str, *, devices=()):
        self.address = address
        self.context = GLib.MainContext.new()
        self.loop = GLib.MainLoop.new(self.context, False)
        self.connection = self._new_connection(address)
        self._request_name(self.connection)
        self.owner = self.connection.get_unique_name()
        self.devices = {}
        for item in devices:
            config = dict(item)
            path = config.pop("path")
            self.devices[path] = {
                "properties": {
                    "Adapter": self.adapter_path,
                    "Address": config.pop("address"),
                    "AddressType": config.pop("address_type", "public"),
                    "Alias": config.pop("alias"),
                    "Name": config.pop("name", "Synthetic Bluetooth device"),
                    "Paired": config.pop("paired", False),
                    "Connected": config.pop("connected", False),
                    "Trusted": config.pop("trusted", False),
                },
                "pair_mode": config.pop("pair_mode", "none"),
                "expected_secret": None,
                "hold_pair_reply": False,
                "pair_invocation": None,
                "input_matches": False,
                "input_count": 0,
            }
            if config:
                raise ValueError("unknown synthetic device fields")
        self.adapter_properties = {
            "Address": "02:00:00:00:00:01",
            "Alias": "Synthetic adapter",
            "Name": "Synthetic adapter",
            "Powered": True,
            "Discovering": False,
        }
        self.agents = {}
        self.discoveries = {}
        self.counters = {
            "start_discovery": 0,
            "stop_discovery": 0,
            "connect": 0,
            "disconnect": 0,
            "pair": 0,
            "cancel_pairing": 0,
            "remove_device": 0,
            "register_agent": 0,
            "unregister_agent": 0,
            "default_agent": 0,
            "pin_requests": 0,
            "passkey_requests": 0,
            "confirmation_requests": 0,
            "display_passkey_requests": 0,
        }
        self._registrations = []
        self._retired_connections = []
        self._thread = None
        self._register_objects()

    @staticmethod
    def _new_connection(address: str):
        flags = Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION
        return Gio.DBusConnection.new_for_address_sync(address, flags, None, None)

    @staticmethod
    def _request_name(connection):
        result = connection.call_sync(
            "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "RequestName",
            _variant("(su)", (BLUEZ, 0)), _variant_type("(u)"), Gio.DBusCallFlags.NONE, 3000, None,
        ).unpack()[0]
        if result not in {1, 4}:
            raise RuntimeError("could not claim private synthetic BlueZ name")

    def _register(self, path: str, xml: str, method_call=None, get_property=None, set_property=None):
        node = Gio.DBusNodeInfo.new_for_xml(xml)
        self.context.push_thread_default()
        try:
            registration_id = self.connection.register_object(
                path, node.interfaces[0], method_call, get_property, set_property,
            )
        finally:
            self.context.pop_thread_default()
        self._registrations.append(registration_id)

    def _register_objects(self):
        manager_node = Gio.DBusNodeInfo.new_for_xml(AGENT_MANAGER_XML)
        object_manager_node = Gio.DBusNodeInfo.new_for_xml(OBJECT_MANAGER_XML)
        self.context.push_thread_default()
        try:
            self._registrations.append(self.connection.register_object(
                "/org/bluez", manager_node.interfaces[0], self._manager_call, None, None,
            ))
            self._registrations.append(self.connection.register_object(
                "/", object_manager_node.interfaces[0], self._object_manager_call, None, None,
            ))
        finally:
            self.context.pop_thread_default()
        self._register(self.adapter_path, ADAPTER_XML, self._adapter_call, self._adapter_get, self._adapter_set)
        for path in self.devices:
            self._register(path, DEVICE_XML, self._device_call, self._device_get, self._device_set)
            # Battery is optional and read-only; it lets inventory exercise
            # the real Battery1 object/property path without hardware.
            self._register(path, BATTERY_XML, None, self._battery_get, None)

    def start(self):
        if self._thread is not None:
            return

        def run():
            self.context.push_thread_default()
            try:
                self.loop.run()
            finally:
                self.context.pop_thread_default()

        self._thread = threading.Thread(target=run, name="private-bluez-peer", daemon=True)
        self._thread.start()

    def set_expected_secret(self, path: str, secret: str | int, *, hold_reply=False):
        device = self.devices[path]
        device["expected_secret"] = secret
        device["hold_pair_reply"] = bool(hold_reply)

    def set_pair_mode(self, path: str, mode: str):
        if mode not in {"none", "pin", "passkey", "confirmation", "display"}:
            raise ValueError("unsupported synthetic pairing mode")
        self.devices[path]["pair_mode"] = mode

    def input_result(self, path: str) -> tuple[bool, int]:
        device = self.devices[path]
        return bool(device["input_matches"]), int(device["input_count"])

    def stats(self) -> dict[str, object]:
        return {
            **self.counters,
            "registered_agent_count": len(self.agents),
            "active_discovery_clients": len([count for count in self.discoveries.values() if count > 0]),
            "discovery_counts": dict(self.discoveries),
            "powered": bool(self.adapter_properties["Powered"]),
            "paired": {path: bool(value["properties"]["Paired"]) for path, value in self.devices.items()},
            "connected": {path: bool(value["properties"]["Connected"]) for path, value in self.devices.items()},
            "trusted": {path: bool(value["properties"]["Trusted"]) for path, value in self.devices.items()},
            "input_results": {path: self.input_result(path) for path in self.devices},
        }

    def _managed_objects(self):
        objects = {
            self.adapter_path: {
                ADAPTER: {name: _variant("b" if type(value) is bool else "s", value)
                          for name, value in self.adapter_properties.items()},
            },
        }
        for path, record in self.devices.items():
            objects[path] = {
                DEVICE: {name: _variant("b" if type(value) is bool else "o" if name == "Adapter" else "s", value)
                         for name, value in record["properties"].items()},
                BATTERY: {"Percentage": _variant("y", 57)},
            }
        return objects

    def _object_manager_call(self, _connection, _sender, _path, _interface, method, _parameters, invocation):
        if method != "GetManagedObjects":
            invocation.return_dbus_error("org.freedesktop.DBus.Error.UnknownMethod", "Unsupported ObjectManager method")
            return
        try:
            invocation.return_value(_variant("(a{oa{sa{sv}}})", (self._managed_objects(),)))
        except Exception:
            invocation.return_dbus_error("org.freedesktop.DBus.Error.Failed", "Synthetic inventory could not be encoded")

    def _manager_call(self, _connection, sender, _path, _interface, method, parameters, invocation):
        values = parameters.unpack()
        if method == "RegisterAgent":
            agent_path, capability = values
            if capability not in {"KeyboardDisplay", "DisplayYesNo", "KeyboardOnly", "NoInputNoOutput"}:
                invocation.return_dbus_error("org.bluez.Error.InvalidArguments", "Unknown agent capability")
                return
            self.agents[sender] = agent_path
            self.counters["register_agent"] += 1
        elif method == "UnregisterAgent":
            if self.agents.get(sender) != values[0]:
                invocation.return_dbus_error("org.bluez.Error.DoesNotExist", "Agent was not registered by this sender")
                return
            del self.agents[sender]
            self.counters["unregister_agent"] += 1
        elif method == "RequestDefaultAgent":
            self.counters["default_agent"] += 1
        else:
            invocation.return_dbus_error("org.freedesktop.DBus.Error.UnknownMethod", "Unsupported AgentManager method")
            return
        invocation.return_value(_variant("()", ()))

    def _adapter_get(self, _connection, _sender, _path, _interface, property_name):
        value = self.adapter_properties[property_name]
        return _variant("b" if type(value) is bool else "s", value)

    def _adapter_set(self, _connection, _sender, _path, _interface, property_name, value):
        if property_name != "Powered":
            return False
        self.adapter_properties[property_name] = bool(value.unpack())
        return True

    def _device_get(self, _connection, _sender, path, _interface, property_name):
        value = self.devices[path]["properties"][property_name]
        return _variant("b" if type(value) is bool else "o" if property_name == "Adapter" else "s", value)

    def _device_set(self, _connection, _sender, path, _interface, property_name, value):
        if property_name != "Trusted":
            return False
        self.devices[path]["properties"][property_name] = bool(value.unpack())
        return True

    @staticmethod
    def _battery_get(_connection, _sender, _path, _interface, property_name):
        if property_name != "Percentage":
            return None
        return _variant("y", 57)

    def _adapter_call(self, _connection, sender, _path, _interface, method, parameters, invocation):
        if method == "StartDiscovery":
            self.discoveries[sender] = self.discoveries.get(sender, 0) + 1
            self.adapter_properties["Discovering"] = True
            self.counters["start_discovery"] += 1
        elif method == "StopDiscovery":
            count = self.discoveries.get(sender, 0)
            if count > 1:
                self.discoveries[sender] = count - 1
            elif count == 1:
                self.discoveries.pop(sender, None)
            self.adapter_properties["Discovering"] = any(self.discoveries.values())
            self.counters["stop_discovery"] += 1
        elif method == "RemoveDevice":
            self.counters["remove_device"] += 1
        else:
            invocation.return_dbus_error("org.bluez.Error.NotSupported", "Unsupported Adapter1 method")
            return
        invocation.return_value(_variant("()", ()))

    def _device_call(self, _connection, sender, path, _interface, method, _parameters, invocation):
        if path not in self.devices:
            invocation.return_dbus_error("org.bluez.Error.DoesNotExist", "Synthetic device disappeared")
            return
        device = self.devices[path]
        props = device["properties"]
        if method == "Connect":
            self.counters["connect"] += 1
            props["Connected"] = True
            invocation.return_value(_variant("()", ()))
        elif method == "Disconnect":
            self.counters["disconnect"] += 1
            props["Connected"] = False
            invocation.return_value(_variant("()", ()))
        elif method == "Pair":
            self.counters["pair"] += 1
            if sender not in self.agents:
                invocation.return_dbus_error("org.bluez.Error.AuthenticationFailed", "No owned pairing agent registered")
                return
            device["pair_invocation"] = invocation
            self._request_pairing_interaction(path, sender, device, invocation)
        elif method == "CancelPairing":
            self.counters["cancel_pairing"] += 1
            invocation.return_value(_variant("()", ()))
            pair_invocation, device["pair_invocation"] = device["pair_invocation"], None
            if pair_invocation is not None:
                pair_invocation.return_dbus_error("org.bluez.Error.Canceled", "Synthetic owned pairing canceled")
        else:
            invocation.return_dbus_error("org.bluez.Error.NotSupported", "Unsupported Device1 method")

    def _request_pairing_interaction(self, path, sender, device, pair_invocation):
        mode = device["pair_mode"]
        if mode == "none":
            self._complete_pair(path)
            pair_invocation.return_value(_variant("()", ()))
            device["pair_invocation"] = None
            return
        if mode == "pin":
            method, signature, values, output = "RequestPinCode", "(o)", (path,), "s"
            self.counters["pin_requests"] += 1
        elif mode == "passkey":
            method, signature, values, output = "RequestPasskey", "(o)", (path,), "u"
            self.counters["passkey_requests"] += 1
        elif mode == "confirmation":
            method, signature, values, output = "RequestConfirmation", "(ou)", (path, 42), ""
            self.counters["confirmation_requests"] += 1
        else:
            method, signature, values, output = "DisplayPasskey", "(ouq)", (path, 42, 2), ""
            self.counters["display_passkey_requests"] += 1

        def finished(connection, result, _data=None):
            try:
                response = connection.call_finish(result).unpack()
            except Exception:
                pair_invocation.return_dbus_error("org.bluez.Error.Rejected", "Synthetic pairing interaction was rejected")
                device["pair_invocation"] = None
                return
            if output:
                value = response[0]
                device["input_count"] += 1
                device["input_matches"] = value == device["expected_secret"]
                if not device["input_matches"]:
                    pair_invocation.return_dbus_error("org.bluez.Error.Rejected", "Synthetic peer rejected the input")
                    device["pair_invocation"] = None
                    return
            if mode == "display" or device["hold_pair_reply"]:
                return
            self._complete_pair(path)
            pair_invocation.return_value(_variant("()", ()))
            device["pair_invocation"] = None

        self.connection.call(
            sender, self.agents[sender], AGENT, method, _variant(signature, values),
            None, Gio.DBusCallFlags.NO_AUTO_START, 5000, None, finished, None,
        )

    def _complete_pair(self, path):
        self.devices[path]["properties"]["Paired"] = True

    def complete_pair(self, path):
        """Complete a held successful Pair reply on the service's own context."""

        source = GLib.idle_source_new()

        def complete(_unused=None):
            device = self.devices[path]
            invocation, device["pair_invocation"] = device["pair_invocation"], None
            if invocation is not None:
                self._complete_pair(path)
                invocation.return_value(_variant("()", ()))
            return GLib.SOURCE_REMOVE

        source.set_callback(complete)
        source.attach(self.context)

    def external_discovery_client(self):
        connection = self._new_connection(self.address)
        connection.call_sync(
            self.owner, self.adapter_path, ADAPTER, "StartDiscovery", _variant("()", ()), None,
            Gio.DBusCallFlags.NO_AUTO_START, 3000, None,
        )
        return connection

    def replace_owner(self):
        old = self.connection
        old.call_sync(
            "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "ReleaseName",
            _variant("(s)", (BLUEZ,)), _variant_type("(u)"), Gio.DBusCallFlags.NONE, 3000, None,
        )
        replacement = self._new_connection(self.address)
        result = replacement.call_sync(
            "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "RequestName",
            _variant("(su)", (BLUEZ, 0)), _variant_type("(u)"), Gio.DBusCallFlags.NONE, 3000, None,
        ).unpack()[0]
        if result not in {1, 4}:
            replacement.close_sync(None)
            raise RuntimeError("could not claim replacement synthetic BlueZ name")
        self.connection = replacement
        self.owner = replacement.get_unique_name()
        self._retired_connections.append(old)
        self.agents.clear()
        # Re-register identical objects on the new unique owner. Registered
        # paths on the old connection remain inert until the caller closes it.
        self._registrations.clear()
        if self._thread is None:
            self._register_objects()
        else:
            self._run_on_context(self._register_objects)
        return old

    def _run_on_context(self, callback, timeout=3.0):
        completed = threading.Event()
        errors = []
        source = GLib.idle_source_new()

        def invoke(_unused=None):
            try:
                callback()
            except Exception as error:
                errors.append(error)
            finally:
                completed.set()
            return GLib.SOURCE_REMOVE

        source.set_callback(invoke)
        source.attach(self.context)
        if not completed.wait(timeout):
            raise TimeoutError("private BlueZ main context did not dispatch replacement registration")
        if errors:
            raise errors[0]

    def close(self):
        if self.loop.is_running():
            self.loop.quit()
        if self._thread is not None:
            self._thread.join(timeout=3)
            if self._thread.is_alive():
                raise RuntimeError("private BlueZ peer main loop did not stop")
            self._thread = None
        for registration_id in reversed(self._registrations):
            try:
                self.connection.unregister_object(registration_id)
            except Exception:
                pass
        self._registrations.clear()
        try:
            self.connection.close_sync(None)
        except Exception:
            pass
        for connection in self._retired_connections:
            try:
                connection.close_sync(None)
            except Exception:
                pass
        self._retired_connections.clear()


def _variant_type(signature: str):
    return GLib.VariantType.new(signature)
