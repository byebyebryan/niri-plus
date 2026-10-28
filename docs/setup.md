# Install the Arch reference desktop

This walkthrough starts from an installed Arch Linux x86-64 system, an ordinary
sudo-capable user, working networking, and package access. It does not install
Arch, partition disks, copy a private home directory, or use a display-free
capture login. Keep a working console login and, when available, SSH recovery
while changing the desktop.
File-copy commands assume new target names. Inspect existing config and unit
paths first; back them up and merge when they already contain your choices.
Run the following commands from the reviewed Niri Plus checkout root and keep
that path in a task-specific variable; package builds below change directories:

```sh
export NIRI_PLUS_CHECKOUT="$(git rev-parse --show-toplevel)"
test -f "$NIRI_PLUS_CHECKOUT/tools/reference/inputs.json"
```

The selected reference is Neutral Slate with Clear Blue focus, a pure-black
Balanced+ Kitty palette, and Noto Sans/Meslo typography. The session uses SDDM
and Niri, GTK portals for file/access/settings/notification interfaces, WLR for
whole-monitor capture, and the pinned SwayNC fork for the on-demand dashboard.
The focused [recipes](#focused-recipes) retain the details for each part.

Niri Plus first-party code is covered by the repository [LICENSE](../LICENSE),
and bundled design assets are indexed in [assets/LICENSES.txt](../assets/LICENSES.txt).
The pinned SwayNC fork keeps its GPL-3.0 terms in the [notification source
recipe](recipes/notifications.md); fetched Zsh dependencies include their own
[third-party notices](../examples/terminal/THIRD_PARTY_NOTICES.md). Chrome,
fonts, GTK themes, and icon themes remain governed by their upstream terms and
package notices; Chrome presents its own terms on first run.

> **Candidate status:** Targeted native checks passed for stock SDDM/Niri login,
> KWallet/Secret Service, packaged Fcitx5 autostart, polkit authorization,
> Gtklock locking/unlocking, and native Wayland input composition in Chrome and
> Kitty. Guest playback passed through a virtual HDA device. Fresh-guide and
> cold-boot replay remain open; physical/SPICE audibility and microphone signal
> are not claimed. A dated acceptance receipt is pending primary review.

## 1. Prepare the account and record the starting state

Confirm that you are an ordinary user with sudo access and can recover from a
console. Record the current network owner before installing or enabling another
manager. The development copy used `systemd-networkd` and `systemd-resolved`;
do not enable NetworkManager until its handover has a tested recovery route.

```sh
id
sudo -v
ip route
systemctl is-active systemd-networkd.service systemd-resolved.service NetworkManager.service || true
systemctl --user status || true
```

Apply Arch's normal full upgrade, then reboot if the transaction asks for it:

```sh
sudo pacman -Syu
```

Record the package baseline with `pacman -Q` before continuing. Arch package
versions move independently of the pinned Niri Plus source inputs.

## 2. Stage the reviewed inputs

The first-party helper and its input inventory are candidate source files in the
Niri Plus checkout containing this guide; the helper is not part of the
published 0.3.1 component archive. It runs as your user and writes only into a
new output tree. It verifies the immutable component archive, its manifest and
all 27 payloads; the independently pinned identity; and the listed public
examples from source commit
[`b62df460884b5a4d5e8c7eeb05c132a0b26814ae`](https://github.com/byebyebryan/niri-plus/tree/b62df460884b5a4d5e8c7eeb05c132a0b26814ae).
It then renders appearance previews and writes `provenance.json` with the input
and output hashes. It does not install packages, write normal configuration,
start services, or import capture-pilot state.

Install the staging prerequisites and choose a new output path:

```sh
sudo pacman -S --needed curl git python unzip
mkdir -p "$HOME/.local/share/niri-plus"
python3 "$NIRI_PLUS_CHECKOUT/scripts/stage-arch-reference.py" \
  --output "$HOME/.local/share/niri-plus/arch-reference-0.3.1"
```

Set these paths for the commands below:

```sh
export STAGE="$HOME/.local/share/niri-plus/arch-reference-0.3.1"
export SOURCE="$STAGE/source"
export BUNDLE="$STAGE/bundle"
export APPEARANCE="$STAGE/appearance"
```

Inspect `$STAGE/provenance.json`. The source checkout is used only to provide
the selected examples; the staged components and previews remain self-contained.
The SwayNC `reference.json` described later is a separate candidate file and is
deliberately not fetched from the pinned public snapshot.

## 3. Install the first-session packages

Install Niri, SDDM, the selected portal providers, and the basic window,
terminal, and launcher tools. The SDDM package supplies its Xorg server and
authentication dependencies; this reference does not require KWin.

```sh
sudo pacman -S --needed \
  niri xwayland-satellite sddm qt6-declarative qt6-svg \
  kitty rofi dolphin \
  xdg-desktop-portal xdg-desktop-portal-gtk xdg-desktop-portal-wlr \
  noto-fonts noto-fonts-emoji ttf-meslo-nerd
```

The pinned public Niri starter is proportional and contains no personal paths,
automatic suspend policy, or session startup hooks. Inspect it and preserve any
existing configuration before installing. On the fresh account, install the
starter only when neither target exists:

```sh
if [ -e "$HOME/.config/niri/config.kdl" ] || [ -L "$HOME/.config/niri/config.kdl" ] ||
   [ -e "$HOME/.config/xdg-desktop-portal/niri-portals.conf" ] ||
   [ -L "$HOME/.config/xdg-desktop-portal/niri-portals.conf" ]; then
  printf '%s\n' 'Existing Niri or portal config found; inspect and merge the staged examples.'
else
  install -Dm644 "$SOURCE/examples/niri/config.kdl" "$HOME/.config/niri/config.kdl" &&
  install -Dm644 "$SOURCE/examples/portals/niri-portals.conf" \
    "$HOME/.config/xdg-desktop-portal/niri-portals.conf" &&
  niri validate --config "$HOME/.config/niri/config.kdl"
fi
```

The portal profile selects GTK for file/access/settings/notification interfaces
and WLR for whole-monitor capture. Individual-window capture remains outside
this reference. If a VirtIO/VirGL guest reproduces the documented whole-monitor
failure with the Arch portal package, the [optional local compatibility
candidate](../tools/vm/desktop/wlr-compat/README.md) explains its reviewed build
and recovery path. It is not required on a physical desktop or where the stock
portal works.

## 4. Verify stock SDDM password login before theming

Check that no other display manager owns the login path. Keep the distribution's
SDDM/PAM configuration unchanged for this first login. From a local console,
enable and start SDDM:

```sh
sudo systemctl enable --now sddm.service
```

Select Niri in the greeter and log in with the account password. Verify the
session and user manager:

```sh
loginctl show-session "$XDG_SESSION_ID" -p Type -p State
systemctl --user is-active niri.service graphical-session.target
```

Log out to SDDM and log in again. If the greeter or session fails, return to the
console, inspect `journalctl -b -u sddm.service`, and restore the previous
display-manager owner. Do not add a PAM module, autologin drop-in, or theme to
repair the stock login gate.

## 5. Add the reference appearance and browser/files

Install the application, appearance, input, audio, and session prerequisites in
one reviewed package transaction. NetworkManager and BlueZ remain installed
only; do not enable them until their actual device/service handovers are ready.

```sh
sudo pacman -S --needed \
  adw-gtk-theme ark base-devel bluez bluez-utils brightnessctl \
  breeze breeze-cursors breeze-icons cliphist dconf fcitx5 \
  fcitx5-chinese-addons fcitx5-configtool fcitx5-gtk fcitx5-qt \
  fontconfig fzf gsettings-desktop-schemas gtk3 gtk4 gtk4-layer-shell \
  gwenview kanshi kwallet kwallet-pam libadwaita libgee libnotify libsecret \
  libpulse json-glib granite7 mpv neovim networkmanager pavucontrol \
  pipewire pipewire-audio pipewire-pulse polkit polkit-kde-agent qt5-wayland qt5ct \
  qt6-wayland qt6ct shared-mime-info swayidle gtklock upower udisks2 \
  wl-clipboard wireplumber xdg-utils zoxide zsh adobe-source-han-sans-cn-fonts
```

`base-devel` and the GTK4 libraries above are for the pinned SwayNC package
recipe. Do not install upstream `swaync` separately. Add `nvidia-utils` only
when the host has supported NVIDIA hardware.

Use the rendered files under `$APPEARANCE` as appearance-only layers. The
[appearance recipe](recipes/appearance.md) gives ordinary GTK3, Qt5/Qt6, KDE,
Rofi, Kitty, and Gtklock targets, the `fonts.json` and `kdeglobals-managed.json`
merge, a reversible GSettings profile for GTK appearance, and the Qt-only
systemd user-service environment profile. The pavucontrol GTK4 dark-surface
check passed through the selected GSettings preference with `GTK_THEME` unset.
The notification recipe owns the selected SwayNC stylesheet target. Merge the
Niri fragment into the starter's existing `layout` block, keep its proportional
columns and bindings, and validate the complete file after each change. Use the
[login recipe](recipes/login.md) to preview the pinned greeter theme and install
it only after the stock password login passed. Use the matching renderer
outputs in `$APPEARANCE`; do not download or copy a second palette snapshot.

The transaction above includes the file tools. Follow the [files recipe](recipes/files.md)
to install the Neovim desktop entry only when absent and apply the staged MIME
defaults with `xdg-mime`, which leaves unrelated associations intact.

The reference browser is Chrome. Its Arch recipe is pinned at commit
`f0071e0692f4545bcb3e0881ea60c031a9f99343` for version `156.0.8078.47`:

```sh
CHROME_BUILD=$(mktemp -d "$HOME/.local/share/niri-plus/chrome-build.XXXXXX")
git clone https://aur.archlinux.org/google-chrome.git "$CHROME_BUILD"
git -C "$CHROME_BUILD" checkout --detach f0071e0692f4545bcb3e0881ea60c031a9f99343
test "$(git -C "$CHROME_BUILD" rev-parse HEAD)" = f0071e0692f4545bcb3e0881ea60c031a9f99343
less "$CHROME_BUILD/PKGBUILD"
cd "$CHROME_BUILD"
makepkg --verifysource
makepkg --syncdeps --rmdeps
```

Inspect the exact generated `google-chrome` package with `pacman -Qip` and
install that file with `sudo pacman -U`. Record the recipe revision and
installed package version. Launch Chrome normally from `Mod+D` for its first
run. Review its terms and browser-default/telemetry choices yourself, and leave
the browser signed out. Do not pass first-run suppression flags or reuse an
isolated lab profile. Use disposable PDF, image, audio/video, and archive
samples to check defaults, browser download/open/upload, and safe archive
extraction. UDisks mounting uses a new disposable disk for its
read/write/unmount check.

## 6. Install the selected notification and clipboard paths

The full dashboard requires the pinned `swaync-bryan` fork. Follow the
[notification recipe](recipes/notifications.md) to review and build its exact
recipe/source tuple as an ordinary user, inspect the package, and install the
replacement transaction. The candidate dashboard config is a small authored
file in this source checkout; verify its recorded hash before copying it. Use
`$APPEARANCE/swaync.css` for the selected stylesheet.

For text and image clipboard history, use the generated minimal-Niri service
and its paired 200-item Cliphist config. The [clipboard recipe](recipes/clipboard.md)
has the exact targets and `niri.service` wants. Do not combine it with the
separate portable collector unit.

Add the current Rofi entries for Network, Bluetooth, Audio, and Session from
`$SOURCE/examples/desktop/`. They retain their native device and session owners.
The Niri starter binds `Mod+D` to the normal Rofi application list. Preserve it
or merge this line into an existing Niri `binds` block when it is absent; the
individual entries do not need separate key bindings:

```kdl
Mod+D { spawn "rofi" "-show" "drun"; }
```

Use the `nmtui` Network entry only after NetworkManager owns the link. The
[network owner handover](recipes/desktop-utilities.md#network-owner-handover)
is a narrow conditional example for the exact cloud-init/networkd starting
state; a system already owned by NetworkManager skips it. Package installation
does not start BlueZ. Start the packaged `bluetooth.service` only when an
adapter is present and ready; do not run a second daemon. The reference menu
entry uses `bluetoothctl`, while `bluetuith` is an optional terminal UI.

Install the shared launcher helper and entries:

```sh
install -Dm755 "$SOURCE/examples/desktop/desktop-session-ready" \
  "$HOME/.local/bin/desktop-session-ready"
install -Dm755 "$SOURCE/examples/desktop/desktop-session-menu" \
  "$HOME/.local/bin/desktop-session-menu"
install -Dm644 "$SOURCE/examples/desktop/niri-plus-network.desktop" \
  "$HOME/.local/share/applications/niri-plus-network.desktop"
install -Dm644 "$SOURCE/examples/desktop/niri-plus-bluetooth.desktop" \
  "$HOME/.local/share/applications/niri-plus-bluetooth.desktop"
install -Dm644 "$SOURCE/examples/desktop/niri-plus-audio.desktop" \
  "$HOME/.local/share/applications/niri-plus-audio.desktop"
install -Dm644 "$SOURCE/examples/desktop/niri-plus-session.desktop" \
  "$HOME/.local/share/applications/niri-plus-session.desktop"
```

The [desktop-utility recipe](recipes/desktop-utilities.md) records each service
owner. Use the [hardware-feedback recipe](recipes/hardware-feedback.md) to
install both helpers from `SOURCE` and merge all six hardware-key binds from the
verified fragment into the existing Niri `binds` block.

## 7. Wire wallet, policy, and authorization services

Keep one owner for each function. Choose and record the power policy. Reuse the
readiness helper installed in section 6, and install the reviewed units into
ordinary user paths:

```sh
install -Dm755 "$SOURCE/examples/session/desktop-power" \
  "$HOME/.local/bin/desktop-power"
install -Dm644 "$SOURCE/examples/session/profiles/minimal-niri/desktop-lock.service" \
  "$HOME/.config/systemd/user/desktop-lock.service"
install -Dm644 "$SOURCE/examples/session/desktop-idle.service" \
  "$HOME/.config/systemd/user/desktop-idle.service"
install -Dm644 "$SOURCE/examples/session/desktop-battery.service" \
  "$HOME/.config/systemd/user/desktop-battery.service"
install -Dm644 "$SOURCE/examples/session/polkit-session.conf" \
  "$HOME/.config/systemd/user/plasma-polkit-agent.service.d/session.conf"
```

On the development copy, `/etc/pam.d/sddm` already contained the package's
optional `pam_kwallet5` auth/session entries. The KWallet PAM package and Niri
unit wiring were added after the initial stock login, so only a later fresh
password login tested their handshake. Keep the installed PAM file unchanged;
inspect it and the `kwallet-pam` package on a new system rather than copying
another machine's file. Wire the packaged PAM initialization unit to the Niri
graphical session with this user drop-in and one Niri wants link:

```sh
mkdir -p "$HOME/.config/systemd/user/plasma-kwallet-pam.service.d"
cat > "$HOME/.config/systemd/user/plasma-kwallet-pam.service.d/session.conf" <<'EOF'
[Unit]
After=graphical-session.target
Requisite=graphical-session.target
EOF
systemctl --user add-wants niri.service plasma-kwallet-pam.service
```

Merge this preference into the existing Niri portal configuration so the
KWallet backend owns the Secret portal for this reference setup:

```ini
[preferred]
org.freedesktop.impl.portal.Secret=kwallet;
```

Finish the appearance and input steps in section 8 before testing the wallet.
The KWallet PAM package and packaged Fcitx5 autostart both need a fresh login
after installation. Do not run `secret-tool` from the earlier stock-login
session.

Before installing the idle service, review
`$SOURCE/examples/session/power.toml.example`, choose values, and save the full
policy to `~/.config/desktop-session/power.toml`. Do not start the policy helper
with a missing or unreviewed policy. Verify the units and add only the idle,
battery, polkit, and KWallet PAM services to Niri; the manual lock unit stays
on-demand:

```sh
systemctl --user daemon-reload
systemd-analyze --user verify \
  "$HOME/.config/systemd/user/desktop-lock.service" \
  "$HOME/.config/systemd/user/desktop-idle.service" \
  "$HOME/.config/systemd/user/desktop-battery.service" \
  plasma-polkit-agent.service plasma-kwallet-pam.service
if ! systemctl is-active --quiet polkit-agent-helper.socket; then
  sudo systemctl start polkit-agent-helper.socket
fi
systemctl --user add-wants niri.service \
  desktop-idle.service desktop-battery.service plasma-polkit-agent.service \
  plasma-kwallet-pam.service
systemctl --user daemon-reload
systemctl --user start \
  desktop-idle.service desktop-battery.service plasma-polkit-agent.service
```

These are candidate Niri session wires; verify one instance at login and clean
teardown at logout using the [session recipe](recipes/session.md). The packaged
PipeWire/WirePlumber user services retain their native activation; do not add
Niri spawns or duplicate units for them. Fcitx5's packaged XDG autostart and the
BlueZ daemon keep their own owners. Do not start a second SwayNC, clipboard,
audio, or input-method process from Niri.

When polkit was installed after `sockets.target` had started, the static helper
socket may still be inactive for this boot. Starting the packaged
`polkit-agent-helper.socket` activates its native route; it is normally socket
activated after boot, so do not enable the static unit or change its packaged
permissions. Run a graphical `pkexec /usr/bin/true` check and authenticate to
confirm the prompt and allow path. Cancelling denies the action; the
development-copy test returned 127 on cancel and 0 after authentication, with
the packaged polkit files unchanged.

The KWallet/Secret Service path, manual Gtklock password check, SDDM-session
lock request, idle restart with an existing locker, polkit prompt/allow path,
native Chrome/Kitty input composition, and guest playback through its virtual
HDA device passed targeted development-copy checks. Repeat them through a fresh
guide replay and cold boot before accepting the complete loop. Physical/SPICE
audibility and microphone signal are not established. Restart cancellation
preserved the same boot ID, and the confirmed Session Shut down action stopped
the development guest normally.

## 8. Add display, input, audio, and shell workflows

Kanshi has no packaged user unit in the current Arch snapshot. Adapt
`$SOURCE/examples/displays/kanshi.conf` to the actual outputs, then use the
single startup owner described in the [display recipe](recipes/displays.md).
The installed Fcitx5 package has its own XDG autostart desktop entry. Niri's
packaged session starts `xdg-desktop-autostart.target`; verify
`app-org.fcitx.Fcitx5@autostart.service` and one `fcitx5` process after the
fresh login described below.
Do not add a Niri `fcitx5 -d` spawn or a second user service. The
[input recipe](recipes/input.md#create-the-reference-profile) supplies a guarded
fresh-account profile for `keyboard-us`, Pinyin, US layout, and `Super+Space`.
Use `fcitx5-configtool` when modifying an existing profile.

For direct Niri-launched applications, merge these values into the existing
Niri `environment` block and validate the complete config:

```kdl
environment {
    QT_IM_MODULE "fcitx"
    XMODIFIERS "@im=fcitx"
    SDL_IM_MODULE "fcitx"
}
```

`QT_IM_MODULE` is for Qt clients using Fcitx under Niri; `XMODIFIERS` is for
XIM clients under X11/XWayland; retain `SDL_IM_MODULE` for SDL2 clients.
Leave `GTK_IM_MODULE` unset globally. Niri's environment block does not change
the systemd user-manager environment; the appearance recipe's `environment.d`
file covers user services only. See the [Fcitx Wayland guide](https://fcitx-im.org/wiki/Using_Fcitx_5_on_Wayland/en)
for toolkit-specific behavior.

The Niri starter has no `PATH` override. For Niri-spawned commands such as
Kanshi, the Rofi Session helper, feedback helpers, and the clipboard launcher,
print the account's absolute home path and merge that line into the same
`environment` block. Do not put `~` or `$HOME` in the KDL value. If you already
customize `PATH`, retain its other required directories:

```sh
printf 'PATH "%s/.local/bin:/usr/local/bin:/usr/bin"\n' "$HOME"
```

Targeted development-copy checks passed for native composition in Chrome 156
launched with `--ozone-platform=wayland` only and Kitty 0.49.2 using native
Wayland text input. Preedit, cancellation, candidate selection, commit, and
`Super+Space` Latin switching worked; the candidate popup followed fields at
scale 1.5. These checks need a fresh-guide replay before E3 acceptance. Do not
add `GTK_IM_MODULE`, `--enable-wayland-ime`, or a forced text-input version to
these tested routes.

PipeWire and WirePlumber keep their packaged socket/session ownership. If their
packages were installed after this user manager was already running, start the
standard units for the current session before checking audio:

```sh
systemctl --user start pipewire.socket pipewire-pulse.socket wireplumber.service
systemctl --user is-active pipewire.socket pipewire-pulse.socket wireplumber.service
wpctl status
```

On the latest development-copy pass, an attached virtual ICH9 HDA device
produced the real PipeWire sink
`alsa_output.pci-0000_00_1b.0.analog-stereo`; a three-second test tone reached
the ALSA PCM (`RUNNING`) and its monitor. This checks the guest playback path
only. It does not establish physical or SPICE audibility or microphone signal.
Do not substitute a dummy sink for playback acceptance. The
[hardware-feedback recipe](recipes/hardware-feedback.md) verifies volume and
notification controls. Check brightness and radio features only when the
corresponding hardware exists.

### Fresh password-login gate for wallet and autostart

After completing the appearance, session, and input changes, log out to SDDM
and password-login again. This is the first login after installing `kwallet-pam`
and Fcitx5, so it exercises the real PAM handoff and starts the packaged input
method autostart. Check one Fcitx5 process and the KWallet PAM unit; then store
and read a disposable secret. Keep it in the wallet until after the cold-login
check:

```sh
systemctl --user is-active plasma-kwallet-pam.service
systemctl --user status app-org.fcitx.Fcitx5@autostart.service
pgrep -ax fcitx5
busctl --user status org.freedesktop.secrets
busctl --user status org.freedesktop.impl.portal.desktop.kwallet
secret-tool store --label='Niri Plus disposable check' service niri-plus-reference account disposable
secret-tool lookup service niri-plus-reference account disposable
```

Reboot and password-login once more. Check the secret again before clearing it:

```sh
secret-tool lookup service niri-plus-reference account disposable
secret-tool clear service niri-plus-reference account disposable
```

The targeted development-copy pass opened the wallet without a second password
prompt. Repeat this sequence on a fresh guide installation before calling E3
complete; do not change PAM if the normal package handoff is still being tested.

Stage the four pinned shell dependency trees manually from the verified
examples. Choose a new leaf, then follow the [terminal recipe](recipes/terminal.md)
to add the source shim and Kitty shell choice:

```sh
ZSH_BUNDLE="$HOME/.local/share/niri-plus/zsh-neutral-slate"
python3 "$SOURCE/examples/terminal/fetch.py" "$ZSH_BUNDLE"
```

This fetcher requires network access and runs only when invoked; it is not a
shell-startup installer. Do not copy prompt caches from another home. On the
targeted development-copy check, the first Kitty Git prompt fetched the pinned
Powerlevel10k `gitstatusd` binary, completion selected `alpha-reference` from
`completion-check/al`, and Up/Enter repeated the prior command. Repeat those
checks after a fresh guide replay.

## 9. Replay the task checklist and recover cleanly

Before claiming the reference complete, run the tasks in the login, files,
notifications, clipboard, session, display, input, and hardware-feedback
recipes. Reboot to SDDM, password-login, test core tasks, log out, and log in
again. Record package versions and whether each required service has exactly one
owner. A required manual repair returns the guide to review; incorporate it in
the owning recipe before a separate fresh replay.

Keep backups of any native files changed and exact preimages for privileged
SDDM files. To back out a user service, stop only the unit introduced, remove
only its exact `niri.service.wants` link, and restore its saved file. Keep the
console path working until SDDM login, lock/unlock, and session teardown pass.

## Focused recipes

- [SDDM login and greeter](recipes/login.md)
- [Neutral Slate appearance](recipes/appearance.md)
- [Files and removable media](recipes/files.md)
- [Notifications and dashboard](recipes/notifications.md)
- [Clipboard history](recipes/clipboard.md)
- [Locking and session services](recipes/session.md)
- [Display profiles](recipes/displays.md)
- [Fcitx5 input](recipes/input.md)
- [Volume and brightness feedback](recipes/hardware-feedback.md)
- [Network, Bluetooth, Audio, and Session entries](recipes/desktop-utilities.md)
- [Kitty and Zsh](recipes/terminal.md)
