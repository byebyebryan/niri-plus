# Notifications and an on-demand panel

`Mod+N` opens notification history and system information through SwayNC. The
desktop has no permanent bar. Volume and brightness feedback appear briefly
when their keys are used.

The [hardware-feedback recipe](hardware-feedback.md) includes those helpers,
their Niri bindings, dependencies and internal/external brightness distinction.

## Start with upstream SwayNC

On Arch, install `swaync` and `libnotify` (for the `notify-send` check), and follow its
[configuration guide](https://github.com/ErikReider/SwayNotificationCenter#configuring).
Use a single notification daemon in the session. Keep the old daemon's
configuration until the new one is working.

Add this to Niri's `binds` block:

```kdl
Mod+N repeat=false { spawn "swaync-client" "-t" "-sw"; }
```

If your package supplies `swaync.service`, inspect it before enabling or adding
session dependencies:

```sh
systemctl --user cat swaync.service
systemctl --user status swaync.service
```

Follow [Niri's systemd setup](https://niri-wm.github.io/niri/Example-systemd-Setup.html)
to scope it to the session. Do not start both a service and a separate
`spawn-at-startup` instance.

The packaged service is already part of `graphical-session.target`. After
stopping your previous notifier through its existing startup mechanism, add
SwayNC to Niri's startup and start it in your running Niri session:

```sh
systemctl --user add-wants niri.service swaync.service
systemctl --user start swaync.service
```

This adds a user-unit dependency for future sessions. To undo that addition,
stop SwayNC and remove only the `niri.service.wants/swaync.service` link created
under your user-unit directory, then restore your previous notifier's startup.

## What the fork adds

My [SwayNC fork](https://github.com/byebyebryan/SwayNotificationCenter) adds the
Niri notification activation work and a native dashboard. Its cards cover
system resources, the primary network connection, connected Bluetooth devices,
and battery state. Missing hardware hides; battery estimates respect reported
charge limits.

CPU and RAM refresh every second, active GPU information every two seconds, and
battery information every five seconds while open. Network and Bluetooth use
D-Bus snapshots and signals. Closing the panel cancels reads, timers, and
subscriptions. These features need the fork's implementation.

Network and Bluetooth cards use existing NetworkManager and BlueZ services.
GPU queries support NVIDIA hardware with `nvidia-utils`; other GPU vendors do
not get this metrics row. Install optional integrations only where they apply.

The managed setup builds the exact source and recipe recorded in the
[working setup](../reference.md#working-setup) as `swaync-bryan`. The packaging
replaces upstream SwayNC in one package transaction. It is not an AUR package
selected by a general update command.

Read the fork's source and packaging instructions before adopting it. Its
configuration and CSS are selected together in the managed source; a theme
alone does not add the dashboard widgets.

The pinned Arch recipe can be inspected before building:

```sh
mkdir -p swaync-build
cd swaync-build
curl --fail --location --output PKGBUILD \
  https://raw.githubusercontent.com/byebyebryan/SwayNotificationCenter/cd1038d1c824f256ecb5a448d78df9f71b64850a/packaging/arch/PKGBUILD
less PKGBUILD
```

That recipe pins its source archive and checksum. Read it before executing it.
Preinstall its runtime dependencies so temporary build dependencies can be
removed safely:

```sh
sudo pacman -S --needed base-devel gtk4 gtk4-layer-shell libadwaita glib2 libgee json-glib libpulse granite7
makepkg --syncdeps --rmdeps
```

Build as your ordinary user. Inspect the runtime package with `pacman -Qip`,
then install that exact `swaync-bryan-0.12.6-15` package with `sudo pacman -U`.
If a debug package is also produced, it is separate from the runtime package.
Review the replacement transaction; the fork conflicts with upstream `swaync`.

After installing the fork, the [dashboard configuration](../../examples/notifications/config.json)
and [charcoal/blue stylesheet](../../examples/notifications/style.css) remain
the earlier historical baseline. For the selected Neutral Slate candidate, use
the [appearance recipe](appearance.md); its SwayNC file is a frozen CSS render,
not a deployed stylesheet. Back up your existing SwayNC files before merging
under `~/.config/swaync`. The stylesheet imports the package's default styles.
The configuration requires this fork; upstream SwayNC does not have its dashboard.

Installing the replacement package does not replace an already running process.
After installing and merging configuration, restart only SwayNC, or load it on
your next Niri login:

```sh
systemctl --user restart swaync.service
```

A restart clears its in-memory notification history. Use this same scoped
restart when adopting the fork from a running upstream SwayNC instance.

## Verify the behavior

Open and close the panel with `Mod+N`. Send a sample notification using a tool
such as `notify-send` to check delivery. Test application focus separately with
an action-bearing notification from a real application, such as your terminal;
a plain `notify-send` message does not supply a focus action. Test network,
Bluetooth, and battery cards against the hardware your machine actually has.

On my desktop, notification configuration can reload independently of idle and
locking. Keep that separation when adding your own services. Restore your
previous notifier and session wiring if the replacement does not work as
expected.
