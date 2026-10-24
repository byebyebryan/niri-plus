# Locking and session services

The desktop uses small user services for manual locking, idle behavior,
authorization, and battery monitoring. Each job has an owner and an independent
configuration lifetime.

## Manual locking

My setup selects Gtklock. A dedicated `desktop-lock.service` owns the active
locker, so reloading idle policy does not stop it and repeated lock requests
reuse the same service.

On Arch, install `gtklock` and `python` (needed by the readiness helper):

```sh
sudo pacman -S --needed gtklock python
```

Review the
[example service](../../examples/session/desktop-lock.service), and check your
distribution's Gtklock PAM setup before relying on it. Do not replace your
existing working lock path until you have checked authentication and all
connected displays.

After reviewing both files, install the helper and unit from the clone:

```sh
mkdir -p ~/.local/bin ~/.config/systemd/user
install -m 755 examples/session/desktop-session-ready ~/.local/bin/desktop-session-ready
cp examples/session/desktop-lock.service ~/.config/systemd/user/
systemd-analyze --user verify ~/.config/systemd/user/desktop-lock.service
systemctl --user daemon-reload
```

The helper checks the captured Wayland socket before starting the locker. Add
this Niri binding once the service is configured. Replace an existing
`Ctrl+Alt+Delete` binding if present; Niri's default configuration uses that key
to quit the session:

```kdl
Ctrl+Alt+Delete { spawn "systemctl" "--user" "start" "desktop-lock.service"; }
```

The example is a manual lock path. Handling `loginctl lock-session` requires an
idle listener such as swayidle, in addition to the lock service.

## Idle policy is a choice

My current machines power off displays after ten minutes. Battery suspend is
after thirty minutes, with no automatic suspend on external power. Automatic
locking and lock-before-suspend are disabled in my personal policy.

Choose your own locking and suspend rules before adapting these values. Consult
[swayidle](https://github.com/swaywm/swayidle) and
[Niri's systemd guide](https://niri-wm.github.io/niri/Example-systemd-Setup.html)
for the session integration. My power helper also observes UPower and preserves
per-machine policy in private managed configuration. The public example covers
manual locking; configure idle and battery policy separately using the choices
above and the maintained swayidle documentation.

## Authorization and the graphical session

An authorization agent is still needed for applications that request elevated
permissions. My setup uses polkit-kde-agent, started after the Wayland socket is
ready. It belongs to the Niri session and stops with the graphical session.

Follow [Niri's important software guide](https://niri-wm.github.io/niri/Important-Software.html)
for the package and startup requirements. Using a KDE component such as Dolphin
or an authorization agent is compatible with choosing Niri as the desktop.

## Inspect before changing

Useful read-only checks include:

```sh
systemctl --user status graphical-session.target niri.service
systemctl --user cat desktop-lock.service
systemctl --user status desktop-lock.service
loginctl show-session self -p Type -p State
```

Check manual locking and unlock on your own machine, then test the idle behavior
you selected. Restore the previous units and configuration to roll back; keep a
working way to unlock and recover while making changes.
