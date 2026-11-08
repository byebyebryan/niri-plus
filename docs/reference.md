# The desktop at a glance

The bindings below describe my managed Niri desktop. Portable examples and
component guides let you adopt the parts you want.

The [component source map](components.md) distinguishes published components,
the Arch reference and dated adoption evidence. Components 0.4.3, SwayNC
0.12.6-18 and the black-workspace sidebar identity are delivered on Carbon,
Starship and Snap through chezmoi, as recorded in the
[managed-host delivery record](../data/setup.json). The numbered Arch install
target now uses SwayNC 0.12.6-18 from fork release 1. The dated fresh-guest
acceptance remains package 17 evidence. Package 18 retains package 17's
byte-identical runtime paths (`src/`, `data/`, `meson.build`, unchanged
`meson_options.txt`, `man/`), but the pin reset is not a new full fresh-Arch or
physical replay ([sync receipt](planning/swaync-reference-sync-20261107.md)).
Earlier delivery records retain their historical context.

Published components 0.9.2 include the
[optional unified session screen](recipes/session.md#optional-unified-session-screen).
It replaces Ctrl+Alt+Delete with the action grid only when its profile is selected.
The baseline bindings below and dated fleet evidence do not establish adoption
of that screen.

## Keyboard reference

`Mod` is Niri's compositor modifier, normally Super on a regular session.

<!-- niri-plus:keys -->
| Task | Binding |
| --- | --- |
| Applications | Mod+D |
| Terminal | Mod+Return or Mod+T |
| Browser | Mod+B |
| File manager | Mod+E |
| SSH Plus | Mod+S |
| Tmux Plus | Mod+G |
| Agent Plus | Mod+A |
| Notification panel | Mod+N |
| Clipboard history | Mod+Y |
| Manual lock | Ctrl+Alt+Delete |
| Turn off displays (Niri default) | Mod+Shift+P |
| Niri overview | Mod+O |
| Native key overlay | Mod+Shift+/ |
| Focus a column | Mod+H/L or Mod+Left/Right |
| Focus a window | Mod+J/K or Mod+Down/Up |
| Change column width | Mod+R |
| Maximize column | Mod+F |
| Fullscreen window | Mod+Shift+F |
| Screenshot | Print |
<!-- /niri-plus:keys -->

`Mod+Shift+P` uses Niri's immediate `power-off-monitors` action; fresh input wakes
the displays. The [away-mode recipe](recipes/away-mode.md) offers a separate
manual latch and an optional replacement binding. Select that profile
explicitly if you want the latch on this key.

For the optional screen, Ctrl+Alt+Delete instead launches
`desktop-session-menu --screen`. Lock, Display off and Suspend form the first
row; Log out, Restart and Shut down form the second. Every action has a
five-second cancellable countdown as its confirmation, with automatic execution
at expiry. Display off does not add a
lock; Lock always locks then turns displays off. Its profile replaces the
baseline lock binding and is unavailable while locked.

## Launchers

Plain applications use `rofi -show drun`. The clipboard helper is a small
standalone program. The Rofi Plus tools each supply their own launch contract.

| Picker | Component guide | Main behavior |
| --- | --- | --- |
| SSH Plus | [Get started](https://github.com/byebyebryan/rofi-ssh-plus/blob/main/docs/getting-started.md) | Recent hosts and explicit SSH access. |
| Tmux Plus | [Get started](https://github.com/byebyebryan/rofi-tmux-plus/blob/main/docs/getting-started.md) | Browse sessions across configured host scopes. |
| Agent Plus | [Get started](https://github.com/byebyebryan/rofi-agent-plus/blob/main/docs/getting-started.md) | Open or focus dedicated native agent TUI windows. |

Up/Down move through rows. Tab/Shift+Tab cycle named actions while keeping the
filter and row. Enter runs the visible action. Escape/Ctrl+G cancel. Tmux's
Left/Right changes host scope; SSH and Agent keep their own filter-editing
behavior. Use the full launcher instructions rather than copying only a binary
name.

## Common utilities

`Mod+D` opens the application list. **Network, Audio and Bluetooth** open the
[direct Rofi controls](recipes/rofi-controls.md): search devices, cycle named
actions with Tab/Shift+Tab and run the visible action with Enter. Open selects
a device page; Details explains its native state. Current/default devices have
green framing, while blue marks keyboard selection. The action strip and
status have separate places.

Network retains `nm-connection-editor`, Audio retains `pavucontrol`, and
Bluetooth retains `bluetoothctl` for deeper settings and recovery. Native
providers keep device ownership. **Session** retains its existing lock, logout
and confirmed power actions; see the [utility recipe](recipes/desktop-utilities.md).

The historical 0.4.1 delivery passed exact installed-file, native dependency,
fresh callback/startup and no-write repeat checks on 2026-10-29; its result
remains in the [0.4.1 delivery history](../data/history/setup-0.4.1.json).
Physical Wi-Fi/wallet, speaker/microphone and peripheral actions remain
normal-use checks. The [Arch agent guide](setup-agent.md) now targets
0.4.3/SwayNC 0.12.6-18; the scoped fresh-base qualification is in the sync
receipt linked above.
The [0.4.1 fresh-base receipt](planning/black-workspace-receipt.md#fresh-arch-reference)
records only the earlier guest tasks and documented VirtIO sharing branch.

## Session and hardware ownership

| Capability | Owner | Boundary |
| --- | --- | --- |
| Login screen | SDDM | The greeter theme and root-owned assets are separate from the user session. |
| Window/session navigation | Niri | Keyboard, pointer, touchpad, window layout, and the native quit confirmation. |
| Output profiles | Kanshi | Selects monitor layouts; does not own the shell or display-manager theme. |
| Idle and power | swayidle and the session policy | Display-off, lock, suspend, lid, and battery timing remain explicit policy. |
| Manual display-away | Optional `desktop-away` companion | Explicit away entry keeps displays off until input returns; it does not own automatic idle or suspend. |
| Manual lock | Gtklock through `desktop-lock.service` | An independent user unit keeps manual locks separate from idle reloads. |
| Portals | GTK / WLR / KWallet | GTK owns file/access/settings/notification interfaces; WLR supplies whole-monitor capture; KWallet owns secrets. |
| Input methods | Fcitx5 | Text composition and candidate UI remain separate from the keyboard layout. |
| Authorization | polkit-kde-agent | Applications request authorization; the agent supplies the graphical prompt. |
| Removable storage | UDisks2 plus polkit and filesystem support | File-manager mounting is separate from the common utility entries. |
| Brightness | Laptop backlight device | Hardware-key feedback applies to the laptop panel; external-monitor DDC/CI is separate. |

## Working setup

Crisper Neutral Slate, the pure-black workspace, Balanced+ terminal and the
components0.4.3/SwayNC17 sidebar are delivered on Carbon, Starship and Snap.
The sidebar uses a unified information surface and separate notification cards
with 75% fill; chezmoi selects host layout and policy. Carbon's delivery completed
on 2026-11-07. Exact installed checks, retained preimages and recovery artifacts
stay in the private consumer receipts. This public sync changes the reference
and showcase, with no new fleet deployment.

The earlier black-workspace-only rollout changed Niri configuration and controls
role metadata; its 23-target/no-write repeat results remain in
[the dated 0.4.1 delivery history](../data/history/setup-0.4.1.json). Fresh guest,
managed delivery, physical hardware and human visual acceptance are separate.

<!-- niri-plus:snapshot -->
The producer, consumer, host results, and selected identity hash are recorded in
[the delivery record](../data/setup.json). Public examples identify their
origin in [the example manifest](../examples/manifest.json). All files needed by
these example recipes are included here; access to my private dotfiles is not
required.
<!-- /niri-plus:snapshot -->

## Appearance

The [Neutral Slate Design page](design.md) shows the selected palette, type,
and launcher, information, terminal, and login/lock surfaces. Its illustrations
are samples, not native or deployed screenshots. The [terminal recipe](recipes/terminal.md)
links to the generated [Neutral Slate Kitty fragment](../examples/kitty/neutral-slate.conf).
The [appearance recipe](recipes/appearance.md) links to the Niri, Rofi, SwayNC,
Gtklock, Qt 5/6, and KDE color examples and describes their owners and merge
boundaries.

## Examples and verification

The [Arch walkthrough](setup.md) gives the order. Focused guides cover
[display profiles](recipes/displays.md), [SDDM login](recipes/login.md),
[idle/power and authorization](recipes/session.md),
[hardware feedback](recipes/hardware-feedback.md), [input methods](recipes/input.md),
and [files/default applications](recipes/files.md).

- [Niri configuration](../examples/niri/config.kdl): portable window layout and
  base bindings, with no personal paths or service startup hooks.
- [Portal preferences](../examples/portals/niri-portals.conf): GTK file picker and
  notification integration, with WLR whole-monitor sharing.
- [Clipboard collector](../examples/clipboard/clipboard-history@.service) and
  [picker](../examples/clipboard/rofi-clipboard): sample service and frozen helper.
- [Manual lock service](../examples/session/desktop-lock.service): a focused
  Gtklock service example.
- [Optional away-mode binding](../examples/session/profiles/minimal-niri/away-mode.kdl)
  and [installation recipe](recipes/away-mode.md): keep it separate from automatic
  idle and suspend policy.
- [Common utility recipe](recipes/desktop-utilities.md): portable application
  launchers and Session power-policy example.

The site build checks its routes, links, example inventory, and asset hashes.
Browser checks cover responsive layout, keyboard controls, walkthrough behavior,
and reading with JavaScript disabled. Niri and shell examples have separate
syntax checks. Authentication, hardware behavior, suspend, and a clean-machine
installation require checks on the target system.

## Sources and further reading

- [Niri documentation](https://niri-wm.github.io/niri/)
- [The SwayNC fork](https://github.com/byebyebryan/SwayNotificationCenter)
- [Fleet Plus](https://dev.byebyebryan.com/fleet-plus/)
- [Cliphist](https://github.com/sentriz/cliphist)
- [Gtklock](https://github.com/jovanlanik/gtklock)
- [UDisks2](https://github.com/storaged-project/udisks)
- [Media sources and attribution](../assets/provenance.json)
