# Capture-first VM plan for Niri Plus

Updated 2026-10-28 after the core desktop/media pass. Reuse the
Starship workstation lab for Arch Linux x86-64 only. Ubuntu/Debian are deferred
for much later, with no guest preparation, release selection or compatibility
work in the current sequence. Viewing, interaction and playback review remain
local to Starship.
Phases 1-2 completed on 2026-10-27: host tools, shared networking, clean Arch
baseline and the native screenshot/recording pilot are established. The guest
is stopped and retained. See the [pilot receipt](capture-pilot-receipt.md) for
measured state, the browser preview and remaining acceptance boundaries.
Phases 3–4 completed locally on 2026-10-28; their
[desktop receipt](desktop-demonstration-receipt.md) records the expanded tasks
and separate stopped `desktop-demo` checkpoint.

This is the environment workstream of the
[demonstration and adoption plan](demo-and-adoption-pass.md). No chezmoi
integration is planned for the lab. The demonstrated desktop and later guide
share recorded public inputs; a successful recording does not establish a
successful clean installation.

Starship is the workstation and already hosts Docker. Keep the virtualization
tools, VM definitions, guest disks and useful checkpoints available between
uses. Start VMs on demand and stop them when their work is finished; there is
no deadline to delete the lab after capture or installation testing.

## Core desktop milestone

The parent plan's work packages 0–4 are complete locally: browser/files and
portal tasks, SwayNC/clipboard, session wiring, native media and site integration.
The [desktop receipt](desktop-demonstration-receipt.md) records the conditional
VM portal build and remaining boundaries. Preserve both earlier checkpoints and
the separate `desktop-demo` checkpoint; use an offline working copy for future
changes and run one Arch guest at a time.

Full SDDM/lock/power/audio/input/output qualification and replay from
`arch-base` follow as a separate Arch installation milestone. The Rofi controls
design comes after that guide. Public publication and fleet rollout remain separate.

## Completed pilot contract

The first implementation pass ended with the native screenshot and recording.
The table and storyboard below describe that completed scope, not remaining
desktop acceptance.

| Needed for the pilot | Outside the pilot |
| --- | --- |
| Starship QEMU/KVM guest, local viewer and host-to-guest SSH. | Remote viewer access, fleet integration and additional hypervisor hosts. |
| Arch, Niri, Chrome, Kitty/Zsh and an application-launch path. | SwayNC, Cliphist, Dolphin and detailed workflow scenes. |
| Current desktop/terminal colors, Noto/Meslo fonts, sample page/project and guest-side recording. | SDDM, lock/power acceptance, audio and complete installation qualification. |
| One screenshot, one 15-30 second clip, and a short assembly/capture receipt. | Full overview/focused clips, site integration, public guide and clean-base replay. |
| One retained lab network with the Arch guest attached. | Other distribution guests and cross-guest tests; deferred without a scheduled trial. |

Use a published immutable component bundle and the independently pinned
identity from [the component record](../../data/components.json). Freeze a
committed, publication-verified tuple when implementation starts; a concurrent
draft pin is not a tested input. Record the public source commit supplying the
remaining examples before assembly. Keep concurrent local shell edits out of
the capture input; do not build the guest from a dirty checkout or copy personal
home configuration.

The pilot should show this short sequence, with timing adjusted for readability:

| Approximate time | Actual task |
| --- | --- |
| 0-5 seconds | Chrome showing a local sample page beside Kitty with the current Zsh prompt. |
| 5-12 seconds | Keyboard focus/column navigation between the browser and terminal. |
| 12-22 seconds | Scroll the sample page, then run a harmless command in the sample project that shows readable colored output. |
| 22-30 seconds | Return to the browser/terminal arrangement and hold a clean final frame. |

Accept the pilot when the exported file plays locally on Starship, the current
palette and fonts are visible, text is readable at the intended site playback size,
input/cursor/motion are coherent, and encoding has no obvious stalls or artifacts.
Inspect frame timing/drops where the recorder exposes them. Report the actual
resolution, frame rate, renderer, recorder settings and any remaining limits;
1080p/30 fps is an initial target, not an unmeasured performance claim.

Retain the source recording, a PNG still and the assembly/capture receipt
outside Git. Include sample/VM labeling and the exact input versions so an
accepted derivative can later be added to the site. Establish capture quality
before extending the desktop or producing the remaining media.

## Outcome and scope

Build a reusable Arch Linux desktop that can be assembled from public inputs,
exercised locally on Starship and used for actual software demonstrations.
Start with the minimum Niri/browser/terminal setup needed for a representative
recording. Add SDDM, full session coverage and clean-base installation acceptance
as the later walkthrough workstream requires them.

The walkthrough starts at an installed Arch system with a normal account,
working networking and package access. Preparing that baseline is lab work;
partitioning instructions and maintaining an OS image are not the product.
Retain the selective component recipes for readers with an existing desktop.

The VM is also suitable for the later Rofi controls work. That future work does
not block this baseline and must not silently replace current utilities during
the initial rehearsal. Containers can continue to serve component tests; no
parallel containerized desktop or homelab migration is needed here.

## Arch scope

The sole active reference target is installed Arch Linux x86-64 with an ordinary
account, network and package access. The retained `niri-plus-arch` guest supplies
capture and a fresh-base installation rehearsal; preparing an Arch OS baseline
is lab work rather than a partitioning/install-Arch product.

Only one working Arch guest runs at a time. Offline recovery copies do not
imply extra running desktops. Ubuntu/Debian and other distributions have no
scheduled milestone, guest definitions, reserved resources or compatibility
abstraction work. Reopen them only through a future scope decision.

An Arch task receipt establishes only the tested task and baseline. Public
component availability, native media, clean-install replay and physical-device
acceptance remain different evidence.

## Retained machine and host contract

| Item | Contract and measured baseline |
| --- | --- |
| Host | Starship, local QEMU/KVM managed through system libvirt. |
| Guest | `niri-plus-arch`, Arch Linux x86-64; one active working guest. Offline checkpoints are not additional running desktops. |
| Compute | Initially four vCPUs with host CPU support and 8 GiB fixed RAM per guest; increase only when a test demonstrates a need. |
| Storage | One working 64 GiB sparse qcow2 disk plus bounded offline checkpoints under the dedicated `niri-plus` libvirt storage directory. No other distro allocations are scheduled. |
| Firmware | Q35 machine, UEFI/OVMF, guest-specific writable variables; Secure Boot is outside this first baseline. |
| Graphics | VirtIO with 3D enabled, explicitly using the AMD render device. No PCI assignment or Nvidia changes. |
| Console | Native local SPICE/OpenGL viewer using a Unix socket or libvirt graphics file descriptor; qualify the local path before proceeding. |
| Display | One virtual output, initially 1920x1080 at scale 1; freeze a readable capture mode after the pilot. |
| Network | One VirtIO NIC on `niri-plus-lab`. Inspect the pilot's cloud-image network owner; the expanded desktop adopts NetworkManager for its virtual Ethernet connection with SSH/console recovery and no competing owner. |
| Audio | Add one virtual sound device and guest PipeWire/WirePlumber for later audio/portal checks; the first recording is silent. |
| Access | From Starship only: local SPICE viewer for guest screen/input, and direct host-to-guest SSH for commands and file export. |
| Account | Ordinary `demo` user with a guest-only password and sudo; `niri-session` is sufficient for the capture pilot, with SDDM added for the installation walkthrough. |

Read-only Starship preflight on 2026-10-26 found a Ryzen 9 7900X, 24 logical CPUs,
93 GiB total RAM with about 79 GiB available, and about 222 GiB free on the
filesystem holding `/var/lib`. KVM is accessible. The AMD render device currently
has the stable path `/dev/dri/by-path/pci-0000:11:00.0-render`; confirm its PCI
identity again before writing the domain. Never rely on `renderD128` numbering
to choose the GPU.

The pilot installed the required QEMU/libvirt, virt-install, OVMF and local
viewer tooling, using the existing dnsmasq package for the managed network.
Its package transaction added 89 packages without changing existing package
versions or removing packages; normal package hooks ran. See the receipt for
exact versions and retained logs. Do not repeat installation or add
`virt-manager` without a concrete need. Any later package change needs a reviewed
transaction; do not perform an Arch partial upgrade.

Retain the installed host tools as a Starship-local workstation
capability. Keep short setup/operation/recovery notes and the reusable VM
definition with this workstream; package receipts, local paths, credentials and
images stay outside Git. Add no
chezmoi package selectors, hooks or fleet deployment machinery for the lab.
The actual desktop components keep their existing public ownership and personal
chezmoi delivery.

Record which packages were already present and which services/network/storage
objects this lab introduces. Retain the lab for Arch capture, installation
rehearsal and later Rofi controls work. Its normal idle state is stopped VMs
with their disks and checkpoints retained, rather than an uninstalled hypervisor
or deleted guests. Keeping it available does not add a fleet-deployment
requirement or reopen the decision to keep the host setup outside chezmoi.

Use only the libvirt sockets/services needed for QEMU, networking and storage,
and record the prior state. Prefer normal local authorization; do not expose a
libvirt TCP listener or loosen global GPU device permissions. A reviewable
domain and one network definition should be the durable inputs, with host paths
and addresses supplied locally. Guest and lab-network autostart stay disabled;
start them explicitly for lab work. Retain their definitions across boots and
uses; the shared network can remain active between guest runs without repeated
teardown. Do not activate an additional default NAT
network as a side effect of installing the tools. Libvirt owns the per-network
dnsmasq process; do not enable the standalone `dnsmasq.service` for this lab.

## Host networking and interruption boundary

Read-only checks found NetworkManager, Docker, firewalld and Tailscale active,
with Wi-Fi as the default route. Use standard libvirt managed NAT: one private
virtual bridge, guest subnet, per-network DHCP/DNS and forwarding/firewall rules.
There are no physical NICs attached to this bridge; `wlan0` keeps its existing
host connection. This is not a bridge onto the home LAN. See
[libvirt's NAT example](https://libvirt.org/formatnetwork.html#nat-based-network)
and [network filtering description](https://libvirt.org/firewall.html).

The pilot selected `niri-plus-lab`, bridge `virbr-np`, subnet
`192.168.124.0/24` and Arch reservation `192.168.124.10`. Reuse that definition;
recheck host/VPN routes and Docker ranges before changing it. Keep the live
network inventory and recovery preimages privately with the lab.

The accepted integration loaded firewalld's packaged libvirt zone and selected
libvirt's supported iptables network backend to coexist with Docker forwarding.
Do not reapply old firewall preimages over later host state. The pilot verified
host/guest connectivity and preserved service PIDs; later host boots or
Docker/firewall restarts remain separate lifecycle checks.

Starship reaches guests directly at their reserved IPs, for example
`ssh demo@GUEST_IP`. Viewing and operation remain local to Starship. No remote
viewer, jump host, console tunnel, subnet-route advertisement or per-guest SSH
port mapping is needed. Use explicit addresses or lab-local SSH aliases; do not
change the host DNS resolver merely to make guest names resolve.

Before activation, record routes, DNS, firewall backend/zones/forwarding policy,
relevant service state and current connectivity. Check libvirt/firewalld
integration and Docker's forwarding policy rather than assuming guest NAT will
work. Docker documents its own forwarding/firewall behavior in its
[firewall guide](https://docs.docker.com/engine/network/packet-filtering-firewalls/).
Do not flush rules, disable a firewall or broadly relax the host's forwarding
policy to make the guest connect. Any needed adjustment must target the lab
bridge/subnet and have a recorded rollback.

Brief setup-related network disruption is acceptable; zero interruption is not
a hard requirement. Prefer managed activation and only the necessary service
reloads. Preserve the existing Wi-Fi profile, host default route/DNS, Docker
networks and Tailscale configuration. After activation, check host SSH, DNS,
Wi-Fi, Docker and Tailscale health, then guest DHCP/DNS, outbound downloads and
SSH from Starship. Recover the prior lab-network/firewall state if an existing host
path fails; do not continue the recording with a broken host network.

NAT is not an isolation guarantee against guest access to the LAN. It also does
not test Wi-Fi scanning or pairing: guests still see virtual Ethernet. CPU/GPU
rendering and recording consume host resources regardless of network mode.

## Local graphics, viewing and capture pilot

Niri's [VM guidance](https://niri-wm.github.io/niri/Getting-Started.html#virtual-machines)
requires 3D acceleration. The pilot established AMD-backed VirGL and readable
1920x1080 recording at a measured average of about 30 fps. This qualifies that
capture workload rather than general graphics performance. The shared render
device remains attached to the host.

Use native SPICE OpenGL with a local viewer on Starship, explicitly selecting
the AMD render node. Choose a managed Unix socket or libvirt's graphics file
descriptor access, with no TCP display listener. Libvirt supports this local
path directly; the separate EGL-headless/remote-console combination is no
longer part of the plan. See the
[graphics definitions](https://libvirt.org/formatdomain.html#graphical-framebuffers).

Check that a local Starship graphical session and compatible viewer are
available before the interactive pilot. Keep a serial/host-to-guest SSH recovery
path. Verify viewer keyboard grab/release and guest Super shortcuts explicitly;
preserve the host's existing bindings. Test only the owned guest/viewer, without
injecting input into unrelated host windows or recording the host desktop.
Turn off host/guest clipboard synchronization, file transfer and USB redirection.
The guest's own clipboard must still work normally.

Qualify the recording path while producing the first deliverable:

1. Boot the guest, reach its console and SSH, start Niri and inspect its renderer.
   Record the renderer/version and confirm the intended accelerated path.
2. Apply the current Niri/Kitty appearance and selected fonts, and install the
   public Zsh setup. View it locally on Starship, open Kitty and Chrome, scroll
   and switch columns, resize/focus windows, and test key capture/release. Use the actual
   selected palette and browser for this pilot.
3. Produce one guest screenshot and a 15-30 second guest-side recording,
   initially targeting 1080p/30 fps. Check readability, cursor, animation pacing,
   dropped frames and whether the recorder distorts the experience.
4. Close/reopen the local viewer and confirm Niri and the recording remain
   alive. Export the file to Starship through host-to-guest SSH and inspect local
   playback, including the intended site playback size.

Evaluate the resulting still and clip against the milestone above. Keep them
even if the later walkthrough uncovers assembly fixes. Full SDDM, lock, power
and installation testing are later tasks.

Use a screencopy-compatible recorder such as `wf-recorder`, subject to its own
compatibility check. Niri documents support for the older `wlr-screencopy` and
newer capture protocol paths in its
[capture guide](https://niri-wm.github.io/niri/Screencasting.html). Record inside
the guest so the final media excludes the host desktop and viewer framing or
scaling. SDDM/boot evidence uses clearly identified console stills when
needed; a guest-session recorder cannot capture an entire boot/login sequence.

Start with silent video, adding captions later. Do not assume hardware video
encoding is available through VirtIO; CPU encoding is acceptable if the pilot
passes. Later, verify Chrome whole-monitor sharing separately through the
selected WLR portal; a recorder working does not establish browser portal
acceptance.

If the local rendering/capture path fails, keep the capability test small and
inspect the measured failure. Alternatives are adjusting the local viewer or
guest display/capture mode, or a qualified software-rendering
trial. Do not escalate automatically to GPU passthrough, a container desktop or
PVE migration. Choose a fallback after the failure is understood.

## Public guest baseline and dependency record

The retained baseline came from the verified official Arch cloud image
recorded in the pilot receipt, with its published checksum and detached
signature checked using an isolated keyring. NoCloud prepared the ordinary
account, locale/timezone, network, sudo, SSH and console recovery. The clean
checkpoint contains no Niri Plus desktop, private chezmoi or personal home
import. Reuse it for the installation rehearsal rather than introducing a new
ISO-install workstream.

Track the guest's package versions and package sources, the public Niri Plus
source commit, immutable component bundle/hash, identity/hash and independent
project release pins. Arch is rolling release: a package list and image alone are
not a promise of byte-for-byte future rebuilds. Keep the tested images and
package evidence locally; describe the actual tested baseline on the site.

The guest must use public setup instructions and artifacts for the desktop.
During capture preparation, keep a short record of every additional assembly
step or fix; completion of the guide is not a prerequisite. Reconcile those notes
into the public reference profile and instructions during the later rehearsal.
Keep lab-only SSH, virtual-display and test-fixture settings distinguishable
from the reader-facing desktop. Never fill a missing public step by importing
the private chezmoi setup.

Use Chrome for the primary browser story, from a reviewed package recipe/source
with recorded provenance. Do not silently substitute Chromium in the media.
Resolve installation prerequisites before the assembly rehearsal. Keep the
browser unsigned-in with no synchronization or personal extensions. Choose and
document a guest-only secret backend; do not import wallet files or imply that
guest authentication establishes the fleet's KWallet/PAM acceptance.

## Checkpoints and reset contract

Save one clean base before desktop assembly. Add working checkpoints/clones
only when useful; there is no checkpoint framework to build before recording.
Do not depend on live memory snapshots or assume a copied qcow2 file also
preserves UEFI variables and machine configuration. Libvirt distinguishes clean
inactive disk snapshots from crash-consistent live ones in its
[snapshot documentation](https://libvirt.org/formatsnapshot.html).

| Checkpoint | Contents | Use |
| --- | --- | --- |
| `arch-base` | Installed Arch, account, network, SSH and console recovery; no desktop. | Authoritative start for the complete Niri Plus installation rehearsal. |
| `niri-plus` (existing pilot) | Basic Niri/Chrome/Kitty/Zsh, appearance and capture harness. | Protected recovery point for the accepted pilot; not full-desktop acceptance. |
| `desktop-demo` (next) | Expanded desktop with core workflow results and media/input receipt. | Reference for site demonstrations and later work; clean-install qualification remains separate. |

The pilot already saved `arch-base` before desktop assembly and `niri-plus`
after capture/recovery checks. Preserve both with their original meaning.
Create an offline working copy of the pilot for the next slice, retaining disk,
UEFI variables and domain XML together; establish that it boots and its guest
guard/access still work before desktop changes. Initially reuse the same owned
guest identity with only one active instance; never boot duplicate identities
concurrently.

Save `desktop-demo` only after its native tasks pass. The final guide must
later pass from a fresh `arch-base` copy; starting at a desktop checkpoint would
skip installation/session work. Media can precede that replay, with labels
that do not imply clean-install acceptance.

For each checkpoint preserve disk contents, domain XML, UEFI variables, package
and source receipt, and verification results. Keep the source checkpoint off
and immutable while cloning it. Reconcile UUID/MAC, machine identity and SSH
host keys if a clone will coexist with its source. Initially run only one clone
at a time and verify its identity after every restore.

Keep images under the dedicated libvirt storage area, outside Git. Limit the
Arch sequence to one working image and at most these three checkpoints.
Allocate no Ubuntu/Debian images. Prefer sparse independent copies or filesystem
reflinks when supported; qualify restoration before modifying a working copy
and before the clean-install rehearsal.
Avoid a growing backing-file chain in this first pass.

Monitor actual allocated image/capture space. Stop creating images or recording
if the host filesystem would fall below 50 GiB free. Copy accepted media out
before discarding a capture clone; checkpoint deletion must name exact owned
files and retain the last verified recovery point.

## Desktop coverage and evidence

The accepted [Arch installation pass](arch-installation-pass.md) owns the next
guide/development/fresh-replay sequence and its task-level acceptance gates.
Preserve the existing `desktop-demo` checkpoint as well as the earlier pilot
and base while qualifying that separate working copy.

This is the eventual coverage checklist, not a prerequisite for the first
recording. Initially qualify Niri/Chrome/Kitty and the current appearance, then
add notifications/clipboard and other demonstrated flows. The installation
workstream completes the remaining core checklist later.

| Area | VM acceptance | Remaining boundary |
| --- | --- | --- |
| Login and lifecycle | Cold boot to SDDM, password login to Niri, logout/login, reboot; user services start once and stop with the session. Apply and inspect the neutral greeter in this guest. | Physical-host SDDM/PAM/wallet behavior remains separate. |
| Browser and files | Chrome/download, Dolphin open/Open with, sample upload, MIME defaults and GTK picker; whole-monitor WLR sharing starts and stops. | No private accounts or downloads; per-window capture stays outside the baseline. |
| Appearance and terminal | Current Crisper Neutral Slate/Clear Blue desktop, pure-black Balanced+ Kitty, Noto/Meslo, cursor/icons, GTK and Qt surfaces, Zsh prompt/completion/history. | No new palette redesign or personal SDK environment. |
| Information and clipboard | Pinned SwayNC fork, CPU/RAM and virtual Ethernet status, sample notifications, text/image Cliphist, launcher bindings and clean teardown. | Missing GPU/battery/Bluetooth cards hide; no fabricated live hardware values. |
| Session and authorization | Polkit prompt using an owned reversible guest operation, Gtklock lock/unlock, independent idle reload while locked, explicit guest power policy and cancel paths. | Physical suspend/resume, lid and host authentication are not established. |
| Displays and input | One-output Kanshi profile, readable scaling, keyboard layout and configured Fcitx5 text entry; test changed output modes where supported. | Real docks, monitor hotplug and physical input devices need hardware checks. |
| Utilities and audio | Current Network/BT/Audio/Session entry points; virtual Ethernet state, guest audio playback/volume feedback, logout and cancel-first power actions. | No adapter/backlight means no radio pairing or physical brightness acceptance; Rofi controls remain future work. |
| Ordinary files/media | Disposable PDF/image/archive/audio/video examples with the documented applications; optionally a guest-only virtual removable disk. | Real USB mounting, codecs beyond the selected samples and physical devices are separate. |
| Optional remote/agent workflows | Public launcher setup against owned sample sessions or a disposable endpoint; actual native agent TUI only when its prerequisites are met. | No fleet enrollment, personal SSH keys, production sessions or borrowed provider credentials. |

Default guest power policy disables automatic suspend/display-off during
recording; list it explicitly as demo policy. Qualify idle/manual lock in a
separate owned guest trial and restore the recording policy afterward. A
guest-only reboot/logout/lock is permitted during the future implementation;
none of those actions should target Starship's host session.

Show natural missing-hardware behavior in the native VM. If extra hardware
cards need illustrations, reuse isolated sample renderings with visible fixture
labels rather than passing them off as the VM's actual telemetry.

Optional agent authentication, if needed, uses a dedicated guest-only account
and explicit access scope; keep credentials out of clean images, Git and media.
Without it, defer that authenticated sequence and record its status honestly.
No live agent conversation is required to accept the core desktop. Remote
extensions can use a small disposable endpoint; they do not require changes to
the three desktop hosts or homelab services.

## Execution order and completion gates

| Phase and status | Result | Gate before proceeding |
| --- | --- | --- |
| 1. Workstation lab — complete | Retained tools, NAT network, Arch guest/storage and operating notes. | Pilot receipt records connectivity and host preservation; later host reboot/firewall lifecycle checks remain explicit. |
| 2. Capture pilot — complete | Current-theme Niri/Chrome/Kitty/Zsh, screenshot, 24.5-second clip and receipt. | Native rendering/encoding passed; manual viewer key handling and complete desktop acceptance remain distinct. |
| 3. Core desktop assembly — complete locally | Browser/files/portals, SwayNC/clipboard, session wiring and notes. | Parent work packages 0-3 pass on a protected working copy using public inputs. |
| 4. Media/local site — complete locally | Overview/focused clips, posters, captions, links and provenance. | Parent work package 4 passes; reviewable local changes are ready for separate publication. |
| 5. Complete Arch guide/replay — following milestone | Wider desktop checklist and corrected instructions from a fresh `arch-base` copy. | Password login, core tasks, reboot and service teardown/relogin pass without undocumented repairs. |
| Retain for reuse — throughout | Accepted evidence plus retained definitions/images/checkpoints. | Guests stopped when idle; images remain useful; deletion is not a completion requirement. |

Phases 1–4 are delivered locally; the [desktop receipt](desktop-demonstration-receipt.md)
records the tasks, VM portal compatibility build and limits. Full Arch
installation acceptance follows separately. The parent plan
then schedules a Network-first Rofi controls design, not automatic controls
implementation. Ubuntu/Debian are deferred for much later with no scheduled
trial or current compatibility work.

The pilot resolved Arch networking/rendering/capture viability. Keep pending
checks specific: physical viewer key handling, later host/network lifecycle,
the expanded native tasks and the fresh-base installation replay. A successful
recording does not resolve those by implication.

Keep small recipes and reviewable definitions rather than building a generic
VM orchestrator or unattended distro installer. Stop the VM between sessions
and retain useful tools/images, with no automatic expiry. Prepare local source
and media; push, release, site publication and fleet deployment remain separate
actions within authorization.

## Optional future maintenance

Pruning old images or retiring a guest is a later maintenance choice, not the
expected final step of this project. First export accepted media, provenance and
the assembly/test notes. Remove only this lab's domains, disk/NVRAM/checkpoint files and dedicated
storage definitions. Retiring one distro guest does not remove the shared
network. After the last lab guest is stopped and no other consumers remain,
remove the exact `niri-plus-lab` network through libvirt, check its bridge,
per-network dnsmasq and managed firewall cleanup, and restore any lab-specific
service or explicit firewall changes. Do not restore an old global firewall
snapshot over unrelated later changes. Review dependencies before removing
newly added packages, retaining tools that have acquired another use. Existing
dnsmasq, Docker and desktop packages are not lab-owned. Keeping the hypervisor,
shared network and useful guests installed is the default after this pass.

Phases 1–4 are delivered locally. The next work is the complete Arch guide and
fresh-base replay; public-site publication remains separate.
Ubuntu/Debian remain deferred without a scheduled trial.
