# Niri Plus Arch VM pilot and desktop task assembly

**Historical 0.3.1 tooling.** This directory retains the original pilot and
incremental assembler with their recorded input pins. Do not run them over the
current reference to refresh it. The current
[Arch agent guide](../../docs/setup-agent.md) owns the installation route;
the [resource/showcase receipt](../../docs/planning/resource-and-showcase-receipt.md)
records the later 0.4.1 working-guest observation and capture procedure.

This directory documents two stages on the retained Niri Plus reference VM:
the capture pilot setup and the incremental desktop task assembly applied on
top of it. The core desktop assembly is complete in an already installed
x86-64 Arch QEMU guest with a normal `demo` account, stopped between uses. It
does not describe a full Arch installation or clean-image replay. The guest
must be named `niri-plus-arch` and report QEMU in its DMI vendor field. Every
mutating entry point checks both values before it does work.

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

## Add the desktop task assembly

After the pilot is staged and a Niri session is active, run the separate,
guest-guarded desktop assembler from the copied tool directory:

```sh
bash /tmp/niri-plus-vm/desktop/assemble-desktop.sh
```

It verifies the exact pilot receipt and installed inputs before changing the
demo home. It installs the following Arch packages with `pacman -S --needed`
and stops if the guest has pending full-upgrade work:

```text
adw-gtk-theme ark base-devel bluez bluez-utils breeze breeze-cursors breeze-icons
cliphist dconf desktop-file-utils dolphin glib2 gsettings-desktop-schemas gtk3
gtk4 gtk4-layer-shell granite7 gwenview json-glib libadwaita libgee libnotify libpulse
mpv neovim networkmanager pavucontrol pipewire pipewire-pulse qt5-wayland qt5ct
qt6-wayland qt6ct shared-mime-info udisks2 wl-clipboard wireplumber
xdg-desktop-portal xdg-desktop-portal-gtk xdg-desktop-portal-wlr
```

`libnotify` is an explicit desktop runtime package because notification probes
use `notify-send`; the assembly does not rely on SwayNC's transitive dependency
to provide that command.

The core assembler installs Arch's repository WLR portal package. For this
VirGL VM's tested whole-monitor sharing route, the separate
[VM-only WLR compatibility step](desktop/wlr-compat/README.md) installs the
pinned `0.8.2-1.3` candidate after the core assembly. Re-running the core
assembler can restore the repository package, so apply the compatibility step
again afterward when needed. This is not a fleet or default-adoption change.

The pinned SwayNC fork is built as `demo` from recipe revision
`cd1038d1c824f256ecb5a448d78df9f71b64850a` and source revision
`4114c9cd56f086e166253880d0c96c6c5212e4aa`. Its runtime libraries are
installed before `makepkg --syncdeps --rmdeps`; the script verifies the
resulting `swaync-bryan 0.12.6-15` package before installation. NetworkManager
is installed only. It does not enable NetworkManager or transfer the existing
network connection; the dashboard needs a real NetworkManager
PrimaryConnection supplied by the guest owner.

The assembly adds the Dolphin `Mod+E`, panel `Mod+N` and clipboard `Mod+Y`
bindings. It installs the published Network, Bluetooth, Audio and Session
launchers; MIME defaults; explicit GTK/WLR portal providers; the generated
Neutral Slate GTK/Qt palette settings; and the selected Adwaita dark, Breeze
icons/cursor and Noto/Meslo fonts. Dolphin and other KDE applications use the
generated KDE color groups with the Breeze Qt style. The GTK settings portal
uses the dark preference. BlueZ uses its native `bluetooth.service`; PipeWire
and WirePlumber use their native user units. Only the SwayNC panel and
Cliphist collectors are attached to Niri's graphical session. Missing GPU,
battery or Bluetooth telemetry stays hidden; the fixture does not supply fake
hardware values.

The assembly receipt records exact package/input versions, managed file hashes,
the admitted pilot preimage and its backup, GSettings preimages, and service
links under `~/.local/share/niri-plus-vm/desktop/` and
`~/.local/state/niri-plus-vm/desktop-recovery/`.

Start the local fixture in a Kitty window and open its loopback page in Chrome:

```sh
python ~/.local/share/niri-plus-vm/desktop/sample_server.py
```

The page downloads a Markdown file, accepts that same file through the real
browser picker and reports the received SHA-256, and links a small SVG for
Gwenview. Its display-share button calls `getDisplayMedia` only after a click,
then reports the actual selected `displaySurface`, track state and stop event.
Choose the whole monitor in Chrome's system chooser and WLR monitor selection
to check that route. The
fixture binds only to `127.0.0.1` and stores no uploaded files.

## Core desktop task result

The assembly completed in the retained, previously installed Arch VM. The
pinned `swaync-bryan 0.12.6-15` package was built and installed. Chrome's
download, Dolphin's Markdown default opening the file in Neovim, Gwenview's SVG
open, and Chrome's GTK picker upload all passed; the upload SHA-256 matched the
fixture's expected bytes. Clipboard text and PNG capture/paste passed, along
with rofi-clipboard Delete, Cancel, and Clear confirmation flows.

The published utility entry points received smoke checks only. There was no
Bluetooth adapter, so no pairing, connection, or device-data result is
claimed. `libnotify` is listed directly so `notify-send` probes do not depend
on SwayNC's transitive package dependencies. The completed guest had
`libnotify` through SwayNC; this source inventory correction did not trigger a
guest reassembly.

A powered-off cold boot also passed: Niri was active with exactly one SwayNC
unit and two `wl-paste` collectors. The captured child PATH included
`~/.local/bin`, GTK/Qt theme selection was present, all 25 managed target
hashes matched, and native `Mod+D` opened the drun surface and launched
Dolphin. Host services, native host process IDs, DNS configuration and the
default route were unchanged. The guest is now off; a `desktop-demo` checkpoint
with disk, UEFI variables, XML and receipts passed `qemu-img check`, while the
protected `arch-base` and pilot `niri-plus` checkpoint checksums remained unchanged.

The browser's whole-monitor share first failed with the repository WLR portal
and unpatched upstream 0.8.2. The explicit local `0.8.2-1.3` compatibility
candidate then passed with a live 1920x1080 track, advancing frames, and clean
stop/node removal. It passed again with TRACE and resource guards removed; the
[WLR compatibility record](desktop/wlr-compat/README.md) has the measurements,
path details, source pin, patch hashes, and recovery order. This candidate is a
post-assembly VM step only; it does not change the assembler's repository
package selection or fleet defaults.

## Native guest evidence helper

`desktop-native.py` is a guest-only JSON command helper staged by the transfer
commands above at `/tmp/niri-plus-vm/desktop-native.py`. The bootstrap and desktop assembler do not automatically install it into
the pilot's persistent `tools/` directory. Run one JSON object per
invocation; it prints the result as JSON. For example, from the guest:

```sh
printf '%s\n' '{"action":"windows"}' | python3 /tmp/niri-plus-vm/desktop-native.py
```

Supported operations are:

| Action | Request fields | Result |
| --- | --- | --- |
| `windows` | none | Current Niri windows as JSON. |
| `wait-window` | `app_id` | Waits for exactly one matching native window. |
| `spawn` | `arguments` string array | Spawns a guest command through Niri. |
| `keys` | `arguments` string array; optional window `id` | Sends native key events with `wtype`, optionally focusing that guest window first. |
| `focus` / `close` | window `id` | Focuses or closes a currently listed guest window. |
| `start-recording` | validated `name` | Selects the guest's 1920x1080 output mode and starts `wf-recorder --no-damage` at 30 fps. |
| `screenshot` | same `name` | Saves a guest still beside the active recording. |
| `stop-recording` | same `name` | Stops the owned recorder, checks the video decodes, and completes its receipt. |

The recording and still are written under
`~/Videos/niri-plus-vm/desktop-<name>-<UTC>/`; operation receipts are under
`~/.local/state/niri-plus-desktop/recordings/`. The recorder uses a fresh
directory and a validated name for each scene. `--no-damage` requests
continuous frames even when the screen is visually still.

Every operation first runs the shared guest guard: the kernel hostname must be
exactly `niri-plus-arch`, the DMI vendor must contain `QEMU`, and the DMI
product name must be present. The helper then requires a non-root account with
home `/home/demo` and discovers exactly one Niri socket owned by that user.
Running it on the workstation fails before it reads the JSON request or probes
Niri. The `keys` operation invokes `wtype` inside the guarded guest, so those
native keyboard events go to the VM's Niri session, not the workstation.

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

The desktop task assembly and the original capture pilot are separate results
on the retained, already installed guest. Review the exported pilot video
locally for readable text, focus movement, browser scrolling, colored terminal
output, smoothness, and artifacts. Keep setup, assembly, and capture receipts
with their corresponding evidence.

This does not establish a full Arch replay or clean-base installation. SDDM,
locking and idle behavior, power and lid policy, physical hardware, and full
audio behavior remain unaccepted. Utility launchers only received smoke checks;
the guest had no Bluetooth adapter. The tty autologin is only a capture
harness. The WLR compatibility package remains a VM-only opt-in after assembly,
with no fleet/default adoption. Label media as a staged Arch guest sample.
