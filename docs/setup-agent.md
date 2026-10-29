# Agent setup guide

This is the operational guide for an agent assembling the reference desktop.
Read the [human setup overview](setup.md) for highlights, or use the
[plain Markdown version](../setup/agent.md) of this guide. Follow the numbered
stages in order and open each linked recipe before applying its part.

## Execution contract

The target is one user-authorized Arch Linux x86-64 machine with an installed
OS, an ordinary sudo-capable account and working package/network access. The
reference includes the browser, terminal, appearance and everyday desktop
services below. OS installation, partitioning, Ubuntu/Debian, authenticated
agent tools and personal fleet deployment are outside this route.

Before changing anything, establish the account/home, OS and package versions,
local or SSH access, active graphical session, current display manager, network
manager, portal/secret providers and configuration authority. Inspect existing
files, units and startup owners. If the target is already managed by chezmoi or
another tool, change that source within the user's requested scope; do not
apply fresh-account copies over its deployed files.

When the user wants selected pieces or an existing setup adapted, apply only
that scope and record the other stages as out of scope. Do not reset a working
desktop to recreate the fresh-install tests. The commands below are individual
reviewed steps, not one batch script; use your file-reading tools for inspection
steps such as the PKGBUILD review.

Keep a small execution record outside the source checkout:

- Target and reviewed source revision; existing owners and package baseline.
- Files to merge or create, backups/preimages and recovery access.
- User choices: actual output profiles/scales, keyboard/input languages,
  browser preferences, and idle/locking/suspend policy. A reference example is
  a choice to review, not permission to replace an existing preference.
- Per-stage result: passed, failed, unavailable hardware, or awaiting human
  action, with the actual observation and any restoration still required.

Use the user's existing authorization for the agreed setup. Ask only for
missing choices, credentials through their native prompt, or a disruptive
transition that is not already authorized. Keep the current console/SSH
recovery path working. Coordinate display-manager handover, network handover,
logout and reboot with active work; do not restart an occupied SDDM session.
Do not read passwords from private files or put them in chat, clipboard history,
logs or captures. Browser terms/account choices and password prompts require
the user's native interaction unless a disposable test account and an explicit
input mechanism were supplied for that test.

Do not continue past a failed gate or substitute another compositor, portal
family, secret backend or package pin to hide a failure. Diagnose and record
it, restore the affected scope when needed, and return the unresolved decision.
Source checks, installed files, a running service and a completed native task
are different observations. Missing hardware and human-only checks remain
explicit; they are not passes.

## Inputs and working directory

Obtain a reviewed checkout containing this guide, its input inventory and
`scripts/stage-arch-reference.py`. Record its revision before starting. Some
inputs are still an unpublished candidate separate from components 0.3.1; a
hosted guide does not prove the candidate files exist on the public default
branch. If the supplied revision/export is missing, obtain that exact source
instead of substituting the older release or a private machine's configuration.

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
export NIRI_PLUS_CHECKOUT="$PWD"
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

> **Locally qualified reference, 2026-10-28:** The written route passed from a
> fresh installed-Arch base, including password login, wallet unlock, locking,
> input, files, clipboard, audio feedback, reboot and logout/relogin. Whole-monitor
> sharing passed again after a full guest power-off/start using the documented
> VirtIO compatibility branch. This is a local candidate; publication, physical
> hardware and human acceptance remain separate. The
> [installation receipt](planning/arch-installation-receipt.md) records exact
> inputs, results, recovery and limits.

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

**Stage 1 gate:** Record the target, existing owners, recovery path, package
baseline and upgrade result. Resolve an unexpected starting state before
starting another network manager or display manager.

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

**Stage 2 gate:** The new staging tree has a verified provenance record,
component payloads and rendered appearance. Record its exact paths and hashes.
An existing or failed staging output is not a successful new stage.

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

**Stage 3 gate:** The complete Niri config validates; the intended portal
configuration is installed or deliberately merged. Keep the existing login
owner and recovery path until the next planned transition.

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

**Stage 4 gate:** Actual stock password login, logout to the greeter and
relogin work. Record the Niri/graphical-session owners. A greeter preview or
successful SSH login does not satisfy this gate.

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

**Stage 5 gate:** The selected GTK, Qt/KDE, Rofi, Kitty and greeter layers
come from the same staged identity. Inspect real application surfaces and
validate Niri after merging. Record Chrome's source/package, the user's
first-run choices and actual file-default tasks; keep account state local.

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

**Stage 6 gate:** One notification owner, two paired clipboard collectors,
and the intended launcher entries are installed. Exercise the panel, exact
text/image restore and Delete/Cancel/Clear. Check feedback only on available
devices. Network and Bluetooth retain their selected native owners.

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
fresh-replay test returned 127 on cancel and 0 after authentication, with
the packaged polkit files unchanged.

The KWallet/Secret Service path, manual Gtklock password check, SDDM-session
lock request, idle restart with an existing locker, polkit prompt/allow path,
native Chrome/Kitty input composition, and guest playback through its virtual
HDA device passed the fresh-guide replay. Physical/SPICE audibility and
microphone signal are not established. Restart cancellation preserved the same
boot ID; confirmed Restart rebooted the guest, and confirmed Shut down powered
it off. A later full power-on, logout and relogin restored the expected owners.

**Stage 7 gate:** Units verify, the full power policy is explicitly chosen,
and startup ownership has no duplicates. Test real polkit cancel/allow and
manual lock rejection/unlock. Keep the locker alive during an idle reload.
Complete stage 8 and its fresh password-login gate before testing the wallet.

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

Fresh-guide checks passed for native composition in Chrome 156
launched with `--ozone-platform=wayland` only and Kitty 0.49.2 using native
Wayland text input. Preedit, cancellation, candidate selection, commit, and
`Super+Space` Latin switching worked; the candidate popup followed fields at
scale 1.5. See the receipt for exact committed text and versions. Do not
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

On the fresh-guide replay, an attached virtual ICH9 HDA device
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

The fresh-guide replay opened the wallet without a second password prompt and
read the disposable secret after password login following reboot. A later cold
power-on and final relogin also retained the native provider and passed a new
disposable store/read/clear check. Keep PAM unchanged while testing its normal
package handoff.

Stage the four pinned shell dependency trees manually from the verified
examples. Choose a new leaf, then follow the [terminal recipe](recipes/terminal.md)
to add the source shim and Kitty shell choice:

```sh
ZSH_BUNDLE="$HOME/.local/share/niri-plus/zsh-neutral-slate"
python3 "$SOURCE/examples/terminal/fetch.py" "$ZSH_BUNDLE"
```

This fetcher requires network access and runs only when invoked; it is not a
shell-startup installer. Do not copy prompt caches from another home. On the
fresh-guide check, the first Kitty Git prompt fetched the pinned Powerlevel10k
`gitstatusd` binary, Tab completed a partial directory path, and Up/Enter repeated
the prior command. This first prompt needs network access; it is not an offline
startup guarantee.

**Stage 8 gate:** One Kanshi and one packaged Fcitx owner; supported output
change restored; actual composition in Chrome and Kitty; real audio sink and
signal where available; fresh-login wallet lookup; first terminal prompt,
history and completion. Do not use pasted Unicode as IME evidence or a dummy
sink as hardware playback evidence.

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

## Completion report

Use this checklist with the linked recipes. Report the observed result for
each row; do not silently drop tasks that could not be exercised.

| Area | Required observation |
| --- | --- |
| Login and secrets | Stock login before theming, themed login, actual polkit cancel/allow, disposable wallet lookup after another password login; clear the disposable secret. |
| Session and power | Lock rejects/accepts input, repeated lock retains one locker, idle reload preserves it, the graphical session's loginctl lock request works; restore any short test timer. |
| Displays and input | Actual supported output/scale change and restoration; preedit, cancel, candidate selection and committed text in Chrome and Kitty. |
| Everyday desktop | Available panel metrics; Rofi entries; exact text/image clipboard restore, Delete and Cancel-first Clear; volume/mute restoration with no history pollution. |
| Files and devices | PDF/image/audio/video/archive defaults, archive byte comparison, browser download/open/upload via GTK picker; available radio/storage/backlight tasks recorded separately. Format only a new explicitly authorized disposable disk. |
| Audio and sharing | Real sink/monitor signal where available; whole-monitor share advances frames, Stop releases tracks/nodes; repeat sharing after a full cold start. Use the conditional VirtIO branch only for its demonstrated guest failure. |
| Lifecycle | Planned reboot, logout teardown and password relogin restore exactly the intended owners. Keep recovery available until this passes. |

At handoff, report the target and source revision, installed versions and
provenance, changed files/service owners, user choices, per-task observations,
remaining human/hardware work, compatibility branches, backups/recovery and
final running/stopped state. State whether the requested scope is complete or
which required task is unresolved. Do not push, publish or extend to other
hosts unless that was part of the user's request.

The dated [installation receipt](planning/arch-installation-receipt.md) records
the earlier fresh Arch VM qualification. Moving this walkthrough into an agent
guide does not establish a new native replay or physical-host acceptance.

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
