# Notifications and an on-demand panel

`Mod+N` opens notification history and system information through SwayNC. The
desktop has no permanent bar. Volume and brightness feedback appear briefly
when their keys are used; those helpers are covered by the
[hardware-feedback recipe](hardware-feedback.md).

## Build the selected Arch package

The Arch reference uses the existing `swaync-bryan` fork because its unified
information panel and notification activation behavior are part of the selected
profile. Upstream SwayNC remains a smaller alternative, but it does not provide
these widgets.

| Input | Pin |
| --- | --- |
| Fork release | [`niri-plus-2`](https://github.com/byebyebryan/SwayNotificationCenter/releases/tag/niri-plus-2) |
| Arch recipe revision | `d2a4bc709b7ea77567ca50fac9b1001088f90815` |
| Recipe archive SHA-256 | `ffcd5dbc373e062a82ec0daee3be5ae35385bfb1e73c0569c141801ca848ab0c` |
| SwayNC source revision | `96a2a9c4574e26fc6d6839a0e19d506a7638898e` |
| Source archive SHA-256 | `68f1cfa73eb79e344589fb2b1d62d04bb282034910f6118e366a979c5c256658` |
| Runtime package | `swaync-bryan 0.12.6-20` |

Fetch and verify the immutable Arch recipe archive before extracting it:

```sh
SWAYNC_BUILD=$(mktemp -d)
curl --fail --location --output "$SWAYNC_BUILD/recipe.tar.gz" \
  https://codeload.github.com/byebyebryan/SwayNotificationCenter/tar.gz/d2a4bc709b7ea77567ca50fac9b1001088f90815
printf '%s  %s\n' \
  ffcd5dbc373e062a82ec0daee3be5ae35385bfb1e73c0569c141801ca848ab0c \
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

The [`reference.json`](../../examples/notifications/reference.json) is the
authored profile for the current 0.4.3/SwayNC 0.12.6-20 Arch install target. Its
SHA-256 is
`c40e8a0cbf1327c87b5b713b6c68ba3d0462dff654d7b51d1bd58333bdf79543`. It
selects the unified `information`, `title` and `notifications` widgets,
width 448, full-height fit, zero margins, ungrouped notifications, bold local
time, plain date and inline Do Not Disturb control. The profile remains a
reviewed checkout input, separate from both the published bundle and pinned
public-example snapshot. The old profile bytes are retained at
[`tools/reference/history/notifications-0.4.1.json`](../../tools/reference/history/notifications-0.4.1.json)
with their original SHA-256
`da55b379747d5ac0208730354ebfd8901dc268ac8e5b5b717e81ee9243d15577`.

Keep using the `NIRI_PLUS_CHECKOUT` path exported by the main guide, since the
build above changes the current directory. If running this recipe in a separate
shell, export that variable from the reviewed checkout before building.

With the verified stager output from the
[Arch walkthrough](../setup-agent.md#2-stage-the-reviewed-inputs), set `STAGE` to that
directory and install only after backing up any existing SwayNC files:

```sh
printf '%s  %s\n' \
  c40e8a0cbf1327c87b5b713b6c68ba3d0462dff654d7b51d1bd58333bdf79543 \
  "$NIRI_PLUS_CHECKOUT/examples/notifications/reference.json" | sha256sum --check
install -Dm644 "$NIRI_PLUS_CHECKOUT/examples/notifications/reference.json" \
  "$HOME/.config/swaync/config.json"
install -Dm644 "$STAGE/appearance/swaync.css" \
  "$HOME/.config/swaync/style.css"
```

The stylesheet is rendered from the separately pinned 0.4.3 Neutral Slate
identity. It imports the fork's packaged base stylesheet. The config requires the fork;
the older `examples/notifications/config.json` remains a historical portable
specimen, not the selected Arch dashboard config.

When the optional `shared.swaync_sidebar` identity block is present, the
rendered style gives the sidebar, information surface, and notification cards
75% charcoal backgrounds. Its `opacity`, `border_color`, and
`card_border_color` values set the surface alpha and outlines. The sidebar has
one left border; internal information dividers retain their separator color.
Notification text and controls remain opaque and focus and critical outlines
remain active. Omitting the block keeps the legacy stylesheet output.

The style is available in the [0.4.3 maintenance backport](https://github.com/byebyebryan/niri-plus/releases/tag/components-v0.4.3),
which changes only the two appearance implementation files from 0.4.2 and
retains all 42 other runtime payloads. The current numbered reference selects
this sidebar appearance.

The authored reference profile uses this edge-attached layout with individual
notification cards. Merge the same values into another SwayNC config when
selecting that layout:

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

The current Arch install target selects the unified information panel in
[fork release 2](https://github.com/byebyebryan/SwayNotificationCenter/releases/tag/niri-plus-2),
with the matching [components 0.4.3 appearance](https://github.com/byebyebryan/niri-plus/releases/tag/components-v0.4.3).
The selected profile is:

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

For other configurations, merge these widget entries while retaining any
separately selected controls, including a volume widget. The opening row has
bold local time and a plain date in equal columns, without captions. System uses read-only
CPU/RAM and active GPU/VRAM meters. Connections keeps the active connection identity and labelled Signal/IP detail
in the left column, with upload/download rates in the right. Long IPv6 values
ellipsize with a complete tooltip.
Bluetooth uses device metadata for icons and distinguishes `0%` from an
unreported battery. Battery uses a 0–100 gauge and marks only an actual reported
charge limit. Missing sections disappear with their dividers, while their
readers continue to observe changes whenever the panel is open.

Networking uses two equal columns. The
left has the active SSID or Ethernet identity above a Signal/IP label and
right-aligned value. Signal uses the same percentage formatting as CPU/RAM.
The right has labelled upload and download rates from that primary interface,
sampled once per second while the panel is open. Reopening or changing interfaces
starts a fresh baseline; unavailable values stay distinct from measured zero.
The current components 0.4.3 appearance selection supplies the translucent
sidebar and matching information/notification cards.
The [fork maintenance guide](https://github.com/byebyebryan/SwayNotificationCenter/blob/niri-plus/docs/fork-maintenance.md)
records its upstream baseline, downstream contracts and native regression checks.

## Configurable notification-history retention

The current fork lets an operator set separate maximum ages for notification
cards retained in control-center history. Merge these optional keys into the
existing `~/.config/swaync/config.json`, preserving its widgets and other
settings. Do not replace the complete config with this two-key fragment.

The following values illustrate the keys. They are an explicit personal policy,
not the portable reference defaults:

```json
{
  "history-retention": 3600,
  "history-retention-critical": 0
}
```

After editing, reload the config with `swaync-client --reload-config` (or
`swaync-client -R`). Enabling a limit can expire and remove older history
immediately after that reload.

Both properties are integer seconds and default to `0`, meaning unlimited.
`history-retention` applies to low and normal urgency; critical urgency uses
`history-retention-critical` independently. Resident notifications are exempt.
Age begins when a notification is accepted into effective history, and an
accepted replacement starts a new age. The monotonic age clock continues
through suspend. Existing admission and visibility rules still decide whether a
notification enters effective history. Do Not Disturb, a closed sidebar and
notification grouping do not pause its age. Reloading configuration recalculates
expiry from the original receipt time; enabling a limit may remove overdue
entries immediately.
Increasing a limit does not restart age, and disabling a limit does not restore
entries already removed. An active inline reply defers removal until focus
leaves the reply controls.

History expiry removes the card without ending a still-visible popup; the popup
remains actionable until its own lifecycle ends. Setting either retention limit
to a nonzero value makes the daemon omit the D-Bus `persistence` capability.
Clients may keep a previously advertised capability through a config reload
because the protocol has no standard capability-change signal. These global
age limits do not track read state, cap notification counts, or set
per-application policy.

The authored [`reference.json`](../../examples/notifications/reference.json)
omits both settings and inherits the fork defaults of unlimited history. Bryan's
separate chezmoi policy sets ordinary retention to 3600 seconds and critical
retention to 0; that is personal machine policy, not a portable profile default.
The package-20 producer and recipe provenance are recorded in the
[release supplement](../planning/swaync-reference-release2-20261114.md). Its
bounded native checkpoint-copy supplement passed login, panel/DND, default and
overridden retention, action activation and cold-boot checks. It does not claim
a fresh OS or full 21-task replay. The prior 21-task replay is package-18
evidence and remains in the
[2026-11-08 qualification](../planning/reference-qualification-20261108.md).

Legacy dashboard and standalone widgets remain available. The current
components 0.4.3/SwayNC 0.12.6-20 reference route has a qualified bounded
checkpoint-copy supplement recorded in the
[release supplement](../planning/swaync-reference-release2-20261114.md). The
[dated package-18 qualification](../planning/reference-qualification-20261108.md)
records its own fresh replay, supplemental checks, evidence limits and VM
suspend/resume waiver. Physical-device acceptance remains separate.

The earlier scoped package 0.12.6-17 staging, installation, password/cold login,
sidebar/DND, clipboard and direct-controls checks and their native media retain
their dates in the [sync receipt](../planning/swaync-reference-sync-20261107.md).
Native widget and private-bus checks retain their own scope, separate from that
replay and physical hardware acceptance. The [fork widget documentation](https://github.com/byebyebryan/SwayNotificationCenter/blob/niri-plus/docs/system-widgets.md)
covers formats, suffixes, lifecycle and stylesheet hooks.

This SwayNC profile does not select the separate components 0.5.0 Away
companion, 0.9.2 session screen or 0.10.0 Close All helper.

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
notification from a real application. Check the System, Connections, Bluetooth,
and Battery sections against available devices. Missing hardware should remain
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
