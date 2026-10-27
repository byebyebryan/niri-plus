# Demonstrations and public adoption walkthrough

Revised planning draft, 2026-10-27. Capture and recording come first, followed
by the full desktop demonstrations and a reader-facing installation walkthrough.
Virtualization is a retained Starship workstation capability, with VMs used on
demand and no chezmoi integration for the host tooling.
The host/Arch capture pilot completed on 2026-10-27; see the
[pilot receipt](capture-pilot-receipt.md). Full installation rehearsal, site
implementation and rollout have not started. Rofi controls remain a separate
candidate for the following design pass.
Later Ubuntu/Debian trials share the VM lab but are not prerequisites for the
Arch pilot or core media.

## Immediate milestone

The first implementation pass delivered one current-theme desktop screenshot and
a 24.5-second browser/terminal clip from the VM, with recorded public inputs
and a short assembly/capture receipt. Inspect the result locally on Starship
for readable text, current colors/fonts, coherent navigation and smooth recording before
expanding the setup. The [capture-first VM plan](vm-reference-environment.md)
contains the concrete pilot sequence and acceptance criteria.

Full installation qualification, detailed workflow clips and site integration
follow as distinct milestones. Preparing the first recording does not require
a finished guide or SDDM/locking/power testing.

## Outcome and inspected baseline

Give a visitor a connected route: watch a task, understand the pieces behind it,
assemble those pieces, and verify the same result. Preserve the personal story:
Chrome and ordinary file interaction alongside keyboard-driven terminal and
agent work. Keep maintenance appropriate for a personal desktop.

The current site has four illustrated tour scenes, an Agent Plus native sample
image, and isolated SwayNC images. Those images use preview/default themes or
sample hardware data; they do not show the complete current Neutral Slate
desktop. There is no current full desktop recording. Keep the existing labels
and attribution accurate when adding new media.

The setup page links a seven-stage assembly map to focused recipes. It starts
from a working Niri session and explicitly has no clean-install acceptance.
The portable base Niri configuration intentionally omits service startup and
several integration bindings. These choices need an explicit assembly path
before the complete result can be described as reproducible.

Reusable desktop, shell and appearance code is public in immutable component
bundles; freeze the published tuple before implementation rather than coupling
the plan to a version that may change during concurrent work. Current examples
regenerate from those owners. Personal policy, environment,
machine selection and fleet deployment remain in private chezmoi. Existing
independent projects keep their own release authority.

## Recommended shared reference environment

Use a versioned public reference setup for media capture and the later
installation rehearsal. Record the component, identity and independent project
pins used by each milestone. It must be possible to build using the public
repository, release artifacts and documented prerequisites alone.

First assemble and record the demonstrated workflows, keeping notes as we go.
Then use those notes to finish the guide and repeat it from a clean baseline.
Native demonstration evidence and clean-install acceptance remain separate;
recordings can be published before the complete installation route is qualified.

Target one documented Arch Linux baseline first: an installed system, ordinary
user account and working network. Document any required graphics/login
prerequisites before starting. OS partitioning and maintaining a distribution
are outside this walkthrough. EndeavourOS differences can be recorded after
the first route is rehearsed.

After the Arch recording pilot, Ubuntu LTS and Debian stable are additional
compatibility candidates. Select and record one exact release per distro when
its trial starts. Check dependencies and capture/session viability first;
record gaps and tested tasks separately. A distro trial does not imply a
supported installation guide until its own clean-base replay passes.

Keep the existing path for adding individual components to an already working
Niri session. The complete reference walkthrough supplies the missing glue;
it does not replace personal configuration with a wholesale dotfiles copy.
Power, locking and output profiles remain explicit reader choices.

Use a local Starship QEMU/KVM VM as the primary reference environment, with
recoverable checkpoints and resettable working clones. Keep the tools, VM
definitions and useful guest images between uses; stop VMs when their work is
finished. No cleanup deadline follows capture or setup testing. First verify that it can
run the actual Niri/application stack, display the selected appearance and be
viewed and recorded reliably. VM-only evidence cannot establish physical radio,
backlight, dock or authentication behavior on Bryan's machines.

## VM reference environment

Read-only preflight on 2026-10-26 compared Starship with the existing PVE host.
Both options use QEMU/KVM; the practical differences are the available graphics
path, management and where the demo is viewed.

- Starship: `/dev/kvm` is accessible, approximately 80 GiB RAM was available,
  and AMD Radeon 610M/NVIDIA render nodes are accessible. The normal QEMU/libvirt
  tools are not installed. The AMD integrated GPU is the preferred candidate
  for a shared virtual 3D device, subject to a small guest rendering test.
- PVE: 9.2.21, approximately 20 GiB RAM available, storage below one-third used,
  with NAS and Docker guests running. Only the ASPEED display controller and
  a card node were discovered; no GPU render node was present. It has capacity
  for an install-test guest, but accelerated desktop capture would require a
  separately qualified graphics path. Software rendering is not ruled out.

The selected direction is a VM for the combined walkthrough and demonstration
work. Plan one local Starship guest through libvirt: four vCPUs, 8 GiB RAM,
64 GiB thin disk, UEFI and VirtIO graphics/storage/network. Use the AMD render
device for shared acceleration; Nvidia passthrough is unnecessary for this
scope. Graphics horsepower is not the reason to choose Starship: available
CPU/RAM and an accessible rendering path make it a practical first host.

Use one named libvirt NAT network, `niri-plus-lab`, for Arch and later distro
guests, with reserved guest IPs. Starship connects directly and owns all viewing,
interaction and recording review. The virtual bridge does not attach the physical
Wi-Fi interface. Check subnet overlap and firewalld/Docker forwarding behavior
before activation, then verify host and guest connectivity. Brief setup-related
network disruption is acceptable; preserve the host's existing configuration
and record recovery. There is no requirement to engineer zero interruption.

The [VM reference plan](vm-reference-environment.md) defines host setup,
local Starship access, the guest baseline, checkpoint recovery, desktop coverage
and the implementation gates. Host virtualization stays installed locally with
short setup/operation/recovery notes; it adds no chezmoi selectors or fleet
package hooks.
The first deliverable is one current-theme browser/terminal recording,
qualifying accelerated Niri, local viewer input and guest-side recording
together. Use native local SPICE/OpenGL viewing on Starship; remote viewing,
SSH console tunnels and EGL-headless rendering are outside this scope. Actual
usability remains to be tested.

Containers remain useful for isolated component checks, but a second full
desktop harness is outside this pass. PVE remains a fallback if there is a
measured reason to move the guest. No virtualization package, VM, bridge,
device assignment or PVE guest configuration has been changed.

## Demonstration set

Start with the pilot still and short clip. After capture quality passes, expand
to a 45-75 second overview and focused clips of roughly 20-45 seconds. Browser,
terminal and information/clipboard scenes form the core; authenticated agent
and cross-host sequences follow when their separate prerequisites are met.
Final durations follow clarity and readability, rather than becoming quotas.

| Scene | Task to show | What the viewer should learn | Instruction destination |
| --- | --- | --- | --- |
| Browser and files | Navigate Chrome beside a terminal; download and open a harmless sample in Dolphin; select a local file through a browser file picker. | The graphical half is useful and comfortable; Niri navigation connects it to terminal work. | Base session, browser/files, portal and MIME steps. |
| Building in terminals | Navigate a small public/sample project, show the prompt and editing workflow, then open and return to a dedicated agent TUI through Agent Plus. | Keyboard work, readable terminal colors and native agent ownership are central to the setup. | Kitty/Zsh and optional Agent Plus steps. |
| Information and clipboard | Open/close SwayNC, inspect sample notifications and available cards, then retrieve text and an image with the clipboard picker. | Information appears on demand; there is no permanent bar; clipboard content keeps its original form. | Notification and clipboard steps. |
| Work across hosts | Use SSH Plus and Tmux Plus to reach or return to a session on an owned demo endpoint. | Remote work remains close to the keyboard and is an optional extension. | Remote prerequisites and the maintained component guides. |

The overview introduces the browser/terminal split, navigation and on-demand
information. Focused clips explain individual tasks, with a small action/key
caption and a direct setup link. Start terminal capture with a sample repository;
add a harmless guest-only native agent sequence later when its prerequisites
are met. Do not use private work or existing native conversations.
If a particular action is not actually exercised, explain it as an illustration
or omit it from the recording rather than implying it occurred.

Use a fresh demo browser profile, local sample download/upload pages, sample
documents and isolated clipboard/notification state. Remote demonstrations use
an explicitly owned endpoint and sample sessions. No private browser accounts,
passwords, real notifications or existing agent/tmux sessions enter the media.

These are recordings of real software in a staged native demo session. Label
that setting at the point of use, identify fixture hardware data, and distinguish
it from Bryan's daily desktop. Any later daily-session recording needs a
separately agreed capture scope. Respect the repository's existing boundary
against operating the user's desktop, devices, locks or native sessions.

Deliver a readable poster and browser-playable video with native controls,
textual steps/captions and keyboard/mobile access. Keep explicit playback
available from the overview and tour. Any short hover preview is a separate,
deferred silent derivative with reduced-motion/data-saving/touch fallbacks.
Extend the existing media provenance record with source versions, session
scope, fixture labels, dimensions and file hashes; keep original captures and
editing notes outside generated site output.

## Guided installation route

Rewrite the main setup page as one ordered route, retaining focused recipes for
detail and selective adoption. Each stage needs prerequisites, exact public
inputs, scoped commands, a visible expected result, a troubleshooting pointer
and a way back.

1. Establish the baseline and recovery point. Record the tested environment,
   release tuple, optional components and explicit policy choices.
2. Start Niri with Kitty and Rofi. Verify navigation, the application launcher,
   session PATH and the intended login/startup path.
3. Add Chrome or the reader's chosen browser, Dolphin, GTK/WLR portal routing,
   application defaults and the download/open/upload-file task.
4. Apply the selected desktop and terminal identity, fonts, cursor and icons.
   Explain what is generated and which native preferences are merged.
5. Add SwayNC and Cliphist. Wire and verify the actual launch bindings,
   collectors, session services and notification behavior used in the tour.
6. Add authorization, manual locking, explicit idle/power policy, hardware-key
   feedback and the current common utility entries. Keep greeter/root changes
   separately inspectable and preserve a working login path.
7. Add the shared Zsh core and pinned upstream plugins. Verify a new shell,
   prompt/history/completion and missing optional tools. Keep personal SDK and
   environment customization outside the generic instructions.
8. Offer SSH/Tmux/Agent Plus as an optional extension, including the real launch
   contracts and explicit access prerequisites. The core desktop must remain
   useful without that ecosystem.

Audit every demonstrated entry point against this route: bindings, helper
locations and executable modes, dependencies, session PATH/environment,
configuration files, service activation/teardown, fonts and policy inputs.
Reconcile the base example with the selected appearance merge and the extra
integration bindings. A file existing in the repository is not proof that the
reader has installed or enabled it.

During rehearsal, follow the written steps in a clean account, keep a command
transcript and checkpoints, and record every undocumented adjustment. Repeat
the corrected route from the initial snapshot. Require a new graphical session
and the browser/file, launcher, terminal, notification and clipboard tasks to
work using public inputs. Record unsupported hardware/authentication checks
separately instead of calling the whole fleet physically accepted.

## Work order and exit gates

| Phase | Reviewable result | Gate |
| --- | --- | --- |
| A. Capture scope and workstation lab | Small storyboard, recorded public input versions and a reusable Starship VM. | A usable isolated desktop is viewable locally on Starship; host setup and recovery are recorded. |
| B. Capture pilot, end of next implementation pass | One still, a 15-30 second browser/terminal recording and its receipt. | Current appearance, readable motion/text, reliable capture and sample content; inspect the retrieved file before expanding the environment. |
| C. Demonstrated desktop assembly | Add SwayNC/clipboard and other pieces needed for the scenes; keep assembly notes. | Every shown workflow actually works and has recorded public inputs; complete installation acceptance is not claimed. |
| D. Focused media and site integration | Overview/focused clips, posters, captions, setup links and provenance. | Real native output is labeled correctly; playback, keyboard/mobile, reduced-motion and no-JavaScript reading work. Optional remote/agent prerequisites do not block core media. |
| E. Public installation walkthrough, later | Gap audit, corrected ordered guide, scoped examples and a clean-base rehearsal. | Rebuild from the initial snapshot, boot/login and complete the documented core tasks without undocumented fixes. |
| F. Later distro trials | Ubuntu/Debian guests on the shared lab network, with per-release dependency and task receipts. | Arch pilot already delivered; record gaps and installation acceptance independently for each distro. |
| G. Publication and continued reuse | Independently checked media/guide updates, retained artifacts and an available workstation VM lab. | Publish checked milestones independently; do not hold Arch media for later distro trials. Stop guests when idle, retaining useful images/checkpoints; deletion is optional future maintenance. |

A-B are the next implementation slice. Once the capture pilot passes, media,
guide and distro trials can proceed as separate follow-ons; later rows are not
a requirement to finish every branch before publishing an earlier milestone.

The captured setup and assembly notes become the guide's source of truth.
Keep their versions aligned, but do not delay recording for a complete guide,
SDDM/lock/power acceptance, or an unattended installer. Add those installation
checks in the later rehearsal. Keep the existing theme and component baseline
while preparing demonstrations.

If the later rehearsal changes a demonstrated behavior, update the affected
clip or identify its earlier tested version. A clip proves the shown workflow;
only the clean-base replay establishes installation acceptance. Publish those
statuses separately rather than holding core media for the complete guide.

## Follow-on candidate: coherent Rofi controls

Bryan finds `nmtui` unpleasant and wants to consider direct Rofi controls instead
of opening a separate interface for routine desktop actions. This is an
experience direction to design next, not an approved implementation or a
change to the current entry points.

Current behavior is mixed: Network opens `nmtui` in Kitty; Bluetooth opens
`bluetoothctl` in Kitty; Audio opens the graphical `pavucontrol`; Session already
uses a Rofi menu. Keep this distinction accurate in the current walkthrough.

Proposed priority for the next design pass:

1. Network first: current connection/status and a clear route to select or
   manage a connection. Settle credential prompting, errors and pending state
   before implementation; inspect existing tools before choosing reuse or
   custom code.
2. Define shared interaction and visual conventions, using the existing Session
   menu as a starting point. Keep the familiar Network/Bluetooth/Audio/Session
   names reachable through the application launcher.
3. Evaluate Audio and Bluetooth next. Establish their common actions and
   advanced-tool handoffs; Bluetooth scanning/pairing needs its own asynchronous
   state, confirmation and cleanup design.

Keep native NetworkManager, BlueZ, audio and session owners authoritative.
Preserve existing authorization, credentials/pairings and policy; menus need
fresh state, visible pending/error results and cancellation without accidental
actions. Retain independent locking, native logout confirmation and Cancel-first
restart/shutdown behavior. Decide code ownership and delivery after the Network
scope is clear, before starting a writer.

The media/walkthrough pass can proceed against the current released baseline.
Show the common utility entry points briefly; reserve detailed control-flow
demonstrations for the selected Rofi design. A later controls release updates
the affected guide section and clip without reworking the whole desktop tour.
