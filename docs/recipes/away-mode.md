# Manual display-away mode

The optional `desktop-away` companion lets you latch Niri displays off during
unattended SSH or browser-agent work. It starts in normal mode and changes
display power only after an explicit `desktop-away away` command or shortcut.
The existing `desktop-power`/`swayidle` pair remains the sole automatic idle
and suspend policy. Do not connect its automatic resume event to
`desktop-away resume`.
Away mode controls display power only; it does not keep the computer awake or
inhibit system sleep. Existing suspend timers, lid behavior and power policy
continue to apply while away.

The latch deliberately ignores application inhibitors and corrects later
application or hotplug wakeups. Normal video and presentation behavior remains
under the current policy until you enter away mode; resume before starting
interactive playback or a presentation.

## Select and stage the separate release

The numbered Arch reference still selects components 0.4.1. Away mode is a
separate, opt-in selection from the published components 0.5.0 archive. Its
[input pin](../../tools/reference/away-inputs.json) and
[stager](../../scripts/stage-desktop-away.py) verify all 46 archive payloads,
then extract only the canonical helper and unit. The stager retains the
original archive, full manifest, input pin and provenance receipt. It does not
install files, start services or replace the reference bundle. The adjacent
[archive verifier](../../scripts/stage-arch-reference.py) is required by the
stager.

Use a Wayland Niri session with `niri.service` and
`graphical-session.target` active, `systemd --user`, and Python 3.11 or newer.
The helper uses existing readable physical evdev input or
`libwayland-client` with `ext-idle-notify` version 2. No additional raw-input
permissions, group membership or device rules are required.

Start from the root of a reviewed Niri Plus checkout. Record its revision; the
profile later in this recipe comes from this checkout, not the frozen 0.4.1
`$SOURCE` tree:

```sh
export NIRI_PLUS_CHECKOUT="$PWD"
git -C "$NIRI_PLUS_CHECKOUT" rev-parse HEAD
test -f "$NIRI_PLUS_CHECKOUT/scripts/stage-desktop-away.py"
test -f "$NIRI_PLUS_CHECKOUT/tools/reference/away-inputs.json"
mkdir -p "$HOME/.local/share/niri-plus"
export AWAY_STAGE="$HOME/.local/share/niri-plus/desktop-away-0.5.0"
test ! -e "$AWAY_STAGE" && test ! -L "$AWAY_STAGE"
python3 -B "$NIRI_PLUS_CHECKOUT/scripts/stage-desktop-away.py" --output "$AWAY_STAGE"
```

Review `$AWAY_STAGE/inputs.json` and `$AWAY_STAGE/provenance.json` before
installing. Confirm the release tuple is 0.5.0 and the selected file records
are exactly `components/desktop/bin/desktop-away` and
`components/desktop/systemd/user/desktop-away.service`.

## Inspect and install the selected files

Check these paths and any existing unit wants before changing them:

- `~/.local/bin/desktop-away`
- `~/.config/systemd/user/desktop-away.service`
- `~/.config/niri/config.kdl` and the selected Niri config's existing includes
- `~/.config/niri/local/away-mode.kdl`
- `~/.config/systemd/user/niri.service.wants/desktop-away.service`

The commands below are for a new, unmanaged adoption only. Keep exact preimages
and modes for any existing targets. Do not follow or overwrite a symlink, or
replace a different service/helper without reviewing its owner. If an active or
managed away helper already exists, inspect its running service and configuration
owner, then make this change in that source; installing these files and running
`start` would not replace the already running process.

After review, install only the two selected 0.5.0 files:

```sh
install -Dm755 "$AWAY_STAGE/components/desktop/bin/desktop-away" \
  "$HOME/.local/bin/desktop-away"
install -Dm644 "$AWAY_STAGE/components/desktop/systemd/user/desktop-away.service" \
  "$HOME/.config/systemd/user/desktop-away.service"
```

Keep `~/.local/bin` in the graphical session's `PATH` so Niri can run the
binding. The user unit runs the helper at its fixed `%h/.local/bin/desktop-away`
path and is tied to `graphical-session.target`.

## Add the optional Niri binding

The authored [minimal Niri profile fragment](../../examples/session/profiles/minimal-niri/away-mode.kdl)
comes from the reviewed `NIRI_PLUS_CHECKOUT`, not the reference's frozen
0.4.1 `$SOURCE` tree. It is deliberately separate from the generated helper
and unit.

Inspect the current configuration for a `Mod+Shift+P` binding. Keep a copy of
the existing config before changing it, and resolve any conflict intentionally.
On Niri 25.11 or newer, install the fragment and add its include at the
top level of `config.kdl`, after the current `binds` section:

```sh
install -Dm644 \
  "$NIRI_PLUS_CHECKOUT/examples/session/profiles/minimal-niri/away-mode.kdl" \
  "$HOME/.config/niri/local/away-mode.kdl"
```

```kdl
include "local/away-mode.kdl"
```

The path is relative to `config.kdl`. Niri merges included `binds` sections;
the included binding overrides an earlier binding for the same key. If your
Niri version does not support includes, copy only the one `Mod+Shift+P` entry
into your existing `binds` block instead. Use one route, not both, and do not
add a second copy of the binding. See Niri's
[include rules](https://niri-wm.github.io/niri/Configuration%3A-Include.html).

Validate the complete config before starting the service:

```sh
niri validate --config "$HOME/.config/niri/config.kdl"
systemd-analyze --user verify "$HOME/.config/systemd/user/desktop-away.service"
systemctl --user daemon-reload
systemctl --user add-wants niri.service desktop-away.service
systemctl --user start desktop-away.service
```

The service's normal startup does not latch displays off. `Mod+Shift+P` runs
`desktop-away away`; `desktop-away status` reports the latch, selected input
backend and DRM power states. `desktop-away resume` releases the explicit
latch remotely. Stopping the service while away restores ordinary display
power, and a new graphical session starts in normal mode.

If `desktop-away away` cannot reach its controller, it sends a one-shot normal
DPMS-off request and returns a nonzero status; no enforced latch is active.
Treat that result as a failure, not as away mode. Use ordinary session input or
display controls to wake the display, then recover or start the service in the
active graphical user's session before relying on `status` or `resume`.

## Input, inhibitors and display limits

When physical evdev input is already readable, the helper observes keyboard,
mouse and touchpad events without a grab. It rejects virtual devices, stale
buffered input, shortcut releases/repeats and audio/display jack events. It does
not store key codes, text or pointer coordinates.

Otherwise it uses `libwayland-client` and `ext-idle-notify` version 2 in
input-only mode. It ignores application inhibitors and exposes no key codes,
text or pointer positions. This follows compositor seat input, including
OS-level injected input; it cannot establish that input was physical. Neither
route adds input-group membership, ACLs, udev rules or a privileged service.
Check `desktop-away status` to see which backend was selected.

The helper polls DRM power every 250 ms and corrects wakeups at most twice per
second. A brief flash before reblanking is possible; unknown output state is not
proof that a display is off. Normal video/presentation inhibitors are retained
outside the explicit away latch.

On Starship, Chrome navigation/clicks and fresh standard screenshots worked
with DRM reporting Off, and mouse input restored the display. An explicitly
cropped screenshot timed out; the headless-extension path and other capture
modes remain unqualified. Physical panel and input return on Snap and Carbon
remain separate acceptance items. See the dated
[integration record](../planning/desktop-away-integration.md).

## Verify and roll back

After installation, confirm `desktop-away status` reports normal mode. Enter
away mode once, confirm the latch state, then release it with `desktop-away
resume` and confirm ordinary display power returns. Separately check the actual
browser automation and physical input path on the target machine. Do not claim
panel acceptance from a DRM state alone.

To remove a new unmanaged extension, stop only `desktop-away.service`, which
restores ordinary display power. Remove only the
`niri.service.wants/desktop-away.service` link and Niri include if this setup
introduced them; if you merged the binding directly, remove only that line.
Restore any saved config, helper or unit preimages and their modes. Remove the
installed fragment and selected files only when newly created by this setup.
If a wants link, unit or service was already present, preserve it and restore
its recorded activation state. Reload the user manager. Leave `desktop-power`,
`swayidle`, locker, suspend and their existing startup links untouched.

The isolated source checks are in
[`scripts/check-desktop-away.py`](../../scripts/check-desktop-away.py). The
original local trial remains a historical repository note. The
[integration record](../planning/desktop-away-integration.md) keeps source,
staging, consumer delivery and physical acceptance as separate evidence.
