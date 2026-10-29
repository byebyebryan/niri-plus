"""Bounded PulseAudio-compatible controls; native servers retain ownership."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess
from typing import Callable

from .model import (
    ActionKind, ActionSpec, Availability, DetailFact, DetailsSnapshot,
    InventorySnapshot, OperationRequest, OperationResult, PendingRef, ResultKind,
    TargetRef, TargetSnapshot, Utility,
)


NORMAL_VOLUME = 65536


class AudioError(RuntimeError):
    pass


@dataclass(frozen=True)
class _Node:
    target: TargetSnapshot
    name: str
    direction: str
    values: tuple[int, ...]
    muted: bool | None


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class AudioBackend:
    """Each explicit action re-reads server identity, device identity and values."""

    def __init__(self, *, runner: Callable = subprocess.run, pactl: str | None = None):
        self._run = runner
        self._pactl = pactl or shutil.which("pactl") or "pactl"
        self._nodes: dict[TargetRef, _Node] = {}
        self._results: dict[str, tuple[str, OperationResult]] = {}

    def _call(self, *arguments: str, read_json: bool = False):
        try:
            result = self._run(
                [self._pactl, "--format=json", *arguments],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=4, check=False, text=True,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise AudioError("Audio server request unavailable or timed out; refresh before retrying") from error
        if result.returncode:
            raise AudioError("Audio server rejected the request; refresh or open the advanced mixer")
        if not read_json:
            return None
        if len(result.stdout) > 8 * 1024 * 1024:
            raise AudioError("Audio inventory exceeds the supported size")
        try:
            return json.loads(result.stdout)
        except (ValueError, TypeError) as error:
            raise AudioError("Audio server returned an unreadable inventory") from error

    @staticmethod
    def _epoch(info: object) -> str:
        if not isinstance(info, dict) or not info.get("server_name") or not info.get("cookie"):
            raise AudioError("Audio server identity is unavailable")
        return _digest([info.get("server_string"), info["server_name"], str(info["cookie"])])

    def _observe(self) -> InventorySnapshot:
        info = self._call("info", read_json=True)
        epoch = self._epoch(info)
        sinks = self._call("list", "sinks", read_json=True)
        sources = self._call("list", "sources", read_json=True)
        if epoch != self._epoch(self._call("info", read_json=True)):
            raise AudioError("Audio server changed during refresh; retry against the new server")
        nodes: dict[TargetRef, _Node] = {}
        for direction, records, default_key in (
            ("output", sinks, "default_sink_name"),
            ("input", sources, "default_source_name"),
        ):
            if not isinstance(records, list) or len(records) > 2048:
                raise AudioError("Audio device inventory is invalid")
            for record in records:
                if not isinstance(record, dict):
                    raise AudioError("Audio device record is invalid")
                name, index = record.get("name"), record.get("index")
                if not isinstance(name, str) or not name or "\0" in name or type(index) is not int:
                    raise AudioError("Audio device identity is invalid")
                properties = record.get("properties") or {}
                if not isinstance(properties, dict):
                    properties = {}
                serial = properties.get("object.serial", index)
                ref = TargetRef("audio-" + direction, _digest([epoch, direction, name, index, serial]))
                active_port = record.get("active_port")
                if isinstance(active_port, dict):
                    active_port = active_port.get("name")
                port = next((p for p in (record.get("ports") or []) if isinstance(p, dict) and p.get("name") == active_port), {})
                unavailable = port.get("availability") in {"no", "not available", "unavailable"}
                availability = Availability.UNAVAILABLE if unavailable else Availability.AVAILABLE
                raw_volume = record.get("volume")
                values = tuple(
                    channel["value"] for channel in raw_volume.values()
                    if isinstance(channel, dict) and type(channel.get("value")) is int and channel["value"] >= 0
                ) if isinstance(raw_volume, dict) else ()
                if isinstance(raw_volume, dict) and len(values) != len(raw_volume):
                    values = ()
                volume = round(max(values) / NORMAL_VOLUME * 100) if values else None
                muted = record.get("mute") if type(record.get("mute")) is bool else None
                is_default = name == info.get(default_key)
                role = "Default " + direction if is_default else direction.capitalize()
                mute_label = "Muted" if muted is True else "Unmuted" if muted is False else "Mute state unknown"
                summary = " · ".join([
                    direction.capitalize() if unavailable else "",
                    f"{volume}%" if volume is not None else "Volume unknown", mute_label,
                ]).removeprefix(" · ")
                title = str(record.get("description") or properties.get("device.description") or name)
                facts = (
                    DetailFact("Direction", direction), DetailFact("Native device", name),
                    DetailFact("Default", "Yes" if is_default else "No"),
                    DetailFact("Volume", f"{volume}%" if volume is not None else "Unknown"),
                    DetailFact("Mute", mute_label),
                    DetailFact("Server state", str(record.get("state") or "Unknown")),
                    DetailFact("Port availability", str(port.get("availability") or "Unknown")),
                )
                state = {"direction": direction, "volume_percent": volume, "muted": muted, "is_default": is_default}
                revision = _digest([ref.to_json(), values, muted, is_default, unavailable])
                target = TargetSnapshot(
                    ref, title[:4096], summary, availability, revision,
                    status="Unavailable" if unavailable else role,
                    active=is_default, filter_terms=(name[:512], direction, mute_label),
                    facts=facts, state=state,
                )
                nodes[ref] = _Node(target, name, direction, values, muted)
        self._nodes = nodes
        ordered = sorted(nodes.values(), key=lambda n: (n.direction != "output", not n.target.active, n.target.title.casefold(), n.name))
        default_output = next((n.target.title for n in ordered if n.direction == "output" and n.target.active), "Unknown")
        default_input = next((n.target.title for n in ordered if n.direction == "input" and n.target.active), "Unknown")
        return InventorySnapshot(
            Utility.AUDIO, _digest([n.target.revision for n in ordered]),
            datetime.now(timezone.utc).isoformat(), tuple(n.target for n in ordered),
            notice=f"Default output: {default_output} · input: {default_input}. Defaults do not move existing streams.",
        )

    def snapshot(self, utility: Utility = Utility.AUDIO) -> InventorySnapshot:
        if utility != Utility.AUDIO:
            return InventorySnapshot(Utility.AUDIO, "unavailable", datetime.now(timezone.utc).isoformat(), (), "This adapter owns Audio only")
        try:
            return self._observe()
        except (AudioError, ValueError) as error:
            self._nodes = {}
            return InventorySnapshot(Utility.AUDIO, "unavailable", datetime.now(timezone.utc).isoformat(), (), str(error))

    def _node(self, ref: TargetRef) -> _Node:
        self._observe()
        if ref not in self._nodes:
            raise AudioError("Audio device or server changed; refresh and select the current device")
        return self._nodes[ref]

    def target(self, ref: TargetRef) -> TargetSnapshot | None:
        try:
            return self._node(ref).target
        except (AudioError, ValueError):
            return None

    def details(self, ref: TargetRef) -> DetailsSnapshot | None:
        target = self.target(ref)
        if target is None:
            return None
        return DetailsSnapshot(ref, target.title, target.facts, target.revision)

    def actions(self, ref: TargetRef) -> tuple[ActionSpec, ...]:
        try:
            node = self._node(ref)
        except (AudioError, ValueError):
            return ()
        if node.target.availability == Availability.UNAVAILABLE:
            return ()
        actions = []
        if not node.target.active:
            actions.append(ActionSpec("set-default", "Set default", ActionKind.OPERATION, {"direction": node.direction}))
        for action_id, label in (("volume-up", "Volume +5%"), ("volume-down", "Volume −5%")):
            actions.append(ActionSpec(action_id, label, ActionKind.OPERATION, {"direction": node.direction},
                                      enabled=bool(node.values), disabled_reason="Volume is unknown" if not node.values else ""))
        if node.muted is not None:
            actions.append(ActionSpec("mute", "Unmute" if node.muted else "Mute", ActionKind.OPERATION,
                                      {"direction": node.direction, "desired_muted": not node.muted}))
        return tuple(actions)

    def execute(self, request: OperationRequest) -> OperationResult:
        signature = _digest([request.invocation_id, request.target.to_json(), request.action_id, dict(request.parameters)])
        previous = self._results.get(request.request_id)
        if previous:
            return previous[1] if previous[0] == signature else OperationResult(ResultKind.ERROR, "Request identity was reused for another operation")
        try:
            node = self._node(request.target)
            if node.target.availability == Availability.UNAVAILABLE:
                raise AudioError("Audio device is unavailable; no setting was changed")
            if request.parameters.get("direction", node.direction) != node.direction:
                raise AudioError("Audio direction changed; select the current device")
            command_part = "sink" if node.direction == "output" else "source"
            if request.action_id == "set-default":
                self._call("set-default-" + command_part, node.name)
            elif request.action_id in {"volume-up", "volume-down"}:
                if not node.values:
                    raise AudioError("Volume is unknown; refresh or open the advanced mixer")
                maximum = max(node.values)
                delta = 5 if request.action_id == "volume-up" else -5
                # Do not amplify beyond 100%. A pre-existing amplified device
                # can still be reduced gradually instead of jumping to 100%.
                desired = maximum if delta > 0 and maximum >= NORMAL_VOLUME else max(0, maximum + round(NORMAL_VOLUME * delta / 100))
                if delta > 0 and maximum < NORMAL_VOLUME:
                    desired = min(NORMAL_VOLUME, desired)
                values = tuple(round(v * desired / maximum) for v in node.values) if maximum else tuple(desired for _ in node.values)
                self._call("set-" + command_part + "-volume", node.name, *(str(v) for v in values))
            elif request.action_id == "mute":
                desired_muted = request.parameters.get("desired_muted")
                if type(desired_muted) is not bool:
                    raise AudioError("Mute requires an explicit desired state")
                self._call("set-" + command_part + "-mute", node.name, "1" if desired_muted else "0")
            else:
                raise AudioError("Unsupported audio action")
            observed = self._node(request.target).target
            result = OperationResult(ResultKind.COMPLETE, observed.summary, target=observed)
        except (AudioError, ValueError) as error:
            result = OperationResult(ResultKind.ERROR, str(error))
        self._results[request.request_id] = (signature, result)
        if len(self._results) > 128:
            self._results.pop(next(iter(self._results)))
        return result

    def provide_secret(self, pending: PendingRef, secret_stream) -> OperationResult:
        return OperationResult(ResultKind.ERROR, "Audio does not request credentials")

    def refresh(self, pending: PendingRef) -> OperationResult:
        return OperationResult(ResultKind.ERROR, "No pending audio request")

    def cancel(self, pending: PendingRef) -> OperationResult:
        return OperationResult(ResultKind.ERROR, "No pending audio request")

    def close(self) -> None:
        self._nodes.clear()
        self._results.clear()
