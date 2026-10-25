# Build the parts you want

Start with a working Niri session, then add one part at a time. These recipes
target Arch or EndeavourOS and assume you are comfortable inspecting
configuration and managing user services.

The examples are a portable starting point adapted from my configuration. They
are not a copy of my entire home directory. See [the working setup record](reference.md#working-setup)
for versions, provenance, and what has been checked.

## Start with a working Niri session

Install Niri using your distribution's packages and launch it as a session from
your display manager or with `niri-session`. Follow
[Niri's getting-started guide](https://niri-wm.github.io/niri/Getting-Started.html)
for the baseline. Keep your current desktop available while trying it.

On Arch, the basic window, terminal, launcher, and file tools are:

```sh
sudo pacman -S --needed niri kitty rofi dolphin xdg-desktop-portal-gtk xdg-desktop-portal-gnome
```

Choose and install your browser separately. I use Chrome. Niri's
[important software guide](https://niri-wm.github.io/niri/Important-Software.html)
covers portals, an authorization agent, Xwayland, and the rest of a usable
session. Screencasting uses the GNOME portal; file picking can be routed to GTK
without making Nautilus your file manager.

From a clone of Niri Plus, try the example as a separate file first:

```sh
niri validate --config examples/niri/config.kdl
```

Review it and back up your existing `~/.config/niri/config.kdl` before merging
the parts you want. The example has no session startup hooks, fleet routes,
personal filesystem paths, or automatic suspend policy. Niri reloads its
configuration when it changes.

The [portal example](../examples/portals/niri-portals.conf) selects GTK for file
dialogs and GNOME for screencasting. Before checking file dialogs, inspect your
existing `~/.config/xdg-desktop-portal/niri-portals.conf` if present and back it
up. Merge these preferences, or install the example if you have no override:

```sh
mkdir -p ~/.config/xdg-desktop-portal
cp examples/portals/niri-portals.conf ~/.config/xdg-desktop-portal/niri-portals.conf
```

Log out and back into Niri to load the selected portal configuration. Wallet
and secret-service integration are separate preferences; preserve your existing
backend if you already use one.

## Check the browser and file workflow

Start your browser, download a harmless sample file, open it in Dolphin, and
exercise a web upload file picker. Check a screen-sharing selection as well if
you need it. These tasks establish that your session's portals and desktop
integration are useful for the way you work.

## Add the common utilities

Follow the [desktop utility recipe](recipes/desktop-utilities.md) for the
Network, Bluetooth, Audio, and Session application entries. Install only the
services you use. On Arch, the supporting packages include:

```sh
sudo pacman -S --needed networkmanager bluez bluez-utils pavucontrol udisks2
```

`nmtui` needs NetworkManager to own the devices; `bluetoothctl` needs the BlueZ
service and an adapter; `pavucontrol` needs a PulseAudio-compatible audio
server. UDisks2 supports removable media through file managers. Choose the
system-service and polkit setup that fits your distribution. These utilities
do not configure audio routing, radios, backlight, or suspend policy.
See the Arch package records for [NetworkManager](https://archlinux.org/packages/extra/x86_64/networkmanager/),
[BlueZ](https://archlinux.org/packages/extra/x86_64/bluez/),
[BlueZ utilities](https://archlinux.org/packages/extra/x86_64/bluez-utils/),
[pavucontrol](https://archlinux.org/packages/extra/x86_64/pavucontrol/), and
[UDisks2](https://archlinux.org/packages/extra/x86_64/udisks2/).

## Add notifications and information

Follow the [notification recipe](recipes/notifications.md). You can begin with
upstream SwayNC. The system dashboard and the activation fixes described on
this site require the pinned fork, rather than just the theme files.

## Add clipboard history

Follow the [clipboard recipe](recipes/clipboard.md) for text and image
collection, the Rofi picker, and session ownership. Test with sample clipboard
content before making it your normal history.

## Choose locking and idle behavior

Follow the [session recipe](recipes/session.md). Choose manual locking,
automatic locking, display power-off, and suspend intervals explicitly. My own
policy leaves automatic locking and lock-before-suspend disabled; those are
personal choices, not defaults supplied by these examples.

## Add the terminal workflows

Kitty and your native agent tools can be used directly. Add SSH Plus, Tmux Plus,
and Agent Plus only where their workflows are useful. Use their maintained
installation guides through [Fleet Plus](https://dev.byebyebryan.com/fleet-plus/start/).

The complete launch arguments matter for the Rofi Plus action keys. Use each
project's launcher instructions before adding the corresponding
[Niri binding](reference.md#launchers).

## Make it yours and keep a way back

Review the [key reference](reference.md#keyboard-reference), choose your own
window sizes, and add monitor profiles and appearance preferences. Keep source
configuration in version control or a dotfile manager.

For each addition, check the service status and one real task before continuing.
To back out, restore that part's configuration and stop only the user services
you introduced. Do not remove the previous notification daemon or change power
policy until the replacement works in your session.

## Terminal workflow and appearance

Read the [Kitty and Zsh guide](recipes/terminal.md) for the selected colors,
portable shell files, pinned plugins, fetcher, and history/navigation workflow. The
[Neutral Slate Design page](design.md) shows the selected palette and typography
across desktop surfaces. The [Kitty and Zsh guide](recipes/terminal.md) links to
the generated [Kitty color fragment](../examples/kitty/neutral-slate.conf) and
the [common utility recipe](recipes/desktop-utilities.md). Use the
[appearance recipe](recipes/appearance.md) to review and merge the scoped native
appearance examples without replacing component behavior.
