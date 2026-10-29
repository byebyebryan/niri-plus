"""Typed boundary between the Rofi frontend and native adapters.

Secrets are intentionally absent from every JSON-capable model in this module.
The one secret handoff is a separate ``ControlsBackend.provide_secret`` call
which receives a private in-memory stream from the controller.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import BinaryIO, Mapping, Protocol, Sequence


MAX_ID_LENGTH = 512
MAX_TEXT_LENGTH = 4096
MAX_FACTS = 128


class Utility(StrEnum):
    NETWORK = "network"
    AUDIO = "audio"
    BLUETOOTH = "bluetooth"


class Availability(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class ActionKind(StrEnum):
    NAVIGATE = "navigate"
    OPERATION = "operation"
    CONFIRM = "confirm"
    DETAIL = "detail"
    BACK = "back"


class ResultKind(StrEnum):
    COMPLETE = "complete"
    NEEDS_SECRET = "needs-secret"
    NEEDS_CONFIRMATION = "needs-confirmation"
    PENDING = "pending"
    ERROR = "error"
    UNAVAILABLE = "unavailable"
    CANCELLED = "cancelled"


def _bounded_text(value: str, name: str, limit: int = MAX_TEXT_LENGTH) -> str:
    if not isinstance(value, str) or not value or len(value) > limit:
        raise ValueError(f"{name} must be a non-empty string of at most {limit} characters")
    if "\x00" in value:
        raise ValueError(f"{name} must not contain NUL")
    return value


def _safe_parameters(value: Mapping[str, object]) -> dict[str, str | int | bool | None]:
    """Accept bounded scalar request data and reject secret-like field names."""

    result: dict[str, str | int | bool | None] = {}
    if len(value) > 16:
        raise ValueError("operation parameters are too numerous")
    for key, item in value.items():
        _bounded_text(key, "parameter name", 80)
        folded = key.casefold()
        if any(word in folded for word in ("password", "secret", "credential", "token")):
            raise ValueError("secret material is not valid operation metadata")
        if isinstance(item, str):
            _bounded_text(item, "parameter value", 512)
        elif item is not None and not isinstance(item, (bool, int)):
            raise ValueError("operation parameters must be JSON scalars")
        result[key] = item
    return result


@dataclass(frozen=True, slots=True)
class TargetRef:
    """Opaque, stable backend identity; never reconstructed from row text."""

    kind: str
    stable_id: str

    def __post_init__(self) -> None:
        _bounded_text(self.kind, "target kind", 64)
        _bounded_text(self.stable_id, "target identity", MAX_ID_LENGTH)

    def to_json(self) -> dict[str, str]:
        return {"kind": self.kind, "stable_id": self.stable_id}

    @classmethod
    def from_json(cls, value: object) -> TargetRef:
        if not isinstance(value, dict) or set(value) != {"kind", "stable_id"}:
            raise ValueError("invalid target reference")
        return cls(value["kind"], value["stable_id"])


@dataclass(frozen=True, slots=True)
class DetailFact:
    label: str
    value: str

    def __post_init__(self) -> None:
        _bounded_text(self.label, "fact label", 160)
        _bounded_text(self.value, "fact value", MAX_TEXT_LENGTH)


@dataclass(frozen=True, slots=True)
class TargetSnapshot:
    ref: TargetRef
    title: str
    summary: str
    availability: Availability
    revision: str
    status: str = ""
    active: bool = False
    filter_terms: tuple[str, ...] = ()
    facts: tuple[DetailFact, ...] = ()
    state: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _bounded_text(self.title, "target title")
        _bounded_text(self.summary or "unknown", "target summary")
        _bounded_text(self.revision, "target revision", 256)
        if self.status:
            _bounded_text(self.status, "target status", 256)
        if len(self.filter_terms) > 32 or len(self.facts) > MAX_FACTS:
            raise ValueError("target metadata exceeds its item limit")
        for term in self.filter_terms:
            _bounded_text(term, "filter term", 512)
        _safe_parameters(self.state)


@dataclass(frozen=True, slots=True)
class InventorySnapshot:
    utility: Utility
    revision: str
    observed_at: str
    targets: tuple[TargetSnapshot, ...]
    notice: str = ""

    def __post_init__(self) -> None:
        _bounded_text(self.revision, "inventory revision", 256)
        _bounded_text(self.observed_at, "observation time", 128)
        if len(self.targets) > 4096:
            raise ValueError("inventory has too many targets")
        refs = [target.ref for target in self.targets]
        if len(refs) != len(set(refs)):
            raise ValueError("inventory target identities must be unique")
        if self.notice:
            _bounded_text(self.notice, "inventory notice", 1024)

    def find(self, ref: TargetRef) -> TargetSnapshot | None:
        return next((target for target in self.targets if target.ref == ref), None)


@dataclass(frozen=True, slots=True)
class DetailsSnapshot:
    target: TargetRef
    title: str
    facts: tuple[DetailFact, ...]
    revision: str

    def __post_init__(self) -> None:
        _bounded_text(self.title, "details title")
        _bounded_text(self.revision, "details revision", 256)
        if len(self.facts) > MAX_FACTS:
            raise ValueError("details have too many facts")


@dataclass(frozen=True, slots=True)
class ActionSpec:
    """Action available for one pinned target.

    ``parameters`` contains only non-secret intent, e.g. ``desired_muted`` or
    ``persistence``. It is revalidated by the adapter at execution time.
    """

    action_id: str
    label: str
    kind: ActionKind
    parameters: Mapping[str, object] = field(default_factory=dict)
    confirmation: str = ""
    enabled: bool = True
    disabled_reason: str = ""

    def __post_init__(self) -> None:
        _bounded_text(self.action_id, "action id", 128)
        _bounded_text(self.label, "action label", 256)
        _safe_parameters(self.parameters)
        if self.confirmation:
            _bounded_text(self.confirmation, "confirmation", 1024)
        if self.disabled_reason:
            _bounded_text(self.disabled_reason, "disabled reason", 512)


@dataclass(frozen=True, slots=True)
class PendingRef:
    """Opaque reference to one request owned by the backend/controller."""

    request_id: str
    target: TargetRef
    generation: int

    def __post_init__(self) -> None:
        _bounded_text(self.request_id, "pending request id", 128)
        if type(self.generation) is not int or self.generation < 0:
            raise ValueError("pending generation must be a non-negative integer")

    def to_json(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "target": self.target.to_json(),
            "generation": self.generation,
        }

    @classmethod
    def from_json(cls, value: object) -> PendingRef:
        if not isinstance(value, dict) or set(value) != {"request_id", "target", "generation"}:
            raise ValueError("invalid pending reference")
        return cls(
            value["request_id"],
            TargetRef.from_json(value["target"]),
            value["generation"],
        )


@dataclass(frozen=True, slots=True)
class OperationRequest:
    invocation_id: str
    request_id: str
    target: TargetRef
    action_id: str
    expected_revision: str
    parameters: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _bounded_text(self.invocation_id, "invocation id", 128)
        _bounded_text(self.request_id, "request id", 128)
        _bounded_text(self.action_id, "action id", 128)
        _bounded_text(self.expected_revision, "expected revision", 256)
        _safe_parameters(self.parameters)


@dataclass(frozen=True, slots=True)
class OperationResult:
    kind: ResultKind
    message: str = ""
    target: TargetSnapshot | None = None
    pending: PendingRef | None = None
    secret_prompt: str = ""
    persistence_required: bool = False
    # Authentication prompts are controller-memory only, never UIState/JSON.
    confirmation_prompt: str = ""
    display_prompt: str = ""

    def __post_init__(self) -> None:
        if self.message:
            _bounded_text(self.message, "operation message", 1024)
        if self.secret_prompt:
            _bounded_text(self.secret_prompt, "secret prompt", 256)
        if self.kind in {ResultKind.NEEDS_SECRET, ResultKind.NEEDS_CONFIRMATION, ResultKind.PENDING} and self.pending is None:
            raise ValueError("needs-secret and pending results require an opaque pending reference")
        if self.kind != ResultKind.NEEDS_SECRET and self.secret_prompt:
            raise ValueError("only needs-secret results may include a prompt")
        if self.persistence_required and self.kind != ResultKind.NEEDS_SECRET:
            raise ValueError("persistence choice is only valid before secret submission")
        if self.confirmation_prompt:
            _bounded_text(self.confirmation_prompt, "authentication confirmation", 1024)
            if self.kind != ResultKind.NEEDS_CONFIRMATION:
                raise ValueError("authentication confirmation requires needs-confirmation")
        if self.display_prompt:
            _bounded_text(self.display_prompt, "authentication display", 1024)
            if self.kind != ResultKind.PENDING:
                raise ValueError("authentication display requires pending")


class ControlsBackend(Protocol):
    """Per-invocation backend contract implemented by native adapters."""

    def snapshot(self, utility: Utility) -> InventorySnapshot: ...

    def target(self, ref: TargetRef) -> TargetSnapshot | None: ...

    def details(self, ref: TargetRef) -> DetailsSnapshot | None: ...

    def actions(self, ref: TargetRef) -> Sequence[ActionSpec]: ...

    def execute(self, request: OperationRequest) -> OperationResult: ...

    def provide_secret(self, pending: PendingRef, secret_stream: BinaryIO) -> OperationResult: ...

    def respond_confirmation(self, pending: PendingRef, accepted: bool) -> OperationResult: ...

    def refresh(self, pending: PendingRef) -> OperationResult: ...

    def cancel(self, pending: PendingRef) -> OperationResult: ...

    def close(self) -> None: ...
