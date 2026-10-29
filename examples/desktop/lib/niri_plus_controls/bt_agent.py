"""Temporary BlueZ Agent1 for one explicitly requested device pairing.

Authentication values stay in this object and visible controller frames. They
are never placed in target facts, continuation metadata, files or diagnostics.
"""

import uuid


AGENT_INTERFACE = "org.bluez.Agent1"
MANAGER_INTERFACE = "org.bluez.AgentManager1"
XML = """<node><interface name="org.bluez.Agent1">
 <method name="Release"/>
 <method name="Cancel"/>
 <method name="RequestPinCode"><arg type="o" direction="in"/><arg type="s" direction="out"/></method>
 <method name="RequestPasskey"><arg type="o" direction="in"/><arg type="u" direction="out"/></method>
 <method name="DisplayPinCode"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
 <method name="DisplayPasskey"><arg type="o" direction="in"/><arg type="u" direction="in"/><arg type="q" direction="in"/></method>
 <method name="RequestConfirmation"><arg type="o" direction="in"/><arg type="u" direction="in"/></method>
 <method name="RequestAuthorization"><arg type="o" direction="in"/></method>
 <method name="AuthorizeService"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
</interface></node>"""


class PairingAgent:
    def __init__(self, peer, owner, device_path):
        self.peer, self.owner, self.device_path = peer, owner, device_path
        self.path = "/org/niri_plus/Pairing/" + uuid.uuid4().hex
        self.challenge = None
        self.display = ""
        self.error = ""
        self._registered = False
        self._object_id = None
        self._closed = False

    def register(self):
        GLib = self.peer.GLib
        node = self.peer.Gio.DBusNodeInfo.new_for_xml(XML)
        self.peer.context.push_thread_default()
        try:
            self._object_id = self.peer._connection().register_object(
                self.path, node.interfaces[0], self._method, None, None)
        finally:
            self.peer.context.pop_thread_default()
        try:
            self.peer.call(self.owner, "/org/bluez", MANAGER_INTERFACE, "RegisterAgent", "(os)",
                           (self.path, "KeyboardDisplay"))
            self._registered = True
        except Exception:
            self.close()
            raise

    @staticmethod
    def _reject(invocation, message="Pairing request is outside this operation"):
        invocation.return_dbus_error("org.bluez.Error.Rejected", message)

    def _method(self, _connection, sender, _path, _interface, method, parameters, invocation):
        GLib = self.peer.GLib
        if self._closed or sender != self.owner:
            return self._reject(invocation)
        values = parameters.unpack()
        if method in {"Release", "Cancel"}:
            self._discard_challenge()
            self.display = ""
            if method == "Release":
                self._registered = False
                self.error = "Bluetooth pairing agent was released; refresh before retrying"
            invocation.return_value(GLib.Variant("()", ()))
            return
        if not values or values[0] != self.device_path:
            return self._reject(invocation)
        if method in {"DisplayPinCode", "DisplayPasskey"}:
            if method == "DisplayPinCode":
                code = values[1]
                if not isinstance(code, str) or not code.isascii() or not code.isdigit() or len(code) != 6:
                    return self._reject(invocation, "Unsupported displayed PIN format")
                self.display = f"Type {code} on the Bluetooth device, then press Enter there."
            else:
                code, entered = values[1:]
                if not 0 <= code <= 999999 or not 0 <= entered <= 6:
                    return self._reject(invocation, "Unsupported displayed passkey format")
                self.display = f"Type {code:06d} on the Bluetooth device, then press Enter there. {entered}/6 digits entered."
            invocation.return_value(GLib.Variant("()", ()))
            return
        if method not in {"RequestPinCode", "RequestPasskey", "RequestConfirmation", "RequestAuthorization", "AuthorizeService"}:
            return self._reject(invocation, "Unsupported pairing interaction")
        if self.challenge is not None:
            return self._reject(invocation, "A pairing interaction is already pending")
        if method == "RequestConfirmation":
            if not 0 <= values[1] <= 999999:
                return self._reject(invocation, "Invalid pairing confirmation")
            prompt = f"Does this code match the Bluetooth device? {values[1]:06d}"
        elif method == "RequestAuthorization":
            prompt = "Authorize pairing with this explicitly selected Bluetooth device?"
        elif method == "AuthorizeService":
            prompt = "Authorize the requested service on this selected Bluetooth device?"
        elif method == "RequestPasskey":
            prompt = "Bluetooth passkey (up to 6 digits)"
        else:
            prompt = "Bluetooth PIN (1–16 characters)"
        self.challenge = (method, invocation, prompt)

    def _discard_challenge(self):
        challenge, self.challenge = self.challenge, None
        if challenge:
            challenge[1].return_dbus_error("org.bluez.Error.Canceled", "Pairing interaction cancelled")

    def provide_secret(self, stream):
        if not self.challenge or self.challenge[0] not in {"RequestPinCode", "RequestPasskey"}:
            raise ValueError("No owned pairing input is pending")
        raw = bytearray(stream.read(257))
        try:
            if not 1 <= len(raw) <= 256:
                raise ValueError("Pairing input is empty or too long")
            value = raw.decode("utf-8")
            method, invocation, _prompt = self.challenge
            if method == "RequestPasskey":
                if not value.isascii() or not value.isdigit() or not 1 <= len(value) <= 6:
                    raise ValueError("A passkey must contain 1–6 digits")
                result = self.peer.GLib.Variant("(u)", (int(value),))
            else:
                if not 1 <= len(value) <= 16 or any(ord(char) < 32 or ord(char) == 127 for char in value):
                    raise ValueError("A PIN must contain 1–16 printable characters")
                result = self.peer.GLib.Variant("(s)", (value,))
            self.challenge = None
            invocation.return_value(result)
        finally:
            raw[:] = b"\x00" * len(raw)

    def confirm(self, accepted):
        if type(accepted) is not bool or not self.challenge or self.challenge[0] not in {
                "RequestConfirmation", "RequestAuthorization", "AuthorizeService"}:
            raise ValueError("No owned pairing confirmation is pending")
        _method, invocation, _prompt = self.challenge
        self.challenge = None
        if accepted:
            invocation.return_value(self.peer.GLib.Variant("()", ()))
        else:
            self._reject(invocation, "Pairing was declined")

    def close(self):
        if self._closed:
            return
        self._closed = True
        self._discard_challenge()
        self.display = ""
        if self._registered:
            try:
                if self.peer.owner() == self.owner:
                    self.peer.call(self.owner, "/org/bluez", MANAGER_INTERFACE, "UnregisterAgent", "(o)", (self.path,))
            except Exception:
                pass
            self._registered = False
        if self._object_id is not None:
            self.peer._connection().unregister_object(self._object_id)
            self._object_id = None
