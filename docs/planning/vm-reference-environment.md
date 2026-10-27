# Capture-first VM plan for Niri Plus

Revised planning draft, 2026-10-27. Establish reusable virtualization on Starship,
starting with an Arch VM, and deliver a representative screenshot and short
recording first. Use one
shared libvirt NAT network for that guest and later Ubuntu/Debian trials. Full
desktop demonstrations and the installation walkthrough remain later milestones.
Viewing, interaction and playback review take place locally on Starship.
Execution started on 2026-10-27. The host tools, shared network and clean Arch
baseline are now established; desktop assembly and capture qualification are
in progress. See the [pilot receipt](capture-pilot-receipt.md) for measured state.

This is the environment workstream of the
[demonstration and adoption plan](demo-and-adoption-pass.md). No chezmoi
integration is planned for the lab. The demonstrated desktop and later guide
share recorded public inputs; a successful recording does not establish a
successful clean installation.

Starship is the workstation and already hosts Docker. Keep the virtualization
tools, VM definitions, guest disks and useful checkpoints available between
uses. Start VMs on demand and stop them when their work is finished; there is
no deadline to delete the lab after capture or installation testing.

## Next implementation milestone

The next pass ends with a usable capture pilot, not the entire workstream.

| Needed for the pilot | Outside the pilot |
| --- | --- |
| Starship QEMU/KVM guest, local viewer and host-to-guest SSH. | Remote viewer access, fleet integration and additional hypervisor hosts. |
| Arch, Niri, Chrome, Kitty/Zsh and an application-launch path. | SwayNC, Cliphist, Dolphin and detailed workflow scenes. |
| Current desktop/terminal colors, Noto/Meslo fonts, sample page/project and guest-side recording. | SDDM, lock/power acceptance, audio and complete installation qualification. |
| One screenshot, one 15-30 second clip, and a short assembly/capture receipt. | Full overview/focused clips, site integration, public guide and clean-base replay. |
| One shared lab network, initially with only the Arch guest attached. | Ubuntu/Debian guests and cross-guest tests, after the Arch capture pilot. |

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

## Distro scope and scheduling

| Guest | Purpose | Admission |
| --- | --- | --- |
| `niri-plus-arch` | Primary capture desktop and first complete installation walkthrough. | Create first; its screenshot/clip is the next deliverable. |
| `niri-plus-ubuntu` | Explore the same desktop on one Ubuntu LTS baseline. | Follow-on trial after the Arch pilot; record the exact release when selected. |
| `niri-plus-debian` | Explore the same desktop on one Debian stable baseline. | Follow-on trial after the Arch pilot; record the exact release when selected. |

Networking is shared, but guest disks, accounts, configuration and evidence are
separate. Keep comparable virtual hardware and record necessary differences.
Run one guest at a time by default; start a second only for a defined cross-host
demonstration or connectivity test. Additional distro installations must not
compete with the recording pilot for resources or become its completion gates.

For each later distro, first check Niri and recorder availability, release
compatibility, Python/toolkit versions and public fork/bundle installation.
Record package-name, unit-name and session differences before expanding into
full assembly. A source build or unavailable dependency is a documented gap,
not a reason to upgrade unrelated components or claim support prematurely.
Status progresses from not tested, to explored with gaps, to the specific tasks
actually verified. Only a clean-base replay qualifies an installation guide for
that exact distro/release. No multi-distro support promise is part of this pilot.

## Proposed machine and host changes

| Item | Initial choice |
| --- | --- |
| Host | Starship, local QEMU/KVM managed through system libvirt. |
| Guest | Initially `niri-plus-arch`, Arch Linux x86-64; add the other distro guests later. Offline checkpoints are not additional running desktops. |
| Compute | Initially four vCPUs with host CPU support and 8 GiB fixed RAM per guest; increase only when a test demonstrates a need. |
| Storage | Initially one 64 GiB sparse qcow2 disk per guest, VirtIO storage, under a dedicated `niri-plus` libvirt storage directory; allocate later guests only when used. |
| Firmware | Q35 machine, UEFI/OVMF, guest-specific writable variables; Secure Boot is outside this first baseline. |
| Graphics | VirtIO with 3D enabled, explicitly using the AMD render device. No PCI assignment or Nvidia changes. |
| Console | Native local SPICE/OpenGL viewer using a Unix socket or libvirt graphics file descriptor; qualify the local path before proceeding. |
| Display | One virtual output, initially 1920x1080 at scale 1; freeze a readable capture mode after the pilot. |
| Network | One VirtIO NIC per guest on the shared libvirt NAT network `niri-plus-lab`; guest NetworkManager owns Arch's virtual Ethernet connection. |
| Audio | Add one virtual sound device and guest PipeWire/WirePlumber for later audio/portal checks; the first recording is silent. |
| Access | From Starship only: local SPICE viewer for guest screen/input, and direct host-to-guest SSH for commands and file export. |
| Account | Ordinary `demo` user with a guest-only password and sudo; `niri-session` is sufficient for the capture pilot, with SDDM added for the installation walkthrough. |

Read-only Starship preflight on 2026-10-26 found a Ryzen 9 7900X, 24 logical CPUs,
93 GiB total RAM with about 79 GiB available, and about 222 GiB free on the
filesystem holding `/var/lib`. KVM is accessible. The AMD render device currently
has the stable path `/dev/dri/by-path/pci-0000:11:00.0-render`; confirm its PCI
identity again before writing the domain. Never rely on `renderD128` numbering
to choose the GPU.

Normal QEMU/libvirt management packages are not installed; dnsmasq is already
installed. The expected starting package set is `qemu-desktop`, `libvirt`,
`virt-install` and `edk2-ovmf`, with existing `dnsmasq` for the managed network
and `virt-viewer` on Starship.
`virt-manager` is optional. Inspect the actual package transaction and existing
service/socket ownership before installation. Do not perform an Arch partial
upgrade; resolve any required system-upgrade scope explicitly before proceeding.

Install and retain the needed host tools as a Starship-local workstation
capability. Keep short setup/operation/recovery notes and the reusable VM
definition with this workstream; package receipts, local paths, credentials and
images stay outside Git. Add no
chezmoi package selectors, hooks or fleet deployment machinery for the lab.
The actual desktop components keep their existing public ownership and personal
chezmoi delivery.

Record which packages were already present and which services/network/storage
objects this lab introduces. Retain the lab for capture, setup testing, distro
experiments and later Rofi controls work. Its normal idle state is stopped VMs
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

Choose an unused private IPv4 subnet after checking all host/VPN route tables,
existing virtual networks and Docker ranges. Use a distinct short bridge name,
such as `virbr-np`, and the network name `niri-plus-lab`. Add DHCP reservations
for each guest as it is created; keep the selected addresses in the local lab
inventory. There is one shared network, not one network per distro.

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
SSH from Starship. When a second guest is added, also check guest-to-guest
connectivity. Recover the prior lab-network/firewall state if an existing host
path fails; do not continue the recording with a broken host network.

NAT is not an isolation guarantee against guest access to the LAN. It also does
not test Wi-Fi scanning or pairing: guests still see virtual Ethernet. CPU/GPU
rendering and recording consume host resources regardless of network mode.

## Local graphics, viewing and capture pilot

Niri's [VM guidance](https://niri-wm.github.io/niri/Getting-Started.html#virtual-machines)
requires 3D acceleration. The AMD iGPU is expected to be adequate for ordinary
desktop composition; performance is not yet measured. Using it as a shared
render device does not require detaching it from the host.

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

Create the Arch baseline from verified official installation media, recording
the ISO/version/hash and installation choices. Include a bootable disk, ordinary
user, locale/timezone, working virtual network, sudo, SSH and a console recovery
path. It must contain no Niri Plus desktop, private chezmoi checkout or personal
home-directory import.

Track the guest's package versions and package sources, the public Niri Plus
source commit, immutable component bundle/hash, identity/hash and independent
project release pins. Arch is rolling release: a package list and ISO alone are
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
| `niri-base` (optional) | Basic Niri, terminal and working graphics; SDDM is not required yet. | Recording pilot and debugging later stages. |
| `niri-plus` (later) | Assembled desktop with the demonstrated workflows checked. | Further capture work and later controls; installation acceptance is recorded separately. |

Save `arch-base` before desktop assembly so the later rehearsal has a clean
starting point. Add the other checkpoints only when useful, rather than
building a checkpoint framework before the first recording. The final guide
must pass from `arch-base`; starting at `niri-base` would skip the login/session
work. Media can use the working desktop before that later rehearsal passes;
its label must not imply clean-install acceptance.

For each checkpoint preserve disk contents, domain XML, UEFI variables, package
and source receipt, and verification results. Keep the source checkpoint off
and immutable while cloning it. Reconcile UUID/MAC, machine identity and SSH
host keys if a clone will coexist with its source. Initially run only one clone
at a time and verify its identity after every restore.

Keep images under the dedicated libvirt storage area, outside Git. Limit the
initial Arch pass to one working image and at most these three checkpoints.
Create later distro images only when starting their trials, initially with one
clean base and one working image each; do not replicate every Arch intermediate
checkpoint. Prefer sparse independent copies or filesystem reflinks when
supported; qualify the restore procedure before each clean-install rehearsal.
Avoid a growing backing-file chain in this first pass.

Monitor actual allocated image/capture space. Stop creating images or recording
if the host filesystem would fall below 50 GiB free. Copy accepted media out
before discarding a capture clone; checkpoint deletion must name exact owned
files and retain the last verified recovery point.

## Desktop coverage and evidence

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

| Phase | Result | Gate before proceeding |
| --- | --- | --- |
| 1. Workstation VM capability | Retained Starship tools, shared `niri-plus-lab` NAT network, Arch domain/storage and short setup/operation notes. | Subnet/firewall integration checked; host connectivity restored/verified after any brief setup disruption; no guest/network autostart or exposed console. |
| 2. Recording pilot, end of next implementation pass | Basic Arch/Niri/Chrome/Kitty/Zsh with current appearance; one still, a 15-30 second recording and its receipt. | Usable local Starship viewer/input, intended renderer, readable exported recording and representative motion/colors. |
| 3. Demonstration assembly | Add the pieces needed for the parent plan's remaining scenes and record assembly steps. | Each demonstrated task actually works; public input versions and any additional fixes are recorded. |
| 4. Media and site | Overview/focused clips, posters, captions and provenance. | Sample data, truthful labels and reviewed playback; core media can ship before optional agent/remote prerequisites or the full guide. |
| 5. Installation rehearsal, later | Guide gap audit and corrected public instructions followed from a fresh `arch-base` clone. | Restore works; cold boot/SDDM login, core tasks, service teardown and repeat login pass without undocumented steps. |
| 6. Later distro trials | Add Ubuntu/Debian separately on the same network, recording exact releases, prerequisites and gaps. | Arch capture already delivered; each distro has its own task/install status and bounded disk/resource use. |
| 7. Retain for reuse | Accepted media/notes plus retained VM definitions, useful guest disks and clean checkpoints. | Guests stopped when idle; storage use recorded; deleting the lab is not a completion requirement. |

Phases 1-2 are the next implementation slice. After that pilot, media/guide work
and distro trials are independent follow-ons; Ubuntu/Debian exploration need not
wait for the complete Arch guide, and it cannot block the Arch media. The table
does not require completing every later branch before delivering a milestone.

Planning review, 2026-10-27: the shared-network lifecycle, local Starship access,
accepted brief setup disruption and per-distro resource/evidence boundaries
are now explicit. Runtime questions remain guest NAT/firewall compatibility,
local viewer key capture, rendering/encoding quality and later distro
dependencies.
The first pilot resolves the Arch networking/capture questions; it does not
claim those runtime checks have passed already.

Keep small recipes and reviewable definitions rather than building a generic
VM orchestrator or unattended distro installer. Stop the VM between work
sessions unless a bounded recording/test needs it running. Keep the tools and
images available for the next use, with no automatic expiry or deletion policy.

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

The active implementation slice is phases 1-2 only. Later distro trials,
complete installation acceptance and site publication remain separate work.
