# Common desktop utilities

Network, Bluetooth, Audio and Session are available from the regular Rofi
application list: use `Mod+D` and search for the displayed name. The current
managed desktop uses [direct Rofi controls](rofi-controls.md) for the first
three and the shared Session helper for locking, logout and power actions.
Components 0.4.1 are installed on Carbon, Starship and Snap; the
[managed setup record](../../data/setup.json) keeps installed checks and
physical-device acceptance separate.

This page retains the earlier `nmtui`, `bluetoothctl` and `pavucontrol` launchers
as a simple recovery option. It also owns the conditional network handover and
shared Session behavior used by the main guide. **Follow the main agent guide
for current direct-control installation.** Do not install the three legacy
entries over the direct entries: they deliberately use the same desktop IDs.

## Retained entry requirements

| Entry | Required software and readiness |
| --- | --- |
| Network | `kitty`, NetworkManager, and its `nmtui` text interface. On Arch, `nmtui` is shipped by the [`networkmanager` package](https://archlinux.org/packages/extra/x86_64/networkmanager/files/). NetworkManager must own the connection devices. Package installation alone does not hand off a network link; use the [conditional handover](#network-owner-handover) only for the documented cloud-init/networkd starting state. |
| Bluetooth | `kitty`, [`bluez`](https://archlinux.org/packages/extra/x86_64/bluez/), [`bluez-utils`](https://archlinux.org/packages/extra/x86_64/bluez-utils/) for `bluetoothctl`, a working system D-Bus, and the packaged `bluetooth.service`. A Bluetooth adapter must be present for radio and pairing operations. The separate Arch `bluetuith` terminal UI may also be installed; the reference menu entry intentionally opens `bluetoothctl`. |
| Audio | [`pavucontrol`](https://archlinux.org/packages/extra/x86_64/pavucontrol/) and a running PulseAudio-compatible server, such as PipeWire's PulseAudio server or PulseAudio. |
| Session | Python 3.11 or later, `rofi`, `systemd` user services, `niri` for native logout, and an active Wayland socket. Install the [independent manual lock service](../../examples/session/desktop-lock.service) before using Lock. |

Removable-drive mounting through a file manager has a separate prerequisite:
install [UDisks2 (`udisks2` on Arch)](https://archlinux.org/packages/extra/x86_64/udisks2/), keep its service and polkit authorization
available, and install the filesystem support for the media you use. UDisks2
is not invoked by these four entries.

## Retained portable files

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

The opt-in [native session screen](session.md#optional-unified-session-screen)
uses `desktop-session-menu --screen` and the adjacent `desktop-suspend` helper.
It provides a six-action grid. Selecting an action starts its cancellable
countdown, which is the confirmation before automatic execution. The default
launcher invocation above keeps the reference's legacy
menu; select the screen's portable Ctrl+Alt+Delete profile intentionally.
The Niri starter binds `Mod+D` to `rofi -show drun`, which lists these entries;
the entries themselves do not need separate key bindings.

## Optional Close All

The components 0.10.0 **release candidate** adds the first-party
[`niri-close-all` utility](../../examples/desktop/niri-close-all) and its
[opt-in Niri profile](../../examples/desktop/profiles/minimal-niri/close-all.kdl).
It requests ordinary closes for **all normal windows across every workspace
and output in the captured Niri session**. It is not limited to the focused
workspace, output or application.

The helper reads `niri msg --json windows` once, validates and deduplicates its
unsigned window IDs, then sends one `niri msg action close-window --id ID`
request per captured ID. Niri's [window IPC](https://niri-wm.github.io/niri/niri_ipc/struct.Window.html)
describes toplevel windows; layer-shell panels are separate surfaces. Floating
and unfocused windows are included. Additional IPC fields are ignored, but an
invalid ID rejects the entire snapshot before any close request is sent.

Applications keep their normal save/cancel dialogs and may remain open. New
dialogs and windows created after the snapshot are not added to the operation.
The helper does not kill applications, quit the session, focus each window,
or repeatedly query until the desktop is empty. A disappeared or refused ID
is attempted once without retry; other captured IDs are still attempted.
The helper checks the captured compositor socket before each request and stops
if that socket changes or disappears.

Use Python 3.11+ and a Niri session exposing `NIRI_SOCKET`. For a reviewed
checkout containing this candidate, first inspect existing target and binding
preimages. Install only the helper, and merge or include the optional profile:

```sh
install -Dm755 examples/desktop/niri-close-all "$HOME/.local/bin/niri-close-all"
```

```kdl
Mod+Shift+Q repeat=false hotkey-overlay-title="Close all windows (all workspaces and outputs)" { spawn "niri-close-all"; }
```

Keep `Mod+Q { close-window; }` unchanged. The portable starter does not select
Close All automatically. This action dispatches immediately when invoked;
it is separate from the session screen's six-action countdown. No hot-corner
tool, startup service or additional privilege is required.

For read-only inspection, `niri-close-all --dry-run` prints the one captured
ID list without sending closes. After a valid snapshot, both modes print a JSON record with `scope`,
`dry_run`, `snapshot_ids`, `requested_ids`, `failed_ids` and
`not_attempted_ids`. `requested_ids` means Niri accepted the request, not that
an application actually closed. Exit status is 0 when the snapshot and every
attempted request succeed (including an empty desktop), 1 on snapshot/IPC or
partial request failure, and 2 for invalid command-line arguments.
An invalid or unavailable snapshot reports an error on stderr without sending
any close request.

Managed consumers must wait for a published immutable archive, verify its
manifest, and select only the helper/profile alongside their existing pins.
The qualified reference is not updated by this optional candidate. Tests use
private IPC command fixtures; never test it by closing ordinary live work.
Removing the optional binding and helper reverses adoption; applications
already closed by an explicit invocation cannot be reopened by that rollback.

## Network owner handover

NetworkManager is installed by the main walkthrough, but installation does not
start it or transfer a connection. If NetworkManager already owns the active
link, keep it and skip this section. This example applies only when
`systemd-networkd` owns `eth0`, `/etc/systemd/network/10-cloud-init-eth0.network`
is the exact active rule, cloud-init currently configures networking, and
`/etc/resolv.conf` is already a symlink to the resolver stub. If any owner,
path, or resolver differs, keep the existing owner and review a machine-specific
migration; do not use this sample as a general network-manager swap.

Keep a local console available and leave your current recovery connection
untouched. The rollback timer below is armed first and re-enables networkd after
120 seconds unless you cancel it after proving the new path. The scripts live
in root-owned `/run`, so the transient rollback stays available for this boot
without becoming another installed service:

```sh
if sudo test -e /run/niri-plus-guide || sudo test -L /run/niri-plus-guide; then
  printf '%s\n' 'Inspect existing /run/niri-plus-guide before continuing.' >&2
  exit 1
fi
sudo install -d -o root -g root -m700 /run/niri-plus-guide
sudo tee /run/niri-plus-guide/network-rollback.sh >/dev/null <<'EOF'
#!/usr/bin/bash
set -euo pipefail

network_file=/etc/systemd/network/10-cloud-init-eth0.network
disabled_file="$network_file.reference-disabled"
nm_conf=/etc/NetworkManager/conf.d/90-niri-plus-reference.conf
cloud_conf=/etc/cloud/cloud.cfg.d/99-niri-plus-reference-network.cfg
expected_nm=$'[main]\ndns=systemd-resolved'
expected_cloud='network: {config: disabled}'

check_owned_file() {
    local path="$1" expected="$2" current
    [[ ! -L "$path" ]] || { echo "refusing symlink: $path" >&2; exit 1; }
    if [[ -e "$path" ]]; then
        current="$(cat -- "$path")"
        [[ "$current" == "$expected" ]] || {
            echo "refusing changed file: $path" >&2
            exit 1
        }
    fi
}

check_owned_file "$nm_conf" "$expected_nm"
check_owned_file "$cloud_conf" "$expected_cloud"
if [[ -e "$network_file" && -e "$disabled_file" ]]; then
    echo "both network rule paths exist; inspect before recovery" >&2
    exit 1
fi
if [[ ! -e "$network_file" && ! -f "$disabled_file" ]]; then
    echo "network rule preimage is missing" >&2
    exit 1
fi
[[ ! -L "$network_file" && ! -L "$disabled_file" ]] || {
    echo "refusing network-rule symlink" >&2
    exit 1
}

systemctl disable --now NetworkManager.service
rm -f -- "$nm_conf" "$cloud_conf"
if [[ ! -e "$network_file" ]]; then
    mv -- "$disabled_file" "$network_file"
fi
systemctl enable --now \
    systemd-networkd.service systemd-networkd-wait-online.service \
    systemd-networkd.socket systemd-networkd-varlink.socket \
    systemd-networkd-varlink-metrics.socket systemd-networkd-resolve-hook.socket
EOF
sudo chmod 700 /run/niri-plus-guide/network-rollback.sh

sudo tee /run/niri-plus-guide/network-handover.sh >/dev/null <<'EOF'
#!/usr/bin/bash
set -euo pipefail

network_file=/etc/systemd/network/10-cloud-init-eth0.network
disabled_file="$network_file.reference-disabled"
nm_conf=/etc/NetworkManager/conf.d/90-niri-plus-reference.conf
cloud_conf=/etc/cloud/cloud.cfg.d/99-niri-plus-reference-network.cfg

[[ -f "$network_file" && ! -L "$network_file" ]] || {
    echo "expected cloud-init networkd rule is absent or not a regular file" >&2
    exit 1
}
[[ ! -e "$disabled_file" && ! -L "$disabled_file" ]] || {
    echo "rollback preimage path already exists" >&2
    exit 1
}
[[ ! -e "$nm_conf" && ! -L "$nm_conf" ]] || {
    echo "inspect existing NetworkManager config before continuing" >&2
    exit 1
}
[[ ! -e "$cloud_conf" && ! -L "$cloud_conf" ]] || {
    echo "inspect existing cloud-init config before continuing" >&2
    exit 1
}
systemctl is-active --quiet systemd-networkd.service || {
    echo "systemd-networkd is not the active owner" >&2
    exit 1
}
systemctl is-active --quiet systemd-resolved.service || {
    echo "systemd-resolved is not active" >&2
    exit 1
}
systemctl is-active --quiet NetworkManager.service && {
    echo "NetworkManager is already active; skip this handover" >&2
    exit 1
}
[[ -L /etc/resolv.conf ]] || {
    echo "/etc/resolv.conf is not a symlink; inspect before continuing" >&2
    exit 1
}

install -d /etc/NetworkManager/conf.d /etc/cloud/cloud.cfg.d
printf '[main]\ndns=systemd-resolved\n' > "$nm_conf"
printf 'network: {config: disabled}\n' > "$cloud_conf"
mv -- "$network_file" "$disabled_file"
systemctl disable --now \
    systemd-networkd.socket systemd-networkd-varlink.socket \
    systemd-networkd-varlink-metrics.socket systemd-networkd-resolve-hook.socket
systemctl disable --now systemd-networkd.service systemd-networkd-wait-online.service
systemctl enable --now NetworkManager.service
EOF
sudo chmod 700 /run/niri-plus-guide/network-handover.sh
```

Inspect the exact active rule and resolver link before scheduling anything. Do
not overwrite pre-existing NetworkManager or cloud-init files. Then arm the
rollback and run the handover through transient system units:

```sh
sudo sed -n '1,160p' /etc/systemd/network/10-cloud-init-eth0.network
readlink /etc/resolv.conf
sudo systemd-run --unit=niri-plus-network-rollback --on-active=120s \
  /run/niri-plus-guide/network-rollback.sh
sudo systemctl status niri-plus-network-rollback.timer
sudo systemd-run --wait --unit=niri-plus-network-handover \
  /run/niri-plus-guide/network-handover.sh
```

Verify the existing address stayed attached, NetworkManager has an active
connection, networkd and all four activation sockets are stopped, and DNS plus
HTTPS work before the timer expires:

```sh
nmcli -g GENERAL.STATE,GENERAL.CONNECTION device show eth0
nmcli -t -f NAME,TYPE,DEVICE connection show --active
ip -4 address show dev eth0
systemctl is-active NetworkManager.service systemd-resolved.service
systemctl is-active \
  systemd-networkd.service systemd-networkd-wait-online.service \
  systemd-networkd.socket systemd-networkd-varlink.socket \
  systemd-networkd-varlink-metrics.socket systemd-networkd-resolve-hook.socket || true
readlink /etc/resolv.conf
getent ahosts archlinux.org
curl --fail --silent --show-error --head https://archlinux.org/
```

If all checks pass, cancel the rollback before its 120-second deadline and
confirm the timer stopped:

```sh
sudo systemctl stop niri-plus-network-rollback.timer
sudo systemctl is-active niri-plus-network-rollback.timer || true
```

If the link or checks fail, do not stop the timer; let systemd restore networkd.
If the timer has already failed or the console is still available, inspect the
transient-unit logs and invoke the same root-owned rollback script manually:

```sh
sudo journalctl -b -u niri-plus-network-handover.service \
  -u niri-plus-network-rollback.service --no-pager
sudo /run/niri-plus-guide/network-rollback.sh
```

After a successful handover, direct Network controls can observe the native
connection; `nmtui` remains available as a recovery tool.
The change is local to the selected owner and cloud-init rule; it does not
configure another machine's networking or alter unrelated interfaces.

## Install and choose policy

For the **legacy launcher option only**, use the reviewed repository checkout.
The current 0.4.1 staged `SOURCE` intentionally omits the three old device
entries. In the main walkthrough, `NIRI_PLUS_CHECKOUT` names that checkout.
These commands overwrite the four listed desktop IDs, so inspect existing
entries and keep their preimages before choosing this alternative:

```sh
LEGACY_SOURCE="$NIRI_PLUS_CHECKOUT"
test -f "$LEGACY_SOURCE/examples/desktop/niri-plus-network.desktop"
install -Dm755 "$LEGACY_SOURCE/examples/desktop/desktop-session-ready" "$HOME/.local/bin/desktop-session-ready"
install -Dm755 "$LEGACY_SOURCE/examples/desktop/desktop-session-menu" "$HOME/.local/bin/desktop-session-menu"
install -Dm644 "$LEGACY_SOURCE/examples/desktop/niri-plus-network.desktop" "$HOME/.local/share/applications/niri-plus-network.desktop"
install -Dm644 "$LEGACY_SOURCE/examples/desktop/niri-plus-bluetooth.desktop" "$HOME/.local/share/applications/niri-plus-bluetooth.desktop"
install -Dm644 "$LEGACY_SOURCE/examples/desktop/niri-plus-audio.desktop" "$HOME/.local/share/applications/niri-plus-audio.desktop"
install -Dm644 "$LEGACY_SOURCE/examples/desktop/niri-plus-session.desktop" "$HOME/.local/share/applications/niri-plus-session.desktop"
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

The table below describes the retained native behavior without optional
confirmation adoption. [Full-screen manual confirmation](session.md#optional-suspend-countdown)
can route Lock, display-off, Suspend, Restart and Shut down through one shared
five-second, Escape-cancellable overlay. Its host policy is independent of the
automatic idle policy; Log out retains Niri's own confirmation.

| Choice | Dispatch |
| --- | --- |
| Lock | Starts the independent `desktop-lock.service`, so policy reloads do not stop a manual lock. |
| Log out | Runs `niri msg action quit` and preserves Niri's native confirmation. |
| Suspend | If configured, starts the lock service first; then requests `systemctl suspend`. A failed lock request prevents suspend. |
| Restart | Shows a second Rofi picker with Cancel selected by default; Restart dispatches `systemctl reboot`. |
| Shut down | Shows the same confirmation pattern; Shut down dispatches `systemctl poweroff`. |
| Cancel / Escape | Returns without dispatching an action. |

The retained Rofi route does not use `--skip-confirmation`, directly start a locker, restart
Niri, or change the existing idle/lid policy. The `desktop-lock.service` keeps
manual locking independent from idle behavior. On battery and desktop systems,
configure suspend, lock-before-suspend, and lid behavior together in the
separately owned session policy.

## Pairing with Bluetooth

The Bluetooth entry opens `bluetoothctl` in Kitty. Installing BlueZ does not
start its daemon. When an adapter is present and you are ready to use it, start
the packaged service; enable it only if you want it available after each boot.
Do not start a second `bluetoothd` process:

```sh
sudo systemctl start bluetooth.service
systemctl status bluetooth.service
bluetoothctl list
```

If no controller is listed, stop here and check that the host exposes an
adapter. Arch's [Bluetooth guide](https://wiki.archlinux.org/title/Bluetooth)
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
