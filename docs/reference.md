# The desktop at a glance

The bindings below describe my managed Niri desktop. Portable examples and
component guides let you adopt the parts you want.

The [component source map](components.md) distinguishes published components,
the tested Arch reference and dated adoption evidence. Components 0.4.1, direct
device controls and the black workspace identity are installed on Carbon,
Starship and Snap. Earlier delivery records retain their historical context.

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
| Niri overview | Mod+O |
| Native key overlay | Mod+Shift+/ |
| Focus a column | Mod+H/L or Mod+Left/Right |
| Focus a window | Mod+J/K or Mod+Down/Up |
| Change column width | Mod+R |
| Maximize column | Mod+F |
| Fullscreen window | Mod+Shift+F |
| Screenshot | Print |
<!-- /niri-plus:keys -->

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

The 0.4.1 delivery on all three hosts passed exact installed-file,
native dependency, fresh callback/startup and no-write repeat checks on
2026-10-29. Physical Wi-Fi/wallet, speaker/microphone and peripheral actions
remain normal-use checks. The numbered Arch guide still selects 0.3.1 until
its updated fresh-base replay passes.

## Session and hardware ownership

| Capability | Owner | Boundary |
| --- | --- | --- |
| Login screen | SDDM | The greeter theme and root-owned assets are separate from the user session. |
| Window/session navigation | Niri | Keyboard, pointer, touchpad, window layout, and the native quit confirmation. |
| Output profiles | Kanshi | Selects monitor layouts; does not own the shell or display-manager theme. |
| Idle and power | swayidle and the session policy | Display-off, lock, suspend, lid, and battery timing remain explicit policy. |
| Manual lock | Gtklock through `desktop-lock.service` | An independent user unit keeps manual locks separate from idle reloads. |
| Portals | GTK / WLR / KWallet | GTK owns file/access/settings/notification interfaces; WLR supplies whole-monitor capture; KWallet owns secrets. |
| Input methods | Fcitx5 | Text composition and candidate UI remain separate from the keyboard layout. |
| Authorization | polkit-kde-agent | Applications request authorization; the agent supplies the graphical prompt. |
| Removable storage | UDisks2 plus polkit and filesystem support | File-manager mounting is separate from the common utility entries. |
| Brightness | Laptop backlight device | Hardware-key feedback applies to the laptop panel; external-monitor DDC/CI is separate. |

## Working setup

Crisper Neutral Slate, the pure-black workspace and the independent Balanced+
terminal are installed on Carbon, Starship and Snap. The overview surround is
charcoal so empty workspace boundaries remain visible. All 23 scoped targets
matched their reviewed source; status/diff were empty and repeat applies made
no writes. This refinement changed only Niri config and controls role metadata.
Existing UI palettes, terminal colors, packages, services and sessions were
preserved. The greeter remains
`/usr/local/share/sddm/themes/niri-neutral-fe1a7a554ed6`; SDDM was not restarted.

This is scoped deployment evidence, not a fresh-install or complete physical
acceptance record. New login/unlock appearance, application visuals, device and
backlight behavior, and docking checks remain for normal use.

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
