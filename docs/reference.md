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

## Working setup

The managed source selects the minimal Niri shell with SwayNC and Gtklock on
Starship, Snap, and Carbon. This is a dated source configuration record, rather
than a claim that these public recipes have been exercised on a fresh install.

<!-- niri-plus:snapshot -->
The private machine configuration revision and selected immutable artifacts are recorded in
[the source snapshot](../data/setup.json). Public examples identify their
origin in [the example manifest](../examples/manifest.json). All files needed by
these example recipes are included here; access to my private dotfiles is not
required.
<!-- /niri-plus:snapshot -->

## Examples and verification

- [Niri configuration](../examples/niri/config.kdl): portable window layout and
  base bindings, with no personal paths or service startup hooks.
- [Portal preferences](../examples/portals/niri-portals.conf): GTK file picker and
  GNOME screencasting, following upstream guidance.
- [Clipboard collector](../examples/clipboard/clipboard-history@.service) and
  [picker](../examples/clipboard/rofi-clipboard): sample service and frozen helper.
- [Manual lock service](../examples/session/desktop-lock.service): a focused
  Gtklock service example.

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
- [Media sources and attribution](../assets/provenance.json)
