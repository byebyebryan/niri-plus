# Volume and brightness feedback

Hardware keys provide small, replaceable notifications through the existing
notification daemon. The helpers keep microphone and speaker feedback distinct;
the popups are transient and do not enter SwayNC history.

## Install the helpers

The [volume helper](../../examples/feedback/notify-volume) uses WirePlumber's
`wpctl` and `notify-send` from `libnotify`. The
[brightness helper](../../examples/feedback/notify-brightness) uses
`brightnessctl` and the same notifier. In the main walkthrough, `SOURCE` names
the verified example tree. On Arch:

```sh
sudo pacman -S --needed wireplumber libnotify brightnessctl
install -Dm755 "$SOURCE/examples/feedback/notify-volume" "$HOME/.local/bin/notify-volume"
install -Dm755 "$SOURCE/examples/feedback/notify-brightness" "$HOME/.local/bin/notify-brightness"
```

Inspect any existing files with these names before installing. A running audio
server and WirePlumber supply the default sink/source; the notification daemon
must already be selected. `~/.local/bin` must be available in Niri's `PATH`.

## Bind and inspect

Inspect the six entries in the [Niri binding fragment](../../examples/feedback/binds.kdl)
from the verified `SOURCE` tree, then merge them into the existing `binds`
block, replacing existing bindings for those keys. The fragment is:

```kdl
XF86AudioLowerVolume allow-when-locked=true { spawn "notify-volume" "down"; }
XF86AudioRaiseVolume allow-when-locked=true { spawn "notify-volume" "up"; }
XF86AudioMute allow-when-locked=true { spawn "notify-volume" "mute"; }
XF86AudioMicMute allow-when-locked=true { spawn "notify-volume" "mic-mute"; }
XF86MonBrightnessDown allow-when-locked=true { spawn "notify-brightness" "down"; }
XF86MonBrightnessUp allow-when-locked=true { spawn "notify-brightness" "up"; }
```

Keep one `binds` block and preserve the existing layout and unrelated keys.
Validate the complete configuration with `niri validate`. These bindings retain
the personal behavior of allowing hardware controls while locked.

Volume changes use five-percentage-point steps, with increases capped at 100%.
Mute targets the default output; microphone mute targets the default input.
The helper reads the resulting level and replaces only that control's prior
popup. You can inspect the default audio nodes without changing them:

```sh
wpctl status
wpctl get-volume @DEFAULT_AUDIO_SINK@
wpctl get-volume @DEFAULT_AUDIO_SOURCE@
```

The helpers' `show` and `mic-show` modes display a popup without changing volume.
Use them in your own session when ready to check appearance. Then make a small
volume change and restore it. [Audio](desktop-utilities.md) opens pavucontrol
for device and per-application routing; the feedback helper retains the selected
default device.

## Internal and external brightness

The brightness helper addresses the Linux backlight class, not keyboard LEDs.
It changes brightness in five-percentage-point steps and keeps the decrease
above zero. A machine without a backlight device gets a no-op. Check device
access with `brightnessctl --list` before relying on the keys.

External-monitor DDC/CI is a separate, hardware-dependent path. Physical monitor
controls are the baseline; installing this helper does not establish DDC support.
Test a small backlight adjustment and restore it on each applicable laptop.

Restore your previous binding entries and helper files to undo this addition.
The isolated [desktop example check](../../scripts/check-desktop.py) uses command
stubs for audio and notification calls; it does not change live audio, send a
desktop popup or adjust a display.
