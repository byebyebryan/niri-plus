# Direct Rofi controls implementation receipt

Historical implementation receipt, 2026-10-29. The candidate results below
describe the implementation pass. **0.4.0 was subsequently published and
delivered to Carbon, Starship and Snap**; the [current recipe](../recipes/rofi-controls.md)
records the released tuple and acceptance limits. The numbered Arch reference
remains 0.3.1 pending its updated replay.

This opening records the implementation pass. The subsequent publication pass
uses the reviewed replacement tuple below; see the
[0.4.0 release and current setup recipe](../recipes/rofi-controls.md) for its
publication status. The earlier captures retain their original source pins.

The [design plan](rofi-controls-pass.md) and
[pre-implementation review](rofi-controls-design-review.md) define the scope.
The [candidate recipe](../recipes/rofi-controls.md) describes installation,
operations and recovery. The [interactive illustration](../../design/rofi-controls/index.html)
uses fictional stateful devices; it is separate from the native captures below.

## Result

Network, Audio and Bluetooth now have direct Rofi helpers. Network covers saved
profiles, nearby personal/open Wi-Fi, masked credentials, persistence, exact
activation cancellation, adapter scans, global radio scope, and existing wired
profiles. Audio retains separate input/output defaults, channel balance,
explicit mute and repeatable inline adjustment. Bluetooth adds paired-device
operations, bounded discovery, pairing prompts and a separate trust choice.
Session, Clipboard, notification cards, power/locking, independent Plus pickers
and the terminal palette retain their existing implementations.

The supported Rofi fallback is **Open / Details on the list, then a pinned
target with its own actions**. Up/Down does not silently change an operation's
target. One invocation owns its controller, private callback socket, Rofi children
and backend lifetime; there is no startup daemon or Rofi fork. Only pinned
pending views use a bounded timer. Editable lists are not periodically rebuilt.
Alt+R refreshes facts and requests a scoped bounded Wi-Fi scan when available.

The two-line rows preserve green current/default framing versus blue selection,
with independent Saved/Paired/Muted text. Controls use the canonical desktop
identity and cap their 52em window at 96% of the output. Terminal framing and
ANSI values are unchanged. Open Wi-Fi, global radio, disconnect, power, pairing
and trust decisions have explicit target/scope and Cancel-first confirmations.

## Original isolated qualification candidate

- Code producer commit: `2d9ec75814f787c4ecfc39d848e733bed562ab11`.
- Version 0.4.0, API 1; **44 files**: 33 desktop, 7 shell, 4 appearance.
- Archive SHA-256: `24b79711edb67b1f3860e843dfb6c7383760e8a5f2476dc61ebbaf54c779518e`.
- Root manifest SHA-256: `c02950fb980f2a7c4e710f6dd49d16b8f1558d51ebb62090f662f2b302060d90`.
- Two builds were byte-identical. Every unpacked payload hash and mode matched.
- Native tests then imported/executed the extracted package from a separate
  consumer prefix containing spaces, including the sibling callback entrypoint.
- Existing 0.3.1 launcher examples are frozen baseline/recovery files; generated
  candidate entries live under `examples/desktop/direct-controls/`.

The archive is retained locally. These hashes do not identify a published
release URL. The identity remains independently pinned; no personal admission
selector or immutable published producer record was overwritten.

## Publication review follow-up, 2026-10-29

Review found two Network issues after the original qualification: scan throttling
compared libnm's CLOCK_BOOTTIME milliseconds with GLib's monotonic microseconds,
and a saved SAE profile could be missed on a compatible PSK/SAE transition AP.
The fixes use libnm's matching clock, require native AP/profile compatibility,
and retain the selected profile's key management for retries. Regression tests
cover recent/expired/never-scanned adapters, the independent clocks, exact saved
profile reuse, and native compatibility rejection. The packaging test's old
100 kB budget was also updated to 128 KiB for the expanded source inventory;
explicit-input, per-member hash/mode and deterministic-build checks remain.

The reviewed source is `5494554a53527a12f1042a6a742066ec2bb8280c`.
Its replacement 0.4.0 candidate still has 44 files. Two builds matched, and every
extracted payload hash/mode was checked:

- Archive SHA-256: `2d1bdcd6c8b19131b740d44df40232e418108763849f758b423afdb782759491`.
- Manifest SHA-256: `1a614eea6be0421945cd42fdf0ad19e49efa28a68c76eba9d5c9b72b1807f108`.
- Source suite: 79 tests, 76 passed and 3 native-binding module skips.
- System-Python native-binding suite: 71 passed, including both new regressions.
- Extracted replacement bundle: all 14 isolated real-NetworkManager checks
  passed; host routes, resolver and protected service PIDs were unchanged.

This replacement has no new physical-device acceptance. The X11/Wayland,
credential-agent, Audio and Bluetooth qualification below belongs to the
original candidate, whose UI and other backends were not changed by this fix.
The internal HTML review report also retains that original candidate's hashes.

## Qualification

| Gate | Observed result | Limit |
| --- | --- | --- |
| General suite | 79 tests: 76 passed and 3 explicit native-binding module skips in the build venv | The separate system-Python gate covers those bindings. |
| Native binding unit contracts | 69 tests passed using installed PyGObject/libnm/libsecret | Inert peers and callbacks; not physical devices. |
| Native X11 Rofi | Passed fixed actions, duplicate selection, cursor/filter restoration, masked submission, pending completion, inline Audio and Escape against the extracted candidate | Private Xvfb/XTEST and synthetic devices. |
| Native Wayland Rofi | Passed on nested Niri 26.04 at scale 1.25, no DISPLAY in Rofi; repeated volume 45→50→55→60, explicit mute, duplicate selection/actions, CJK long title/full second line, masked-prompt Escape without reopen | Private winit output and synthetic devices; not an attended desktop. |
| Real NetworkManager/libnm | 14 checks passed: private virtual Ethernet activation, accepted-versus-active, exact cancellation, another adapter retained, daemon-restart rejection | Private mount/network/UTS namespaces; no physical Wi-Fi. |
| Native NM credential agent | 19 checks passed: root-owned private AgentManager, unique agents/connections, scoped GetSecrets, flags/storage, request-new/retry, Save/Delete failures, cancel and retirement | Real libnm agent methods; synthetic activation and in-memory SecretStore backing. |
| Real PipeWire/Pulse | 23 checks passed: separate defaults, repeated volume, balance, input mute, amplification policy, stale node, missing server | Private virtual sinks/monitor sources and policy-only WirePlumber; no speakers/microphone. |
| Native BlueZ protocol | 10 behavioral checks passed: PIN/passkey, matching-code/display, trust separation, pairing cancel/success race, connection wait, discovery ownership and stale owner | Real GIO/D-Bus against synthetic org.bluez; no physical adapter or bluetoothd behavior claim. |
| Existing desktop and terminal | 31 desktop and 81 terminal checks passed | Headless regression checks; no live desktop operations. |
| Stateful design preview | 111 browser checks passed | Fictional sample outcomes only. |

Rofi binary reports `Version: 2.0.0-dirty`, SHA-256
`4f8dcd3a87d4c41af3e7c5f3ab4891a0926f21ab659072e5471e7332cf30a1ca`.
Nested Niri reports `26.04 (8ed0da4)`, SHA-256
`f09e0b1cb2144794fb615c90e9cdaff6adc0cb6b05347503123bc392aeea66d3`.
The real NM service proof used version `1.58.1-2`.
Standard/portable site and browser closeout are recorded with the final review
snapshot, separately from these native results.

## Findings resolved during implementation

Native proof rejected the HTML's per-highlight action updates, so the documented
focused-device fallback was used. Rofi's timer could not be armed by a script
frame theme change; the owner admits it only on pending processes. A resumed
process must negotiate newline headers before switching to the row delimiter.
Two-line rows need explicit native row height, and scaled outputs need a width
cap. These were qualified in actual Rofi, not assumed from HTML.

Real libnm proof caught constructor-only client initialization, `get_iface`
versus the fake peer's earlier method, `NM.Device.get_path()` shadowing the
D-Bus identity method, cipher flags alongside PSK/SAE, and GI callback arity.
Those corrections are exercised by the native checkers. The libnm credential
agent deliberately rejects an unprivileged fake NM owner; successful proof
uses a root-owned peer on an isolated bus without weakening authentication.
Review also caught the missing open-Wi-Fi warning; its Cancel-first and stale
security behavior now has explicit coverage.

## Protection, remaining acceptance and delivery

Host routes/resolver and captured NetworkManager/Docker/Tailscale/Niri/SwayNC/
idle/349d service PIDs matched before and after the real-service proof. Nested
Niri recorded its native host PID baseline unchanged. Owned menu/compositor,
service, scan, agent, signal and callback resources were cleaned up; another
Bluetooth discovery client was retained. Two orphaned earlier controls-fixture
Xvfb processes were identified by their private trace/stderr paths and stopped
by exact PID. Retained Arch guests/checkpoints were not booted or changed.

Physical Wi-Fi credentials, rfkill/removal, real wallet unlock/compatibility,
actual output/microphone behavior, and real Bluetooth adapter/keyboard pairing
remain separate acceptance work. A staged first-host trial with recovery and
human task checks precedes release/fleet admission; this pass does not claim
those results. Preview visual feedback does not establish device-task acceptance.
No other distribution, global service restart, device removal or pairing
cleanup was introduced.

Luna implemented the frontend/fixtures, Network and credential slices, preview,
and native BlueZ/Wayland checks. The primary owned architecture, Audio/BlueZ
adapters and pairing, difficult native registration/protocol corrections,
real-service isolation, integration, review, packaging and delivery gates.
