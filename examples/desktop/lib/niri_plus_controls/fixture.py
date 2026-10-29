"""Inert, stateful fixture backend used by unit and private-Xvfb proofs."""

from __future__ import annotations

from dataclasses import dataclass, field
import datetime as dt
import io
import uuid
from typing import BinaryIO, Mapping, Sequence

from .model import (
    ActionKind,
    ActionSpec,
    Availability,
    ControlsBackend,
    DetailFact,
    DetailsSnapshot,
    InventorySnapshot,
    OperationRequest,
    OperationResult,
    PendingRef,
    ResultKind,
    TargetRef,
    TargetSnapshot,
    Utility,
)


@dataclass(slots=True)
class _Record:
    ref: TargetRef
    title: str
    kind: str
    state: dict[str, object]
    availability: Availability = Availability.AVAILABLE
    status: str = ""
    details: dict[str, str] = field(default_factory=dict)
    filter_terms: tuple[str, ...] = ()
    revision: int = 1


@dataclass(slots=True)
class _Pending:
    ref: PendingRef
    utility: Utility
    persistence: str
    secret_received: bool = False
    refresh_count: int = 0


class FixtureBackend(ControlsBackend):
    """A pure in-memory backend. It never contacts host services or devices."""

    def __init__(self, utility: Utility | str, *, complete_after_refresh: int = 1):
        self.utility = Utility(utility)
        self.complete_after_refresh = max(1, int(complete_after_refresh))
        self._records = self._seed(self.utility)
        self._pending: dict[str, _Pending] = {}
        self.events: list[dict[str, object]] = []
        self._closed = False

    @staticmethod
    def _seed(utility: Utility) -> dict[TargetRef, _Record]:
        if utility == Utility.NETWORK:
            records = (
                _Record(
                    TargetRef("connection", "nm:uuid:home-001"),
                    "Home",
                    "connection",
                    {"connected": True, "adapter": "wlan0", "security": "WPA2 Personal", "ssid": "Home"},
                    status="Connected",
                    details={"Adapter": "wlan0", "Security": "WPA2 Personal", "Profile": "Home"},
                    filter_terms=("wifi", "wlan0", "connected"),
                ),
                _Record(
                    TargetRef("access-point", "nm:ap:studio:wlan0:01"),
                    "Studio",
                    "access-point",
                    {"connected": False, "adapter": "wlan0", "security": "WPA3 Personal", "signal": 76, "saved": True},
                    status="Saved · Available",
                    details={"Adapter": "wlan0", "Security": "WPA3 Personal", "Signal": "76%", "Saved profile": "Studio"},
                    filter_terms=("wlan0", "wpa3", "saved", "76%"),
                ),
                _Record(
                    TargetRef("access-point", "nm:ap:studio:wlan1:02"),
                    "Studio",
                    "access-point",
                    {"connected": False, "adapter": "wlan1", "security": "WPA3 Personal", "signal": 42, "saved": False},
                    status="Available",
                    details={"Adapter": "wlan1", "Security": "WPA3 Personal", "Signal": "42%"},
                    filter_terms=("wlan1", "wpa3", "42%"),
                ),
                _Record(
                    TargetRef("profile", "nm:uuid:guest-unavailable"),
                    "Guest",
                    "profile",
                    {"connected": False, "adapter": "wlan0", "security": "Open", "saved": True},
                    Availability.UNAVAILABLE,
                    status="Saved · Adapter unavailable",
                    details={"Adapter": "wlan0", "Security": "Open", "Profile": "Guest", "Availability": "Unavailable"},
                    filter_terms=("saved", "unavailable"),
                ),
                _Record(
                    TargetRef("radio", "nm:radio:wifi"),
                    "Wi-Fi radio",
                    "radio",
                    {"powered": True, "scope": "global", "affected": "wlan0, wlan1"},
                    status="Global Wi-Fi on",
                    details={"Scope": "Global Wi-Fi radio", "Affected interfaces": "wlan0, wlan1", "Ethernet": "Unaffected"},
                    filter_terms=("radio", "global", "wifi", "wlan0", "wlan1"),
                ),
                _Record(
                    TargetRef("device", "fixture:network:cjk-01"),
                    "路由器 <Studio> — Example Long Adapter Label 0123456789 ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                    "device",
                    {"connected": False, "adapter": "wlan-extra-long-device-name", "security": "WPA3 Personal", "signal": 63},
                    status="Available",
                    details={"Adapter": "wlan-extra-long-device-name", "Security": "WPA3 Personal", "Signal": "63%"},
                    filter_terms=("cjk", "long label", "wlan-extra-long-device-name"),
                ),
            )
        elif utility == Utility.AUDIO:
            records = (
                _Record(
                    TargetRef("audio-output", "pw:device:usb-speakers:71"),
                    "USB speakers",
                    "audio-output",
                    {"direction": "output", "volume_percent": 45, "muted": False, "is_default": True, "available": True},
                    status="Default output · 45% · Unmuted",
                    details={"Direction": "Output", "Volume": "45%", "Mute": "Unmuted", "Default": "Yes"},
                    filter_terms=("output", "default", "usb"),
                ),
                _Record(
                    TargetRef("audio-output", "pw:device:headphones:72"),
                    "Headphones",
                    "audio-output",
                    {"direction": "output", "volume_percent": 30, "muted": False, "is_default": False, "available": True},
                    status="Output · 30% · Unmuted",
                    details={"Direction": "Output", "Volume": "30%", "Mute": "Unmuted", "Default": "No"},
                    filter_terms=("output", "headset"),
                ),
                _Record(
                    TargetRef("audio-input", "pw:device:usb-microphone:73"),
                    "USB microphone",
                    "audio-input",
                    {"direction": "input", "volume_percent": 65, "muted": True, "is_default": True, "available": True},
                    status="Default input · 65% · Muted",
                    details={"Direction": "Input", "Volume": "65%", "Mute": "Muted", "Default": "Yes"},
                    filter_terms=("input", "microphone", "default"),
                ),
                _Record(
                    TargetRef("audio-output", "pw:device:hdmi:74"),
                    "HDMI / DisplayPort",
                    "audio-output",
                    {"direction": "output", "volume_percent": None, "muted": False, "is_default": False, "available": False},
                    Availability.UNAVAILABLE,
                    status="Unavailable · Volume unknown",
                    details={"Direction": "Output", "Availability": "Unavailable", "Volume": "Unknown"},
                    filter_terms=("hdmi", "unavailable"),
                ),
            )
        else:
            records = (
                _Record(
                    TargetRef("bluetooth-device", "bluez:/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF"),
                    "Headphones",
                    "bluetooth-device",
                    {"paired": True, "trusted": True, "connected": True, "battery_percent": None, "adapter": "hci0"},
                    status="Connected · Paired · Battery unknown",
                    details={"Adapter": "hci0", "Paired": "Yes", "Trusted": "Yes", "Connected": "Yes", "Battery": "Unknown"},
                    filter_terms=("paired", "connected", "hci0"),
                ),
                _Record(
                    TargetRef("bluetooth-device", "bluez:/org/bluez/hci0/dev_11_22_33_44_55_66"),
                    "BT speaker",
                    "bluetooth-device",
                    {"paired": True, "trusted": False, "connected": False, "battery_percent": 54, "adapter": "hci0"},
                    status="Paired · Disconnected · Battery 54%",
                    details={"Adapter": "hci0", "Paired": "Yes", "Trusted": "No", "Connected": "No", "Battery": "54%"},
                    filter_terms=("paired", "disconnected", "hci0"),
                ),
                _Record(
                    TargetRef("bluetooth-adapter", "bluez:/org/bluez/hci0"),
                    "Bluetooth adapter hci0",
                    "bluetooth-adapter",
                    {"powered": True, "connected_devices": "Headphones"},
                    status="Powered on · 1 connected device",
                    details={"Adapter": "hci0", "Powered": "Yes", "Connected devices": "Headphones"},
                    filter_terms=("adapter", "power", "hci0"),
                ),
            )
        return {record.ref: record for record in records}

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("fixture backend is closed")

    @staticmethod
    def _revision(record: _Record) -> str:
        return f"fixture-{record.revision}"

    def _summary(self, record: _Record) -> str:
        state = record.state
        if record.kind == "connection":
            return f"Wi-Fi · {state['adapter']} · {state['security']}"
        if record.kind == "access-point":
            saved = "Saved · " if state.get("saved") else ""
            suffix = "Connected" if state.get("connected") else f"{state['signal']}%"
            return f"{saved}{state['adapter']} · {state['security']} · {suffix}"
        if record.kind == "profile":
            return f"Saved profile · {state['adapter']} · {state['security']}"
        if record.kind == "radio":
            return "Global Wi-Fi radio · Ethernet unaffected"
        if record.kind.startswith("audio-"):
            direction = str(state["direction"]).title()
            volume = state.get("volume_percent")
            volume_label = "Volume unknown" if volume is None else f"{volume}%"
            mute = "Muted" if state.get("muted") else "Unmuted"
            default = "Default " + direction.lower() if state.get("is_default") else direction
            return f"{default} · {volume_label} · {mute}"
        if record.kind == "bluetooth-device":
            connection = "Connected" if state.get("connected") else "Disconnected"
            paired = "Paired" if state.get("paired") else "Not paired"
            battery = state.get("battery_percent")
            battery_label = "Battery unknown" if battery is None else f"Battery {battery}%"
            return f"{paired} · {connection} · {battery_label}"
        if record.kind == "bluetooth-adapter":
            return "Powered on" if state.get("powered") else "Powered off"
        return record.status or "State unknown"

    def _status(self, record: _Record) -> str:
        if record.kind == "connection":
            return "Connected" if record.state.get("connected") else "Disconnected"
        if record.kind == "access-point":
            return "Connected" if record.state.get("connected") else record.status
        if record.kind == "radio":
            return "Global Wi-Fi on" if record.state.get("powered") else "Global Wi-Fi off"
        if record.kind.startswith("audio-"):
            direction = str(record.state["direction"]).title()
            default = f"Default {direction.lower()} · " if record.state.get("is_default") else f"{direction} · "
            volume = record.state.get("volume_percent")
            volume_text = "Volume unknown" if volume is None else f"{volume}%"
            mute_text = "Muted" if record.state.get("muted") else "Unmuted"
            return default + volume_text + " · " + mute_text
        if record.kind == "bluetooth-device":
            return self._summary(record)
        if record.kind == "bluetooth-adapter":
            return self._summary(record)
        return record.status or "State unknown"

    def _snapshot_target(self, record: _Record) -> TargetSnapshot:
        facts = tuple(DetailFact(label, value) for label, value in record.details.items())
        return TargetSnapshot(
            ref=record.ref,
            title=record.title,
            summary=self._summary(record),
            availability=record.availability,
            revision=self._revision(record),
            status=self._status(record),
            active=bool(
                record.state.get("connected")
                or (record.kind.startswith("audio-") and record.state.get("is_default"))
            ),
            filter_terms=record.filter_terms,
            facts=facts,
            state=record.state.copy(),
        )

    def snapshot(self, utility: Utility) -> InventorySnapshot:
        self._ensure_open()
        if Utility(utility) != self.utility:
            raise ValueError("fixture backend utility mismatch")
        targets = tuple(self._snapshot_target(item) for item in self._records.values())
        return InventorySnapshot(
            utility=self.utility,
            revision="fixture-inventory-" + str(sum(item.revision for item in self._records.values())),
            observed_at=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            targets=targets,
        )

    def target(self, ref: TargetRef) -> TargetSnapshot | None:
        self._ensure_open()
        record = self._records.get(ref)
        return self._snapshot_target(record) if record else None

    def details(self, ref: TargetRef) -> DetailsSnapshot | None:
        self._ensure_open()
        record = self._records.get(ref)
        if not record:
            return None
        facts = tuple(DetailFact(label, value) for label, value in record.details.items())
        if record.availability != Availability.AVAILABLE and not any(f.label == "Availability" for f in facts):
            facts += (DetailFact("Availability", "Unavailable"),)
        return DetailsSnapshot(ref, record.title, facts, self._revision(record))

    def actions(self, ref: TargetRef) -> Sequence[ActionSpec]:
        self._ensure_open()
        record = self._records.get(ref)
        if not record:
            return ()
        if record.availability != Availability.AVAILABLE:
            return ()
        if self.utility == Utility.NETWORK:
            if record.kind == "connection" and record.state.get("connected"):
                return (
                    ActionSpec(
                        "disconnect",
                        "Disconnect",
                        ActionKind.CONFIRM,
                        confirmation=f"Disconnect {record.title} on {record.state['adapter']}?",
                    ),
                )
            if record.kind == "radio":
                action_label = "Turn Wi-Fi off" if record.state.get("powered") else "Turn Wi-Fi on"
                return (
                    ActionSpec(
                        "set-wifi-radio",
                        action_label,
                        ActionKind.CONFIRM if record.state.get("powered") else ActionKind.OPERATION,
                        parameters={"desired_on": not bool(record.state.get("powered"))},
                        confirmation="Turn off the global Wi-Fi radio on wlan0 and wlan1? Ethernet remains enabled.",
                    ),
                )
            if record.kind in {"access-point", "device"}:
                return (
                    ActionSpec(
                        "connect",
                        "Connect",
                        ActionKind.OPERATION,
                    ),
                )
            return (
                ActionSpec("advanced-settings", "Advanced settings", ActionKind.OPERATION),
            )
        if self.utility == Utility.AUDIO:
            direction = str(record.state.get("direction", "output"))
            actions = []
            if not record.state.get("is_default"):
                actions.append(
                    ActionSpec(
                        "set-default",
                        f"Set this {direction} as default",
                        ActionKind.OPERATION,
                        parameters={"direction": direction},
                    )
                )
            if type(record.state.get("volume_percent")) is int:
                actions.extend(
                    (
                        ActionSpec("volume-up", "Volume +5%", ActionKind.OPERATION),
                        ActionSpec("volume-down", "Volume −5%", ActionKind.OPERATION),
                    )
                )
            actions.append(
                ActionSpec(
                    "mute",
                    "Unmute" if record.state.get("muted") else "Mute",
                    ActionKind.OPERATION,
                    parameters={
                        "direction": direction,
                        "desired_muted": not bool(record.state.get("muted")),
                    },
                )
            )
            return tuple(actions)
        if record.kind == "bluetooth-adapter":
            powered = bool(record.state.get("powered"))
            return (
                ActionSpec(
                    "set-adapter-power",
                    "Turn Bluetooth off" if powered else "Turn Bluetooth on",
                    ActionKind.CONFIRM if powered else ActionKind.OPERATION,
                    parameters={"desired_on": not powered},
                    confirmation="Turn off adapter hci0? Headphones will disconnect; pairings stay.",
                ),
            )
        connected = bool(record.state.get("connected"))
        return (
            ActionSpec(
                "set-device-connection",
                "Disconnect" if connected else "Connect",
                ActionKind.OPERATION,
                parameters={"desired_connected": not connected},
            ),
        )

    def execute(self, request: OperationRequest) -> OperationResult:
        self._ensure_open()
        record = self._records.get(request.target)
        if record is None:
            return OperationResult(ResultKind.UNAVAILABLE, "Target no longer exists")
        if record.availability != Availability.AVAILABLE:
            return OperationResult(ResultKind.UNAVAILABLE, "Target is unavailable")
        action = request.action_id
        parameters = dict(request.parameters)
        self.events.append(
            {
                "event": "execute",
                "utility": self.utility.value,
                "target": request.target.stable_id,
                "action": action,
                "parameters": parameters,
            }
        )
        if action in {"disconnect", "connect", "set-wifi-radio", "set-device-connection", "set-adapter-power"} and request.expected_revision != self._revision(record):
            return OperationResult(ResultKind.UNAVAILABLE, "Target state changed; refresh and review the action")
        if action in {"volume-up", "volume-down"}:
            volume = record.state.get("volume_percent")
            if type(volume) is not int:
                return OperationResult(ResultKind.UNAVAILABLE, "Volume is unknown for this device")
            direction = 5 if action == "volume-up" else -5
            updated = min(100, max(0, volume + direction))
            record.state["volume_percent"] = updated
            record.details["Volume"] = f"{updated}%"
            self._bump(record)
            return OperationResult(ResultKind.COMPLETE, f"Volume {updated}%", self._snapshot_target(record))
        if action == "mute":
            desired = parameters.get("desired_muted")
            if type(desired) is not bool:
                return OperationResult(ResultKind.ERROR, "Mute action has no explicit desired state")
            record.state["muted"] = desired
            record.details["Mute"] = "Muted" if desired else "Unmuted"
            self._bump(record)
            return OperationResult(ResultKind.COMPLETE, record.details["Mute"], self._snapshot_target(record))
        if action == "set-default":
            direction = parameters.get("direction")
            if direction not in {"input", "output"}:
                return OperationResult(ResultKind.ERROR, "Default action has an invalid direction")
            for other in self._records.values():
                if other.kind.startswith("audio-") and other.state.get("direction") == direction:
                    value = other is record
                    if other.state.get("is_default") != value:
                        other.state["is_default"] = value
                        other.details["Default"] = "Yes" if value else "No"
                        self._bump(other)
            return OperationResult(ResultKind.COMPLETE, "Default device updated", self._snapshot_target(record))
        if action == "disconnect":
            if record.kind != "connection" or not record.state.get("connected"):
                return OperationResult(ResultKind.UNAVAILABLE, "Connection is no longer active")
            record.state["connected"] = False
            self._bump(record)
            return OperationResult(ResultKind.COMPLETE, f"Disconnected {record.title} on {record.state['adapter']}", self._snapshot_target(record))
        if action == "set-wifi-radio":
            desired = parameters.get("desired_on")
            if type(desired) is not bool:
                return OperationResult(ResultKind.ERROR, "Wi-Fi radio action has no explicit desired state")
            record.state["powered"] = desired
            for other in self._records.values():
                if other.kind == "radio":
                    self._bump(other)
            return OperationResult(ResultKind.COMPLETE, "Global Wi-Fi radio updated", self._snapshot_target(record))
        if action == "connect":
            persistence = parameters.get("persistence")
            if not bool(record.state.get("saved")) and persistence not in {"remember", "once"}:
                return OperationResult(ResultKind.ERROR, "Choose remember or once before connecting")
            if bool(record.state.get("saved")):
                persistence = "existing"
            pending = PendingRef(request.request_id, record.ref, record.revision)
            self._pending[pending.request_id] = _Pending(pending, self.utility, persistence)
            return OperationResult(
                ResultKind.NEEDS_SECRET,
                "Password entry is required",
                target=self._snapshot_target(record),
                pending=pending,
                secret_prompt=f"Password for {record.title}",
            )
        if action == "set-device-connection":
            desired = parameters.get("desired_connected")
            if type(desired) is not bool:
                return OperationResult(ResultKind.ERROR, "Bluetooth action has no explicit desired state")
            record.state["connected"] = desired
            self._bump(record)
            return OperationResult(ResultKind.COMPLETE, "Bluetooth connection state updated", self._snapshot_target(record))
        if action == "set-adapter-power":
            desired = parameters.get("desired_on")
            if type(desired) is not bool:
                return OperationResult(ResultKind.ERROR, "Bluetooth power action has no explicit desired state")
            record.state["powered"] = desired
            self._bump(record)
            return OperationResult(ResultKind.COMPLETE, "Bluetooth adapter power updated", self._snapshot_target(record))
        if action == "advanced-settings":
            return OperationResult(ResultKind.COMPLETE, "Fixture advanced settings handoff only")
        return OperationResult(ResultKind.ERROR, "Fixture does not implement this action")

    def provide_secret(self, pending: PendingRef, secret_stream: BinaryIO) -> OperationResult:
        self._ensure_open()
        operation = self._pending.get(pending.request_id)
        if operation is None or operation.ref != pending:
            return OperationResult(ResultKind.UNAVAILABLE, "Credential request is no longer active")
        # Consume without retaining or recording bytes. This is an inert transport
        # proof; it does not represent a real NetworkManager secret policy.
        secret = secret_stream.read(4097)
        if len(secret) > 4096:
            del secret
            self._pending.pop(pending.request_id, None)
            return OperationResult(ResultKind.ERROR, "Credential exceeds the fixture limit")
        operation.secret_received = True
        self.events.append(
            {
                "event": "secret-received",
                "request_id": pending.request_id,
                "bytes": len(secret),
                "secret_recorded": False,
            }
        )
        del secret
        return OperationResult(
            ResultKind.PENDING,
            "Fixture request accepted; waiting for the next owned refresh",
            target=self._snapshot_target(self._records[pending.target]),
            pending=pending,
        )

    def refresh(self, pending: PendingRef) -> OperationResult:
        self._ensure_open()
        operation = self._pending.get(pending.request_id)
        if operation is None or operation.ref != pending:
            return OperationResult(ResultKind.UNAVAILABLE, "Pending request is no longer active")
        operation.refresh_count += 1
        self.events.append({"event": "pending-refresh", "request_id": pending.request_id})
        if operation.refresh_count < self.complete_after_refresh:
            return OperationResult(ResultKind.PENDING, "Still connecting", pending=pending)
        self._pending.pop(pending.request_id, None)
        record = self._records.get(pending.target)
        if record is None:
            return OperationResult(ResultKind.UNAVAILABLE, "Target disappeared during the fixture request")
        if self.utility == Utility.NETWORK:
            if record.kind in {"access-point", "device"}:
                for other in self._records.values():
                    if other.kind == "connection" and other.state.get("connected"):
                        other.state["connected"] = False
                        self._bump(other)
                record.state["connected"] = True
                record.status = "Connected"
                record.details["Status"] = "Connected"
                self._bump(record)
        return OperationResult(ResultKind.COMPLETE, "Connected · fixture address 192.0.2.42", self._snapshot_target(record))

    def cancel(self, pending: PendingRef) -> OperationResult:
        self._ensure_open()
        operation = self._pending.pop(pending.request_id, None)
        if operation is None or operation.ref != pending:
            return OperationResult(ResultKind.UNAVAILABLE, "Pending request is no longer active")
        self.events.append({"event": "pending-cancelled", "request_id": pending.request_id})
        record = self._records.get(pending.target)
        return OperationResult(ResultKind.CANCELLED, "Fixture request cancelled", self._snapshot_target(record) if record else None)

    def set_external_volume(self, ref: TargetRef, value: int | None) -> None:
        """Test hook proving relative volume actions use a fresh observation."""

        record = self._records[ref]
        record.state["volume_percent"] = value
        record.details["Volume"] = "Unknown" if value is None else f"{value}%"
        self._bump(record)

    def _bump(self, record: _Record) -> None:
        record.revision += 1
        record.status = self._status(record)

    def close(self) -> None:
        self._closed = True
        self._pending.clear()
        self.events.append({"event": "closed"})


def prompt_secret_fixture(prompt: str, secret: bytes) -> tuple[OperationResult, FixtureBackend]:
    """Small unit-test convenience; the secret is passed only as a memory pipe."""

    backend = FixtureBackend(Utility.NETWORK)
    target = TargetRef("access-point", "nm:ap:studio:wlan0:01")
    request = OperationRequest("fixture", str(uuid.uuid4()), target, "connect", "fixture-1", {"persistence": "remember"})
    result = backend.execute(request)
    if result.kind != ResultKind.NEEDS_SECRET or result.pending is None:
        return result, backend
    provided = backend.provide_secret(result.pending, io.BytesIO(secret))
    return provided, backend
