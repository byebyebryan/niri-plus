import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "components/desktop/lib"
sys.path.insert(0, str(LIB))

SPEC = importlib.util.spec_from_file_location("controls_test_appearance", ROOT / "components/appearance/render.py")
appearance_renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(appearance_renderer)

from niri_plus_controls.app import ControlsApp, Page
from niri_plus_controls.appearance import load_appearance
from niri_plus_controls.fixture import FixtureBackend
from niri_plus_controls.model import TargetRef, Utility
from niri_plus_controls.rofi import RECORD_SEPARATOR, ScriptRequest


def private_appearance():
    identity = json.loads((ROOT / "design/identity.json").read_text())
    artifacts = appearance_renderer.render(identity)
    directory = tempfile.TemporaryDirectory(prefix="controls-appearance-test-")
    path = Path(directory.name) / "controls-appearance.json"
    path.write_text(artifacts["controls-appearance.json"])
    return directory, load_appearance(path)


def selected_target(ref):
    return {"schema_version": 1, "row": "target", "ref": ref.to_json()}


def callback(app, retv, info=None):
    state = app._resume_state
    data = state.payload() if state is not None else {}
    output = app.handle(ScriptRequest(retv, data, info))
    return output


def initial_app(utility, backend=None, prompt_secret=None):
    directory, appearance = private_appearance()
    backend = backend or FixtureBackend(utility)
    app = ControlsApp(
        utility,
        uuid.uuid4().hex,
        backend,
        appearance,
        prompt_secret=prompt_secret or (lambda _prompt: None),
    )
    callback(app, 0)
    return directory, app, backend


def parse_records(frame):
    """Decode enough of a rendered frame to inspect Rofi's typed row metadata."""
    initial_marker = "\x00delim\x1f\\x1e\n"
    if initial_marker in frame:
        rows = frame.split(initial_marker, 1)[1]
        return [record for record in rows.split(RECORD_SEPARATOR) if "\x00info\x1f" in record]
    return [record for record in frame.split(RECORD_SEPARATOR) if "\x00info\x1f" in record]


def row_info(frame):
    # Rofi row metadata uses field separators and a JSON info value.
    info_rows = []
    for record in parse_records(frame):
        if "\x00" not in record:
            continue
        _, fields = record.split("\x00", 1)
        values = fields.split("\x1f")
        if "info" in values:
            info_rows.append(json.loads(values[values.index("info") + 1]))
    return info_rows


class ControlsFrontend(unittest.TestCase):
    def test_alt_r_scans_only_the_selected_wifi_adapter_without_leaving_editable_list(self):
        from dataclasses import replace
        from niri_plus_controls.model import ActionKind, ActionSpec, OperationResult, PendingRef, ResultKind

        backend = FixtureBackend(Utility.NETWORK)
        selected = TargetRef("access-point", "nm:ap:studio:wlan1:02")
        backend._records[selected].state["device_path"] = "/device/wlan1"
        original_snapshot, original_target, original_actions = backend.snapshot, backend.target, backend.actions
        sample = original_target(selected)
        device = replace(sample, ref=TargetRef("wifi-device", "adapter1"), title="wlan1",
                         state={"device_path": "/device/wlan1"})
        backend.snapshot = lambda utility: replace(original_snapshot(utility), targets=original_snapshot(utility).targets + (device,))
        backend.target = lambda ref: device if ref == device.ref else original_target(ref)
        backend.actions = lambda ref: (ActionSpec("rescan", "Rescan", ActionKind.OPERATION),) if ref == device.ref else original_actions(ref)
        requests = []
        backend.execute = lambda request: requests.append(request) or OperationResult(ResultKind.PENDING, "Scan accepted", device,
            PendingRef("scan", device.ref, 1))
        app, _ = self.make(Utility.NETWORK, backend=backend)
        frame = callback(app, 10, selected_target(selected))
        self.assertEqual([(request.target, request.action_id) for request in requests], [(device.ref, "rescan")])
        self.assertEqual(app._resume_state.page, Page.LIST)
        self.assertIsNone(app._resume_state.pending)
        self.assertIn("Scan accepted", frame)

    def test_open_wifi_warning_precedes_persistence_and_rechecks_security(self):
        app, backend = self.make(Utility.NETWORK)
        target = TargetRef("access-point", "nm:ap:studio:wlan1:02")
        record = backend._records[target]
        record.state["security"] = "open"
        selected = selected_target(target)
        callback(app, 1, selected)
        while app._resume_state.action_id != "connect":
            callback(app, 16, selected)
        frame = callback(app, 1, selected)
        self.assertEqual(app._resume_state.page, Page.OPEN_WARNING)
        self.assertIn("does not encrypt wireless traffic", frame)
        choices = row_info(frame)
        self.assertEqual(choices[0]["decision"], "cancel")
        callback(app, 1, choices[0])
        self.assertFalse(backend.events)
        frame = callback(app, 1, selected)
        confirm = next(info for info in row_info(frame) if info["decision"] == "confirm")
        record.state["security"] = "wpa-psk"
        record.revision += 1
        callback(app, 1, confirm)
        self.assertEqual(app._resume_state.page, Page.TARGET)
        self.assertFalse(backend.events, "Changed open-network approval cannot submit a connection")

    def test_pairing_confirmation_is_cancel_first_and_authentication_stays_out_of_metadata(self):
        from niri_plus_controls.model import OperationResult, PendingRef, ResultKind

        app, backend = self.make(Utility.BLUETOOTH)
        target = backend.snapshot(Utility.BLUETOOTH).targets[0]
        callback(app, 1, selected_target(target.ref))
        pending = PendingRef("owned-pairing", target.ref, 1)
        sample_code = "004219"
        output = app._handle_operation_result(app._resume_state,
            OperationResult(ResultKind.NEEDS_CONFIRMATION, "Confirm pairing", target, pending,
                            confirmation_prompt="Does the device display " + sample_code + "?"), "pair-device")
        self.assertEqual(app._resume_state.page, Page.AUTH_CONFIRM)
        self.assertIn(sample_code, output)
        self.assertNotIn(sample_code, json.dumps(app._resume_state.payload()))
        choices = row_info(output)
        self.assertEqual(choices[0]["decision"], "cancel")
        self.assertNotIn(sample_code, json.dumps(choices))
        responses = []
        backend.respond_confirmation = lambda handle, accepted: responses.append((handle, accepted)) or OperationResult(ResultKind.CANCELLED, "Pairing declined", target)
        callback(app, 1, choices[0])
        self.assertEqual(responses, [(pending, False)])
        self.assertEqual(app._resume_state.page, Page.TARGET)
        self.assertEqual(app._authentication_prompt, "")

    def test_pending_failure_returns_to_pinned_target_without_polling_a_dead_handle(self):
        from niri_plus_controls.model import OperationResult, PendingRef, ResultKind

        app, backend = self.make(Utility.BLUETOOTH)
        target = backend.snapshot(Utility.BLUETOOTH).targets[0]
        callback(app, 1, selected_target(target.ref))
        app._handle_operation_result(app._resume_state,
            OperationResult(ResultKind.PENDING, "Connecting", target, PendingRef("attempt", target.ref, 1)), "connect")
        output = app._handle_pending_result(app._resume_state, OperationResult(ResultKind.ERROR, "Device removed"))
        self.assertEqual(app._resume_state.page, Page.TARGET)
        self.assertIsNone(app._resume_state.pending)
        self.assertIn("Device removed", output)

    def test_new_rofi_process_negotiates_delimiter_on_every_resumed_page(self):
        from dataclasses import replace

        app, _backend = self.make(Utility.AUDIO)
        for page in (Page.TARGET, Page.ADJUST, Page.PENDING, Page.DETAILS, Page.CONFIRM, Page.CONNECT_CHOICE):
            app._resume_state = replace(app._resume_state, page=page)
            output = app.handle(ScriptRequest(0, {}, None))
            self.assertIn("\x00delim\x1f\\x1e\n", output, page)
            headers = output.split("\x00delim\x1f\\x1e\n", 1)[0]
            self.assertNotIn(RECORD_SEPARATOR, headers, page)

    def tearDown(self):
        for name in ("app", "backend", "appearance_dir"):
            value = getattr(self, name, None)
            if name == "backend" and value:
                value.close()
            elif name == "appearance_dir" and value:
                value.cleanup()

    def make(self, utility, backend=None, prompt_secret=None):
        self.appearance_dir, self.app, self.backend = initial_app(utility, backend, prompt_secret)
        return self.app, self.backend

    def test_inventory_rows_keep_duplicate_native_ids_and_fixed_action_pair(self):
        app, backend = self.make(Utility.NETWORK)
        frame = callback(app, 0)
        studios = [
            info for info in row_info(frame)
            if info.get("row") == "target" and info["ref"]["stable_id"].startswith("nm:ap:studio:")
        ]
        self.assertEqual(
            {item["ref"]["stable_id"] for item in studios},
            {"nm:ap:studio:wlan0:01", "nm:ap:studio:wlan1:02"},
        )
        actions = app._rows_action_set(app._resume_state, None)
        self.assertEqual([(action.action_id, action.label) for action in actions], [("open", "Open"), ("details", "Details")])
        selected = TargetRef("access-point", "nm:ap:studio:wlan1:02")
        frame = callback(app, 16, selected_target(selected))
        self.assertEqual(app._resume_state.action_id, "details")
        self.assertEqual(app._resume_state.page, Page.LIST)
        self.assertFalse(backend.events, "Tab action cycling must not run backend I/O")
        frame = callback(app, 17, selected_target(selected))
        self.assertEqual(app._resume_state.action_id, "open")
        self.assertFalse(backend.events)
        self.assertIn("Studio", frame)
        self.assertIn("\x00new-selection\x1f2", frame)

    def test_pinned_target_rejects_other_duplicate_row_identity(self):
        app, backend = self.make(Utility.NETWORK)
        target = TargetRef("access-point", "nm:ap:studio:wlan1:02")
        callback(app, 1, selected_target(target))
        self.assertEqual(app._resume_state.page, Page.TARGET)
        other = TargetRef("access-point", "nm:ap:studio:wlan0:01")
        callback(app, 1, selected_target(other))
        self.assertEqual(app._resume_state.target, target)
        self.assertIn("identity did not match", app._resume_state.notice)
        self.assertFalse(backend.events)

    def test_audio_adjust_repeats_inline_and_mute_keeps_explicit_intent(self):
        app, backend = self.make(Utility.AUDIO)
        target = TargetRef("audio-output", "pw:device:usb-speakers:71")
        callback(app, 1, selected_target(target))
        self.assertEqual(app._resume_state.page, Page.TARGET)
        callback(app, 16, selected_target(target))
        callback(app, 16, selected_target(target))
        self.assertEqual(app._resume_state.action_id, "adjust")
        frame = callback(app, 1, selected_target(target))
        self.assertEqual(app._resume_state.page, Page.ADJUST)
        for expected in (50, 55, 60):
            frame = callback(app, 1, selected_target(target))
            self.assertEqual(app._resume_state.action_id, "volume-up")
            self.assertEqual(app._targets[target].state["volume_percent"], expected)
        self.assertIn("60%", frame)
        for _ in range(2):
            callback(app, 16, selected_target(target))
        self.assertEqual(app._resume_state.action_id, "mute")
        self.assertIs(app._resume_state.visible_action_parameters["desired_muted"], True)
        frame = callback(app, 1, selected_target(target))
        self.assertTrue(app._targets[target].state["muted"])
        executed = [event for event in backend.events if event["event"] == "execute"]
        self.assertIs(executed[-1]["parameters"]["desired_muted"], True)
        self.assertIn("Unmute", frame)
        # An external mute update after the label was shown must invalidate the
        # stale desired state before it reaches the backend.
        backend._records[target].state["muted"] = False
        executed_before = len(executed)
        frame = callback(app, 1, selected_target(target))
        self.assertEqual(len([event for event in backend.events if event["event"] == "execute"]), executed_before)
        self.assertIn("Observed state changed", app._resume_state.notice)
        self.assertIn("Mute", frame)

    def test_confirm_cancel_is_first_and_details_back_preserves_stable_target(self):
        app, backend = self.make(Utility.NETWORK)
        target = TargetRef("connection", "nm:uuid:home-001")
        callback(app, 1, selected_target(target))
        callback(app, 16, selected_target(target))
        callback(app, 16, selected_target(target))
        self.assertEqual(app._resume_state.action_id, "disconnect")
        frame = callback(app, 1, selected_target(target))
        self.assertEqual(app._resume_state.page, Page.CONFIRM)
        choices = row_info(frame)
        self.assertEqual(choices[0]["decision"], "cancel")
        self.assertEqual(app._render_confirmation(app._resume_state, backend.target(target)).selected_index, 0)
        callback(app, 1, choices[0])
        self.assertEqual(app._resume_state.page, Page.TARGET)
        self.assertFalse(backend.events)

        # Home offers Details on the target page; Back returns to the same
        # pinned native identity, then its Back returns to the selected row.
        callback(app, 16, selected_target(target))
        self.assertEqual(app._resume_state.action_id, "details")
        frame = callback(app, 1, selected_target(target))
        self.assertEqual(app._resume_state.page, Page.DETAILS)
        back = next(item for item in row_info(frame) if item.get("row") == "back")
        callback(app, 1, back)
        self.assertEqual(app._resume_state.page, Page.TARGET)
        self.assertEqual(app._resume_state.target, target)
        callback(app, 16, selected_target(target))
        self.assertEqual(app._resume_state.action_id, "back")
        frame = callback(app, 1, selected_target(target))
        self.assertEqual(app._resume_state.page, Page.LIST)
        self.assertEqual(app._resume_state.return_target, target)
        self.assertIn("Home", frame)
        self.assertFalse(backend.events)

    def test_new_network_persistence_choice_then_one_pending_result_and_secret_pipe(self):
        sentinel = bytearray(b"fakesecretneverpersist9xq")
        app, backend = self.make(Utility.NETWORK, prompt_secret=lambda _prompt: sentinel)
        target = TargetRef("access-point", "nm:ap:studio:wlan1:02")
        callback(app, 1, selected_target(target))
        callback(app, 16, selected_target(target))
        callback(app, 16, selected_target(target))
        self.assertEqual(app._resume_state.action_id, "connect")
        frame = callback(app, 1, selected_target(target))
        self.assertEqual(app._resume_state.page, Page.CONNECT_CHOICE)
        choices = row_info(frame)
        self.assertEqual(choices[0]["persistence"], "cancel")
        once = next(item for item in choices if item.get("persistence") == "once")
        frame = callback(app, 1, once)
        self.assertEqual(app._resume_state.page, Page.PENDING)
        self.assertEqual(app._resume_state.return_page, Page.TARGET)
        self.assertNotIn(b"fakesecretneverpersist9xq", frame.encode())
        self.assertFalse(any(b"fakesecretneverpersist9xq" in json.dumps(event).encode() for event in backend.events))
        self.assertEqual(sentinel, bytearray(len(sentinel)))
        frame = callback(app, 28)
        self.assertEqual(app._resume_state.page, Page.TARGET)
        self.assertEqual(len([event for event in backend.events if event["event"] == "execute"]), 1)
        self.assertEqual(len([event for event in backend.events if event["event"] == "secret-received"]), 1)
        self.assertEqual(len([event for event in backend.events if event["event"] == "pending-refresh"]), 1)
        self.assertNotIn("fakesecretneverpersist9xq", frame)

    def test_saved_network_profile_does_not_offer_a_new_persistence_choice(self):
        app, backend = self.make(Utility.NETWORK, prompt_secret=lambda _prompt: None)
        target = TargetRef("access-point", "nm:ap:studio:wlan0:01")
        selected = selected_target(target)
        callback(app, 1, selected)
        while app._resume_state.action_id != "connect":
            callback(app, 16, selected)
        frame = callback(app, 1, selected)
        self.assertNotEqual(app._resume_state.page, Page.CONNECT_CHOICE)
        self.assertNotIn("remember or once", frame)
        execute = next(event for event in backend.events if event.get("event") == "execute")
        self.assertEqual(execute["parameters"], {})
        self.assertEqual(app._resume_state.page, Page.TARGET)


if __name__ == "__main__":
    unittest.main()
