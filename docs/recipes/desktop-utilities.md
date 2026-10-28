# Common desktop utilities

These small application entries put Network, Bluetooth, Audio, and Session
actions in the regular Rofi application list. Use `Mod+D`, then search for the
entry by its displayed name. They are portable examples for a Niri session;
they do not add new keybindings or change power policy on their own.

The managed entries are installed on Carbon, Starship and Snap as of
2026-10-26. They passed native desktop-entry discovery, exact-byte checks and
no-op repeat applies. The [setup record](../../data/setup.json) keeps this
five-file deployment separate from appearance delivery and physical/device
acceptance. The steps below are the portable installation path.

## Requirements

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
The Niri starter binds `Mod+D` to `rofi -show drun`, which lists these entries;
the entries themselves do not need separate key bindings.

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

After a successful handover, `nmtui` in the Rofi Network entry is available.
The change is local to the selected owner and cloud-init rule; it does not
configure another machine's networking or alter unrelated interfaces.

## Install and choose policy

From the main walkthrough, `SOURCE` names the verified example tree. Install
the helpers, then the desktop entries. These commands write only the listed
user files; inspect their contents first if you already manage these names:

```sh
install -Dm755 "$SOURCE/examples/desktop/desktop-session-ready" "$HOME/.local/bin/desktop-session-ready"
install -Dm755 "$SOURCE/examples/desktop/desktop-session-menu" "$HOME/.local/bin/desktop-session-menu"
install -Dm644 "$SOURCE/examples/desktop/niri-plus-network.desktop" "$HOME/.local/share/applications/niri-plus-network.desktop"
install -Dm644 "$SOURCE/examples/desktop/niri-plus-bluetooth.desktop" "$HOME/.local/share/applications/niri-plus-bluetooth.desktop"
install -Dm644 "$SOURCE/examples/desktop/niri-plus-audio.desktop" "$HOME/.local/share/applications/niri-plus-audio.desktop"
install -Dm644 "$SOURCE/examples/desktop/niri-plus-session.desktop" "$HOME/.local/share/applications/niri-plus-session.desktop"
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
