# Common desktop utilities

These small application entries put Network, Bluetooth, Audio, and Session
actions in the regular Rofi application list. Use `Mod+D`, then search for the
entry by its displayed name. They are portable examples for a Niri session;
they do not add new keybindings or change power policy on their own.

## Requirements

| Entry | Required software and readiness |
| --- | --- |
| Network | `kitty`, NetworkManager, and its `nmtui` text interface. On Arch, `nmtui` is shipped by the [`networkmanager` package](https://archlinux.org/packages/extra/x86_64/networkmanager/files/). NetworkManager must own the connection devices. |
| Bluetooth | `kitty`, [`bluez`](https://archlinux.org/packages/extra/x86_64/bluez/), [`bluez-utils`](https://archlinux.org/packages/extra/x86_64/bluez-utils/) for `bluetoothctl`, a working system D-Bus, and the BlueZ `bluetooth.service`. A Bluetooth adapter must be present for radio and pairing operations. |
| Audio | [`pavucontrol`](https://archlinux.org/packages/extra/x86_64/pavucontrol/) and a running PulseAudio-compatible server, such as PipeWire's PulseAudio server or PulseAudio. |
| Session | Python 3.11 or later, `rofi`, `systemd` user services, `niri` for native logout, and an active Wayland socket. Install the [independent manual lock service](../../examples/session/desktop-lock.service) before using Lock. |

Removable-drive mounting through a file manager has a separate prerequisite:
install [UDisks2 (`udisks2` on Arch)](https://archlinux.org/packages/extra/x86_64/udisks2/), keep its service and polkit authorization
available, and install the filesystem support for the media you use. UDisks2
is not invoked by these four entries.

## Portable files

- [Network entry](../../examples/desktop/niri-plus-network.desktop) runs `kitty -e nmtui`.
- [Bluetooth entry](../../examples/desktop/niri-plus-bluetooth.desktop) runs `kitty -e bluetoothctl`.
- [Audio entry](../../examples/desktop/niri-plus-audio.desktop) opens `pavucontrol`.
- [Session entry](../../examples/desktop/niri-plus-session.desktop) opens the small [Session helper](../../examples/desktop/desktop-session-menu).
- [Wayland readiness check](../../examples/desktop/desktop-session-ready) tests whether the current `WAYLAND_DISPLAY` socket accepts a local connection.
- [Power-policy example](../../examples/desktop/power.toml.example) makes lock-before-suspend an explicit Boolean.

The readiness check confirms a responding Wayland socket, not which compositor
owns it. Launch Session from Niri; `niri msg action quit` is the compositor's
own exit request and will fail safely if Niri is not reachable. Ensure
`~/.local/bin` is in the graphical session's `PATH` so Rofi can find
`desktop-session-menu` and its adjacent `desktop-session-ready` helper.

## Install and choose policy

From a Niri Plus checkout, install the helpers, then the desktop entries. These
commands write only the listed user files; inspect their contents first if you
already manage these names:

```sh
install -Dm755 examples/desktop/desktop-session-ready "$HOME/.local/bin/desktop-session-ready"
install -Dm755 examples/desktop/desktop-session-menu "$HOME/.local/bin/desktop-session-menu"
install -Dm644 examples/desktop/niri-plus-network.desktop "$HOME/.local/share/applications/niri-plus-network.desktop"
install -Dm644 examples/desktop/niri-plus-bluetooth.desktop "$HOME/.local/share/applications/niri-plus-bluetooth.desktop"
install -Dm644 examples/desktop/niri-plus-audio.desktop "$HOME/.local/share/applications/niri-plus-audio.desktop"
install -Dm644 examples/desktop/niri-plus-session.desktop "$HOME/.local/share/applications/niri-plus-session.desktop"
```

Choose your own power setting before copying the sample to
`${XDG_CONFIG_HOME:-$HOME/.config}/desktop-session/power.toml`. The sample
contains `lock_before_suspend = false`, matching the value in the managed
source record captured for its three current hosts. Keep or change it only to
match your chosen policy. The Session helper refuses to suspend when the file
is missing, malformed, or lacks a Boolean value; it never guesses.

The sample configuration is:

```toml
lock_before_suspend = false
```

## Session behavior

| Choice | Dispatch |
| --- | --- |
| Lock | Starts the independent `desktop-lock.service`, so policy reloads do not stop a manual lock. |
| Log out | Runs `niri msg action quit` and preserves Niri's native confirmation. |
| Suspend | If configured, starts the lock service first; then requests `systemctl suspend`. A failed lock request prevents suspend. |
| Restart | Shows a second Rofi picker with Cancel selected by default; Restart dispatches `systemctl reboot`. |
| Shut down | Shows the same confirmation pattern; Shut down dispatches `systemctl poweroff`. |
| Cancel / Escape | Returns without dispatching an action. |

The helper does not use `--skip-confirmation`, directly start a locker, restart
Niri, or change the existing idle/lid policy. The `desktop-lock.service` keeps
manual locking independent from idle behavior. On battery and desktop systems,
configure suspend, lock-before-suspend, and lid behavior together in the
separately owned session policy.

## Pairing with Bluetooth

The Bluetooth entry opens `bluetoothctl` in Kitty. For a pairing session, make
sure `bluetooth.service` is available and start with the controller and agent
setup. Arch's [Bluetooth guide](https://wiki.archlinux.org/title/Bluetooth)
lists the daemon and utility packages and service readiness:

```text
bluetoothctl
power on
agent on
default-agent
scan on
```

When the desired device appears, use its address with `pair`, then `trust` and
`connect` if appropriate. Stop scanning with `scan off` when finished. Device
prompts and available pairing methods vary; accept only the pairing request for
the device you intend to connect.

## Backlight and external displays

Laptop brightness keys and their replaceable notification feedback control the
laptop panel's backlight device. External monitors do not necessarily expose
that device. Monitor brightness through DDC/CI or physical monitor buttons is a
separate capability and is not controlled by these application entries.

The helper's cancellation and dispatch path has isolated checks in
[`scripts/check-terminal.py`](../../scripts/check-terminal.py). The checks use
stubs and do not toggle radios, change audio routing, suspend, restart, power
off, or lock a live desktop.
