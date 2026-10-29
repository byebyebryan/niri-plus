# Rofi controls: design review

Reviewed 2026-10-29 against `f497a07`, the published HTML snapshot, sibling
Plus picker source, installed Rofi `2.0.0-1` documentation and NetworkManager
`1.58.1-2` package metadata. No native UI, service, radio or device was operated.

**Verdict: keep the visual direction; resolve the interaction findings before
building full helpers.** The next implementation milestone is a bounded native
interaction proof, not a launcher replacement or fleet rollout.

The [illustration](../../design/rofi-controls/index.html) remains a visual
reference, not a complete behavioral specification. The
[implementation plan](rofi-controls-pass.md) records these review constraints.

## Keep

- Neutral Slate, the Plus frame and separated action/status areas.
- Green framed current connection/default rows; blue keyboard selection.
- Saved/paired emphasis without claiming connection. Default routing, mute
  and playback/recording stay separate facts.
- Compact rows, explicit unknown values, advanced-tool handoffs, independent
  Session/Clipboard ownership and Network → Audio → Bluetooth order.

No further palette or decoration pass is needed before native qualification.

## 1. Resolve row-specific native action labels — high priority

The HTML calls `paintSelection()` and `updateStrip()` on every cursor move.
Its primary action changes from Details on Home, to Connect on Studio, to
Turn off on the radio row. It also resets the action on each row change.
The existing Plus pickers keep fixed action sets within a view and update
their script headers at explicit callbacks.

Rofi's [script protocol](https://davatorium.github.io/rofi/current/rofi-script.5/)
does not establish an ordinary highlight-change script response. Its
[selection hook](https://davatorium.github.io/rofi/current/rofi-actions.5/)
runs a command. In upstream
[`2.0.0/source/view.c`](https://github.com/davatorium/rofi/blob/2.0.0/source/view.c),
`selection_changed_user_callback()` launches that command; it does not consume
its output as a new script frame. This is an integration gap, not proof that
the desired interaction is impossible.

Required proof: move with Up/Down and pointer between all three row types,
including filtered results, then press Enter without an intervening Tab.
The visible action must match the operation. Preserve caret, filter, identity
and native cancellation, including when background state changes.

Do not solve this with periodic list replacement, device I/O on highlight or
an implicit Rofi fork. If a small supported route cannot pass, use fixed
list-level Open controls / Details actions and put device-specific operations
in a focused device view. Choose that fallback explicitly before building
Network. Never ship a stale label or silently reinterpret Enter.

## 2. Make ordinary Audio actions repeatable — medium priority

The Audio menu exposes up to five action choices. In the walkthrough,
Volume +5% opens a result screen; returning resets the action to Details,
and the sample stays at 45%. This must not become the adjustment contract.

A successful small change should update the observed value inline, preserving
device, filter and active action. Three Enter presses from Volume +5% should
produce 45 → 50 → 55 → 60%, subject to observed native state. Mute changes to
Unmute and back without a success dialog. Errors remain visible/recoverable;
volume adjustment must not unmute a microphone.

If the strip is crowded, use a focused Adjust view with a small fixed action
set. Preserve native hardware keys as the direct volume path. Set default
changes only the relevant input/output default; do not move old streams silently.

## 3. Name targets and actual disruption scope — high priority

Disconnect and radio-off both show generic “selected adapter” copy. The
Disconnect confirmation does not name Home or wlan0. This is insufficient
when more than one connection or adapter exists.

- Disconnect names the profile/network and interface, with Cancel selected.
- Wi-Fi off identifies a global Wi-Fi radio control and enumerates affected
  managed Wi-Fi interfaces/connections; Ethernet remains enabled.
- Bluetooth off names the adapter and connected devices affected; pairings stay.
- A network replacement exposes its context before submission, such as Studio
  on wlan0 replacing Home. Do not pre-disconnect the old connection.

NetworkManager's top-level
[`WirelessEnabled`](https://networkmanager.dev/docs/api/latest/gdbus-org.freedesktop.NetworkManager.html)
property is the shared Wi-Fi switch; an adapter-specific disconnect is a
different operation. Do not describe a global switch as wlan0-only. Hardware
blocks and permission failures need accurate explanations. Revalidate target
and impact at execution.

## 4. Exercise fictional state transitions — medium priority

Most sample data is fixed: after simulated Atelier success, Home is still
marked connected. Bluetooth Connect returns a generic sample result while
headphones remain disconnected. Audio values/defaults likewise do not change.

This is acceptable for a labeled visual study, but end-to-end interaction review
is incomplete. Existing browser check counts do not establish these semantics,
and none establishes native backend behavior.

Before each helper's feature implementation, add its minimal stateful scene:

| Scene | Required visible transition |
| --- | --- |
| Network | Successful replacement moves the connected marker/frame. Failure and cancellation retain the appropriate observed result. Saved/new/persistence distinctions remain accurate. |
| Audio | Volume/mute update inline. Changing the output default moves only that default marker, retaining the input default. |
| Bluetooth | Pending → connected/disconnected/error. Actions follow the new state; paired and battery-unknown remain independent. |

Keep fixtures inside the report; do not operate user devices to make it look
functional. Audio/Bluetooth scene work precedes their own slices and need not
delay the first Rofi/Network proof.

## Native acceptance and evidence

The [theme documentation](https://davatorium.github.io/rofi/current/rofi-theme.5/)
supports combined active/selected states. The model is plausible; CSS remains
browser evidence. The first fixture must qualify green frame plus blue focus,
label contrast, action/status separation, long/CJK labels, duplicate SSIDs on
distinct adapters, empty-filter cancellation and fractional-scale readability.
Keep rank/order stable during navigation and retain stable operation identities.

Credential storage/coexistence, secondary connections, pending refresh and
targeted cancellation retain their separate backend proof. No native mode
experiment, credential entry, guest boot, installation or apply occurs here.

The owned browser walkthrough reproduced findings 2–4. Duplicate Studio rows
were distinguishable by wlan0/wlan1; long CJK/markup-like text stayed within
375/768/1280px layouts. An empty filter remained cancellable. No browser errors
occurred. Evidence stays in the private design-review lab directory.

Exit order: retain appearance → qualify native action model → correct Network
fictional transitions and target/scope confirmations → pass lifecycle/credential
proof → implement Network. Qualify repeatable Audio and Bluetooth transitions
before their own later slices.

This review changes the plan, not the current prototype or installed desktop.
