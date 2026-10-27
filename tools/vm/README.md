# Niri Plus Arch capture pilot

This directory contains a small guest-only setup and one browser/terminal scene
for the retained Niri Plus reference VM. It uses a normal `demo` account in an
x86-64 Arch guest, stopped between uses. The guest must be named `niri-plus-arch` and report QEMU in
its DMI vendor field. Every mutating entry point checks both values before it
does work.

The setup downloads public inputs directly. It does not copy a host home,
chezmoi source, browser profile, SSH key, or local repository checkout into the
guest.

## Inputs

[`pins.json`](pins.json) records the independent input tuple:

- Niri Plus component archive 0.3.1, with archive and manifest SHA-256 values.
- Schema-2 identity SHA-256 `6dbb1631…e8e2455`, verified independently from
  the component archive.
- Clean public Niri Plus source commit
  `b62df460884b5a4d5e8c7eeb05c132a0b26814ae` for the portable Niri starter and
  Niri portal preferences.
- Google Chrome's public AUR recipe commit
  `f0071e0692f4545bcb3e0881ea60c031a9f99343`, which pins Chrome
  `156.0.8078.47` and checksums Google's official package.
- The public shell fetcher downloads its four plugin trees from immutable
  commits and verifies each archive digest before extraction.

The bootstrap renders the Niri, Rofi, and Kitty appearance from the pinned
component renderer and separate identity. It checks that the chosen profile is
Neutral Slate and the terminal background remains pure black. It adapts the
public Niri starter to half-width columns and removes its Dolphin binding,
which is outside this pilot. Rofi remains the application-launch path.

## Set up the guest

Prerequisites are an already installed Arch cloud image, `demo` with sudo
access, working guest networking/DNS, and an SSH route from the workstation.
The bootstrap performs a full guest `pacman -Syu`, installs the packages in
[`bootstrap-guest.sh`](bootstrap-guest.sh), builds the pinned Chrome recipe,
stages the public files, then starts the lab session harness.

From the workstation, transfer this directory and run the bootstrap as `demo`:

```sh
ssh -i <guest-only-key> \
  -o UserKnownHostsFile=<lab-known-hosts> \
  -o StrictHostKeyChecking=yes \
  demo@<guest-ip> mkdir -p /tmp/niri-plus-vm

scp -i <guest-only-key> \
  -o UserKnownHostsFile=<lab-known-hosts> \
  -o StrictHostKeyChecking=yes \
  -r tools/vm/. demo@<guest-ip>:/tmp/niri-plus-vm/

ssh -i <guest-only-key> \
  -o UserKnownHostsFile=<lab-known-hosts> \
  -o StrictHostKeyChecking=yes \
  demo@<guest-ip> bash /tmp/niri-plus-vm/bootstrap-guest.sh
```

`--packages-only` stops after the Arch package transaction. The normal command
then verifies the public inputs, installs the public shell dependencies,
creates the user configs and receipt under
`~/.local/share/niri-plus-vm/`, and enables the guest's tty1 session harness.
It refuses to replace a different existing pilot tree or user config.

The guest harness adds an exact `getty@tty1` autologin drop-in for `demo` and a
`.bash_profile` that starts `niri-session -l` only on tty1. This makes the local
guest viewer usable without a display manager. It is a lab convenience, not
login-manager, password, or clean-install acceptance. The exact guarded
recovery command is:

```sh
bash ~/.local/share/niri-plus-vm/tools/disable-demo-session.sh
```

That script removes only its unchanged tty1 drop-in, restores the exact saved
Arch skeleton `.bash_profile` (or its original absence), then returns tty1 to
the normal getty login prompt. It rejects use outside the verified guest and
refuses unrelated modified files. Partial recovery can resume while the profile
still matches either the managed wrapper or its recorded original.

The setup receipt records package versions, the independently verified input
tuple, plugin receipt, installed font matches, and generated file hashes.
Pacman's default `jack2` provider may be installed as an `ffmpeg` dependency;
the pilot does not configure audio. Portal packages are explicitly GTK and
WLR, and the public `niri-portals.conf` selects GTK file/access/settings with
WLR monitor sharing.

## Capture the pilot

After the tty1 harness has started Niri, connect the local guest viewer and
confirm the desktop is idle. The capture script requires an empty Niri window
list so the recording cannot pick up unrelated guest content. Run it over SSH:

```sh
ssh -i <guest-only-key> \
  -o UserKnownHostsFile=<lab-known-hosts> \
  -o StrictHostKeyChecking=yes \
  demo@<guest-ip> python3 ~/.local/share/niri-plus-vm/tools/capture_scene.py
```

The script discovers exactly one Niri IPC socket owned by `demo`, selects the
advertised 1920x1080@60 mode on `Virtual-1`, and warms Zsh in an unrecorded owned
Kitty window. It then starts a fresh dark Chrome profile and the scene terminal
and records a roughly 25-second scene.
Niri IPC changes focus between the two columns; `wtype` types the local project
command and sends browser Page Down/Page Up keys, returning to the page heading
for the final still. Chrome opens only the local
sample page and has sync, extensions, and first-run prompts disabled. Kitty
runs Zsh with the public shell core and the Meslo font. No agent tools or
personal browser accounts are involved.

Each run writes one H.264/MP4, one PNG still, `capture-receipt.json`, an
`ffprobe` report, recorder log, renderer evidence from `glxinfo`, and the Niri
session log under `~/Videos/niri-plus-vm/pilot-<UTC timestamp>/`. The receipt
reports measured dimensions, frame rate, duration, fonts, renderer evidence,
input pins, and file hashes. The capture is silent and asks `wf-recorder` for
30 fps. Read the measured values rather than treating the requested frame rate
as a benchmark result. The receipt records its selected mode and actual media
dimensions.

The H.264 encoder uses `color_range=tv`. On this stack, the default marked
limited-range samples as full range and lifted decoded black to RGB 16. The
capture compares a blank terminal pixel in the PNG and decoded final video
frame, requiring RGB 0 in both. The receipt records this check; it does not
claim a complete color-calibration measurement.

Copy accepted evidence from the workstation as a separate step, using the
exact path printed by the guest script. Keep the export outside the repository
so capture artifacts stay out of Git:

```sh
mkdir -p "$HOME/Videos/niri-plus-vm"
scp -i <guest-only-key> \
  -o IdentitiesOnly=yes \
  -o UserKnownHostsFile=<lab-known-hosts> \
  -o StrictHostKeyChecking=yes \
  -r demo@<guest-ip>:/home/demo/Videos/niri-plus-vm/pilot-<UTC timestamp> \
  "$HOME/Videos/niri-plus-vm/"
```

The isolated Chrome profile lives at
`~/.cache/niri-plus-vm/chrome-profile` and is not part of the export. To record
again, close Chrome and Kitty, remove only that guest-only sample profile, then
start from an empty Niri window list. Each capture uses a new output directory.

## Acceptance boundary

This pilot demonstrates the current selected colors and fonts in an actual
Niri/Chrome/Kitty guest session and produces measurable media. Review the
exported video locally for readable text, focus movement, browser scrolling,
colored terminal output, smoothness, and artifacts before using it. Keep the
setup and capture receipts with the original recording and still.

It does not establish SDDM, locking, power, audio, notification, clipboard,
physical hardware, or a clean-base installation guide. The guest tty autologin
is only a capture harness. Media should be labelled as a staged Arch guest
sample until the relevant public-adoption and review steps accept it.
