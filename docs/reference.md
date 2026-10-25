# The desktop at a glance

The bindings below describe my managed Niri desktop. Portable examples and
component guides let you adopt the parts you want.

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

`Mod+D` opens the application list. The portable entries for Network,
Bluetooth, Audio, and Session are documented in the
[desktop utility recipe](recipes/desktop-utilities.md). They rely on their
named service/tool owners and keep lock, logout confirmation, and power actions
in their existing native paths.

## Session and hardware ownership

| Capability | Owner | Boundary |
| --- | --- | --- |
| Login screen | SDDM | The greeter theme and root-owned assets are separate from the user session. |
| Window/session navigation | Niri | Keyboard, pointer, touchpad, window layout, and the native quit confirmation. |
| Output profiles | Kanshi | Selects monitor layouts; does not own the shell or display-manager theme. |
| Idle and power | swayidle and the session policy | Display-off, lock, suspend, lid, and battery timing remain explicit policy. |
| Manual lock | Gtklock through `desktop-lock.service` | An independent user unit keeps manual locks separate from idle reloads. |
| Portals | xdg-desktop-portal backends | File selection and screen capture use their selected GTK/GNOME backends. |
| Input methods | Fcitx5 | Text composition and candidate UI remain separate from the keyboard layout. |
| Authorization | polkit-kde-agent | Applications request authorization; the agent supplies the graphical prompt. |
| Removable storage | UDisks2 plus polkit and filesystem support | File-manager mounting is separate from the common utility entries. |
| Brightness | Laptop backlight device | Hardware-key feedback applies to the laptop panel; external-monitor DDC/CI is separate. |

## Working setup

Neutral Slate with Clear Blue accents was delivered in order to Carbon, Starship, and Snap. Each scoped
pass had zero remaining file and hook differences on repeat; the Niri, Kitty,
SwayNC, and native sessions remained in place. The separately managed SDDM
greeter theme is installed at
`/usr/local/share/sddm/themes/niri-neutral-ab2469ae2948`.

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

- [Niri configuration](../examples/niri/config.kdl): portable window layout and
  base bindings, with no personal paths or service startup hooks.
- [Portal preferences](../examples/portals/niri-portals.conf): GTK file picker and
  GNOME screencasting, following upstream guidance.
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
