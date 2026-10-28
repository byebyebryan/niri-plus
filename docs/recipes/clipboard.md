# Text and image clipboard history

Cliphist stores recent text and images, and a Rofi picker lets me retrieve the
original item. `Mod+Y` opens it. The selected minimal-Niri profile caps history
at 200 items through its shared Cliphist config.

## Install one collector profile

On Arch:

```sh
sudo pacman -S --needed cliphist wl-clipboard rofi python
```

Use the verified Arch walkthrough output in `$STAGE`. It contains the selected
generated unit, its 200-item config, and the shared readiness helper. This
service variant relies on Niri's graphical-session links and has no independent
`[Install]` target:

Inspect the config and unit targets before installing. Back up and merge any
existing files at those paths rather than replacing their settings.

```sh
install -Dm755 "$STAGE/source/examples/session/desktop-session-ready" \
  "$HOME/.local/bin/desktop-session-ready"
install -Dm644 "$STAGE/source/examples/clipboard/config" \
  "$HOME/.config/cliphist/config"
install -Dm644 \
  "$STAGE/source/examples/clipboard/profiles/minimal-niri/clipboard-history@.service" \
  "$HOME/.config/systemd/user/clipboard-history@.service"
systemd-analyze --user verify \
  "$HOME/.config/systemd/user/clipboard-history@.service"
systemctl --user daemon-reload
```

Do not also install the authored portable
[`clipboard-history@.service`](../../examples/clipboard/clipboard-history@.service).
That unit is a separate profile and starts a different collector command.

## Add the picker and session dependencies

Install the generated picker from the same verified source snapshot:

```sh
install -Dm755 "$STAGE/source/examples/clipboard/rofi-clipboard" \
  "$HOME/.local/bin/rofi-clipboard"
```

Confirm Niri's systemd user units are active, add only the two clipboard
instances to `niri.service`, and start them in the current session:

```sh
systemctl --user is-active niri.service graphical-session.target
systemctl --user add-wants niri.service \
  clipboard-history@text.service clipboard-history@image.service
systemctl --user daemon-reload
systemctl --user start \
  clipboard-history@text.service clipboard-history@image.service
```

Add this binding to the existing Niri `binds` block and validate the complete
configuration:

```kdl
Mod+Y repeat=false { spawn "rofi-clipboard"; }
```

The shared readiness helper checks that the captured Wayland socket responds;
it does not identify the compositor. Keep `~/.local/bin` in the graphical
session `PATH`.

## Check and recover

Copy disposable text and an image, select each from the picker, and paste the
original into a scratch document. Check Delete, cancel, and Clear all with
disposable history entries. Clipboard history stays local and can contain
sensitive content copied during normal use.

To back out, stop the two instances and remove only the exact wants links and
files you introduced:

```sh
systemctl --user stop clipboard-history@text.service clipboard-history@image.service
rm -f "$HOME/.config/systemd/user/niri.service.wants/clipboard-history@text.service"
rm -f "$HOME/.config/systemd/user/niri.service.wants/clipboard-history@image.service"
```

Retain or remove the Cliphist database separately if you want to keep or erase
the local history.
