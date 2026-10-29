"""Private NetworkManager AgentManager peer used only by controls tests."""

from __future__ import annotations

import sys
import os

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib


AGENT_MANAGER_XML = """
<node>
  <interface name='org.freedesktop.NetworkManager.AgentManager'>
    <method name='Register'>
      <arg name='identifier' type='s' direction='in'/>
    </method>
    <method name='RegisterWithCapabilities'>
      <arg name='identifier' type='s' direction='in'/>
      <arg name='capabilities' type='u' direction='in'/>
    </method>
    <method name='Unregister'/>
  </interface>
  <interface name='org.niri_plus.ControlsTestProbe'>
    <method name='GetStatus'>
      <arg type='s' direction='out'/>
      <arg type='u' direction='out'/>
      <arg type='u' direction='out'/>
      <arg type='u' direction='out'/>
    </method>
    <method name='GetRegistrations'>
      <arg type='a{ss}' direction='out'/>
    </method>
    <method name='GetCounters'>
      <arg type='u' direction='out'/>
      <arg type='u' direction='out'/>
      <arg type='u' direction='out'/>
      <arg type='u' direction='out'/>
      <arg type='u' direction='out'/>
    </method>
    <method name='GetPeerPid'>
      <arg type='u' direction='out'/>
    </method>
    <method name='GetLastAgentFailure'>
      <arg type='s' direction='out'/>
      <arg type='s' direction='out'/>
      <arg type='s' direction='out'/>
    </method>
    <method name='ArmShutdown'>
      <arg type='s' direction='in'/>
    </method>
    <method name='Shutdown'>
      <arg type='s' direction='in'/>
    </method>
    <method name='ProbeGetSecrets'>
      <arg type='s' direction='in'/>
      <arg type='a{sa{sv}}' direction='in'/>
      <arg type='o' direction='in'/>
      <arg type='s' direction='in'/>
      <arg type='as' direction='in'/>
      <arg type='u' direction='in'/>
      <arg type='a{sa{sv}}' direction='out'/>
    </method>
    <method name='ProbeSaveSecrets'>
      <arg type='s' direction='in'/>
      <arg type='a{sa{sv}}' direction='in'/>
      <arg type='o' direction='in'/>
    </method>
    <method name='ProbeDeleteSecrets'>
      <arg type='s' direction='in'/>
      <arg type='a{sa{sv}}' direction='in'/>
      <arg type='o' direction='in'/>
    </method>
    <method name='ProbeCancelGetSecrets'>
      <arg type='s' direction='in'/>
      <arg type='o' direction='in'/>
      <arg type='s' direction='in'/>
    </method>
  </interface>
</node>
"""

BUS_NAME = "org.freedesktop.NetworkManager"
AGENT_PATH = "/org/freedesktop/NetworkManager/AgentManager"
PROBE_PATH = "/org/niri_plus/ControlsTestProbe"
SECRET_AGENT_PATH = "/org/freedesktop/NetworkManager/SecretAgent"
SECRET_AGENT_INTERFACE = "org.freedesktop.NetworkManager.SecretAgent"


def main(address: str) -> int:
    flags = Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION
    connection = Gio.DBusConnection.new_for_address_sync(address, flags, None, None)
    request_name = connection.call_sync(
        "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "RequestName",
        GLib.Variant("(su)", (BUS_NAME, 0)), GLib.VariantType.new("(u)"), Gio.DBusCallFlags.NONE, 2000, None,
    )
    if request_name.unpack()[0] not in {1, 4}:
        raise RuntimeError("private NetworkManager name could not be acquired")
    node = Gio.DBusNodeInfo.new_for_xml(AGENT_MANAGER_XML)
    manager = next(i for i in node.interfaces if i.name == "org.freedesktop.NetworkManager.AgentManager")
    probe = next(i for i in node.interfaces if i.name == "org.niri_plus.ControlsTestProbe")
    registrations: dict[str, str] = {}
    last_identifier = ""
    register_count = 0
    unregister_count = 0
    method_unreg_count = 0
    owner_loss_count = 0
    secret_call_counts = {"GetSecrets": 0, "SaveSecrets": 0, "DeleteSecrets": 0, "CancelGetSecrets": 0}
    last_agent_method = ""
    last_agent_error_name = ""
    last_agent_error_class = ""
    shutdown_token = ""
    loop = GLib.MainLoop.new(None, False)

    def forward_agent_call(identifier, method, parameters, reply_type, invocation):
        nonlocal last_agent_method, last_agent_error_name, last_agent_error_class
        owners = [owner for owner, registered_id in registrations.items() if registered_id == identifier]
        if len(owners) != 1:
            invocation.return_dbus_error("org.niri_plus.Probe.AgentUnavailable", "No unique registered agent matches this identifier")
            return
        secret_call_counts[method] += 1
        last_agent_method = method
        last_agent_error_name = ""
        last_agent_error_class = ""

        def forwarded(connection, result, _user_data):
            nonlocal last_agent_error_name, last_agent_error_class
            try:
                value = connection.call_finish(result)
                invocation.return_value(value)
            except Exception as error:
                try:
                    last_agent_error_name = Gio.DBusError.get_remote_error(error) or "local-agent-error"
                except Exception:
                    last_agent_error_name = "unclassified-agent-error"
                message = str(getattr(error, "message", ""))
                if "Request is outside this invocation" in message:
                    last_agent_error_class = "scope-rejected"
                elif "Request path is outside this invocation" in message:
                    last_agent_error_class = "path-scope-rejected"
                elif "Request identity is outside this invocation" in message:
                    last_agent_error_class = "identity-scope-rejected"
                elif "No agent-owned Wi-Fi credential was provided to save" in message:
                    last_agent_error_class = "no-agent-owned-secret"
                elif "Secret Service" in message:
                    last_agent_error_class = "secret-service-failure"
                elif "Connection identity is unavailable" in message:
                    last_agent_error_class = "connection-identity-unavailable"
                elif "NoSecrets" in message:
                    last_agent_error_class = "other-no-secrets"
                else:
                    last_agent_error_class = "other-agent-error"
                invocation.return_dbus_error("org.niri_plus.Probe.AgentCallFailed", "The registered agent rejected this request")

        connection.call(
            owners[0], SECRET_AGENT_PATH, SECRET_AGENT_INTERFACE, method, parameters,
            reply_type, Gio.DBusCallFlags.NONE, 2500, None, forwarded, None,
        )

    def method_call(_conn, sender, _path, interface, method, parameters, invocation):
        nonlocal last_identifier, register_count, unregister_count, method_unreg_count, shutdown_token
        if interface == "org.freedesktop.NetworkManager.AgentManager":
            if method in {"Register", "RegisterWithCapabilities"}:
                values = parameters.unpack()
                identifier = values[0]
                last_identifier = identifier
                registrations[sender] = identifier
                register_count += 1
                invocation.return_value(GLib.Variant("()", ()))
            elif method == "Unregister":
                registrations.pop(sender, None)
                unregister_count += 1
                method_unreg_count += 1
                invocation.return_value(GLib.Variant("()", ()))
            return
        if interface == "org.niri_plus.ControlsTestProbe" and method == "GetStatus":
            invocation.return_value(GLib.Variant("(suuu)", (
                last_identifier, register_count, unregister_count, len(registrations),
            )))
            return
        if interface == "org.niri_plus.ControlsTestProbe" and method == "GetRegistrations":
            invocation.return_value(GLib.Variant("(a{ss})", (dict(registrations),)))
            return
        if interface == "org.niri_plus.ControlsTestProbe" and method == "GetCounters":
            invocation.return_value(GLib.Variant("(uuuuu)", (
                register_count, unregister_count, method_unreg_count, owner_loss_count,
                sum(secret_call_counts.values()),
            )))
            return
        if interface == "org.niri_plus.ControlsTestProbe" and method == "GetPeerPid":
            invocation.return_value(GLib.Variant("(u)", (os.getpid(),)))
            return
        if interface == "org.niri_plus.ControlsTestProbe" and method == "GetLastAgentFailure":
            invocation.return_value(GLib.Variant("(sss)", (last_agent_method, last_agent_error_name, last_agent_error_class)))
            return
        if interface == "org.niri_plus.ControlsTestProbe" and method == "ArmShutdown":
            token = parameters.get_child_value(0).get_string()
            if shutdown_token or len(token) < 32:
                invocation.return_dbus_error("org.niri_plus.Probe.ShutdownDenied", "Shutdown cannot be armed")
                return
            shutdown_token = token
            invocation.return_value(GLib.Variant("()", ()))
            return
        if interface == "org.niri_plus.ControlsTestProbe" and method == "Shutdown":
            token = parameters.get_child_value(0).get_string()
            if not shutdown_token or token != shutdown_token:
                invocation.return_dbus_error("org.niri_plus.Probe.ShutdownDenied", "Shutdown token is invalid")
                return
            invocation.return_value(GLib.Variant("()", ()))
            GLib.idle_add(loop.quit)
            return
        if interface == "org.niri_plus.ControlsTestProbe" and method == "ProbeGetSecrets":
            identifier = parameters.get_child_value(0).get_string()
            forwarded_parameters = GLib.Variant.new_tuple(*(
                parameters.get_child_value(index) for index in range(1, 6)
            ))
            forward_agent_call(
                identifier, "GetSecrets", forwarded_parameters,
                GLib.VariantType.new("(a{sa{sv}})"), invocation,
            )
            return
        if interface == "org.niri_plus.ControlsTestProbe" and method in {"ProbeSaveSecrets", "ProbeDeleteSecrets"}:
            identifier = parameters.get_child_value(0).get_string()
            agent_method = "SaveSecrets" if method == "ProbeSaveSecrets" else "DeleteSecrets"
            forwarded_parameters = GLib.Variant.new_tuple(
                parameters.get_child_value(1), parameters.get_child_value(2),
            )
            forward_agent_call(identifier, agent_method, forwarded_parameters, GLib.VariantType.new("()"), invocation)
            return
        if interface == "org.niri_plus.ControlsTestProbe" and method == "ProbeCancelGetSecrets":
            identifier = parameters.get_child_value(0).get_string()
            forwarded_parameters = GLib.Variant.new_tuple(
                parameters.get_child_value(1), parameters.get_child_value(2),
            )
            forward_agent_call(identifier, "CancelGetSecrets", forwarded_parameters, GLib.VariantType.new("()"), invocation)
            return
        invocation.return_dbus_error("org.niri_plus.Test.UnknownMethod", "Unsupported fixture call")

    connection.register_object(AGENT_PATH, manager, method_call, None, None)
    connection.register_object(PROBE_PATH, probe, method_call, None, None)

    def owner_changed(_conn, _sender, _path, _interface, _signal, parameters):
        nonlocal unregister_count, owner_loss_count
        name, old_owner, new_owner = parameters.unpack()
        if name.startswith(":") and old_owner and not new_owner and registrations.pop(name, None) is not None:
            unregister_count += 1
            owner_loss_count += 1

    connection.signal_subscribe(
        "org.freedesktop.DBus", "org.freedesktop.DBus", "NameOwnerChanged",
        "/org/freedesktop/DBus", None, Gio.DBusSignalFlags.NONE, owner_changed,
    )
    print("ready", flush=True)
    print(f"pid {os.getpid()}", flush=True)
    try:
        loop.run()
    except KeyboardInterrupt:
        loop.quit()
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: agent_manager_peer.py BUS_ADDRESS")
    raise SystemExit(main(sys.argv[1]))
