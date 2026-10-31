# Manual display-away integration record

**Status: local integration, 2026-10-30.** This record documents guide/profile
integration of the published optional companion and preserves the separate
source, staging, consumer and physical acceptance boundaries. It does not
qualify a new whole-desktop reference or record a new publication/deployment.

## Release and ownership

| Selection | Version and pin | Scope |
| --- | --- | --- |
| Qualified core/reference | Components 0.4.1, API 1; source `317658ee7913bb58536f6ec1b2575043a9494449`; archive SHA-256 `0940e0803c84bc6e1cb941ea4074f14a02db0d124bd8c1c676c3375147427d11`; manifest SHA-256 `30e1ad903fb74d7ee17b74f9f037cdc3ce2224d7538f5096668360aff9b504a4` | Existing 44-file desktop, shell and appearance baseline, selected by `tools/reference/inputs.json`. |
| Optional away companion | Components 0.5.0, API 1; source `4c79ff18cc12152ce072c000bf00131fc2efda15`; archive SHA-256 `c7522cafa49b814e5268dc57392ad3de99c5ee1906b08693a7097475029cf35c`; manifest SHA-256 `e38cccdadd2a6e9edcdce12eceadf5754215595db1514bab95e1c902be9cd9a6` | Standalone stager verifies all 46 archive payloads and selects only `desktop-away` and its user service. |

The optional release is [published as components-v0.5.0](https://github.com/byebyebryan/niri-plus/releases/tag/components-v0.5.0).
The current consumer split is the 0.4.1 core plus the helper/unit selection
from 0.5.0. Do not install or use the full 0.5.0 bundle to replace the
qualified core. The away inputs and stager are independent of the default
reference inventory and do not render appearance files or install anything.

## Behavior and limits

`desktop-power` and its `swayidle` child remain the sole automatic idle,
display and suspend policy. `desktop-away away`, `resume` and `status` operate a
separate explicit latch in the graphical session. A normal session starts
unlatched; stopping the companion while latched restores ordinary display
power. Never connect an automatic idle or sleep resume action to
`desktop-away resume`.
The away latch controls display power only; it does not inhibit system sleep or
keep the machine awake, so the current suspend timers and lid/power policy still
apply.

Normal video and presentation inhibitors keep their current behavior. Once the
user explicitly enters away mode, the companion ignores application inhibitors
and corrects application or hotplug display wakeups. It polls DRM state every
250 ms and limits corrections to two per second. A brief flash before
reblanking is possible, and unknown DRM state is not evidence that a panel is
off.

When existing physical evdev input is readable, the helper observes keyboard,
mouse and touchpad events without grabbing devices or storing input content.
Otherwise it uses `libwayland-client` and `ext-idle-notify` version 2 in
input-only mode. That backend follows compositor seat input, including OS-level
injected input; it cannot prove that an event came from a physical user. Neither
backend adds input-group membership, ACLs, udev rules or a privileged service.

Standard Chrome navigation/clicks and fresh screenshots worked during the
Starship trial with DRM reporting Off. An explicitly cropped screenshot timed
out; not every capture mode or the headless-extension path is qualified. The
original overnight inhibitor owner was not conclusively attributed.

## Dated consumer evidence

The private fleet receipt is summarized here without linking private host paths:

| Host | Recorded result | Remaining acceptance |
| --- | --- | --- |
| Starship | Chrome navigation/clicks and fresh standard screenshots worked with DRM Off. An earlier wake correction took about 0.306 seconds. Human confirmation covered physical mouse return. | Other capture modes and physical panel behavior are not generalized from this trial. |
| Snap | The input-only observer corrected a programmatic wake in about 0.339 seconds; a D-Bus application inhibitor did not release away mode, and the prior display state was restored. | Human physical keyboard/touchpad and panel return remain pending. |
| Carbon | The observer, configuration and unit were installed and converged. The attended display was not blanked for disruptive testing. | Physical return and panel acceptance remain pending. |

These observations are separate from the 0.4.1 Arch VM and its media/capture
receipts. Preserve those receipts unchanged; this integration does not replay or
extend their whole-desktop acceptance.

## Acceptance matrix

| Gate | Evidence and status | Boundary |
| --- | --- | --- |
| Immutable away archive | Primary staging validation passed 8 away-stager tests and 8 existing reference-stage tests. The published archive was downloaded, all 46 payloads were validated, the 44 existing payloads remained byte-identical, and only the two selected files were staged. | Confirms the input stager and archive selection; not installation or device acceptance. |
| Core reference preservation | The 0.4.1 input pin and its dated VM/media receipts remain the required reference baseline. | No new full-reference replay is claimed. |
| Isolated behavior and static config | The existing 21 decision/fake-compositor tests passed unchanged. Primary syntax checks passed 40 cases, including a temporary base config with the opt-in include. | Static and isolated checks; not a live compositor, physical input or panel test. |
| Inhibitors | Normal video/presentation policy remains with its current owner. The explicit away latch deliberately ignores application inhibitors; Snap's D-Bus application-inhibitor check did not resume the latch. | Verify both normal playback behavior and the intended away-mode override on each target. |
| Away/status/resume and recovery | The helper contract is explicit: normal service start and a fresh session begin unlatched; `resume` clears an explicit latch; stopping while latched restores ordinary display power. | A combined target-native check of enter, remote status/resume, stop, session restart and recovery remains a separate acceptance gate. |
| Input freshness and backend | The isolated suite covers fresh versus stale events, shortcut release/repeat, device classification and backend selection; Starship physical mouse return was confirmed. Readable evdev ignores stale/virtual events; Wayland seat input includes OS injection. | Keyboard/mouse/touchpad hotplug and the first Bluetooth wake event require target-native checks. Physical keyboard/touchpad return on Snap and Carbon remains pending; the Wayland backend cannot prove physical attribution. |
| Suspend/resume | The away companion does not add automatic suspend or wire sleep resume to its manual `resume` action. | Keep the selected `desktop-power`/`swayidle` policy and separately test any scheduled suspend/resume on the target. |
| Capture compatibility | Starship standard screenshots worked with DRM Off; an explicitly cropped screenshot timed out. | Other capture modes, including the headless-extension path, remain unqualified. |
| Consumer behavior | Starship, Snap and Carbon observations are summarized above from their dated receipts. | Target-specific evidence; no fleet-wide physical acceptance claim. |
| Physical input and panel return | Starship mouse return was confirmed; Snap and Carbon remain pending. | A DRM state alone does not establish physical panel acceptance. |
| Niri Plus docs/profile/site integration | `export-components.py --check` reported no changes; 29 focused build-contract tests passed; the site build validated 25 pages, 199 files and 982 local links. | Does not establish native-session behavior or alter consumer deployment. The combined final source/browser results are reported separately. |

## Future consumer consolidation

Keep the 0.4.1 core and away-only 0.5.0 selection separate for now. Reconsider a
single consumer pin only after a future complete component bundle passes a new
fresh-base reference qualification, its ordinary consumer checks, and reviewed
per-host adoption. Preserve the current 0.4.1 VM/media evidence and the
per-host away receipts as dated records rather than relabeling them as results
for a later bundle.
