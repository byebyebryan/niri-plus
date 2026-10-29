# Direct Rofi controls

Network, Audio and Bluetooth use the same compact picker as the other Plus
tools: search, choose a device, then run an explicit action. SwayNC remains the
place to glance at status. Session and Clipboard keep their existing helpers.

**Unreleased component 0.4.0 candidate.** This source is separate from the
published 0.3.1 Arch reference and the utilities currently deployed through
chezmoi. Installing the reference guide does not select this candidate. Release,
personal-host admission and physical-device acceptance are separate steps.

[Try the interactive illustration](../../design/rofi-controls/index.html).
It uses fictional devices and simulated outcomes. The green frame marks a
connected/default device; blue marks keyboard selection. Muted, Saved and
Paired remain readable text states.

## Everyday use

Open `Mod+D` and choose **Network**, **Audio** or **Bluetooth**. Up/Down moves
through devices. The landing list has fixed **Open / Details** actions; Tab
and Shift+Tab cycle them. Open pins the chosen device into a focused page,
where the strip presents that device's operations. Enter runs the visible
action. Left/Right and Ctrl+B/Ctrl+F edit search; Escape/Ctrl+G closes the menu.
Back restores the list's filter and selection. Alt+R refreshes native facts
and requests a bounded scan for the selected Wi-Fi adapter when available.
The focused adapter also exposes an explicit Rescan action. Editable lists
never receive a periodic refresh timer.

| Utility | Routine actions | Native tools retained |
| --- | --- | --- |
| Network | Saved profiles and nearby personal/open Wi-Fi, credentials, connect/disconnect, per-adapter scan, global Wi-Fi radio | `nm-connection-editor`; `nmtui` recovery |
| Audio | Separate output/input defaults, repeatable 5% volume steps, mute | `pavucontrol` for streams, ports and profiles |
| Bluetooth | Paired connect/disconnect, adapter power, bounded discovery, explicit pairing and trust | `kitty -- bluetoothctl` recovery |

The **Advanced settings** row appears when its native tool is available.
Opening it closes this menu and hands off to that tool. Opening a menu never
starts a missing service, unblocks a radio, changes a connection or starts
Bluetooth discovery. NetworkManager, BlueZ and the existing audio server keep
device ownership; the helpers add no startup service.

## Network details

Choose an exact saved profile when several match. Nearby APs are grouped by
raw SSID, security and adapter; activation reselects a compatible AP instead of
permanently binding to a BSSID. Ethernet uses existing saved profiles. New EAP,
hidden, WEP, hotspot, VPN and secondary-profile editing stay in the native editor.
Unavailable saved profiles cannot be activated speculatively.

For new personal Wi-Fi, choose **Connect and remember** or **Connect once**,
then enter the password in a separate masked native prompt. Remember creates
a current-user NM-owned profile with autoconnect. Once creates a volatile
profile without autoconnect. Existing profiles retain their permissions,
storage flags and autoconnect choices. Agent-owned secrets use the compatible
Secret Service schema; an unavailable or incompatible wallet is an explicit
failure, not a promise that KWallet and NM secret agents are interchangeable.
Incorrect credentials require an explicit retry.
Open networks first show a Cancel-first warning naming the network and adapter;
continuing rechecks security and identity. New open profiles need no password.

Pending names the native request. **Close menu** leaves an accepted activation
running; only a bounded, noninteractive monitor may remain. **Cancel connection**
revalidates and cancels that exact owned activation. It cannot promise to
restore a previous network. Disconnect and global Wi-Fi-off confirmations name
their impact; global Wi-Fi affects every managed Wi-Fi adapter, preserving Ethernet.
Connected describes observed NM state, with connectivity reported separately.

## Audio and Bluetooth details

Audio's **Adjust** page keeps its device and selected action after each change.
Volume preserves channel balance and never implicitly unmutes an input. Up
does not exceed 100%; an already amplified device steps down gradually. Input
and output defaults are independent and describe future routing; existing
streams are not silently moved.

Bluetooth discovery is explicit and bounded to 20 seconds. Only this client's
scan is released on close. Pairing is a separate choice for a discovered device,
with its address in Details, PIN/passkey input or a matching-code confirmation,
and keyboard code/progress when required. Pairing never silently enables trust.
**Trust device** is a separate confirmed operation. Forget/unpair is deferred.
**Cancel pairing** targets an owned outstanding Pair request; a connection wait
uses **Stop waiting**, since it has no NM-style activation handle. Stopping a
connection wait never rolls back an externally completed connection.

Passwords, PINs and authentication codes stay out of continuation metadata,
arguments, environment variables, history, logs and clipboard. Visible pairing
codes are held in controller memory and rendered only where needed. Masking is
visual privacy, not a promise of isolated or erased process memory.

## Install a reviewed candidate

These steps are for an agent working from the reviewed candidate checkout or
its verified component archive. Record the source commit and bundle hash.
Inspect existing files and keep preimages before merging; on a managed machine,
change its configuration authority rather than copying over deployed files.
No privileged service/network handover is part of this candidate installation.

On Arch, the additional runtime interfaces are `python-gobject`, NetworkManager's
libnm introspection, `libsecret`, `rofi`, `libpulse` (`pactl`) and `bluez`.
Keep the already chosen NetworkManager, PipeWire/PulseAudio, BlueZ, wallet and
polkit providers. Keep the advanced tools above available for recovery.

Install the complete `components/desktop/lib/niri_plus_controls/` directory to
`~/.local/lib/niri_plus_controls/`, and these four executable entrypoints from
`components/desktop/bin/` to `~/.local/bin/`:

```text
desktop-controls
desktop-network-menu
desktop-audio-menu
desktop-bluetooth-menu
```

Keep the package and its sibling entrypoints from the **same bundle**. They use
Python's standard library plus the native bindings; there is no pip installer.
`~/.local/bin` must be in the graphical session's PATH. Render the independently
pinned schema-2 identity through the candidate appearance module, then install
its two new outputs:

| Rendered output | Target |
| --- | --- |
| `niri-plus-controls.rasi` | `${XDG_CONFIG_HOME:-~/.config}/rofi/niri-plus-controls.rasi` |
| `controls-appearance.json` | `${XDG_CONFIG_HOME:-~/.config}/niri-plus/controls-appearance.json` |

The existing Rofi theme, terminal palette, Kitty behavior and Session/Clipboard
configuration retain their owners. Install the candidate's three desktop
entries only after the complete package and appearance files are staged.
The downloadable [example inventory](../../examples/manifest.json) records each
generated file's producer. The wrappers alone are not standalone downloads.

For a fresh target with the reviewed source in `NIRI_PLUS_CHECKOUT`, the scoped
copies are below. On an existing managed target, use its native configuration
authority to produce these paths instead. `NIRI_PLUS_APPEARANCE` must name a new
staging directory; retain its generated manifest with the execution record.

```sh
NIRI_PLUS_DESKTOP="$NIRI_PLUS_CHECKOUT/components/desktop"
NIRI_PLUS_APPEARANCE="${XDG_CACHE_HOME:-$HOME/.cache}/niri-plus/controls-appearance-candidate"
python3 "$NIRI_PLUS_CHECKOUT/components/appearance/render.py" \
  --identity "$NIRI_PLUS_CHECKOUT/design/identity.json" \
  --output "$NIRI_PLUS_APPEARANCE"
install -d "$HOME/.local/lib/niri_plus_controls" "$HOME/.local/bin"
for source in "$NIRI_PLUS_DESKTOP"/lib/niri_plus_controls/*.py; do
  install -m644 "$source" "$HOME/.local/lib/niri_plus_controls/"
done
for helper in desktop-controls desktop-network-menu desktop-audio-menu desktop-bluetooth-menu; do
  install -m755 "$NIRI_PLUS_DESKTOP/bin/$helper" "$HOME/.local/bin/$helper"
done
install -Dm644 "$NIRI_PLUS_APPEARANCE/niri-plus-controls.rasi" \
  "${XDG_CONFIG_HOME:-$HOME/.config}/rofi/niri-plus-controls.rasi"
install -Dm644 "$NIRI_PLUS_APPEARANCE/controls-appearance.json" \
  "${XDG_CONFIG_HOME:-$HOME/.config}/niri-plus/controls-appearance.json"
for utility in network audio bluetooth; do
  install -Dm644 "$NIRI_PLUS_DESKTOP/share/applications/niri-plus-$utility.desktop" \
    "$HOME/.local/share/applications/niri-plus-$utility.desktop"
done
```

This renders all appearance outputs into staging but copies only the two
controls-specific files. It does not apply other toolkit files or restart
anything. Verify a fresh native menu and an actual task on the selected target;
merely finding the launcher entry does not qualify the backend.

## Verification and recovery

Use the owned checks in the reviewed checkout before selecting a personal host:
`scripts/check-rofi-controls-native`, `scripts/check-controls-wayland-native`, `scripts/check-controls-network-native`,
`scripts/check-controls-nm-agent-native`, `scripts/check-controls-audio-native`
and `scripts/check-controls-bluetooth-native`. Installed-bundle checks accept
their documented prefix/library overrides. The network service proof uses
private mount/network/UTS namespaces, not the host's NetworkManager.

Physical Wi-Fi authentication/rfkill/removal, actual headset/microphone behavior,
and Bluetooth adapter/keyboard pairing still require separate acceptance on an
authorized device. An isolated protocol or virtual-device pass does not establish
those results. See the [implementation receipt](../planning/rofi-controls-implementation-receipt.md)
for the exact candidate and evidence.

To recover, close the menu, restore the reviewed desktop-entry/config preimages,
and use the retained native tools. Remove only the candidate files you installed
after checking for unrelated edits. Do not restart network/audio services, alter
pairings, stop another discovery client, or restart SDDM as cleanup.
