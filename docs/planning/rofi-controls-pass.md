# Direct Rofi controls: design and implementation plan

Status: proposed design, 2026-10-28. This pass creates a plan and an illustrated
preview; it does not replace utilities or qualify native behavior.

The Arch reference and human/agent setup split are published at `d3e7505`.
The next improvement is everyday device control: choose Wi-Fi, change audio
output, or connect headphones without opening a terminal or a settings panel.
SwayNC remains the information surface. Rofi provides short, deliberate actions.

Open [the interactive design illustration](../../design/rofi-controls/index.html). Its
fictional devices and outcomes are sample data, not a desktop recording.

## Recommendation and scope

Build a small first-party interface in the existing public desktop component,
using native services. Start with one complete Network slice, then Audio, then
Bluetooth. Keep the existing Session and Clipboard helpers. Use the current
Crisper Neutral Slate identity, Clear Blue accent and Noto Sans, with the same
opaque, square Rofi window and existing width constraints.

| Entry in Mod+D | Current public component | Proposed routine controls | Advanced handoff |
| --- | --- | --- | --- |
| Network | Kitty → `nmtui` | Status, adapters, saved connections, nearby Wi-Fi, connect/disconnect, credentials, rescan, Wi-Fi radio | `nm-connection-editor`; retain `nmtui` as recovery |
| Audio | `pavucontrol` | Output/input selection, default device, volume, mute | `pavucontrol` for streams and profiles |
| Bluetooth | Kitty → `bluetoothctl` | Paired devices, connect/disconnect, adapter power; then discovery and pairing | Existing `bluetoothctl` recovery; do not invent an uninstalled GUI dependency |
| Session | `desktop-session-menu` | Existing Lock, Log out, Suspend, Restart, Shut down | Preserve native session and power owners |
| Clipboard | `rofi-clipboard` | Existing history, copy and guarded deletion | No redesign in this sequence |

Keep familiar launcher names and Mod+D. Do not add a dashboard, a bar, a new
global binding or a common background daemon. Audio and Bluetooth have their
own completion gates; Network success does not silently admit either.

## Reuse investigation

Read-only source review on 2026-10-28 inspected these exact public revisions;
no candidate was installed or operated against native devices.

| Candidate | Inspected revision | Assessment |
| --- | --- | --- |
| [networkmanager-dmenu](https://github.com/firecat53/networkmanager-dmenu/tree/acedf1a6faf2df904208e402d4293f13d1144489) | `acedf1a6` · MIT | Strongest functional reference: Python/libnm, launcher integration, profile selection and activation-state handling. Its current nested menus and notification-based wait path would still need adaptation for the shared action cycle and visible pending/cancel flow. |
| [ronema](https://github.com/P3rf/rofi-network-manager/tree/e7d7027d1bac3a2b6204ac86773a254f4f5c61ba) | `e7d7027` · MIT | Broad Bash/nmcli menu. Inspected paths parse human-readable output, supply new passwords as command arguments, and include whole-network restart and password sharing. Those paths are unsuitable foundations for this contract. |
| [rofi-bluetooth](https://github.com/nickclyde/rofi-bluetooth/tree/0cca4d4aa1c82c9373ce5da781d73683a29484c6) | `0cca4d4` · GPL-3.0 | Useful interaction reference. Inspected discovery cleanup uses process-name matching; pairing/removal and trust toggles are broader than the intended first slice. Do not copy it into the MIT component without a separate licensing decision. |

Recommendation: own the small UI/state layer, use upstream libnm for Network,
and retain upstream tools as references and advanced/recovery routes. This is
not a new network manager or a maintained fork of each menu. If native proof
shows that the custom interaction is disproportionately expensive, reconsider
a configured `networkmanager-dmenu` pilot before committing to a large UI layer.
No third-party code has been copied in this design pass.

## Shared interaction contract

- Up/Down selects a row. Tab/Shift+Tab cycles its named actions; Enter executes
  the visibly selected action. Moving to another row selects its primary action.
- Preserve the filter and selected object while cycling actions or refreshing.
  Use stable identities, not row numbers or labels. If an object disappears,
  select the nearest surviving row and show that it is unavailable on retry.
- Left/Right and Ctrl+B/Ctrl+F edit the filter. Escape/Ctrl+G follows Rofi's
  cancel path. Alt+R refreshes device state and requests a bounded Wi-Fi scan
  when supported; it is not a periodic host-work timer.
- Show the current action beside its key hint, with alternatives visible in
  muted text. Click selects a row; a labeled action button activates it. Native
  Rofi pointer behavior must be qualified separately from the HTML illustration.
- Each row has a name plus a readable status line: device, connected/saved,
  signal/security, mute/default as applicable. Use text as well as status color.
  Long names must remain identifiable; a Details page shows the full value.
- Keep a compact context line above the list and the action hints below it.
  Present unavailable hardware/service and permission errors explicitly. Opening
  the menu must not start services, unblock radios or alter connections.
- Details pages have a Back row. Escape closes the utility; it does not execute
  Back or a destructive action. Confirmation dialogs use native row navigation,
  with Cancel first and selected by default; no action cycling is needed there.

Reuse the public Rofi protocol and the already accepted key convention. Do not
import private Agent Plus, SSH Plus or Tmux Plus implementation modules. Bind
Tab/Shift+Tab through custom callbacks 7/8 and disable native element Tab keys.

## Network: the first complete slice

### List and actions

Open against cached NetworkManager state, with active connections first,
available networks next, then unavailable saved profiles and utility actions.
Show all managed Ethernet/Wi-Fi devices and disambiguate adapters. Group repeated
access points by raw SSID, security class and adapter, choosing a compatible AP
again at activation. Multiple compatible saved profiles require an explicit
profile choice. Do not pin a connection permanently to one BSSID.

| Row state | Primary action | Other actions |
| --- | --- | --- |
| Active connection | Details | Disconnect, with impact confirmation |
| Available saved profile | Connect | Details |
| Available new personal/open Wi-Fi | Connect | Details |
| Saved but unavailable | Details | Advanced settings; no speculative activation |
| Unsupported new security / unmanaged device | Details | Advanced settings |
| Wi-Fi radio | Turn on/off | Confirm before turning off when it would break a current link |
| Refresh / Advanced settings | Named action | None |

Creation supports open networks and explicitly recognized WPA2/WPA3 Personal.
An open network gets a plain warning and confirmation. New enterprise/EAP,
hidden networks, WEP, hotspot creation, static addressing and VPN editing stay
in advanced settings. Existing saved configurations remain owned by NM; unusual
authentication or secondaries must be qualified before promising one-click
activation. Do not expose Forget, reveal-password, QR sharing or restart-all
networking in this release. Never pre-disconnect a working link before asking
NM to activate the selected replacement.

### Credentials and persistence

For a new protected network: choose network → masked credential prompt →
Connect and remember / Connect once / Cancel → pending → result. The review
page names the adapter and persistence choice; Enter alone in an empty password
prompt cannot create or activate a profile.

Proposed default is **Connect and remember**: a profile restricted to the current
user, NM-managed persistent secrets, and autoconnect enabled for that new
profile. **Connect once** uses a volatile, non-autoconnecting profile. Do not
rewrite permissions, secret flags, priority or autoconnect on existing profiles.
Do not promise KWallet storage: Secret Service availability and an NM secret
agent are different contracts.

Pass credentials in memory through the native API. Never use command arguments,
environment variables, clipboard, Rofi row metadata/state, logs or report
fixtures. Retain whitespace exactly; discard the prompt's trailing delimiter
only. Masking is visual privacy, not secure isolation or a guarantee of memory
erasure. Administrative authorization remains the existing polkit agent.

The credential proof must cover existing stored and agent-owned secrets, no
agent, rejected credentials, retry and cancellation. Prefer the existing native
secret route. If a transient `NMSecretAgentOld` implementation is necessary,
scope it to the utility's requested connection/device and interaction, decline
unrelated requests, unregister on exit, and prove coexistence with another
agent. Do not add an always-running credential agent as an incidental change.
Failed attempts may remove only a demonstrably unchanged profile created by
that exact attempt; never delete or overwrite a pre-existing profile on failure.

### Pending, results and cancellation

| State | What the user sees | Required behavior |
| --- | --- | --- |
| Opening / scanning | Cached rows and “Refreshing…” | List stays usable; coalesce scans and bound waits. |
| Authenticating / obtaining address | Named network, device, current stage | Remain responsive; NM accepting a request is not connection success. |
| Connected | “Connected” and observed address/state | Do not equate this with verified Internet access. |
| Captive / limited connectivity | Separate connectivity label | Offer browser/advanced guidance without claiming authentication succeeded. |
| Failed / denied / device removed | Specific reason and Retry / Back / Advanced | Preserve recoverable context, never automatically loop credentials. |
| Cancel connection | “Cancelling…” then observed outcome | Revalidate and cancel only the utility's exact activation. |
| Close menu / Escape while pending | Menu closes | Stop owned UI/read work; do not issue a broad disconnect. |

Before submitting an activation, Escape means no action. After NM accepts it,
closing the menu leaves that native request running. A bounded owned operation
monitor may remain until terminal state or deadline when native activation
requires the requesting bus connection; it must have no surviving UI, secret
prompt or unbounded watcher. Reopening reads native state. Explicit **Cancel
connection** attempts targeted cancellation instead. If cancellation loses the
race to success or another actor changes the target, report the observed state
and stop; do not disconnect an unrelated replacement or silently reconnect an
old profile. Confirmed cancellation is not a promise to restore the previous
network. An observation timeout means “status unknown”, not “connection failed”.

Use profile UUID, device/AP object identity, daemon-owner epoch and an owned
request generation. Record the returned active-connection handle. Revalidate
actions at Enter and cancellation at the backend boundary; selection membership
is not authority to operate. SSIDs, profile names and device aliases are
untrusted data: escape display markup/control characters, preserve raw identity,
and invoke subprocesses without a shell.

## Runtime approach and two prerequisite proofs

Propose Python + PyGObject/libnm with a bounded controller owning Rofi children
and a GLib main context. No new service. The dependency delta is explicit
`python-gobject`/libnm where absent, plus the chosen advanced editor; inspect
actual Arch package ownership before modifying any manifest.

1. **Native Rofi interaction proof.** Compare script mode with a foreground
   dmenu controller using custom exit codes. Prove filtered-row mapping, action
   cycling, cursor/filter/selection preservation, native cancel and one pending
   result transition. Current Agent Plus uses only narrowly scoped one-shot
   callbacks; a reliable periodic refresh cannot be assumed. A controller must
   not continually close/reopen an editable list or steal focus after dismissal.
   Prefer script mode for editable lists if dmenu cannot retain the contract.
2. **NM lifecycle/credential proof.** Exercise request accepted vs activated,
   secret-agent coexistence, persistent/volatile profile ownership, client
   disappearance, secondary connections, daemon restart and targeted cancel.
   Verify them against installed versions; API documentation alone is not proof.

Choose the final transport only after both proofs. This is an implementation
gate, not an open-ended research phase: produce a small owned fixture, record
pass/fail, and return to the reuse option if the UI cannot meet the contract.
No native mode experiment belongs on an attended desktop during planning.
Remove owned signal handlers, timers and processes on close. Use per-session
instance admission and exact owned process handles, never `killall rofi`,
global replacement or process-name matching. An existing live utility should
be reused/focused or rejected visibly, not duplicated with competing workers.

## Audio and Bluetooth follow-ups

Audio uses the current PipeWire/PulseAudio compatibility owner. Use structured
inventory (for example `pactl --format=json`) and exact native identities, not
localized status text. List output and input devices, distinguish default from
actively playing, and support volume in 5% steps capped at 100% plus mute.
Changing the default applies to future streams; moving existing streams is a
separate explicit action, initially available through `pavucontrol`. Do not
silently change Bluetooth profiles, unmute a microphone on volume adjustment,
or replace the current hardware-key feedback helpers. Advanced per-app routing,
profiles, EQ and media controls are outside the first Audio slice.

Bluetooth first covers paired devices and adapter power. Then add a bounded
discovery/pairing slice with its own acceptance: adapter selection, fresh device
identity, PIN/passkey/confirmation dialogs, explicit trust choice and failure
handling. Connecting must not silently pair, trust or remove. Confirm power-off
with connected devices; forgetting a pairing is deferred. Use BlueZ D-Bus and
release only this client's discovery session on exit. Do not stop another
client's scan, expose global discoverability by default, or unblock a hardware
radio automatically. Keep native audio profile ownership independent.

## Ownership, validation and delivery sequence

| Stage | Deliverable | Exit gate |
| --- | --- | --- |
| 0. Design | This plan and sample preview | User can review routine actions, keys, pending/cancel behavior and scope. |
| 1. Proofs | Owned Rofi fixture and NM lifecycle/credential receipt | Both prerequisites pass or a concrete reuse alternative is proposed. No launcher replacement yet. |
| 2. Network | Public helper, launch entry, recovery route and documentation | Fixture tests plus disposable native Arch proof; real Wi-Fi credentials, rfkill and adapter removal qualified separately. |
| 3. Audio | Default/input/output, volume and mute | Native audio routing and a physical output/input check; no claim that a VM proves real headset behavior. |
| 4. Bluetooth | Paired-device actions, then discovery/pairing | Disposable BlueZ fixtures plus physical adapter/device proof, including keyboard/passkey pairing and another discovery client. |
| 5. Publish and admit | Versioned bundle, guide/demo updates and separate fleet pins | Release provenance verified, then requested scoped chezmoi apply and host acceptance; retain recovery tools. |

New implementation belongs in `components/desktop/`, with thin helpers such as
`desktop-network-menu`, `desktop-audio-menu` and `desktop-bluetooth-menu` plus
small shared protocol code if justified. Update the explicit component
inventory/exports and generated examples when implementation is accepted.
Release each useful slice independently; do not wait for all three to ship.
Independent Rofi Plus projects keep their own code and release authority.

Chezmoi owns personal host selection, package/launch admission and exact bundle
pins. Future rollout stages the immutable public bundle, inspects scoped
status/diff/dry-run, and preserves unrelated drift. Qualify Network on an
unattended test host with local recovery before Carbon; a retained VM can prove
wired NM behavior and native Rofi, not physical Wi-Fi or Bluetooth. No VM boot,
network disruption, code release or fleet apply is part of this design pass.

Tests should exercise meaningful boundaries: duplicate/control-character SSIDs,
multi-adapter/profile ambiguity, stale handles, changed daemon owner, external
activation races, secret cancellation, delayed completion, owned cleanup,
missing services, permission denial and exact installed-consumer behavior.
Use fictional state and owned subprocesses; never operate native user devices
as a test fixture. Confirm native readability under fractional scale and long
CJK names. Keep the existing Session lock/power and Cancel-first behavior.

After each accepted slice, update the utilities recipe and both human/agent
setup descriptions, then capture only the affected native flow with honest
version labels. Keep the published human Setup navigation and prominent agent
recommendation. Ubuntu/Debian support and further palette work remain deferred.

## Primary API references

- [Rofi script protocol](https://davatorium.github.io/rofi/current/rofi-script.5/)
  and [dmenu protocol](https://davatorium.github.io/rofi/current/rofi-dmenu.5/):
  metadata, filter/index output, custom callbacks and cancellation.
- [NetworkManager methods](https://networkmanager.dev/docs/api/latest/gdbus-org.freedesktop.NetworkManager.html):
  targeted activation/deactivation, permissions and `AddAndActivateConnection2`
  persistence/lifetime options.
- [libnm secret-agent API](https://networkmanager.dev/docs/libnm/latest/NMSecretAgentOld.html):
  scoped credential callbacks, registration and cleanup.
- [BlueZ adapter](https://bluez.readthedocs.io/en/latest/adapter-api/) and
  [pairing agent](https://bluez.readthedocs.io/en/latest/agent-api/) contracts:
  per-client discovery sessions and pairing interactions.

Repository observations are from public component `0.3.1`, the existing Session
and Clipboard helpers, the identity source, and the sibling Agent Plus launcher
and selection-restoration source. Source inspection establishes design inputs;
it does not establish runtime acceptance of the proposed controls.

## Design review evidence

The HTML illustration passed 67 owned browser checks at 375/768/1280/1600px,
including filter/action preservation, credential-free sample flows, success,
failure, retry, explicit cancellation, Escape, Cancel-first confirmation,
local links and a JavaScript-disabled fallback. Desktop and narrow screenshots
were visually reviewed; 15 preview color roles match the selected identity.
The unchanged public site builds with 21 pages and 739 checked local links;
its existing 726 browser checks pass. These are presentation checks, not native
Rofi or physical-device acceptance. Research clones and generated reports stay
outside the repository. No host configuration, service or device was changed.
