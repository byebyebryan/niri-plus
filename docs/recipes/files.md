# Files, default applications and removable media

Chrome and Dolphin make ordinary downloads, uploads and file operations feel
natural alongside terminal work. These are the personal default-application
roles; choose replacements where your workflow differs.

| Content | Application |
| --- | --- |
| Web links, HTML and PDF | Chrome |
| Directories | Dolphin |
| Images | Gwenview |
| Audio and video | mpv |
| Archives | Ark |
| Plain text and code | Neovim in Kitty |

## Merge default associations

The [MIME example](../../examples/files/mimeapps.list) contains the selected
`[Default Applications]` entries. In the main walkthrough, `SOURCE` names the
verified example tree. Install the corresponding applications first. Chrome is
chosen separately; its `google-chrome.desktop` identifier must exist on your
machine. On Arch, the other applications and integration tools include:

```sh
sudo pacman -S --needed dolphin gwenview mpv ark kitty neovim xdg-utils udisks2
```

The [Neovim desktop entry](../../examples/files/nvim-terminal.desktop) opens
`kitty -e nvim` with the selected files. Inspect any existing entry before
installing it. From the walkthrough, install only when that target is absent:

```sh
NIRI_NVIM_ENTRY="$HOME/.local/share/applications/nvim-terminal.desktop"
if [ -e "$NIRI_NVIM_ENTRY" ] || [ -L "$NIRI_NVIM_ENTRY" ]; then
  printf '%s\n' "Inspect existing entry: $NIRI_NVIM_ENTRY"
else
  install -Dm644 "$SOURCE/examples/files/nvim-terminal.desktop" "$NIRI_NVIM_ENTRY"
fi
```

After Chrome and the file applications are installed, apply the staged defaults
with `xdg-mime`. This updates only the listed default MIME keys in the normal
user database and retains unrelated associations. If you prefer other
applications, edit the staged example or omit those rows before running it:

```sh
python3 - "$SOURCE/examples/files/mimeapps.list" <<'PY'
import configparser
import subprocess
import sys

defaults = configparser.ConfigParser(interpolation=None)
defaults.optionxform = str
if not defaults.read(sys.argv[1], encoding="utf-8"):
    raise SystemExit("could not read staged MIME example")
for mime_type, desktop_list in defaults["Default Applications"].items():
    desktop_id = desktop_list.split(";", 1)[0]
    if not desktop_id:
        raise SystemExit(f"no desktop ID for {mime_type}")
    subprocess.run(["xdg-mime", "default", desktop_id, mime_type], check=True)
PY
```

The script uses the example's first desktop ID for each type. It does not set
browser download behavior or alter other MIME groups. Check the effective
defaults without opening private content:

```sh
xdg-mime query default x-scheme-handler/https
xdg-mime query default application/pdf
xdg-mime query default inode/directory
xdg-mime query default image/png
xdg-mime query default text/plain
```
Desktop launchers, MIME associations and the browser's download preferences are
separate settings. An application missing its desktop entry cannot serve as an
effective default.

## Browser and portal checks

The selected portal profile is GTK for file/access/settings/notification
interfaces, WLR for whole-monitor screen sharing, and KWallet for secrets.
Dolphin remains the file manager; choosing it does not require the KDE picker.
Use the [portal setup steps](../setup-agent.md#3-install-the-first-session-packages) before
checking browser dialogs. The portable portal example preserves your existing
secret backend; the personal KWallet choice is recorded in the reference.

Download disposable PDF, image, video and archive samples, open them from
Dolphin, and check Open with. Select a sample file through a browser upload
dialog. If you use sharing, check a nonprivate monitor in a test call and verify
that stopping sharing releases it. Individual-window sharing is outside this
selected baseline.

## Removable media

UDisks2 and polkit provide the native mounting/authorization path behind Dolphin.
Install filesystem support for the media you actually use. UDisks2 may be
D-Bus activated, so an idle/inactive service alone does not establish a fault.
The [UDisks project](https://github.com/storaged-project/udisks) documents its
storage service. Use a disposable owned drive to check mounting, a sample
read/write and safe unmounting; existing disk formatting is not part of setup.
The targeted development-copy check used a new 64 MiB ext4 volume labeled with
serial `NIRI_GUIDE_SCRATCH`: the native polkit prompt allowed the ordinary user
to mount it, a user-owned writable subdirectory passed a byte check, and the
volume unmounted cleanly. This guest result does not qualify physical media or
authorize formatting an existing drive.

Restore the captured MIME keys and desktop entry to undo your changes. Keep
unrelated associations, storage contents and existing authorization settings.
