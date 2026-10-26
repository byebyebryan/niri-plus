# Login and the neutral greeter

SDDM starts the Niri session; Gtklock locks an already running session. They
share neutral password-form colors and Noto Sans typography, while their
authentication and configuration remain independent. The display manager's
theme is system-owned; the [Gtklock stylesheet](../../examples/theme/gtklock.css)
is a user-session appearance file.

## Retain a working login path

On Arch, the relevant packages are `sddm`, `niri`, `qt6-declarative`, `qt6-svg`,
Noto fonts and the selected Breeze cursors. Start from your distribution's
working SDDM/PAM configuration and select Niri from its session list. Check
normal password login, the Niri session and your existing wallet unlock before
changing appearance. The [SDDM configuration manual](https://man.archlinux.org/man/sddm.conf.5.en)
describes local overrides and precedence; `/etc/sddm.conf` can override files
under `/etc/sddm.conf.d`.

## Derive the theme locally

The input is the standalone [Catppuccin SDDM theme](https://github.com/catppuccin/sddm),
version 1.1.2, Mocha Blue. Niri Plus derives neutral colors from that frozen
input. The [derivation helper](../../examples/login/derive-theme.py) reads the
selected identity and writes a new preview directory. It does not install the
result or control SDDM. The upstream theme retains its own license and credits. Its pinned archive
SHA-256 is `a68fbed896d3066aec1fdaded561e8d20c855f0de4e193bdca4bc0d59ac1e333`.

From a Niri Plus clone:

```sh
work=$(mktemp -d)
curl --fail --location --output "$work/upstream.zip" \
  https://github.com/catppuccin/sddm/releases/download/v1.1.2/catppuccin-mocha-blue-sddm.zip
printf '%s  %s\n' a68fbed896d3066aec1fdaded561e8d20c855f0de4e193bdca4bc0d59ac1e333 "$work/upstream.zip" | sha256sum --check
unzip -q "$work/upstream.zip" -d "$work/upstream"
python3 examples/login/derive-theme.py \
  "$work/upstream/catppuccin-mocha-blue" "$work/derived" \
  --identity design/identity.json
```

The helper prints the generated theme directory. It rejects an existing output
directory, symlink inputs and Plasma-dependent QML. The neutral form uses the
identity's secure surface, input, button, text and error colors. Its local
`theme.conf.user` selects Noto Sans 11 and disables the two background options.
When using individually downloaded files, pass the downloaded
[identity export](../../data/identity.json) to `--identity` instead.

## Preview, then install deliberately

Preview the printed directory with your distribution's Qt6 `sddm-greeter` in
`--test-mode --theme /path/to/generated-theme`. Use a separate test display or
a windowed test environment; test mode is appearance evidence, not a real PAM
or wallet login. Inspect readable fields, focus, errors, fonts and cursor scale.

After reviewing the files, an administrator can copy that generated directory
under `/usr/local/share/sddm/themes/`, with root-owned regular files readable
by SDDM. Retain the old theme and exact override before choosing the new name.
Merge the following values into your existing local configuration, substituting
the generated directory name:

```ini
[Theme]
ThemeDir=/usr/local/share/sddm/themes
Current=niri-neutral-REPLACE_WITH_GENERATED_SUFFIX
CursorTheme=breeze_cursors
CursorSize=24
Font=Noto Sans
```

The managed profile also leaves `[General] InputMethod=` empty for its physical
keyboard login. Retain the existing value if you need an on-screen keyboard.
Keep PAM, wallet integration, display-server and scaling choices with their
current owners. Schedule the display-manager configuration change for a normal
login opportunity; restarting SDDM ends graphical sessions. The current fleet
theme was installed without restarting SDDM, so real greeter acceptance remains
a separate check.

To undo the theme choice, restore the captured override and keep the preceding
theme available. Configure manual locking through the
[session recipe](session.md); selecting an SDDM theme does not configure Gtklock.
