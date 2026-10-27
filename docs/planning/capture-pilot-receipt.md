# Arch capture pilot execution receipt

Completed 2026-10-27. Scope: phases 1-2 of the
[capture-first VM plan](vm-reference-environment.md). The screenshot and native
recording are delivered in the
[browser review](http://starship:8787/reports/a960ddf32de35369ab415a1d25c5a7812ba4152d67092687e46835613e85ea89/).
This is native software in an owned VM,
not a recording or acceptance claim for the daily desktop.

## Inputs and retained environment

- Host: Starship, local KVM/QEMU 11.1.2, libvirt 12.8.0, virt-install 5.1.0,
  virt-viewer 11.0, OVMF 202608. Host tooling stays outside chezmoi.
- Guest: `niri-plus-arch`, four vCPUs, 8 GiB RAM, 64 GiB sparse disk, Q35/UEFI,
  VirtIO graphics with 3D on the AMD render node, ordinary `demo` account.
- Base image: official `Arch-Linux-x86_64-cloudimg-20261015.611680.qcow2` from
  the Arch mirror. SHA-256 matched the published checksum. Detached signature
  verified against the CI public key published by the official arch-boxes
  repository: signing subkey `656E4C5AC1CC3B86E539D97E343635A6859A9174`,
  primary key `1B9A16984A4E8CB448712D2AE0B78BF4326C6F8F`. Verification used
  an isolated keyring; the host pacman trust database was not changed.
- Installed-base preparation: NoCloud seed creates the guest account and
  guest-only SSH access, then completes a full guest upgrade. This is lab
  baseline preparation, not an unattended Niri Plus installer.
- Public desktop inputs: components 0.3.1 with archive and manifest hashes
  from the committed component record; identity SHA-256
  `6dbb163103e911262b5c1a6b1dd8299863ea790f7a12e7fb264fe9603e8e2455`;
  other public examples from source
  `b62df460884b5a4d5e8c7eeb05c132a0b26814ae`.

The host package transaction added 89 packages, with no existing package
versions changed or packages removed. Normal package hooks also ran; the
transaction log is retained. Host preimages, package logs, image/signature verification, guest-only keys and
generated machine definitions are kept privately under
`~/.local/state/niri-plus-lab/`. Guest disks and checkpoints are under
`/var/lib/libvirt/images/niri-plus/`. These are retained for reuse, outside Git.

## Host networking and integration findings

The shared network `niri-plus-lab` uses `virbr-np`, subnet
`192.168.124.0/24`, and reservation `192.168.124.10` for the Arch guest.
No physical NIC is attached to the virtual bridge. Guest/network autostart
remain disabled; their definitions are persistent.

Two integration adjustments were needed:

1. The newly installed libvirt firewalld zone was not in firewalld's running
   configuration. A normal `firewall-cmd --reload` loaded the packaged zone.
2. Libvirt's default nftables network backend accepted guest traffic in its own
   ruleset, but Docker's iptables `FORWARD DROP` path still dropped it. The
   supported `firewall_backend = "iptables"` setting in
   `/etc/libvirt/network.conf`, followed by restarting only `virtnetworkd`,
   rebuilt libvirt's scoped rules in the same forwarding ruleset as Docker.
   No custom forwarding hooks, broad accept policy, disabled firewall or Docker
   restart was needed.

NetworkManager, firewalld, Docker and Tailscale remained active with their
original service PIDs. Host DNS and guest DNS/outbound HTTPS work. Guest DHCP
and SSH work. The host's Wi-Fi profile, resolver and default route were retained.
Later Docker/firewall restarts and the host's next boot remain separate checks.

## Baseline and viewer evidence

Cloud-init completed, the root filesystem expanded to 64 GiB and the guest
agent/SSH services became active. A clean shutdown checkpoint saved the disk,
UEFI variables and domain XML at `checkpoints/arch-base`; `qemu-img check`
reported no errors. The working VM was restarted afterward. This saved
checkpoint has not yet undergone a complete clean-install replay.

Unused default audio, USB-redirection, SPICE-agent and seed-CD devices were
removed from the guest definition before that checkpoint. Host/guest clipboard
copy and file transfer are disabled. The owned local viewer attached through
the libvirt read-only socket with no new user/group/polkit authorization rules:

```sh
virt-viewer --connect 'qemu:///system?socket=/run/libvirt/virtqemud-sock-ro' \
  --attach --domain-name --auto-resize=never --zoom=70 \
  --spice-disable-audio --spice-disable-usbredir niri-plus-arch
```

Viewer attachment and reopening are established. Rendering/capture and guest
virtual-keyboard input passed below. Physical viewer keyboard grab/release and
the feel of manual use remain normal follow-up checks; no host input was
injected to make the clip.

## Native capture and review

The accepted run is `pilot-20261027T080851Z`, retained under the host's private
lab `artifacts/` directory and in the guest's `~/Videos/niri-plus-vm/` tree.

| Evidence | Result |
| --- | --- |
| Software | Niri 26.04, Chrome 156.0.8078.47, Kitty 0.49.2, Zsh 5.9.2; Noto Sans and MesloLGS Nerd Font Mono resolved to their installed fonts. |
| Renderer | Guest Mesa 26.2.5 reports VirGL backed by the AMD iGPU; the compositor uses the guest VirtIO render node. |
| Capture | 1920x1080 H.264/yuv420p, 24.467 seconds, 735 frames, measured average `11025/367` (about 30.04 fps), no audio. Full-file FFmpeg decode passed. |
| Scene | Native Chrome sample page and Kitty/Zsh; guest IPC arranges/focuses the real windows and guest virtual keyboard events type the sample command and scroll the page. |
| Black preservation | PNG and decoded final-video sample at `(1440, 810)` both equal RGB `(0, 0, 0)`; Chromium playback independently returned RGBA `(0, 0, 0, 255)`. This is a targeted check, not full color calibration. |
| Browser report | Native controls, no autoplay, working playback/seek, no browser errors or page overflow at 1440 and 390 px. All four delivered report files match the reviewed source bytes over HTTP. |
| Media provenance | MP4 SHA-256 `b6c3c63e3d60b0fe079d8d3a74f0f8a038813c16fa27453838c77cb1f43aa240`; capture script SHA-256 `4949e3dd503d71c2528ca01c668ae12013817f03b32e9d56a5bf394e223ac288` matches its at-capture setup receipt. |

Review fixes included explicit dark Chrome styling, a prompt warmup before
recording, deterministic window ordering and focus checks, and resetting the
page heading before the final still. The first 1280x800 clip and subsequent
review runs remain retained as earlier evidence.

The recorder originally marked limited-range samples as full range, lifting
decoded black to RGB 16. Its `color_range=tv` codec option corrects that mismatch;
the capture now rejects a lifted-black result. The final stream does not
advertise comprehensive color-space metadata, so there is no wider-gamut or
color-calibration claim.

## Guest integration and recovery checks

The guest bootstrap and fixtures live in [tools/vm](../../tools/vm/README.md).
The lab uses a guest-only tty1 autologin wrapper with `niri-session -l`; this
explicit flag avoids the launcher's login-shell recursion. It is not SDDM or
password-login acceptance. The shared Zsh core runs in Kitty separately from
the Bash login wrapper.

GTK/WLR portal providers were made explicit after Arch's virtual dependency
initially selected COSMIC. Only the superseded COSMIC portal package was
removed, without dependency autoremove. Jack2 remains an unconfigured transitive
dependency; audio is outside the pilot.

Measured checks passed:

- All four mutating entry points reject use on the Starship host before work.
- Rofi opened in the guest and exited through its native Escape cancel path.
- Recovery rejected an altered profile before changing its privileged drop-in.
- The original 57-byte Arch skeleton profile was restored exactly; the lab
  wrapper could then be re-enabled from the retained public inputs.
- Recovery resumed from a partially restored profile. Intentional guest getty
  retries reset only that unit's failed state and avoid duplicate restarts.
- A subsequent cold boot reached SSH and an active Niri session.
- The guest was then shut down cleanly. The retained `niri-plus` checkpoint
  includes disk, UEFI variables and domain definition; its disk check passed.
  It supplements `arch-base`, rather than replacing the clean baseline.

The required site build passed (20 pages, 99 files), along with all 625 owned
browser checks. New tooling also passed shell/Python syntax and real host-refusal
checks. Only scoped local source commits are made; no push, code release,
managed fleet apply or public-site deployment is part of this milestone.

## Use the retained guest

Start the shared network if inactive, then the guest. Both have automatic
startup disabled:

```sh
sudo virsh -c qemu:///system net-start niri-plus-lab
sudo virsh -c qemu:///system start niri-plus-arch
```

Use the local viewer command above. Host-to-guest SSH uses the private lab key
at `~/.local/state/niri-plus-lab/guest_ed25519` and that directory's dedicated
`known_hosts`; the guest is `demo@192.168.124.10`. The guest-only password is
retained in the private lab state, outside Git and the report.

For an ordinary stop:

```sh
sudo virsh -c qemu:///system shutdown niri-plus-arch
```

The working guest is currently stopped. Host tools, shared network definitions,
disk images, both checkpoints and original captures remain available. The lab
network remains active and has no automatic startup. Full workflow media,
installation replay, Ubuntu/Debian trials and physical hardware checks are
separate follow-ons.
