# Arch capture pilot execution receipt

Started 2026-10-27. Scope: phases 1-2 of the
[capture-first VM plan](vm-reference-environment.md). Status: desktop assembly
and capture qualification in progress. This is native software in an owned VM,
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

Host preimages, package logs, image/signature verification, guest-only keys and
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

Viewer attachment is established; compositor rendering, readable captures,
scene interaction and exported playback are the remaining pilot gates.

## Acceptance still to complete

- Install the public desktop profile and verify its actual guest renderer,
  current palette/fonts and normal application processes.
- Produce and inspect one screenshot and a 15-30 second guest-side clip.
- Check keyboard/scene behavior, viewer independence, frame/encoding evidence
  and local playback; record limits without implying physical-host acceptance.
- Retain the guest and artifacts with a usable start/stop record; stop the
  working VM after testing.
- Complete the repository build/browser checks and review only scoped source
  changes. No remote push or site publication is part of this milestone.
