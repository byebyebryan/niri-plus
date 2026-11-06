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
authored Arch reference profile, recorded separately from the published
component bundle and the pinned public example snapshot. Its SHA-256 is
`da55b379747d5ac0208730354ebfd8901dc268ac8e5b5b717e81ee9243d15577`. Verify it
from the reviewed checkout; do not fetch it from the older pinned source
commit. Keep using the `NIRI_PLUS_CHECKOUT` path exported by the main guide,
since the build above changes the current directory. If running this recipe in
a separate shell, export that variable from the reviewed checkout before
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

When the optional `shared.swaync_sidebar` identity block is present, the
rendered style gives the sidebar, information surface, and notification cards
75% charcoal backgrounds. Its `opacity`, `border_color`, and
`card_border_color` values set the surface alpha and outlines. The sidebar has
one left border; internal information dividers retain their separator color.
Notification text and controls remain opaque and focus and critical outlines
remain active. Omitting the block keeps the legacy stylesheet output.

The style is available in the [0.4.3 maintenance backport](https://github.com/byebyebryan/niri-plus/releases/tag/components-v0.4.3).
It changes only the two appearance implementation files from 0.4.2, retaining
all 42 other runtime payloads. The dated Arch reference and optional desktop
feature releases retain their own selections and acceptance records.

For a matching edge-attached layout with individual notification cards, merge
these optional values into a SwayNC config:

```json
{
  "fit-to-screen": true,
  "notification-grouping": false,
  "control-center-width": 448,
  "control-center-margin-top": 0,
  "control-center-margin-bottom": 0,
  "control-center-margin-left": 0,
  "control-center-margin-right": 0
}
```

## Unified information panel

The qualified Arch reference above retains its recorded dashboard profile.
The newer [fork package revision 16](https://github.com/byebyebryan/SwayNotificationCenter/releases/tag/swaync-bryan-0.12.6-16)
adds an opt-in divided information surface. Use it with
[components 0.4.2](https://github.com/byebyebryan/niri-plus/releases/tag/components-v0.4.2)
or the development bundle 0.9.3 for the matching stylesheet and feedback icons.
Keep the existing configuration and change these entries after installing the
new fork:

```json
{
  "widgets": ["information", "title", "notifications"],
  "widget-config": {
    "clock": {"time-format": "%H:%M", "date-format": "%a, %b %-d"},
    "title": {"show-dnd": true},
    "system-stats": {"interval": 1},
    "gpu": {"interval": 2},
    "battery": {"interval": 5}
  }
}
```

This is a fragment to merge into the existing config. Keep any separately
selected controls, including a volume widget. The opening row has bold local
time and a plain date in equal columns, without captions. System uses read-only
CPU/RAM and active GPU/VRAM meters. Connections keeps Ethernet on the left and
its full IP on the right; long IPv6 values ellipsize with a complete tooltip.
Bluetooth uses device metadata for icons and distinguishes `0%` from an
unreported battery. Battery uses a 0–100 gauge and marks only an actual reported
charge limit. Missing sections disappear with their dividers, while their
readers continue to observe changes whenever the panel is open.

[Fork package revision 17](https://github.com/byebyebryan/SwayNotificationCenter/releases/tag/swaync-bryan-0.12.6-17)
keeps this configuration and refines networking into two equal columns. The
left has the active SSID or Ethernet identity above a Signal/IP label and
right-aligned value. Signal uses the same percentage formatting as CPU/RAM.
The right has labelled upload and download rates from that primary interface,
sampled once per second while the panel is open. Reopening or changing interfaces
starts a fresh baseline; unavailable values stay distinct from measured zero.
The existing components 0.4.2 appearance selection still applies unchanged.
The [fork maintenance guide](https://github.com/byebyebryan/SwayNotificationCenter/blob/niri-plus/docs/fork-maintenance.md)
records its upstream baseline, downstream contracts and native regression checks.

Legacy dashboard and standalone widgets remain available. The new native widget
and private-bus checks are separate from the dated Arch VM reference replay and
from physical hardware acceptance. The [fork widget documentation](https://github.com/byebyebryan/SwayNotificationCenter/blob/niri-plus/docs/system-widgets.md)
covers formats, suffixes, lifecycle and stylesheet hooks.

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
