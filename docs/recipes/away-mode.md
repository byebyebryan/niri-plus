# Manual display-away mode

The optional `desktop-away` companion keeps Niri displays off during unattended
SSH/browser-agent work. It leaves the existing automatic idle, battery, locker
and suspend policies with their current owners. It starts in normal mode and
acts on display power only after an explicit `desktop-away away` command.

The helper and its graphical-session unit are included in components 0.5.0.
Installation is opt-in: stage and verify the published bundle before installing
`components/desktop/bin/desktop-away` as `~/.local/bin/desktop-away` and
`components/desktop/systemd/user/desktop-away.service` in the user unit directory.
Wire the service to Niri's lifecycle, reload the user manager, then start it.
No package installer or native-session restart is part of the helper.

For a manual monitor-off shortcut, use:

```kdl
Mod+Shift+P repeat=false { spawn "desktop-away" "away"; }
```

`desktop-away status` reports the latch, input backend and DRM power states.
`desktop-away resume` releases it remotely. Stopping the service while away
restores ordinary display power. A new graphical session starts in normal mode.

## Input without broader permissions

When physical evdev input is already readable, the helper observes keyboard,
mouse and touchpad events without a grab. It rejects virtual uinput devices,
stale buffered input, shortcut releases/repeats and audio/display jack events.

Otherwise it uses `libwayland-client` and `ext-idle-notify` version 2. Its
**input-only** notification ignores application inhibitors and does not expose
key codes, text or pointer positions. No input-group membership, ACL, udev rule
or privileged service is added. The notification uses a 250 ms idle threshold
and a 500 ms shortcut-release grace interval when entering away mode.

The Wayland backend follows compositor seat input. It cannot distinguish
OS-level injected input from physical input. Chrome's in-page CDP activity is
separate from that seat. Validate the actual automation path on a new desktop;
the helper reports which backend it selected rather than claiming equivalence.

## Display and capture limits

The latch observes DRM power every 250 ms and corrects application/hotplug
wakeups, with corrections limited to two per second. It can reblank a brief
flash after a wake; it cannot guarantee that the panel never lights momentarily.
Unknown output state gets an off request and is not accepted as proof of off.

On the initial Starship trial, Chrome navigation/clicks and fresh standard
screenshots worked with DRM Off. An explicitly cropped screenshot timed out;
use the ordinary screenshot path and qualify other capture modes separately.
The trial also confirmed physical mouse return. These observations do not
establish every host's panel, touchpad, suspend or browser-capture behavior.

Isolated tests are in `scripts/check-desktop-away.py` and normal unittest
discovery. The original local-trial receipt remains in
`docs/planning/desktop-away-local-trial.md`; release and host delivery are
separate evidence gates.
