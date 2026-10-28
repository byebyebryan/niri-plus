# Demonstrations and public adoption walkthrough

Updated 2026-10-28 after the Arch core desktop and media pass. Arch Linux
x86-64 is the only reference target for this work. Ubuntu/Debian are deferred
for much later, with no scheduled trial, guest preparation or compatibility
work. Reconsider them only through a separately scoped future decision.

The [pilot receipt](capture-pilot-receipt.md) records the completed host/Arch
capture milestone. The [desktop demonstration receipt](desktop-demonstration-receipt.md) records
core desktop assembly and real site demonstrations (C–D below). A complete Arch
installation rehearsal follows separately, then the Rofi controls design pass.
Public publication and fleet rollout remain separate.

## Outcome and current baseline

Give a visitor a connected route: watch a task, understand the pieces behind it,
assemble those pieces, and verify the same result. Preserve the personal story:
Chrome and ordinary file interaction beside keyboard-driven terminal and agent
work, with information available on demand and no permanent bar.

The pilot established native Niri/Chrome/Kitty/Zsh, selected fonts and colors,
a current-theme still and a 24.5-second recording. It did not qualify the full
desktop or replay the final instructions from a fresh base. Manual local viewer
key grab/release remains distinct from the tested guest virtual-keyboard input.

The local site candidate adds an actual Arch overview and focused browser/files,
terminal and information recordings beside the existing illustrations and isolated
samples. The terminal scene reuses the accepted pilot. Public deployment has not
changed; preserve the separate native/sample/illustration labels.

The setup page links a seven-stage assembly map to focused recipes. It starts
from a working Niri session and has no clean-install acceptance. The portable
base config intentionally omits service startup and several integration binds.
The guarded reference assembly now connects the demonstrated subset; the wider
installation guide still needs a clean-base replay.

## Completed local milestone: core desktop and real demonstrations

Deliver browser/files, terminal and information/clipboard workflows on the Arch
reference guest, with recorded public inputs, assembly notes, reviewed native
media and locally reviewed site changes.

Keep the selected Crisper Neutral Slate/Clear Blue desktop, pure-black Balanced+
terminal and Noto/Meslo typography. Resolve cross-application inconsistencies
within that identity rather than starting another palette design.

### Work packages and task acceptance

| Order | Work | Reviewable result and gate |
| --- | --- | --- |
| 0. Inputs and recovery | Recheck guest/network state, storage and local viewing. Freeze the public source commit, component bundle/hash, independent identity/hash, shell pins, SwayNC recipe/source pins and package versions. Qualify an offline working copy. | Recovery copy boots; protected checkpoints remain intact; every task maps to a public recipe/input. Record manual viewer key handling as pending if it has not been exercised. |
| 1. Browser and files | Restore the Dolphin binding omitted by the pilot. Add MIME/default applications, explicit GTK/WLR routing and the PipeWire/session requirements for browser sharing. Use local sample download/upload pages. | Download a sample, reveal/open it in Dolphin, open through the default handler and upload the same file through the GTK picker. Separately start/stop a whole-monitor WLR browser share. Inspect GTK, Qt and browser appearance together. |
| 2. Information and clipboard | Build/install the pinned SwayNC fork through its public recipe. Add dashboard configuration, Cliphist collectors, the Rofi picker and Mod+N/Mod+Y. | Sample notification/history and panel toggle work; CPU/RAM and actual network state are fresh; missing hardware hides naturally. Text/image selection preserves original content; Delete and confirmed Clear all work, with a 200-item cap. |
| 3. Lifecycle and terminal regression | Establish one session owner for each new daemon/collector. Retain the guest-only login harness for this slice. Check Kitty/Zsh, Rofi drun and current utility entry points without redesigning them. | Fresh Niri sessions start required processes once; ending the session stops them; repeat login works. New Kitty shells retain prompt, history, completion and appearance. Missing hardware/services produce understandable results. |
| 4. Native media and site | Record accepted tasks and make the overview, focused clips, posters, captions, setup links and provenance. Update tour/home entry points. | Actual tasks are visible in reviewed encoded playback; the local site passes build/browser and media checks; task results and remaining gaps are recorded. |

The pilot package set did not install NetworkManager. Inspect the cloud
image's current network owner before expanding it: the dashboard and Network
launcher need NetworkManager to own the guest's virtual Ethernet connection,
with a real PrimaryConnection. If a handover is needed, preserve the reserved
address and guest SSH/console recovery, avoid competing network managers and
verify DHCP/DNS/downloads afterward. Installing a package alone is insufficient.
This changes only the guest; Starship's network ownership stays intact.

Use the selected appearance renderer/output with the dashboard configuration,
not the historical preview stylesheet. Preinstall the fork's runtime
dependencies before its ordinary-user package build so temporary build
dependency removal cannot remove needed runtime libraries. Keep portal
providers explicitly GTK + WLR; guest-side recording is not evidence of browser
sharing, and no GNOME/KDE portal migration belongs in this slice.

Keep a command transcript and assembly notes while doing each package. When a
step is missing, correct its owning source/recipe before calling the task
complete. A required task that fails remains a gap; do not silently substitute
an illustration or drop its acceptance check.

The slice ends with a named assembled-desktop checkpoint, reviewed media, site
changes and a dated execution receipt containing exact versions and per-task
results. Distinguish source checks, native guest tests, site checks and human
review. Do not imply that a site browser suite is a desktop integration suite.

SDDM/password login, wallet/PAM, locking/idle/power, full audio/input/output
coverage and clean-base replay belong to the later installation milestone.
Optional agent authentication, remote endpoints and new Rofi controls do not
block this slice. Briefly show current utility launchers; detailed controls
demonstrations should follow their later design.

## Environment, recovery and ownership

Reuse local Starship libvirt/QEMU, the existing AMD-backed VirtIO graphics,
local SPICE/OpenGL viewer, guest-side capture and host-to-guest SSH. Preserve
the tested Docker/firewalld integration, host networking, Tailscale and native
desktop. No remote/Carbon access, PVE migration or parallel container desktop
is needed. Host virtualization remains outside chezmoi.

Preserve `arch-base`, the existing pilot-only `niri-plus` checkpoint and original
media. Use an offline working copy and run one Arch guest at a time. Preserve
disk, UEFI variables and domain definition together; verify identity and access
after restoring a copy. Save the next assembled checkpoint under a distinct
name rather than relabeling the pilot as full-desktop evidence. The
[VM plan](vm-reference-environment.md) owns the detailed recovery/storage rules.

- Niri Plus owns shared first-party implementation in `components/`, generated
  exports, the reference assembly, fixtures, recipes and site.
- Independent projects, including SwayNC and the Plus launchers, retain their
  implementation/release authority. Use public pins and installation contracts.
- Private chezmoi owns personal policy, host admission and deployment. Public
  inputs must suffice for the guest; do not import a personal home or copy a
  shared fix into a chezmoi fallback.
- Guest-only SSH, login, virtual-output and fixture settings stay distinct from
  portable desktop behavior. Keep small reviewable assembly steps rather than
  building a distribution image pipeline or generic installer/VM framework.

If a shared fix needs a new artifact, validate and prepare its release
separately. Do not label an unpublished artifact as a published pin or silently
roll it out to the personal hosts. Prepare local commits and previews; push,
release, site publication and personal-host apply remain separate actions.

Stop the guest when work ends; retain useful tools, images and checkpoints.
Deleting the lab is not a completion condition.

## Demonstrations and site presentation

| Scene | Actual task | Instruction destination |
| --- | --- | --- |
| Browser and files | Move between Chrome and terminal; download/open a sample in Dolphin and select it through a browser upload picker. | Base session, browser/files, portals and MIME recipes. |
| Building in terminals | Navigate a public/sample project, run a harmless command and show readable prompt/output and keyboard navigation. | Kitty/Zsh and the design page. |
| Information and clipboard | Open/close SwayNC, inspect sample notifications and real available cards, then retrieve text and an image. | Notification, clipboard and session-wiring recipes. |
| Optional later agent/remote work | Open a dedicated native agent TUI or an owned sample SSH/tmux session when its separate prerequisites are met. | Maintained Plus guides and explicit access prerequisites. |

Aim for one readable 45-75 second overview and focused clips of roughly
20-45 seconds for the three core scenes. Reuse pilot footage only when its
versions and behavior still match; durations follow clarity rather than quotas.
Agent/remote demonstrations are not required deliverables for this slice.

Use an unsigned-in demo browser profile, local sample pages/documents, a sample
project and isolated notification/clipboard state. Use the VM's actual system
and virtual Ethernet information. Missing GPU/battery/Bluetooth cards should
hide; any separate fixture rendering must be visibly labeled as sample data.
No personal accounts, private files, real notifications or native conversations
enter the recordings.

Put the overview on the tour with a prominent route from the home page. Place
focused clips beside their task explanations and link to the relevant setup
step. Preserve the first-person story. Keep the design page as the
palette/typography reference, showing the same identity on actual GTK, Qt,
browser and terminal surfaces rather than repeating the selection debate.

Each media item needs a poster, native controls, explicit playback, readable
action/key captions or equivalent textual steps, a useful no-JavaScript path
and a setup link. No autoplay is required. Any hover preview remains a separate
deferred derivative with reduced-motion/data-saving/touch fallbacks.

Extend `assets/provenance.json` with source versions, staged-VM/fixture labels,
dimensions, processing notes and hashes. Keep original captures and private
receipts outside Git; commit only reviewed site derivatives and public evidence
without private guest keys, credentials, addresses or workstation paths.

Decode each full video, inspect dimensions/frame timing and readability at
the intended playback size, and compare encoded terminal black with its PNG
reference. Run the required repository build/browser checks. Explicitly check
playback/seek, keyboard access, narrow screens, reduced motion and textual/poster
fallbacks without JavaScript. Record human review as pending when it has not
occurred. Prepare a reviewable local site; publishing is a separate step.

## Following milestone: complete Arch guide and replay

The accepted [Arch installation pass](arch-installation-pass.md) expands this
milestone into guide, missing-integration and fresh-replay gates, with a native
task matrix and explicit VM/hardware limits. Execution results remain separate.

Target an installed Arch Linux x86-64 system, ordinary account, working network
and package access. OS partitioning and maintaining an OS image are outside the
walkthrough. Existing selective recipes stay useful, but this plan qualifies
Arch only; no other distribution qualification is scheduled.

Turn the captured assembly notes into one ordered route, retaining focused
recipes. Each stage needs prerequisites, exact public inputs, scoped commands,
a visible expected result, troubleshooting and recovery:

1. Establish baseline/recovery and record source/package versions.
2. Start Niri with Kitty/Rofi and document login, PATH and session startup.
3. Add browser/Dolphin, explicit portals, MIME defaults and download/open/upload.
4. Apply desktop/terminal identity, fonts, cursor/icons and native preference merges.
5. Add the pinned SwayNC fork, Cliphist, bindings and session-owned services.
6. Complete authorization, manual locking, explicit idle/power policy, hardware
   feedback and the current utility launchers.
7. Add the shared Zsh core and pinned plugins, verifying a new shell, prompt,
   history and completion; keep personal SDK/environment choices separate.
8. Offer SSH/Tmux/Agent Plus as optional extensions using their maintained
   contracts. The core desktop must work independently.

Finish the wider [VM coverage checklist](vm-reference-environment.md#desktop-coverage-and-evidence):
SDDM password login and guest wallet choice, Gtklock, independent idle/power,
polkit, one-output Kanshi, input/Fcitx5, PipeWire/audio and volume feedback,
ordinary file/media handlers and current utilities. State demo power policy
explicitly and restore it after idle/lock tests. Real Wi-Fi/BT, brightness,
lid/docks and physical suspend remain hardware follow-ups, not passed VM tests.

Carry pilot lessons into the instructions: explicit portal providers and
session ownership, minimal-base command prerequisites, safe existing-profile
handling, an explicit terminal shell and fresh browser preferences. Document
first-shell network behavior, including Powerlevel10k's optional `gitstatusd`
fetch; staged plugin sources or a warmed prompt do not establish an offline
first run. Arch package evidence describes the tested rolling-release baseline
without promising byte-identical future rebuilds.

Qualify restoration, then follow the written route from a fresh `arch-base`
working copy without private imports. Retain a transcript and task results.
Test reboot, password login, core tasks, logout/teardown and repeat login.
Every manual repair must be incorporated into the guide and the corrected
route replayed from a fresh base before installation qualification. Update
affected clips or their version labels when a repair changes shown behavior.
VM acceptance does not establish physical-host PAM/wallet or hardware behavior.

## Work order and exit gates

| Phase and status | Deliverable | Gate |
| --- | --- | --- |
| A. Workstation lab — complete | Retained Starship tools/network and clean Arch checkpoint. | Measured results and recovery inputs are in the pilot receipt. |
| B. Capture pilot — complete | Still, 24.5-second browser/terminal clip and receipt. | Native rendering/capture passed; full desktop and clean-install acceptance remain separate. |
| C. Desktop assembly — complete locally | Browser/files/portal tasks, SwayNC/clipboard, service wiring and assembly notes. | Work packages 0-3 pass with recorded public inputs. |
| D. Media/site — complete locally | Overview/focused clips, posters, captions, setup links and provenance. | Work package 4 passes; locally reviewed changes are ready for a separate publication decision. |
| E. Complete Arch guide/replay — following milestone | Wider desktop coverage, corrected guide and clean-base replay. | Documented tasks plus reboot/login/teardown/relogin pass without undocumented fixes. |
| F. Rofi controls design — after the Arch guide | Network-first interaction/state design and bounded implementation plan. | Actions, credentials, cancellation, errors, pending state, ownership and delivery are settled before implementation. |
| Publication/reuse — per accepted milestone | Checked media/guide updates and retained lab artifacts. | Publish within authorization; stop guests when idle and retain useful images. |

C–D are complete locally as recorded in the [desktop receipt](desktop-demonstration-receipt.md).
They do not depend on E/F, and accepted media can be published independently
of the complete guide.
Keep implementation, local review and publication statuses distinct.

Ubuntu/Debian and other distribution trials are outside this sequence. Do not
create guests, select releases, add dependency abstractions or delay Arch work
for compatibility. A future request may reopen that scope; there is no automatic
distro trial after the guide or Rofi pass.

## Following design pass: coherent Rofi controls

Bryan finds `nmtui` unpleasant and wants direct Rofi controls for routine
desktop actions. Current Network opens `nmtui` in Kitty, Bluetooth opens
`bluetoothctl` in Kitty, Audio opens graphical `pavucontrol`, and Session already
uses Rofi. Keep that distinction accurate in the present guide.

Design Network first: current status, connection selection/management,
credential prompting, pending operations, errors and cancellation. Inspect
existing tools before choosing reuse or custom code. Then define common visual
and keyboard conventions, using Session as a starting point; retain familiar
Network/Bluetooth/Audio/Session launcher names and advanced-tool handoffs.
Evaluate Audio and Bluetooth next; scanning/pairing needs explicit asynchronous
state and cleanup.

Keep NetworkManager, BlueZ, audio and session owners authoritative. Preserve
credentials/pairings, power policy, independent locking and Cancel-first
restart/shutdown. Decide code ownership and delivery before implementation.
The later controls release updates affected recipes/clips without reworking the
whole tour; it does not reopen palette design or multi-distro support.
