"""Rofi 2.0 script-mode wire codec and rendering helpers."""

from __future__ import annotations

from dataclasses import dataclass
import html
import json
import os
import re
from typing import Mapping, Sequence

from .appearance import ControlsAppearance
from .model import ActionSpec, TargetSnapshot


RECORD_SEPARATOR = "\x1e"
FIELD_SEPARATOR = "\x1f"
ROFI_RETV_SELECTED = 1
ROFI_RETV_CUSTOM_1 = 10
ROFI_RETV_CUSTOM_7 = 16
ROFI_RETV_CUSTOM_8 = 17
ROFI_RETV_CUSTOM_19 = 28
MAX_INFO_BYTES = 8192
MAX_DATA_BYTES = 16 * 1024
MAX_FRAME_BYTES = 512 * 1024
MAX_ROWS = 4096
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


class RofiProtocolError(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise RofiProtocolError(f"duplicate JSON field: {key}")
        value[key] = item
    return value


def _parse_json(raw: str | None, *, limit: int, label: str) -> object:
    if raw is None or len(raw.encode("utf-8")) > limit:
        raise RofiProtocolError(f"{label} is missing or exceeds its size limit")
    try:
        return json.loads(raw, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, UnicodeError, RecursionError) as error:
        raise RofiProtocolError(f"{label} is invalid JSON") from error


def _clean(value: str, *, limit: int = 4096) -> str:
    """Bound dynamic text and replace controls before escaping/rendering it."""

    value = _CONTROL.sub(" ", str(value)).replace("\u2028", " ").replace("\u2029", " ")
    value = " ".join(value.split())
    if len(value) > limit:
        value = value[: limit - 1] + "…"
    return value


def _escape(value: str, *, limit: int = 4096) -> str:
    return html.escape(_clean(value, limit=limit), quote=False)


@dataclass(frozen=True, slots=True)
class ScriptRequest:
    retv: int
    data: dict[str, object]
    info: dict[str, object] | None

    @classmethod
    def from_environment(cls, env: Mapping[str, str]) -> ScriptRequest:
        try:
            retv = int(env.get("ROFI_RETV", "0"))
        except ValueError as error:
            raise RofiProtocolError("ROFI_RETV is not an integer") from error
        if retv < 0 or retv > 28:
            raise RofiProtocolError("ROFI_RETV is outside the supported range")
        raw_data = env.get("ROFI_DATA")
        if raw_data:
            data = _parse_json(raw_data, limit=MAX_DATA_BYTES, label="ROFI_DATA")
            if not isinstance(data, dict):
                raise RofiProtocolError("ROFI_DATA must be an object")
        else:
            data = {}
        raw_info = env.get("ROFI_INFO")
        if raw_info:
            info = _parse_json(raw_info, limit=MAX_INFO_BYTES, label="ROFI_INFO")
            if not isinstance(info, dict):
                raise RofiProtocolError("ROFI_INFO must be an object")
        else:
            info = None
        return cls(retv=retv, data=data, info=info)


@dataclass(frozen=True, slots=True)
class RofiRow:
    text: str
    display: str
    info: Mapping[str, object]
    meta: str = ""
    active: bool = False
    urgent: bool = False
    selectable: bool = True
    permanent: bool = False


@dataclass(frozen=True, slots=True)
class RofiFrame:
    prompt: str
    message: str
    state: Mapping[str, object]
    rows: Sequence[RofiRow]
    selected_index: int | None = None
    initial: bool = False

    def render(self) -> str:
        if len(self.rows) > MAX_ROWS:
            raise RofiProtocolError("Rofi frame contains too many rows")
        headers = [
            _option("prompt", self.prompt),
            _option("message", self.message),
            _option("markup-rows", "true"),
            _option("use-hot-keys", "true"),
            _option("no-custom", "false"),
            _option("keep-filter", "true"),
            _option("keep-selection", "true"),
            _option("data", _json(self.state, MAX_DATA_BYTES, "ROFI_DATA")),
        ]
        if self.selected_index is not None:
            if not 0 <= self.selected_index < len(self.rows):
                raise RofiProtocolError("selected row index is outside the frame")
            headers.append(_option("new-selection", str(self.selected_index)))
        if self.initial:
            headers.append(_option("delim", r"\x1e"))
        row_records = [_render_row(row) for row in self.rows]
        if self.initial:
            # Rofi reads script headers one per line. The delim header switches
            # only the entry records that follow it to RS; display markup may
            # then contain real newlines without becoming new rows.
            output = "\n".join(headers) + "\n" + RECORD_SEPARATOR.join(row_records) + RECORD_SEPARATOR
        else:
            output = RECORD_SEPARATOR.join([*headers, *row_records]) + RECORD_SEPARATOR
        if len(output.encode("utf-8")) > MAX_FRAME_BYTES:
            raise RofiProtocolError("Rofi frame exceeds its byte limit")
        return output


def _json(value: object, limit: int, label: str) -> str:
    raw = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    if len(raw.encode("utf-8")) > limit:
        raise RofiProtocolError(f"{label} exceeds its size limit")
    return raw


def _option(key: str, value: str) -> str:
    if any(char in key for char in ("\x00", FIELD_SEPARATOR, RECORD_SEPARATOR, "\n")):
        raise RofiProtocolError("invalid Rofi option name")
    if any(char in value for char in ("\x00", FIELD_SEPARATOR, RECORD_SEPARATOR)):
        raise RofiProtocolError(f"invalid separator in Rofi option {key}")
    return "\x00" + key + FIELD_SEPARATOR + value


def _render_row(row: RofiRow) -> str:
    options: list[str] = [
        "info",
        _json(row.info, MAX_INFO_BYTES, "row info"),
        "display",
        row.display,
        "meta",
        _clean(row.meta, limit=8192),
    ]
    if row.active:
        options.extend(("active", "true"))
    if row.urgent:
        options.extend(("urgent", "true"))
    if row.permanent:
        options.extend(("permanent", "true"))
    if not row.selectable:
        options.extend(("nonselectable", "true"))
    encoded = FIELD_SEPARATOR.join(options)
    if any(char in row.text for char in ("\x00", FIELD_SEPARATOR, RECORD_SEPARATOR, "\n")):
        raise RofiProtocolError("row filter text contains a protocol delimiter")
    if any(char in encoded for char in ("\x00", RECORD_SEPARATOR)):
        raise RofiProtocolError("row metadata contains a protocol delimiter")
    return row.text + "\x00" + encoded


def row_for_target(target: TargetSnapshot, appearance: ControlsAppearance) -> RofiRow:
    name = _escape(target.title, limit=1024)
    state = target.state
    connected = state.get("connected") is True
    is_default = state.get("is_default") is True
    current = target.active or connected or is_default
    saved = state.get("saved") is True
    paired = state.get("paired") is True
    muted = state.get("muted") is True

    labels: list[tuple[str, str]] = []
    if connected:
        labels.append(("Connected", appearance.colors["success"]))
    elif is_default:
        direction = str(state.get("direction", "output")).capitalize()
        labels.append((f"Default {direction.lower()}", appearance.colors["success"]))
    elif target.active:
        labels.append((target.status or "Current", appearance.colors["success"]))
    if saved:
        labels.append(("Saved", appearance.colors["focus"]))
    if paired:
        labels.append(("Paired", appearance.colors["focus"]))
    if "muted" in state and type(state.get("muted")) is bool:
        labels.append(("Muted" if muted else "Unmuted", appearance.colors["warning"] if muted else appearance.colors["secondary"]))
    if not labels:
        labels.append((target.status or "State unknown", appearance.colors["secondary"]))

    shown = {label.casefold() for label, _color in labels}
    detail_terms: list[str] = []
    for source in (target.status, target.summary):
        for raw_term in source.split(" · "):
            term = _clean(raw_term, limit=512)
            folded = term.casefold()
            if not term or folded in shown or folded in {item.casefold() for item in detail_terms}:
                continue
            detail_terms.append(term)
    state_line = f" <span foreground=\"{appearance.colors['separator']}\">·</span> ".join(
        f"<span foreground=\"{_escape(color)}\">{_escape(label, limit=256)}</span>"
        for label, color in labels
    )
    details_line = _escape(" · ".join(detail_terms) or "No additional state details")
    name_markup = f"<b>{name}</b>" if current or saved or paired else name
    markup = (
        f"{name_markup}\n"
        f"<span size=\"smaller\">{state_line} "
        f"<span foreground=\"{appearance.colors['secondary']}\">{details_line}</span></span>"
    )
    metadata = " ".join((target.title, target.summary, target.status, *target.filter_terms))
    info = {"schema_version": 1, "row": "target", "ref": target.ref.to_json()}
    return RofiRow(
        text=_clean(target.title, limit=1024),
        display=markup,
        info=info,
        meta=_clean(metadata, limit=8192),
        active=current,
        selectable=True,
    )


def row_for_action(action: ActionSpec, target: TargetSnapshot) -> RofiRow:
    label = _escape(action.label, limit=512)
    detail = action.confirmation or action.disabled_reason
    secondary = _escape(detail or target.summary)
    display = f"<b>{label}</b>\n<span size=\"smaller\">{secondary}</span>"
    info = {
        "schema_version": 1,
        "row": "action",
        "target": target.ref.to_json(),
        "action_id": action.action_id,
    }
    return RofiRow(
        text=_clean(action.label, limit=512),
        display=display,
        info=info,
        meta=_clean(f"{target.title} {target.summary} {action.label} {detail}", limit=8192),
        selectable=action.enabled,
    )


def message_for_actions(
    actions: Sequence[ActionSpec],
    selected_action: str,
    context: str,
    notice: str,
    appearance: ControlsAppearance,
) -> str:
    labels: list[str] = []
    for action in actions:
        safe = _escape(action.label, limit=256)
        if not action.enabled:
            if action.disabled_reason:
                safe += f" <span foreground=\"{appearance.colors['muted']}\">({_escape(action.disabled_reason, limit=256)})</span>"
            safe = f"<span foreground=\"{appearance.colors['muted']}\">{safe}</span>"
        elif action.action_id == selected_action:
            safe = f"<span foreground=\"{appearance.colors['accent']}\" weight=\"bold\">[{safe}]</span>"
        labels.append(safe)
    action_line = "Enter: " + " · ".join(labels)
    if len(actions) > 1:
        action_line += "  │  Tab: Cycle actions"
    sections = [action_line]
    safe_context = _escape(context, limit=1024)
    if safe_context:
        sections.extend(("──────────────", safe_context))
    safe_notice = _escape(notice, limit=1024)
    if safe_notice and safe_notice != safe_context:
        sections.append(safe_notice)
    return "\u2028\u2028".join(sections)


def message_for_rows(prompt: str, context: str, notice: str, appearance: ControlsAppearance) -> str:
    lines = [f"Enter: <span foreground=\"{appearance.colors['accent']}\" weight=\"bold\">[Choose]</span>"]
    safe_context = _escape(context, limit=1024)
    if safe_context:
        lines.extend(("──────────────", safe_context))
    safe_notice = _escape(notice, limit=1024)
    if safe_notice and safe_notice != safe_context:
        lines.append(safe_notice)
    return "\u2028\u2028".join(lines)


def selected_info(info: Mapping[str, object] | None) -> tuple[str, Mapping[str, object]] | None:
    """Return the typed row discriminator and its data without parsing labels."""

    if info is None or info.get("schema_version") != 1:
        return None
    row = info.get("row")
    if row not in {"target", "action", "choice", "fact", "back", "advanced"}:
        return None
    return str(row), info
