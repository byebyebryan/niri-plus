"""Rofi script-mode controls state machine."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
import io
import json
import uuid
from typing import Callable, Mapping, Sequence

from .appearance import ControlsAppearance
from .model import (
    ActionKind,
    ActionSpec,
    Availability,
    ControlsBackend,
    DetailFact,
    InventorySnapshot,
    OperationRequest,
    OperationResult,
    PendingRef,
    ResultKind,
    TargetRef,
    TargetSnapshot,
    Utility,
)
from .rofi import (
    ROFI_RETV_CUSTOM_1,
    ROFI_RETV_CUSTOM_19,
    ROFI_RETV_CUSTOM_7,
    ROFI_RETV_CUSTOM_8,
    ROFI_RETV_SELECTED,
    RofiFrame,
    RofiProtocolError,
    RofiRow,
    ScriptRequest,
    message_for_actions,
    message_for_rows,
    row_for_action,
    row_for_target,
    selected_info,
    _clean,
    _escape,
)


MAX_STATE_SIZE = 16 * 1024
MAX_PENDING_POLLS = 120
LIST_ACTIONS = (
    ActionSpec("open", "Open", ActionKind.NAVIGATE),
    ActionSpec("details", "Details", ActionKind.DETAIL),
)
PENDING_ACTIONS = (
    ActionSpec("close-menu", "Close menu", ActionKind.NAVIGATE),
    ActionSpec("cancel-connection", "Cancel connection", ActionKind.OPERATION),
)
PENDING_BLUETOOTH_ACTIONS = (
    ActionSpec("close-menu", "Close menu", ActionKind.NAVIGATE),
    ActionSpec("stop-waiting", "Stop waiting", ActionKind.OPERATION),
)


class Page(StrEnum):
    LIST = "list"
    TARGET = "target"
    ADJUST = "adjust"
    DETAILS = "details"
    CONFIRM = "confirm"
    AUTH_CONFIRM = "auth-confirm"
    OPEN_WARNING = "open-warning"
    CONNECT_CHOICE = "connect-choice"
    PENDING = "pending"


def _safe_parameters(value: Mapping[str, object]) -> dict[str, str | int | bool | None]:
    result: dict[str, str | int | bool | None] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key or len(key) > 80:
            raise ValueError("invalid action parameter key")
        if any(word in key.casefold() for word in ("password", "secret", "credential", "token")):
            raise ValueError("secret material cannot be stored in Rofi state")
        if isinstance(item, str):
            if len(item) > 512 or "\x00" in item:
                raise ValueError("action parameter string is invalid")
        elif item is not None and not isinstance(item, (bool, int)):
            raise ValueError("action parameters must be JSON scalars")
        result[key] = item
    return result


@dataclass(frozen=True, slots=True)
class UIState:
    schema_version: int
    invocation_id: str
    utility: Utility
    page: Page = Page.LIST
    action_id: str = "open"
    target: TargetRef | None = None
    parent_page: Page | None = None
    return_page: Page | None = None
    return_target: TargetRef | None = None
    return_previous: TargetRef | None = None
    return_next: TargetRef | None = None
    pending: PendingRef | None = None
    pending_action: str = ""
    pending_parameters: Mapping[str, object] = None  # type: ignore[assignment]
    pending_revision: str = ""
    persistence: str = ""
    confirmation: str = ""
    notice: str = ""
    pending_polls: int = 0
    visible_action_label: str = ""
    visible_action_parameters: Mapping[str, object] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported controls state version")
        if not self.invocation_id or len(self.invocation_id) > 128:
            raise ValueError("invalid controls invocation id")
        if self.pending_polls < 0 or self.pending_polls > MAX_PENDING_POLLS:
            raise ValueError("pending poll count is invalid")
        if len(self.notice) > 1024 or len(self.confirmation) > 1024:
            raise ValueError("controls notice exceeds its limit")
        _safe_parameters(self.pending_parameters or {})
        _safe_parameters(self.visible_action_parameters or {})

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "invocation_id": self.invocation_id,
            "utility": self.utility.value,
            "page": self.page.value,
            "action_id": self.action_id,
            "target": self.target.to_json() if self.target else None,
            "parent_page": self.parent_page.value if self.parent_page else None,
            "return_page": self.return_page.value if self.return_page else None,
            "return_target": self.return_target.to_json() if self.return_target else None,
            "return_previous": self.return_previous.to_json() if self.return_previous else None,
            "return_next": self.return_next.to_json() if self.return_next else None,
            "pending": self.pending.to_json() if self.pending else None,
            "pending_action": self.pending_action,
            "pending_parameters": dict(self.pending_parameters or {}),
            "pending_revision": self.pending_revision,
            "persistence": self.persistence,
            "confirmation": self.confirmation,
            "notice": self.notice,
            "pending_polls": self.pending_polls,
            "visible_action_label": self.visible_action_label,
            "visible_action_parameters": dict(self.visible_action_parameters or {}),
        }

    @classmethod
    def initial(cls, utility: Utility, invocation_id: str) -> UIState:
        return cls(1, invocation_id, utility)

    @classmethod
    def parse(cls, value: Mapping[str, object]) -> UIState:
        required = {
            "schema_version", "invocation_id", "utility", "page", "action_id", "target",
            "parent_page", "return_page", "return_target", "return_previous", "return_next", "pending",
            "pending_action", "pending_parameters", "pending_revision", "persistence",
            "confirmation", "notice", "pending_polls", "visible_action_label",
            "visible_action_parameters",
        }
        if set(value) != required:
            raise ValueError("controls state has an unexpected field set")
        def ref(name: str) -> TargetRef | None:
            item = value[name]
            return TargetRef.from_json(item) if item is not None else None
        pending = value["pending"]
        return cls(
            schema_version=value["schema_version"],  # type: ignore[arg-type]
            invocation_id=value["invocation_id"],  # type: ignore[arg-type]
            utility=Utility(value["utility"]),  # type: ignore[arg-type]
            page=Page(value["page"]),  # type: ignore[arg-type]
            action_id=value["action_id"],  # type: ignore[arg-type]
            target=ref("target"),
            parent_page=Page(value["parent_page"]) if value["parent_page"] is not None else None,
            return_page=Page(value["return_page"]) if value["return_page"] is not None else None,
            return_target=ref("return_target"),
            return_previous=ref("return_previous"),
            return_next=ref("return_next"),
            pending=PendingRef.from_json(pending) if pending is not None else None,
            pending_action=value["pending_action"],  # type: ignore[arg-type]
            pending_parameters=_safe_parameters(value["pending_parameters"]),  # type: ignore[arg-type]
            pending_revision=value["pending_revision"],  # type: ignore[arg-type]
            persistence=value["persistence"],  # type: ignore[arg-type]
            confirmation=value["confirmation"],  # type: ignore[arg-type]
            notice=value["notice"],  # type: ignore[arg-type]
            pending_polls=value["pending_polls"],  # type: ignore[arg-type]
            visible_action_label=value["visible_action_label"],  # type: ignore[arg-type]
            visible_action_parameters=_safe_parameters(value["visible_action_parameters"]),  # type: ignore[arg-type]
        )


class ControlsApp:
    """One active Rofi invocation, its backend, and its in-memory UI caches."""

    def __init__(
        self,
        utility: Utility | str,
        invocation_id: str,
        backend: ControlsBackend,
        appearance: ControlsAppearance,
        *,
        prompt_secret: Callable[[str], bytearray | None],
        advanced_available: bool = False,
    ):
        self.utility = Utility(utility)
        self.invocation_id = invocation_id
        self.backend = backend
        self.appearance = appearance
        self.prompt_secret = prompt_secret
        self.advanced_available = advanced_available
        self.launch_advanced = False
        self._inventory: InventorySnapshot | None = None
        self._targets: dict[TargetRef, TargetSnapshot] = {}
        self._details: dict[TargetRef, tuple[DetailFact, ...]] = {}
        self._actions: dict[TargetRef, tuple[ActionSpec, ...]] = {}
        self._resume_state: UIState | None = None
        self._authentication_prompt = ""

    def handle(self, request: ScriptRequest) -> str | None:
        if request.retv == 0 or not request.data:
            state = self._resume_state
            self._resume_state = None
            if state is None:
                state = UIState.initial(self.utility, self.invocation_id)
                self._refresh_inventory()
            elif state.target is not None and state.page != Page.PENDING:
                target = self._target(state.target, fresh=True)
                if target is not None:
                    self._target_actions(target.ref, fresh=True)
                elif state.page != Page.LIST:
                    state = replace(state, notice="Pinned target is unavailable after credential entry; no new action was run.")
            # Every newly owned Rofi process starts with the newline protocol;
            # the RS delimiter is negotiated in this first response, regardless
            # of which in-memory page it resumes (including pending/password).
            return replace(self._render(state), initial=True).render()
        try:
            state = UIState.parse(request.data)
        except (ValueError, TypeError, KeyError) as error:
            state = UIState.initial(self.utility, self.invocation_id)
            self._refresh_inventory()
            state = replace(state, notice=f"Picker state could not be restored: {_clean(str(error), limit=256)}")
            return self._render(state).render()
        if state.invocation_id != self.invocation_id or state.utility != self.utility:
            state = UIState.initial(self.utility, self.invocation_id)
            self._refresh_inventory()
            state = replace(state, notice="This picker state belongs to another invocation; reopened the inventory.")
            return self._render(state).render()

        selected = selected_info(request.info)
        if request.retv in (ROFI_RETV_CUSTOM_7, ROFI_RETV_CUSTOM_8):
            return self._cycle(state, selected, 1 if request.retv == ROFI_RETV_CUSTOM_7 else -1)
        if request.retv == ROFI_RETV_CUSTOM_1:
            return self._refresh(state, selected)
        if request.retv == ROFI_RETV_CUSTOM_19:
            return self._poll_pending(state)
        if request.retv == ROFI_RETV_SELECTED:
            return self._accept(state, selected)
        return self._render(replace(state, notice="Unsupported Rofi callback; no operation was run."), selected=selected).render()

    def _refresh_inventory(self) -> InventorySnapshot:
        self._inventory = self.backend.snapshot(self.utility)
        self._targets = {item.ref: item for item in self._inventory.targets}
        return self._inventory

    def _target(self, ref: TargetRef, *, fresh: bool = False) -> TargetSnapshot | None:
        target = self.backend.target(ref) if fresh else self._targets.get(ref)
        if target is not None:
            self._targets[ref] = target
        return target

    def _target_actions(self, ref: TargetRef, *, fresh: bool = False) -> tuple[ActionSpec, ...]:
        if fresh or ref not in self._actions:
            self._actions[ref] = tuple(self.backend.actions(ref))
        return self._actions[ref]

    def _list_targets(self) -> tuple[TargetSnapshot, ...]:
        if self._inventory is None:
            self._refresh_inventory()
        return self._inventory.targets if self._inventory else ()

    @staticmethod
    def _neighbors(targets: Sequence[TargetSnapshot], ref: TargetRef) -> tuple[TargetRef | None, TargetRef | None]:
        index = next((i for i, target in enumerate(targets) if target.ref == ref), None)
        if index is None:
            return None, None
        previous = targets[index - 1].ref if index > 0 else None
        following = targets[index + 1].ref if index + 1 < len(targets) else None
        return previous, following

    def _rows_action_set(self, state: UIState, target: TargetSnapshot | None) -> tuple[ActionSpec, ...]:
        if state.page == Page.LIST:
            return LIST_ACTIONS
        if state.page == Page.TARGET:
            if target is None:
                return (ActionSpec("details", "Details", ActionKind.DETAIL), ActionSpec("back", "Back", ActionKind.BACK))
            native = self._target_actions(target.ref)
            if target.availability != Availability.AVAILABLE:
                native = ()
            if self.utility == Utility.AUDIO:
                adjust_ids = {"volume-up", "volume-down", "mute"}
                adjust = any(item.action_id in adjust_ids for item in native)
                default = tuple(item for item in native if item.action_id == "set-default")
                actions = ([ActionSpec("adjust", "Adjust", ActionKind.NAVIGATE)] if adjust else [])
                actions.extend(default)
                actions.extend((ActionSpec("details", "Details", ActionKind.DETAIL), ActionSpec("back", "Back", ActionKind.BACK)))
                return tuple(actions)
            return tuple(native) + (
                ActionSpec("details", "Details", ActionKind.DETAIL),
                ActionSpec("back", "Back", ActionKind.BACK),
            )
        if state.page == Page.ADJUST and target is not None:
            native = self._target_actions(target.ref)
            adjust_ids = {"volume-up", "volume-down", "mute"}
            actions = [item for item in native if item.action_id in adjust_ids]
            actions.append(ActionSpec("back", "Back", ActionKind.BACK))
            return tuple(actions)
        if state.page == Page.PENDING:
            if state.pending_action == "pair-device":
                return (PENDING_ACTIONS[0], ActionSpec("cancel-pairing", "Cancel pairing", ActionKind.OPERATION))
            return PENDING_BLUETOOTH_ACTIONS if self.utility == Utility.BLUETOOTH else PENDING_ACTIONS
        return ()

    def _active_action(self, state: UIState, target: TargetSnapshot | None) -> tuple[tuple[ActionSpec, ...], UIState]:
        actions = self._rows_action_set(state, target)
        if not actions:
            return actions, replace(state, action_id="")
        current = next((item for item in actions if item.action_id == state.action_id), None)
        if current is None:
            selected = next((item for item in actions if item.action_id == "details"), actions[0])
            return actions, replace(
                state,
                action_id=selected.action_id,
                visible_action_label=selected.label,
                visible_action_parameters=dict(selected.parameters),
                notice=state.notice or "The previous action is no longer available; review the current choices.",
            )
        return actions, replace(
            state,
            visible_action_label=current.label,
            visible_action_parameters=dict(current.parameters),
        )

    def _render(
        self,
        state: UIState,
        *,
        initial: bool = False,
        selected: tuple[str, Mapping[str, object]] | None = None,
    ) -> RofiFrame:
        self._resume_state = state
        if state.page == Page.LIST:
            targets = self._list_targets()
            rows = [row_for_target(target, self.appearance) for target in targets]
            if not rows:
                rows = [
                    RofiRow(
                        text="No devices available",
                        display="<b>No devices available</b>\n<span size=\"smaller\">Refresh or close the menu</span>",
                        info={"schema_version": 1, "row": "empty"},
                        meta="no devices available",
                        selectable=False,
                    )
                ]
            if self.advanced_available:
                rows.append(RofiRow("Advanced settings", "Advanced settings\n<span size=\"smaller\">Open the native recovery/settings tool</span>",
                                    {"schema_version": 1, "row": "advanced"}, meta="advanced settings recovery"))
            selected_ref = self._selected_target(selected)
            if selected_ref is None and state.return_target is not None:
                selected_ref = state.return_target
            index = self._find_index(targets, selected_ref)
            if index is None:
                index = 0 if targets else None
            actions, state = self._active_action(state, None)
            self._resume_state = state
            context = self._inventory.notice if self._inventory and self._inventory.notice else f"{len(targets)} devices · refresh with Alt+R"
            message = message_for_actions(actions, state.action_id, context, state.notice, self.appearance)
            return RofiFrame(
                prompt=self._prompt(state),
                message=message,
                state=state.payload(),
                rows=rows,
                selected_index=index,
                initial=initial,
            )

        target = self._target(state.target) if state.target else None
        if state.page in {Page.TARGET, Page.ADJUST, Page.PENDING}:
            actions, state = self._active_action(state, target)
            rows: list[RofiRow]
            if target is None:
                rows = [self._message_row("Target unavailable", "Refresh the inventory before continuing", selectable=False)]
                state = replace(state, notice=state.notice or "Target is unavailable")
            else:
                rows = [row_for_target(target, self.appearance)]
            context = self._context_for(target, state)
            if state.page == Page.PENDING and self._authentication_prompt:
                context += " · " + self._authentication_prompt
            message = message_for_actions(actions, state.action_id, context, state.notice, self.appearance)
            self._resume_state = state
            return RofiFrame(
                prompt=self._prompt(state, target),
                message=message,
                state=state.payload(),
                rows=rows,
                selected_index=0 if rows and rows[0].selectable else None,
            )

        if state.page == Page.DETAILS:
            facts = self._details.get(state.target, ()) if state.target else ()
            if state.target and state.target not in self._details:
                details = self.backend.details(state.target)
                if details:
                    facts = details.facts
                    self._details[state.target] = facts
                    if target is not None:
                        target = replace(target, revision=details.revision, facts=facts)
                        self._targets[state.target] = target
                else:
                    self._details[state.target] = ()
                    state = replace(state, notice=state.notice or "Details could not be read from the native service.")
            rows = [self._fact_row(state.target, fact) for fact in facts if state.target]
            if not facts:
                rows.append(self._message_row("No detail facts available", "The native source returned no details", selectable=False))
            rows.append(self._back_row(state.target, "Back to previous view"))
            rows[-1] = replace(rows[-1], permanent=True)
            rows_spec = (ActionSpec("back", "Back", ActionKind.BACK),)
            state = replace(state, action_id="back", visible_action_label="Back", visible_action_parameters={})
            self._resume_state = state
            return RofiFrame(
                prompt=self._prompt(state, target),
                message=message_for_rows(state.page.value, self._context_for(target, state), state.notice, self.appearance),
                state=state.payload(),
                rows=rows,
                selected_index=len(rows) - 1,
            )

        if state.page in {Page.CONFIRM, Page.OPEN_WARNING}:
            return self._render_confirmation(state, target)
        if state.page == Page.AUTH_CONFIRM:
            rows = [RofiRow(label, f"<b>{label}</b>",
                            {"schema_version": 1, "row": "choice", "decision": decision,
                             "target": state.target.to_json() if state.target else None}, permanent=True)
                    for decision, label in (("cancel", "Cancel pairing"), ("confirm", "Confirm matching code / authorize"))]
            self._resume_state = state
            return RofiFrame(prompt=self._prompt(state, target, "Pairing"),
                             message=message_for_rows("pairing confirmation", self._authentication_prompt or "Pairing confirmation expired; cancel and retry.", "", self.appearance),
                             state=state.payload(), rows=rows, selected_index=0)
        if state.page == Page.CONNECT_CHOICE:
            return self._render_persistence_choice(state, target)
        self._resume_state = state
        return RofiFrame(
            prompt=self._prompt(state, target),
            message=message_for_rows(state.page.value, self._context_for(target, state), state.notice or "Unsupported page", self.appearance),
            state=state.payload(),
            rows=[self._back_row(state.target, "Return to previous view")],
            selected_index=0,
        )

    def _render_confirmation(self, state: UIState, target: TargetSnapshot | None) -> RofiFrame:
        cancel = RofiRow(
            text="Cancel",
            display="<b>Cancel</b>\n<span size=\"smaller\">Return without changing anything</span>",
            info={"schema_version": 1, "row": "choice", "decision": "cancel", "target": target.ref.to_json() if target else None},
            meta=_clean(f"Cancel {target.title if target else ''} {state.confirmation}"),
            permanent=True,
        )
        confirm_label = self._confirmation_label(state, target)
        if state.page == Page.OPEN_WARNING:
            confirm_label = "Continue with unsecured Wi-Fi"
        confirm = RofiRow(
            text=_clean(confirm_label, limit=512),
            display=f"<b>{_escape(confirm_label, limit=512)}</b>\n<span size=\"smaller\">{_escape(state.confirmation or 'Confirm this operation')}</span>",
            info={"schema_version": 1, "row": "choice", "decision": "confirm", "target": target.ref.to_json() if target else None},
            meta=_clean(f"{confirm_label} {target.title if target else ''} {state.confirmation}"),
        )
        context = state.confirmation or "Confirm this exact operation?"
        self._resume_state = state
        return RofiFrame(
            prompt=self._prompt(state, target, "Confirm"),
            message=message_for_rows("confirmation", context, state.notice, self.appearance),
            state=state.payload(),
            rows=[cancel, confirm],
            selected_index=0,
        )

    def _render_persistence_choice(self, state: UIState, target: TargetSnapshot | None) -> RofiFrame:
        choices = [
            ("cancel", "Cancel", "Return without submitting a connection"),
            ("remember", "Connect and remember", "Save for this user and enable autoconnect for the new profile"),
            ("once", "Connect once", "Use a volatile profile without autoconnect"),
        ]
        rows = [
            RofiRow(
                text=label,
                display=f"<b>{_escape(label)}</b>\n<span size=\"smaller\">{_escape(detail)}</span>",
                info={"schema_version": 1, "row": "choice", "persistence": key, "target": target.ref.to_json() if target else None},
                meta=_clean(f"{label} {detail} {target.title if target else ''}"),
                permanent=key == "cancel",
            )
            for key, label, detail in choices
        ]
        self._resume_state = state
        return RofiFrame(
            prompt=self._prompt(state, target, "Connect"),
            message=message_for_rows("connection choice", f"{target.title if target else 'Network'} · choose persistence before submission", state.notice, self.appearance),
            state=state.payload(),
            rows=rows,
            selected_index=0,
        )

    def _accept(self, state: UIState, selected: tuple[str, Mapping[str, object]] | None) -> str | None:
        if state.page == Page.LIST:
            if selected and selected[0] == "advanced" and self.advanced_available:
                if state.action_id == "details":
                    return self._render(replace(state, notice="Advanced opens the existing native editor or recovery tool; it does not alter state by opening this menu.")).render()
                self.launch_advanced = True
                return None
            ref = self._selected_target(selected)
            if ref is None:
                return self._render(replace(state, notice="Select a listed device or connection first.")).render()
            target = self._target(ref, fresh=True)
            if target is None:
                self._refresh_inventory()
                return self._render(replace(state, notice="That item disappeared; the inventory was refreshed."), selected=selected).render()
            targets = self._list_targets()
            previous, following = self._neighbors(targets, ref)
            if state.action_id == "details":
                state = replace(
                    state,
                    page=Page.DETAILS,
                    target=ref,
                    parent_page=Page.LIST,
                    return_page=Page.LIST,
                    return_target=ref,
                    return_previous=previous,
                    return_next=following,
                    notice="",
                )
                self._load_details(ref)
            else:
                self._target_actions(ref, fresh=True)
                state = replace(
                    state,
                    page=Page.TARGET,
                    target=ref,
                    parent_page=Page.LIST,
                    return_page=None,
                    return_target=ref,
                    return_previous=previous,
                    return_next=following,
                    action_id="details",
                    notice="",
                )
            return self._render(state, selected=selected).render()

        if state.page in {Page.TARGET, Page.ADJUST}:
            ref = self._selected_target(selected)
            if state.target is None or ref != state.target:
                return self._render(replace(state, notice="Pinned target identity did not match the selected row; no action was run."), selected=selected).render()
            if state.action_id == "back":
                if state.page == Page.ADJUST:
                    return self._return_from_adjust(state)
                return self._return_to_parent(state)
            if state.action_id == "details":
                self._load_details(ref)
                return self._render(replace(state, page=Page.DETAILS, return_page=state.page, action_id="back", notice=""), selected=selected).render()
            if state.action_id == "adjust" and state.page == Page.TARGET and self.utility == Utility.AUDIO:
                self._target_actions(ref, fresh=True)
                return self._render(replace(state, page=Page.ADJUST, return_page=Page.TARGET, action_id="volume-up", notice=""), selected=selected).render()
            action = self._fresh_action(state)
            if action is None:
                return self._render(replace(state, notice="The selected operation changed or is unavailable. Review the refreshed action labels."), selected=selected).render()
            if not action.enabled:
                return self._render(
                    replace(state, notice=action.disabled_reason or f"{action.label} is unavailable; no operation was run."),
                    selected=selected,
                ).render()
            if action.kind == ActionKind.CONFIRM:
                return self._render(
                    replace(
                        state,
                        page=Page.CONFIRM,
                        return_page=state.page,
                        pending_action=action.action_id,
                        pending_parameters=dict(action.parameters),
                        pending_revision=self._target(ref, fresh=True).revision if self._target(ref) else "",
                        confirmation=action.confirmation or f"Confirm {action.label.lower()}?",
                        notice="",
                    ),
                    selected=selected,
                ).render()
            target = self._target(ref)
            if target is None:
                return self._render(replace(state, notice="Pinned target is no longer available.")).render()
            if action.action_id == "connect" and target.state.get("security") == "open":
                return self._render(replace(state, page=Page.OPEN_WARNING, return_page=state.page,
                    pending_action=action.action_id, pending_parameters=dict(action.parameters), pending_revision=target.revision,
                    confirmation=f"{target.title} on {target.state.get('interface', 'the selected adapter')} is unsecured Wi-Fi. This network does not encrypt wireless traffic. Continue?",
                    notice="")).render()
            if action.action_id == "connect" and self._requires_persistence_choice(ref):
                return self._render(replace(state, page=Page.CONNECT_CHOICE, return_page=state.page, action_id="cancel", notice=""), selected=selected).render()
            return self._execute(state, action, selected)

        if state.page == Page.DETAILS:
            row = selected[0] if selected else None
            if row == "back":
                return self._return_to_parent(state)
            return self._render(replace(state, notice="Choose the Back row to return."), selected=selected).render()

        if state.page == Page.AUTH_CONFIRM:
            info = selected[1] if selected else {}
            if state.pending is None or info.get("target") != (state.target.to_json() if state.target else None):
                return self._render(replace(state, notice="Pairing confirmation target changed; no reply was sent.")).render()
            if info.get("decision") not in {"confirm", "cancel"}:
                return self._render(state).render()
            self._authentication_prompt = ""
            result = self.backend.respond_confirmation(state.pending, info["decision"] == "confirm")
            return self._handle_operation_result(state, result, state.pending_action)

        if state.page in {Page.CONFIRM, Page.OPEN_WARNING}:
            row_info = selected[1] if selected else {}
            if row_info.get("target") is not None and TargetRef.from_json(row_info["target"]) != state.target:
                return self._render(replace(state, notice="Confirmation target changed; no operation was run."), selected=selected).render()
            if row_info.get("decision") == "cancel":
                return self._return_to_parent(replace(state, action_id=state.pending_action, notice="Cancelled; no change was submitted."))
            if row_info.get("decision") == "confirm":
                target = self._target(state.target, fresh=True) if state.target else None
                action = self._current_action(state.pending_action, state.target, fresh=True) if state.target else None
                if target is None or action is None:
                    return self._return_to_parent(replace(state, action_id="details", notice="Target changed during confirmation; review current state."))
                if dict(action.parameters) != dict(state.pending_parameters):
                    self._target_actions(target.ref, fresh=True)
                    return self._return_to_parent(replace(state, action_id=action.action_id, notice="Target state changed; review the updated action before retrying."))
                if state.page == Page.OPEN_WARNING:
                    if target.state.get("security") != "open" or target.revision != state.pending_revision:
                        return self._return_to_parent(replace(state, action_id="connect", notice="Network security or identity changed; review it before connecting."))
                    if self._requires_persistence_choice(target.ref):
                        return self._render(replace(state, page=Page.CONNECT_CHOICE, return_page=state.return_page,
                                                   action_id="cancel", notice="")).render()
                return self._submit(state, action, target.revision)
            return self._render(replace(state, notice="Choose Cancel or the named confirmation row."), selected=selected).render()

        if state.page == Page.CONNECT_CHOICE:
            row_info = selected[1] if selected else {}
            if row_info.get("target") is not None and TargetRef.from_json(row_info["target"]) != state.target:
                return self._render(replace(state, notice="Connection target changed; no request was submitted."), selected=selected).render()
            persistence = row_info.get("persistence")
            if persistence == "cancel":
                return self._return_to_parent(replace(state, action_id="connect", notice="Cancelled; no connection was submitted."))
            if persistence in {"remember", "once"}:
                action = self._current_action("connect", state.target, fresh=True) if state.target else None
                target = self._target(state.target, fresh=True) if state.target else None
                if action is None or target is None:
                    return self._render(replace(state, page=state.parent_page or Page.TARGET, action_id="details", notice="Network is no longer available."), selected=selected).render()
                if not self._requires_persistence_choice(target.ref):
                    return self._return_to_parent(replace(state, action_id="connect", notice="Network profile state changed; review the current connection action."))
                parameters = dict(action.parameters)
                parameters.pop("persistence_choice_required", None)
                parameters["persistence"] = str(persistence)
                return self._submit(state, replace(action, parameters=parameters), target.revision)
            return self._render(replace(state, notice="Choose remember, once, or Cancel."), selected=selected).render()

        if state.page == Page.PENDING:
            if state.action_id == "close-menu":
                return None
            if state.action_id in {"cancel-connection", "stop-waiting", "cancel-pairing"}:
                if state.pending is None:
                    return self._render(replace(state, notice="No owned pending request is available to cancel."), selected=selected).render()
                result = self.backend.cancel(state.pending)
                if result.kind == ResultKind.CANCELLED:
                    if result.target:
                        self._targets[result.target.ref] = result.target
                    return self._return_to_parent(replace(state, action_id=state.pending_action or "connect", pending=None, notice=result.message or "Connection cancellation completed."))
                return self._handle_pending_result(state, result)
            return self._render(replace(state, notice="Choose Close menu or the pending operation action."), selected=selected).render()

        return self._render(replace(state, notice="No action is available on this page."), selected=selected).render()

    def _execute(self, state: UIState, action: ActionSpec, selected: tuple[str, Mapping[str, object]] | None) -> str:
        target = self._target(state.target, fresh=True) if state.target else None
        current = self._current_action(action.action_id, state.target, fresh=True) if state.target else None
        if target is None or current is None:
            return self._render(replace(state, notice="The selected target or operation is no longer available."), selected=selected).render()
        if dict(current.parameters) != dict(state.visible_action_parameters or {}):
            self._target_actions(target.ref, fresh=True)
            return self._render(replace(state, notice="Observed state changed; the action label was updated. Review before continuing."), selected=selected).render()
        return self._submit(state, current, target.revision)

    def _submit(self, state: UIState, action: ActionSpec, revision: str) -> str:
        if state.target is None:
            return self._render(replace(state, notice="No pinned target is available." )).render()
        request = OperationRequest(
            invocation_id=self.invocation_id,
            request_id=str(uuid.uuid4()),
            target=state.target,
            action_id=action.action_id,
            expected_revision=revision,
            parameters=dict(action.parameters),
        )
        result = self.backend.execute(request)
        if result.kind == ResultKind.NEEDS_SECRET:
            if result.pending is None:
                return self._render(replace(state, notice="Backend requested a credential without an owned request." )).render()
            if result.persistence_required:
                self.backend.cancel(result.pending)
                return self._render(replace(state, notice="Backend needs a persistence choice before credentials; no request was submitted." )).render()
            raw_secret = self.prompt_secret(result.secret_prompt or "Network password")
            if raw_secret is None or len(raw_secret) == 0:
                self.backend.cancel(result.pending)
                page = self._operation_return_page(state)
                return self._render(replace(state, page=page, return_page=None if page == Page.TARGET else state.return_page, notice="Credential entry cancelled; no connection was submitted." )).render()
            stream = io.BytesIO(raw_secret)
            try:
                secret_result = self.backend.provide_secret(result.pending, stream)
            finally:
                try:
                    view = stream.getbuffer()
                    view[:] = b"\x00" * len(view)
                    view.release()
                except (BufferError, ValueError):
                    pass
                stream.close()
                raw_secret[:] = b"\x00" * len(raw_secret)
            return self._handle_operation_result(state, secret_result, action.action_id)
        return self._handle_operation_result(state, result, action.action_id)

    def _handle_operation_result(self, state: UIState, result: OperationResult, action_id: str) -> str:
        self._authentication_prompt = result.confirmation_prompt or result.display_prompt
        if result.target:
            self._targets[result.target.ref] = result.target
            self._actions.pop(result.target.ref, None)
        if result.kind in {ResultKind.PENDING, ResultKind.NEEDS_CONFIRMATION}:
            if result.pending is None:
                return self._render(replace(state, notice="Pending result has no owned request handle." )).render()
            return_page = self._operation_return_page(state)
            return self._render(
                replace(
                    state,
                    page=Page.AUTH_CONFIRM if result.kind == ResultKind.NEEDS_CONFIRMATION else Page.PENDING,
                    return_page=return_page,
                    pending=result.pending,
                    pending_action=action_id,
                    pending_parameters={},
                    pending_revision=result.target.revision if result.target else "",
                    pending_polls=0,
                    action_id="close-menu",
                    notice=result.message,
                )
            ).render()
        if result.kind in {ResultKind.COMPLETE, ResultKind.CANCELLED}:
            self._target_actions(result.target.ref, fresh=True) if result.target else None
            page = self._operation_return_page(state)
            return self._render(replace(state, page=page, return_page=None if page == Page.TARGET else state.return_page, pending=None, action_id=action_id, pending_action="", notice=result.message)).render()
        if result.kind == ResultKind.NEEDS_SECRET:
            return self._render(replace(state, notice="Credential request needs a follow-up action." )).render()
        page = self._operation_return_page(state)
        return self._render(replace(state, page=page, return_page=None if page == Page.TARGET else state.return_page, pending=None, action_id=action_id, notice=result.message or "Operation failed; observed state was not changed." )).render()

    def _handle_pending_result(self, state: UIState, result: OperationResult) -> str:
        self._authentication_prompt = result.confirmation_prompt or result.display_prompt
        if result.kind == ResultKind.NEEDS_CONFIRMATION:
            return self._handle_operation_result(state, result, state.pending_action)
        if result.kind == ResultKind.COMPLETE:
            if result.target:
                self._targets[result.target.ref] = result.target
                self._target_actions(result.target.ref, fresh=True)
            page = state.return_page or state.parent_page or Page.TARGET
            return self._render(replace(state, page=page, return_page=None if page == Page.TARGET else state.return_page, pending=None, action_id=state.pending_action or "details", notice=result.message)).render()
        if result.kind == ResultKind.NEEDS_SECRET:
            if result.pending is None:
                return self._render(replace(state, notice="Backend requested a credential without an owned request." )).render()
            raw_secret = self.prompt_secret(result.secret_prompt or "Network password")
            if raw_secret is None or len(raw_secret) == 0:
                cancelled = self.backend.cancel(result.pending)
                if cancelled.kind == ResultKind.CANCELLED:
                    return self._return_to_parent(
                        replace(state, action_id=state.pending_action or "connect", pending=None, notice="Credential entry cancelled; connection request cancelled.")
                    )
                return self._render(replace(state, pending_polls=min(MAX_PENDING_POLLS, state.pending_polls + 1), notice="Credential entry cancelled; request cancellation was requested." )).render()
            stream = io.BytesIO(raw_secret)
            try:
                next_result = self.backend.provide_secret(result.pending, stream)
            finally:
                try:
                    view = stream.getbuffer()
                    view[:] = b"\x00" * len(view)
                    view.release()
                except (BufferError, ValueError):
                    pass
                stream.close()
                raw_secret[:] = b"\x00" * len(raw_secret)
            return self._handle_operation_result(state, next_result, state.pending_action)
        if result.kind == ResultKind.PENDING:
            if state.pending_polls + 1 >= MAX_PENDING_POLLS:
                return self._render(replace(state, pending_polls=MAX_PENDING_POLLS, notice="Status unknown after the bounded observation window. Reopen to read current state." )).render()
            return self._render(replace(state, pending_polls=state.pending_polls + 1, notice=result.message or "Still in progress." )).render()
        if result.kind in {ResultKind.ERROR, ResultKind.UNAVAILABLE, ResultKind.CANCELLED}:
            return self._handle_operation_result(state, result, state.pending_action)
        return self._render(replace(state, notice="Unknown pending result; no follow-up was started." )).render()

    def _poll_pending(self, state: UIState) -> str:
        if state.page != Page.PENDING or state.pending is None:
            return self._render(state).render()
        if state.pending_polls >= MAX_PENDING_POLLS:
            return self._render(replace(state, notice="Status unknown after the bounded observation window. Reopen to read current state." )).render()
        result = self.backend.refresh(state.pending)
        if result.target:
            self._targets[result.target.ref] = result.target
        if result.kind == ResultKind.COMPLETE:
            if result.target:
                self._target_actions(result.target.ref, fresh=True)
            return self._render(replace(state, page=state.return_page or state.parent_page or Page.TARGET, return_page=None, pending=None, action_id=state.pending_action or "details", notice=result.message)).render()
        if result.kind == ResultKind.NEEDS_SECRET:
            return self._handle_pending_result(state, result)
        if result.kind == ResultKind.PENDING:
            return self._handle_pending_result(state, result)
        return self._handle_pending_result(state, result)

    @staticmethod
    def _operation_return_page(state: UIState) -> Page:
        if state.page in {Page.PENDING, Page.AUTH_CONFIRM}:
            return state.return_page or state.parent_page or Page.TARGET
        if state.page in {Page.CONFIRM, Page.OPEN_WARNING, Page.CONNECT_CHOICE}:
            return state.return_page or Page.TARGET
        if state.page in {Page.TARGET, Page.ADJUST}:
            return state.page
        return state.return_page or Page.TARGET

    def _refresh(self, state: UIState, selected: tuple[str, Mapping[str, object]] | None) -> str:
        if state.page in {Page.PENDING, Page.AUTH_CONFIRM}:
            return self._poll_pending(state)
        if state.page == Page.LIST:
            self._refresh_inventory()
            return self._render(replace(state, notice="Inventory refreshed."), selected=selected).render()
        if state.target is not None:
            target = self._target(state.target, fresh=True)
            if target is not None:
                self._target_actions(target.ref, fresh=True)
                state = replace(state, notice="Target state refreshed.")
            else:
                state = replace(state, notice="Pinned target is unavailable; return to the list to choose another.")
        return self._render(state, selected=selected).render()

    def _cycle(
        self,
        state: UIState,
        selected: tuple[str, Mapping[str, object]] | None,
        direction: int,
    ) -> str:
        if state.page in {Page.DETAILS, Page.CONFIRM, Page.OPEN_WARNING, Page.AUTH_CONFIRM, Page.CONNECT_CHOICE}:
            return self._render(state, selected=selected).render()
        target = self._target(state.target) if state.target else None
        actions, state = self._active_action(state, target)
        if len(actions) < 2:
            return self._render(state, selected=selected).render()
        index = next((i for i, action in enumerate(actions) if action.action_id == state.action_id), 0)
        index = (index + direction) % len(actions)
        action = actions[index]
        state = replace(
            state,
            action_id=action.action_id,
            visible_action_label=action.label,
            visible_action_parameters=dict(action.parameters),
            notice="",
        )
        return self._render(state, selected=selected).render()

    def _fresh_action(self, state: UIState) -> ActionSpec | None:
        if state.target is None:
            return None
        target = self._target(state.target, fresh=True)
        if target is None or target.availability != Availability.AVAILABLE:
            return None
        self._target_actions(state.target, fresh=True)
        actions = self._rows_action_set(state, target)
        return next((action for action in actions if action.action_id == state.action_id), None)

    def _current_action(self, action_id: str, ref: TargetRef, *, fresh: bool) -> ActionSpec | None:
        if fresh:
            self._target(ref, fresh=True)
            self._target_actions(ref, fresh=True)
        return next((item for item in self._target_actions(ref) if item.action_id == action_id), None)

    def _requires_persistence_choice(self, ref: TargetRef) -> bool:
        target = self._target(ref)
        return bool(target and (target.state.get("saved") is False or target.state.get("new_wifi") is True))

    def _load_details(self, ref: TargetRef) -> None:
        details = self.backend.details(ref)
        if details:
            self._details[ref] = details.facts
        else:
            self._details[ref] = ()

    def _return_to_parent(self, state: UIState) -> str:
        if state.page == Page.TARGET:
            parent = state.parent_page or Page.LIST
        else:
            parent = state.return_page or state.parent_page or Page.LIST
        if parent in {Page.TARGET, Page.ADJUST} and state.target is not None:
            self._target(state.target, fresh=True)
            self._target_actions(state.target, fresh=True)
            if state.page in {Page.CONFIRM, Page.OPEN_WARNING, Page.AUTH_CONFIRM, Page.CONNECT_CHOICE, Page.PENDING}:
                action_id = state.pending_action or state.action_id
            elif state.page == Page.DETAILS:
                action_id = "details" if parent == Page.TARGET else "volume-up"
            elif state.page == Page.ADJUST:
                action_id = "adjust"
            else:
                action_id = state.action_id
            return self._render(
                replace(
                    state,
                    page=parent,
                    parent_page=state.parent_page,
                    return_page=None if parent == Page.TARGET else state.return_page,
                    action_id=action_id,
                    pending=None,
                    pending_action="",
                    pending_parameters={},
                    notice=state.notice,
                )
            ).render()
        self._refresh_inventory()
        targets = self._inventory.targets if self._inventory else ()
        return_ref = state.return_target
        if return_ref not in {item.ref for item in targets}:
            return_ref = next((ref for ref in (state.return_next, state.return_previous) if ref and ref in {item.ref for item in targets}), None)
            notice = state.notice or "The previous target disappeared; selected the nearest surviving item."
        else:
            notice = state.notice
        if return_ref is None and targets:
            return_ref = targets[0].ref
        index = self._find_index(targets, return_ref)
        state = replace(
            state,
            page=Page.LIST,
            action_id="open",
            target=None,
            parent_page=None,
            return_page=None,
            pending=None,
            pending_action="",
            pending_parameters={},
            notice=notice,
        )
        return self._render(state, selected=("target", {"schema_version": 1, "row": "target", "ref": return_ref.to_json()}) if return_ref else None).render()

    def _return_from_adjust(self, state: UIState) -> str:
        if state.target is None:
            return self._return_to_parent(state)
        target = self._target(state.target, fresh=True)
        if target is None:
            return self._render(replace(state, notice="Pinned audio target is unavailable; no change was made." )).render()
        self._target_actions(target.ref, fresh=True)
        return self._render(replace(state, page=Page.TARGET, return_page=None, action_id="adjust", notice="")).render()

    def _return_target_index(self, state: UIState) -> int | None:
        return self._find_index(self._list_targets(), state.return_target)

    def _selected_target(self, selected: tuple[str, Mapping[str, object]] | None) -> TargetRef | None:
        if selected is None or selected[0] != "target":
            return None
        ref = selected[1].get("ref")
        try:
            return TargetRef.from_json(ref)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _find_index(targets: Sequence[TargetSnapshot], ref: TargetRef | None) -> int | None:
        if ref is None:
            return None
        return next((index for index, target in enumerate(targets) if target.ref == ref), None)

    def _fact_row(self, ref: TargetRef, fact: DetailFact) -> RofiRow:
        return RofiRow(
            text=_clean(fact.label, limit=256),
            display=f"<b>{_escape(fact.label, limit=256)}</b>\n<span size=\"smaller\">{_escape(fact.value)}</span>",
            info={"schema_version": 1, "row": "fact", "target": ref.to_json(), "fact": fact.label},
            meta=_clean(fact.label + " " + fact.value),
            selectable=False,
        )

    def _back_row(self, ref: TargetRef | None, detail: str) -> RofiRow:
        return RofiRow(
            text="Back",
            display=f"<b>Back</b>\n<span size=\"smaller\">{_escape(detail)}</span>",
            info={"schema_version": 1, "row": "back", "target": ref.to_json() if ref else None},
            meta=_clean(f"Back {detail}"),
            permanent=True,
        )

    @staticmethod
    def _message_row(title: str, detail: str, *, selectable: bool) -> RofiRow:
        return RofiRow(
            text=_clean(title, limit=256),
            display=f"<b>{_escape(title, limit=256)}</b>\n<span size=\"smaller\">{_escape(detail)}</span>",
            info={"schema_version": 1, "row": "status"},
            meta=_clean(title + " " + detail),
            selectable=selectable,
        )

    def _context_for(self, target: TargetSnapshot | None, state: UIState) -> str:
        if state.page == Page.PENDING:
            return state.notice or "Request submitted; status is still pending."
        if target is None:
            return "Target state is unavailable"
        return f"{target.status} · {target.summary}"

    def _prompt(self, state: UIState, target: TargetSnapshot | None = None, suffix: str = "") -> str:
        title = {
            Utility.NETWORK: "Network",
            Utility.AUDIO: "Audio",
            Utility.BLUETOOTH: "Bluetooth",
        }[self.utility]
        if target:
            title += " › " + target.title
        elif state.target:
            cached = self._targets.get(state.target)
            if cached:
                title += " › " + cached.title
        if suffix:
            title += " › " + suffix
        return _clean(title, limit=256)

    def _confirmation_label(self, state: UIState, target: TargetSnapshot | None) -> str:
        action = state.pending_action
        if action == "disconnect" and target:
            adapter = target.state.get("adapter", "adapter unknown")
            return f"Disconnect {target.title} on {adapter}"
        if action == "set-wifi-radio":
            return "Turn off global Wi-Fi radio" if dict(state.pending_parameters).get("desired_on") is False else "Turn on global Wi-Fi radio"
        if action == "set-adapter-power":
            return "Turn off Bluetooth adapter" if dict(state.pending_parameters).get("desired_on") is False else "Turn on Bluetooth adapter"
        return "Confirm operation"


def _find_index(targets: Sequence[TargetSnapshot], ref: TargetRef | None) -> int | None:
    if ref is None:
        return None
    return next((index for index, target in enumerate(targets) if target.ref == ref), None)
