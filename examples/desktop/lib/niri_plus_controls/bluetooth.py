"""BlueZ device controls with owned bus, request and discovery lifetimes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import threading
import time

from .model import (
    ActionKind, ActionSpec, Availability, DetailFact, DetailsSnapshot,
    InventorySnapshot, OperationRequest, OperationResult, PendingRef, ResultKind,
    TargetRef, TargetSnapshot, Utility,
)


ADAPTER = "org.bluez.Adapter1"
DEVICE = "org.bluez.Device1"
BATTERY = "org.bluez.Battery1"


class BluetoothError(RuntimeError):
    pass


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class BluezBus:
    """Private client connection; NO_AUTO_START and unique-owner addressing."""

    def __init__(self, connection=None):
        from gi.repository import Gio, GLib
        self.Gio, self.GLib = Gio, GLib
        self.connection = connection
        self.context = GLib.MainContext.new()
        self._calls = {}

    def _connection(self):
        if self.connection is None:
            address = self.Gio.dbus_address_get_for_bus_sync(self.Gio.BusType.SYSTEM, None)
            self.connection = self.Gio.DBusConnection.new_for_address_sync(
                address, self.Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT | self.Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION,
                None, None,
            )
        return self.connection

    def owner(self):
        try:
            result = self._connection().call_sync(
                "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus", "GetNameOwner",
                self.GLib.Variant("(s)", ("org.bluez",)), self.GLib.VariantType.new("(s)"),
                self.Gio.DBusCallFlags.NO_AUTO_START, 3000, None,
            )
            return result.unpack()[0]
        except Exception as error:
            raise BluetoothError("Bluetooth service unavailable; it was not started by this menu") from error

    def call(self, owner, path, interface, method, signature="()", values=()):
        try:
            result = self._connection().call_sync(
                owner, path, interface, method, self.GLib.Variant(signature, values), None,
                self.Gio.DBusCallFlags.NO_AUTO_START, 3000, None,
            )
            return result.unpack() if result else ()
        except Exception as error:
            name = getattr(error, "message", "Bluetooth request failed")
            # BlueZ method errors contain no PIN data; never serialize arguments.
            raise BluetoothError(str(name)[:512]) from error

    def objects(self):
        self.pump()
        owner = self.owner()
        objects = self.call(owner, "/", "org.freedesktop.DBus.ObjectManager", "GetManagedObjects")[0]
        if owner != self.owner():
            raise BluetoothError("Bluetooth service changed during refresh")
        return owner, objects

    def set_power(self, owner, path, desired):
        return self.call(owner, path, "org.freedesktop.DBus.Properties", "Set", "(ssv)",
                         (ADAPTER, "Powered", self.GLib.Variant("b", desired)))

    def set_trust(self, owner, path, desired):
        return self.call(owner, path, "org.freedesktop.DBus.Properties", "Set", "(ssv)",
                         (DEVICE, "Trusted", self.GLib.Variant("b", desired)))

    def pairing_agent(self, owner, path):
        from .bt_agent import PairingAgent
        agent = PairingAgent(self, owner, path)
        agent.register()
        return agent

    def start(self, owner, path, interface, method):
        pending = {"done": False, "error": None, "cancellable": self.Gio.Cancellable()}
        self._calls[id(pending)] = pending

        def finished(connection, result, unused):
            try:
                connection.call_finish(result)
            except Exception as error:
                pending["error"] = str(getattr(error, "message", "Bluetooth request failed"))[:512]
            pending["done"] = True
            self._calls.pop(id(pending), None)

        self.context.push_thread_default()
        try:
            self._connection().call(owner, path, interface, method, None, None,
                                    self.Gio.DBusCallFlags.NO_AUTO_START, 25000,
                                    pending["cancellable"], finished, None)
        finally:
            self.context.pop_thread_default()
        return pending

    def pump(self):
        for _ in range(128):
            if not self.context.pending():
                break
            self.context.iteration(False)

    def stop_waiting(self, pending):
        pending["cancellable"].cancel()

    def close(self):
        for pending in list(self._calls.values()):
            pending["cancellable"].cancel()
        self.pump()
        if self.connection is not None:
            self.connection.close_sync(None)
            self.connection = None


@dataclass
class _Record:
    target: TargetSnapshot
    owner: str
    path: str
    adapter_path: str
    properties: dict


@dataclass
class _Pending:
    ref: PendingRef
    owner: str
    path: str
    native: object
    desired: bool
    deadline: float
    kind: str = "connection"
    agent: object = None
    presented_challenge: object = None


class BluetoothBackend:
    def __init__(self, *, peer=None, clock=time.monotonic, scan_seconds=20):
        self.peer = peer or BluezBus()
        self.clock = clock
        self.scan_seconds = min(30, max(1, scan_seconds))
        self._records = {}
        self._pending = {}
        self._results = {}
        self._generation = 0
        self._discoveries = {}
        self._seen = set()
        self._lock = threading.RLock()
        self._closed = False

    def _observe(self):
        with self._lock:
            owner, objects = self.peer.objects()
            if not isinstance(objects, dict) or len(objects) > 4096:
                raise BluetoothError("Bluetooth inventory is invalid")
            adapters = {path: interfaces[ADAPTER] for path, interfaces in objects.items() if ADAPTER in interfaces}
            records = {}
            for path, properties in adapters.items():
                identity = [owner, path, properties.get("Address")]
                ref = TargetRef("bluetooth-adapter", _digest(identity))
                connected = sorted(
                    str(interfaces[DEVICE].get("Alias") or interfaces[DEVICE].get("Address") or "Device")
                    for interfaces in objects.values() if DEVICE in interfaces
                    and interfaces[DEVICE].get("Adapter") == path and interfaces[DEVICE].get("Connected") is True
                )
                powered = properties.get("Powered")
                title = str(properties.get("Alias") or properties.get("Name") or path.rsplit("/", 1)[-1])
                impact = _digest([owner, path, sorted(
                    p for p, interfaces in objects.items() if DEVICE in interfaces
                    and interfaces[DEVICE].get("Adapter") == path and interfaces[DEVICE].get("Connected") is True
                )])
                state = {"powered": powered if type(powered) is bool else None, "adapter": path.rsplit("/", 1)[-1],
                         "connected_devices": ", ".join(connected) or "None", "impact": impact,
                         "scanning_owned": ref in self._discoveries}
                power_label = "Powered on" if powered is True else "Powered off" if powered is False else "Power unknown"
                summary = f"{state['adapter']} · {power_label} · {len(connected)} connected"
                target = TargetSnapshot(ref, title[:4096], summary, Availability.AVAILABLE if type(powered) is bool else Availability.UNKNOWN,
                                        _digest([identity, state]), status="Adapter", state=state,
                                        filter_terms=(state["adapter"], "adapter", "power"), facts=(
                                            DetailFact("Adapter", path), DetailFact("Address", str(properties.get("Address") or "Unknown")),
                                            DetailFact("Connected devices", state["connected_devices"]),
                                        ))
                records[ref] = _Record(target, owner, path, path, properties)
            for path, interfaces in objects.items():
                properties = interfaces.get(DEVICE)
                if not isinstance(properties, dict):
                    continue
                adapter_path = properties.get("Adapter")
                if adapter_path not in adapters:
                    continue
                identity = [owner, path, adapter_path, properties.get("Address"), properties.get("AddressType")]
                ref = TargetRef("bluetooth-device", _digest(identity))
                paired, connected, trusted = (properties.get(key) if type(properties.get(key)) is bool else None for key in ("Paired", "Connected", "Trusted"))
                own_scan = any(record.owner == owner and record.path == adapter_path for record, _ in self._discoveries.values())
                if own_scan:
                    self._seen.add(ref)
                if paired is False and connected is False and ref not in self._seen:
                    continue
                powered = adapters[adapter_path].get("Powered")
                raw_battery = interfaces.get(BATTERY, {}).get("Percentage")
                battery = int(raw_battery) if connected and type(raw_battery) is int and 0 <= raw_battery <= 100 else None
                title = str(properties.get("Alias") or properties.get("Name") or properties.get("Address") or "Bluetooth device")
                status = "Connected" if connected is True else "Paired" if paired is True else "Not paired" if paired is False else "Pairing state unknown"
                summary = " · ".join([
                    "Paired" if connected is True and paired is True else "Disconnected" if connected is False else "Connection state unknown" if connected is None else "Not paired",
                    f"{battery}% battery" if battery is not None else "Battery unknown",
                ])
                state = {"connected": connected, "paired": paired, "trusted": trusted,
                         "battery_percent": battery, "adapter": adapter_path.rsplit("/", 1)[-1], "powered": powered}
                facts = (
                    DetailFact("Address", str(properties.get("Address") or "Unknown")),
                    DetailFact("Adapter", state["adapter"]), DetailFact("Connection", "Connected" if connected is True else "Disconnected" if connected is False else "Unknown"),
                    DetailFact("Pairing", "Paired" if paired is True else "Not paired" if paired is False else "Unknown"),
                    DetailFact("Trust", "Trusted" if trusted is True else "Not trusted" if trusted is False else "Unknown"),
                    DetailFact("Battery", f"{battery}%" if battery is not None else "Unknown"),
                )
                target = TargetSnapshot(ref, title[:4096], summary,
                                        Availability.UNKNOWN if any(value is None for value in (powered, paired, connected, trusted)) else Availability.AVAILABLE if powered else Availability.UNAVAILABLE,
                                        _digest([identity, state]), status=status, active=connected is True,
                                        filter_terms=(state["adapter"], "paired" if paired else "unpaired", "connected" if connected else "disconnected"),
                                        state=state, facts=facts)
                records[ref] = _Record(target, owner, path, adapter_path, properties)
            self._records = records
            targets = tuple(r.target for r in sorted(records.values(), key=lambda r: (r.target.ref.kind == "bluetooth-adapter", not r.target.active, r.target.title.casefold())))
            return InventorySnapshot(Utility.BLUETOOTH, _digest([t.revision for t in targets]), datetime.now(timezone.utc).isoformat(), targets,
                                     "No Bluetooth adapter" if not adapters else "Pairing, connection and trust are independent. Refresh reads current devices.")

    def snapshot(self, utility=Utility.BLUETOOTH):
        if utility != Utility.BLUETOOTH:
            return InventorySnapshot(Utility.BLUETOOTH, "unavailable", datetime.now(timezone.utc).isoformat(), (), "This adapter owns Bluetooth only")
        try:
            return self._observe()
        except Exception as error:
            self._records = {}
            return InventorySnapshot(Utility.BLUETOOTH, "unavailable", datetime.now(timezone.utc).isoformat(), (), str(error)[:1024] or "Bluetooth unavailable")

    def _record(self, ref):
        self._observe()
        if ref not in self._records:
            raise BluetoothError("Bluetooth device or service changed; refresh and select the current target")
        return self._records[ref]

    def target(self, ref):
        try:
            return self._record(ref).target
        except Exception:
            return None

    def details(self, ref):
        target = self.target(ref)
        return DetailsSnapshot(ref, target.title, target.facts, target.revision) if target else None

    def actions(self, ref):
        try:
            record = self._record(ref)
        except Exception:
            return ()
        state = record.target.state
        if ref.kind == "bluetooth-adapter":
            if type(state["powered"]) is not bool:
                return ()
            desired = not bool(state["powered"])
            actions = [ActionSpec("set-adapter-power", "Turn Bluetooth on" if desired else "Turn Bluetooth off",
                                  ActionKind.OPERATION if desired else ActionKind.CONFIRM,
                                  {"desired_on": desired, "impact": state["impact"]},
                                  confirmation="" if desired else f"Turn off {state['adapter']}? Connected devices: {state['connected_devices']}. Pairings stay.")]
            if state["powered"]:
                actions.append(ActionSpec("start-discovery", "Find devices", ActionKind.OPERATION))
            return tuple(actions)
        if record.target.availability != Availability.AVAILABLE:
            return ()
        actions = []
        if state["connected"] or state["paired"]:
            desired = not state["connected"]
            actions.append(ActionSpec("set-device-connection", "Connect" if desired else "Disconnect",
                               ActionKind.OPERATION if desired else ActionKind.CONFIRM,
                               {"desired_connected": desired},
                               confirmation="" if desired else f"Disconnect {record.target.title} on {state['adapter']}? Pairing and trust stay."))
        if state["paired"] is False:
            actions.append(ActionSpec("pair-device", "Pair", ActionKind.CONFIRM,
                                      confirmation=f"Pair {record.target.title} on {state['adapter']}? Check its address in Details. Pairing may connect it; trust stays unchanged."))
        elif state["paired"] is True:
            desired = not state["trusted"]
            actions.append(ActionSpec("set-device-trust", "Trust device" if desired else "Stop trusting device", ActionKind.CONFIRM,
                                      {"desired_trusted": desired},
                                      confirmation=f"{'Trust' if desired else 'Stop trusting'} {record.target.title} on {state['adapter']}? Trust permits future connections without asking; pairing and connection stay unchanged."))
        return tuple(actions)

    def _stop_discovery(self, ref):
        with self._lock:
            entry = self._discoveries.pop(ref, None)
            if not entry:
                return
            record, timer = entry
            timer.cancel()
            try:
                if self.peer.owner() == record.owner:
                    self.peer.call(record.owner, record.path, ADAPTER, "StopDiscovery")
            except Exception:
                pass

    def execute(self, request: OperationRequest):
        if self._closed:
            return OperationResult(ResultKind.UNAVAILABLE, "Bluetooth controls are closed")
        signature = _digest([request.invocation_id, request.target.to_json(), request.action_id, dict(request.parameters)])
        previous = self._results.get(request.request_id)
        if previous:
            return previous[1] if previous[0] == signature else OperationResult(ResultKind.ERROR, "Request identity was reused for another operation")
        try:
            record = self._record(request.target)
            state = record.target.state
            if request.action_id == "set-adapter-power" and request.target.kind == "bluetooth-adapter":
                desired = request.parameters.get("desired_on")
                if type(desired) is not bool or type(state["powered"]) is not bool:
                    raise BluetoothError("Bluetooth power requires an explicit desired state")
                if not desired and request.parameters.get("impact") != state["impact"]:
                    raise BluetoothError("Connected devices changed; review the updated power-off confirmation")
                self.peer.set_power(record.owner, record.path, desired)
                observed = self._record(request.target).target
                if observed.state["powered"] is not desired:
                    raise BluetoothError("Power state is not yet confirmed; refresh. Hardware blocks remain owned by the system.")
                result = OperationResult(ResultKind.COMPLETE, observed.summary, observed)
            elif request.action_id == "start-discovery" and request.target.kind == "bluetooth-adapter":
                if not state["powered"]:
                    raise BluetoothError("Turn on the adapter before discovery")
                with self._lock:
                    if request.target not in self._discoveries:
                        self.peer.call(record.owner, record.path, ADAPTER, "StartDiscovery")
                        timer = threading.Timer(self.scan_seconds, self._stop_discovery, args=(request.target,))
                        timer.daemon = True
                        self._discoveries[request.target] = (record, timer)
                        timer.start()
                result = OperationResult(ResultKind.COMPLETE, f"Scanning on {state['adapter']} for at most {self.scan_seconds}s. Back/Refresh shows discovered devices.", record.target)
            elif request.action_id == "set-device-connection" and request.target.kind == "bluetooth-device":
                desired = request.parameters.get("desired_connected")
                if type(desired) is not bool or state["powered"] is not True or type(state["connected"]) is not bool or type(state["paired"]) is not bool:
                    raise BluetoothError("Connection requires an explicit intent and a powered adapter")
                if state["connected"] == desired:
                    result = OperationResult(ResultKind.COMPLETE, record.target.summary, record.target)
                else:
                    if desired and not state["paired"]:
                        raise BluetoothError("Pair the device before connecting")
                    self._generation += 1
                    pending = PendingRef(request.request_id, request.target, self._generation)
                    native = self.peer.start(record.owner, record.path, DEVICE, "Connect" if desired else "Disconnect")
                    self._pending[pending] = _Pending(pending, record.owner, record.path, native, desired, self.clock() + 25)
                    result = OperationResult(ResultKind.PENDING, "Connecting" if desired else "Disconnecting", record.target, pending)
            elif request.action_id == "pair-device" and request.target.kind == "bluetooth-device":
                if state["powered"] is not True or state["paired"] is not False:
                    raise BluetoothError("Pairing requires a freshly discovered unpaired device on a powered adapter")
                if any(entry.kind == "pairing" for entry in self._pending.values()):
                    raise BluetoothError("Another owned pairing is still pending")
                agent = self.peer.pairing_agent(record.owner, record.path)
                try:
                    native = self.peer.start(record.owner, record.path, DEVICE, "Pair")
                except Exception:
                    agent.close()
                    raise
                self._generation += 1
                pending = PendingRef(request.request_id, request.target, self._generation)
                self._pending[pending] = _Pending(pending, record.owner, record.path, native, True,
                                                  self.clock() + 120, "pairing", agent)
                result = OperationResult(ResultKind.PENDING, "Pairing with the selected device. Trust is unchanged.", record.target, pending)
            elif request.action_id == "set-device-trust" and request.target.kind == "bluetooth-device":
                desired = request.parameters.get("desired_trusted")
                if type(desired) is not bool or state["paired"] is not True:
                    raise BluetoothError("Trust requires an explicit choice for a paired device")
                if request.expected_revision != record.target.revision:
                    raise BluetoothError("Device state changed; review the trust confirmation again")
                self.peer.set_trust(record.owner, record.path, desired)
                observed = self._record(request.target).target
                if observed.state["trusted"] is not desired:
                    raise BluetoothError("Trust state is not yet confirmed; refresh")
                result = OperationResult(ResultKind.COMPLETE, "Observed the requested trust state. Pairing and connection were not changed.", observed)
            else:
                raise BluetoothError("Unsupported Bluetooth action")
        except Exception as error:
            result = OperationResult(ResultKind.ERROR, str(error)[:1024] or "Bluetooth request failed")
        self._results[request.request_id] = (signature, result)
        if len(self._results) > 128:
            self._results.pop(next(iter(self._results)))
        return result

    def refresh(self, pending):
        entry = self._pending.get(pending)
        if entry is None:
            return OperationResult(ResultKind.ERROR, "No matching owned Bluetooth request")
        try:
            try:
                record = self._record(pending.target)
            except BluetoothError:
                # LE pairing may resolve a random address to its identity
                # address. Only a successful reply to this exact owned Pair
                # call can establish that transition on the same native path.
                record = next((item for item in self._records.values()
                               if entry.kind == "pairing" and entry.native.get("done")
                               and not entry.native.get("error") and item.owner == entry.owner
                               and item.path == entry.path and item.target.state.get("paired") is True), None)
                if record is None:
                    raise
            if record.owner != entry.owner or record.path != entry.path:
                raise BluetoothError("Bluetooth target changed while waiting")
            if entry.agent and entry.agent.error:
                raise BluetoothError(entry.agent.error)
            if self.clock() >= entry.deadline:
                self._finish_pending(pending, entry, cancel_pairing=True)
                return OperationResult(ResultKind.ERROR, "Bluetooth status unknown after the bounded wait; refresh", record.target)
            if entry.native.get("done"):
                if entry.native.get("error"):
                    raise BluetoothError(str(entry.native["error"]))
                observed = record.target.state["paired"] if entry.kind == "pairing" else record.target.state["connected"]
                if observed == entry.desired:
                    self._finish_pending(pending, entry)
                    return OperationResult(ResultKind.COMPLETE, record.target.summary, record.target)
            if entry.agent and entry.agent.challenge:
                entry.presented_challenge = entry.agent.challenge
                method, _invocation, prompt = entry.agent.challenge
                if method in {"RequestPinCode", "RequestPasskey"}:
                    return OperationResult(ResultKind.NEEDS_SECRET, "Pairing input for the pinned Bluetooth device", record.target, pending, secret_prompt=prompt)
                return OperationResult(ResultKind.NEEDS_CONFIRMATION, "Confirm pairing with the pinned Bluetooth device", record.target, pending, confirmation_prompt=prompt)
            return OperationResult(ResultKind.PENDING, "Waiting for observed Bluetooth state", record.target, pending,
                                   display_prompt=entry.agent.display if entry.agent else "")
        except Exception as error:
            self._finish_pending(pending, entry)
            return OperationResult(ResultKind.ERROR, str(error)[:1024] or "Bluetooth request unavailable")

    def _finish_pending(self, pending, entry, *, cancel_pairing=False):
        self._pending.pop(pending, None)
        if cancel_pairing and entry.kind == "pairing" and not entry.native.get("done"):
            try:
                record = self._record(pending.target)
                if record.owner == entry.owner and record.path == entry.path and record.target.state["paired"] is False:
                    self.peer.call(entry.owner, entry.path, DEVICE, "CancelPairing")
            except Exception:
                pass
        if entry.agent:
            entry.agent.close()
        self.peer.stop_waiting(entry.native)

    def cancel(self, pending):
        entry = self._pending.get(pending)
        if entry is None:
            return OperationResult(ResultKind.ERROR, "No matching owned Bluetooth request")
        self._finish_pending(pending, entry, cancel_pairing=True)
        if entry.kind == "pairing":
            return OperationResult(ResultKind.CANCELLED, "Stopped this owned pairing attempt. Refresh to observe the device; no pairing was removed and trust was not changed.")
        # BlueZ Connect has no NM-style per-activation handle. Cancelling the
        # client wait must not disconnect a connection another actor completed.
        return OperationResult(ResultKind.CANCELLED, "Stopped waiting. Bluetooth may still connect or disconnect; refresh to observe the result.")

    def provide_secret(self, pending, secret_stream):
        entry = self._pending.get(pending)
        try:
            if entry is None or entry.agent is None:
                raise BluetoothError("No matching owned pairing input")
            if self.clock() >= entry.deadline:
                raise BluetoothError("Pairing input expired")
            self._record(pending.target)
            if entry.agent.challenge is not entry.presented_challenge:
                raise BluetoothError("Pairing input changed before submission")
            entry.agent.provide_secret(secret_stream)
            return self.refresh(pending)
        except Exception:
            if entry:
                self._finish_pending(pending, entry, cancel_pairing=True)
            return OperationResult(ResultKind.ERROR, "Bluetooth pairing input was invalid or no longer requested")

    def respond_confirmation(self, pending, accepted):
        entry = self._pending.get(pending)
        try:
            if entry is None or entry.agent is None:
                raise BluetoothError("No matching owned pairing confirmation")
            if self.clock() >= entry.deadline:
                raise BluetoothError("Pairing confirmation expired")
            self._record(pending.target)
            if entry.agent.challenge is not entry.presented_challenge:
                raise BluetoothError("Pairing confirmation changed before submission")
            entry.agent.confirm(accepted)
            if not accepted:
                return self.cancel(pending)
            return self.refresh(pending)
        except Exception:
            if entry:
                self._finish_pending(pending, entry, cancel_pairing=True)
            return OperationResult(ResultKind.ERROR, "Bluetooth pairing confirmation is no longer available")

    def close(self):
        if self._closed:
            return
        self._closed = True
        for ref in list(self._discoveries):
            self._stop_discovery(ref)
        for pending, entry in list(self._pending.items()):
            self._finish_pending(pending, entry, cancel_pairing=True)
        self._pending.clear()
        self.peer.close()
