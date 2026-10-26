# Keyboard, languages and candidate text

Niri owns keyboard/pointer behavior; Fcitx5 owns text composition. My setup uses
Fcitx5 with Chinese input, Source Han Sans CN fallback, and automatic Wayland
DPI/fractional scaling for candidate text. Personal dictionaries and input history
are not included in the public examples.

## Install and select engines

On Arch, the corresponding packages are:

```sh
sudo pacman -S --needed fcitx5 fcitx5-chinese-addons fcitx5-configtool fcitx5-gtk fcitx5-qt adobe-source-han-sans-cn-fonts
```

Use `fcitx5-configtool` to select your keyboard and input engines and choose your
switching shortcut. My desktop uses Mod+Space; retain or change it in the Fcitx
configuration, checking for conflicts in Niri. Start one Fcitx5 instance, either
through your existing session mechanism or this top-level Niri statement:

```kdl
spawn-sh-at-startup "command -v fcitx5 >/dev/null 2>&1 && fcitx5 -d"
```

## Match the session integration

The managed Niri environment contains `XMODIFIERS="@im=fcitx"`,
`QT_IM_MODULE="fcitx"` and `SDL_IM_MODULE="fcitx"`. Merge these keys into the
existing Niri `environment` block if you need that integration. GTK Wayland input
uses its supported protocol path; avoid adding a global `GTK_IM_MODULE` value
without checking the application and compositor requirements. Fcitx's
[Wayland guide](https://fcitx-im.org/wiki/Using_Fcitx_5_on_Wayland)
explains the toolkit differences. New environment values need newly launched
applications or the next normal session.

Merge the two settings from [classicui.conf](../../examples/input/classicui.conf)
into `~/.config/fcitx5/conf/classicui.conf`: `ForceWaylandDPI=0` and
`EnableFractionalScale=True`. Keep existing appearance preferences and engine
configuration. Noto Sans and Source Han fallback are part of the
[shared appearance](appearance.md), while native candidate rendering still needs
inspection at the display's scale.

## Verify and recover

Use disposable English and Chinese text in Chrome and Kitty. Check preedit,
candidate selection, cancellation, shortcut switching, fallback glyphs, and
candidate-window position after changing outputs. Check each laptop's scale,
not only the desktop at scale 1. Use `fcitx5-diagnose` locally when investigating;
review its environment/application details before sharing the output.

To undo the addition, restore only the environment/startup entries and Fcitx
configuration you changed. Keep your existing dictionaries and input history.
