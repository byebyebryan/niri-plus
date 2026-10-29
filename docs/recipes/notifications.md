# Notifications and an on-demand panel

`Mod+N` opens notification history and system information through SwayNC. The
desktop has no permanent bar. Volume and brightness feedback appear briefly
when their keys are used; those helpers are covered by the
[hardware-feedback recipe](hardware-feedback.md).

## Build the selected Arch package

The Arch reference uses the existing `swaync-bryan` fork because its dashboard
and notification activation behavior are part of the selected panel. Upstream
SwayNC remains a smaller alternative, but it does not provide these dashboard
widgets.

| Input | Pin |
| --- | --- |
| Arch recipe revision | `cd1038d1c824f256ecb5a448d78df9f71b64850a` |
| Recipe archive SHA-256 | `297852ede6f49cd9a2e75204d734807529e84b2dd0b01f6fc8789da4b53d9ff0` |
| SwayNC source revision | `4114c9cd56f086e166253880d0c96c6c5212e4aa` |
| Source archive SHA-256 | `8b69e2f47692a0dc53b00c5e9cf8c9df62c1295e5e7ee36acf16e40359f6bc83` |
| Runtime package | `swaync-bryan 0.12.6-15` |

Fetch and verify the immutable Arch recipe archive before extracting it:

```sh
SWAYNC_BUILD=$(mktemp -d)
curl --fail --location --output "$SWAYNC_BUILD/recipe.tar.gz" \
  https://codeload.github.com/byebyebryan/SwayNotificationCenter/tar.gz/cd1038d1c824f256ecb5a448d78df9f71b64850a
printf '%s  %s\n' \
  297852ede6f49cd9a2e75204d734807529e84b2dd0b01f6fc8789da4b53d9ff0 \
  "$SWAYNC_BUILD/recipe.tar.gz" | sha256sum --check
mkdir "$SWAYNC_BUILD/source"
tar -xzf "$SWAYNC_BUILD/recipe.tar.gz" --strip-components=1 -C "$SWAYNC_BUILD/source"
cd "$SWAYNC_BUILD/source/packaging/arch"
less PKGBUILD
```

The recipe pins the SwayNC source archive and its checksum. Preinstall the
runtime libraries before allowing `makepkg` to remove temporary build
dependencies:

```sh
sudo pacman -S --needed \
  base-devel gtk4 gtk4-layer-shell libadwaita glib2 libgee \
  json-glib libpulse granite7 libnotify
makepkg --verifysource
makepkg --syncdeps --rmdeps
```

Build as your ordinary user. Inspect the resulting runtime package with
`pacman -Qip`, then install that exact package with `sudo pacman -U`. Review the
transaction: the fork replaces upstream `swaync`.

## Install the reference config and rendered stylesheet

The small [`reference.json`](../../examples/notifications/reference.json) is an
authored Arch walkthrough candidate, recorded separately from the 0.3.1
component bundle and the pinned public example snapshot. Its SHA-256 is
`da55b379747d5ac0208730354ebfd8901dc268ac8e5b5b717e81ee9243d15577`. Verify it
from the candidate checkout; do not fetch it from the older pinned source
commit. Keep using the `NIRI_PLUS_CHECKOUT` path exported by the main guide,
since the build above changes the current directory. If running this recipe in
a separate shell, export that variable from the candidate checkout before
building. The config selects the dashboard and the same 1/2/5-second widget
refresh intervals as the existing panel design.

With the verified stager output from the
[Arch walkthrough](../setup-agent.md#2-stage-the-reviewed-inputs), set `STAGE` to that
directory and install only after backing up any existing SwayNC files:

```sh
printf '%s  %s\n' \
  da55b379747d5ac0208730354ebfd8901dc268ac8e5b5b717e81ee9243d15577 \
  "$NIRI_PLUS_CHECKOUT/examples/notifications/reference.json" | sha256sum --check
install -Dm644 "$NIRI_PLUS_CHECKOUT/examples/notifications/reference.json" \
  "$HOME/.config/swaync/config.json"
install -Dm644 "$STAGE/appearance/swaync.css" \
  "$HOME/.config/swaync/style.css"
```

The stylesheet is rendered from the separately pinned Neutral Slate identity.
It imports the fork's packaged base stylesheet. The config requires the fork;
the older `examples/notifications/config.json` remains a historical portable
specimen, not the selected Arch dashboard config.

## Start one session owner

The package supplies `swaync.service`. Inspect it, confirm the selected Niri
session targets are active, then add exactly one Niri dependency and start the
unit in the current session:

```sh
systemctl --user cat swaync.service
systemctl --user is-active niri.service graphical-session.target
systemctl --user add-wants niri.service swaync.service
systemctl --user daemon-reload
systemctl --user start swaync.service
```

Add this binding to the existing Niri `binds` block and validate the complete
configuration:

```kdl
Mod+N repeat=false { spawn "swaync-client" "-t" "-sw"; }
```

Do not also start a separate `spawn-at-startup` SwayNC process. To undo the new
session dependency, stop the unit and remove only the exact
`~/.config/systemd/user/niri.service.wants/swaync.service` link you created.

## Verify the panel

Open and close the panel with `Mod+N`. Send a disposable notification with
`notify-send`; test application focus separately with an action-bearing
notification from a real application. Check the System, Network, Bluetooth,
and Battery cards against available devices. Missing hardware should remain
hidden rather than be represented with fixture values.

CPU and RAM refresh every second, active GPU information every two seconds, and
battery information every five seconds while open. Network and Bluetooth use
D-Bus snapshots and signals. Closing the panel cancels reads, timers, and
subscriptions. NetworkManager and BlueZ keep their native service ownership;
GPU metrics require supported NVIDIA hardware and `nvidia-utils`.

When replacing a running upstream SwayNC process, restart only its service
after reviewing the new package/config. A restart clears in-memory notification
history. Keep the previous daemon's configuration and startup path until the
fork works through logout and login.
