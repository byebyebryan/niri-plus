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
`[Default Applications]` entries. Merge only the types you want into
`${XDG_CONFIG_HOME:-$HOME/.config}/mimeapps.list`, retaining unrelated groups
and preferences. Install the corresponding applications first. Chrome is chosen
separately; its `google-chrome.desktop` identifier must actually exist on your
machine. On Arch, the other applications and integration tools include:

```sh
sudo pacman -S --needed dolphin gwenview mpv ark kitty neovim xdg-utils udisks2
```

The [Neovim desktop entry](../../examples/files/nvim-terminal.desktop) opens
`kitty -e nvim` with the selected files. Inspect any existing entry before
installing it at `~/.local/share/applications/nvim-terminal.desktop`.
Check the effective defaults without opening private content:

```sh
xdg-mime query default inode/directory
xdg-mime query default application/pdf
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
Use the [portal setup steps](../setup.md#start-with-a-working-niri-session) before
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

Restore the captured MIME keys and desktop entry to undo your changes. Keep
unrelated associations, storage contents and existing authorization settings.
