# Text and image clipboard history

Cliphist stores recent text and images, and a Rofi picker lets me retrieve the
original item. `Mod+Y` opens it. My managed history is capped at 200 entries.

## Install the pieces

On Arch:

```sh
sudo pacman -S --needed cliphist wl-clipboard rofi python
```

The [example collector service](../../examples/clipboard/clipboard-history@.service)
has separate text and image instances tied to `graphical-session.target`.
Inspect its commands and the [Cliphist documentation](https://github.com/sentriz/cliphist)
before adapting it to your session.

Copy the example unit into your user-unit directory after reviewing it:

```sh
mkdir -p ~/.config/systemd/user
mkdir -p ~/.local/bin ~/.config/cliphist
install -m 755 examples/session/desktop-session-ready ~/.local/bin/desktop-session-ready
cp examples/clipboard/config ~/.config/cliphist/config
cp examples/clipboard/clipboard-history@.service ~/.config/systemd/user/
systemd-analyze --user verify ~/.config/systemd/user/clipboard-history@.service
systemctl --user daemon-reload
systemctl --user start clipboard-history@text.service clipboard-history@image.service
```

Starting the services above runs the collectors in your current session. To
start them with Niri on future logins, add the session dependencies as described
in [Niri's systemd guide](https://niri-wm.github.io/niri/Example-systemd-Setup.html).
Avoid enabling an additional collector if one is already running.

## Add the picker

The [picker example](../../examples/clipboard/rofi-clipboard) is a frozen copy of
the small helper used by my managed desktop. Its actions are Enter to copy,
Delete to remove one item, and Ctrl+Shift+Delete to request a confirmed clear.

```sh
mkdir -p ~/.local/bin
install -m 755 examples/clipboard/rofi-clipboard ~/.local/bin/rofi-clipboard
```

Ensure `~/.local/bin` is on your session's PATH and add this to Niri's `binds`:

```kdl
Mod+Y repeat=false { spawn "rofi-clipboard"; }
```

The helper uses your normal Rofi configuration. A custom theme is optional. The
shared `desktop-session-ready` helper checks the captured Wayland socket before
a collector starts.

## Check both kinds of content

Copy sample text, choose it through the picker, and paste it into a scratch
document. Repeat with a sample image. Check Delete, cancel, and Clear all using
disposable content.

Clipboard history remains local state, and can contain sensitive content copied
during normal use. Choose whether to use history on your machine accordingly.

To stop the example collectors:

```sh
systemctl --user stop clipboard-history@text.service clipboard-history@image.service
```

Remove only the session links and files you introduced when undoing the recipe.
