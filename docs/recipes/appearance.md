# Neutral Slate appearance files

These are appearance-only examples for Neutral Slate with Clear Blue accents.
The stylesheets and toolkit palettes match the canonical chezmoi adapters;
the Niri fragment is authored from the canonical identity. Each manifest entry records the SHA-256
of `design/identity.json` so the build rejects a stale palette association.
They are public examples, not proof of native installation or deployment.

## Files and owners

| Download | Surface | Scope |
| --- | --- | --- |
| [Niri focus and background fragment](../../examples/theme/niri-neutral-slate.kdl) | Niri | Canvas and focus-ring colors. Merge the two settings into the existing `layout` block; keep its widths, gaps, border mode, shadows, and other layout settings. |
| [Rofi theme](../../examples/theme/neutral-slate.rasi) | Rofi launcher | Theme declarations and colors only. Existing actions, key bindings, and launcher configuration remain yours. |
| [SwayNC stylesheet](../../examples/theme/swaync.css) | Selected SwayNC fork | CSS only; imports the packaged base stylesheet. The fork still owns panel behavior and widget structure. |
| [Gtklock stylesheet](../../examples/theme/gtklock.css) | Gtklock | Password-form appearance only. Authentication, lock-service lifetime, and power behavior stay with their current owners. |
| [Qt 5 palette](../../examples/theme/qt5-palette.conf) | qt5ct | QPalette colors only. Keep the selected Fusion style and portal dialog setting. |
| [Qt 6 palette](../../examples/theme/qt6-palette.conf) | qt6ct | QPalette colors only. Keep the selected Breeze style and portal dialog setting. |
| [KDE color scheme](../../examples/theme/NeutralSlate.colors) | KDE / native Qt focus | Includes KDE `Colors:*` role groups. It is a color scheme file, not a replacement for `kdeglobals`. |

The SDDM greeter is not in this bundle. Its root-owned theme and assets remain
separately managed and must be reviewed in their own context.

## Dependencies and native variation

Use Noto Sans at 11pt for UI text, Source Han Sans CN as the CJK fallback, and
MesloLGS Nerd Font at 11pt for terminal text. Breeze Dark icons and
`breeze_cursors` are separate dependencies; the Niri fragment does not select
or install them. The website exports the [Noto Sans license](../../assets/licenses/noto.txt),
[Meslo license](../../assets/licenses/meslo.txt), and [Source Han license](../../assets/licenses/source-han.txt).

The SwayNC stylesheet targets the selected fork and its dashboard widgets. It
does not recolor other GTK programs. Applications that follow Adwaita or
Libadwaita keep their own supported colors and may look different from the
specimens. Gtklock has its own explicit stylesheet because it owns a separate
password surface.

Qt palettes set `QPalette` roles; they do not set Qt style, icon theme, portal
dialogs, or KDE's named focus colors. KDE also reads its owned `[Colors:*]`
groups from `kdeglobals`. Install `NeutralSlate.colors` under
`${XDG_DATA_HOME:-$HOME/.local/share}/color-schemes/`. Merge its `[Colors:*]` and
`[ColorEffects:*]` sections into your existing
`${XDG_CONFIG_HOME:-$HOME/.config}/kdeglobals`, keeping unrelated groups and
preferences. If KDE System Settings is already available, selecting the scheme
there can perform the native color-group update. The corresponding targeted
font and scheme values are:

```ini
[General]
ColorScheme=NeutralSlate
font=Noto Sans,11,-1,5,50,0,0,0,0,0
fixed=MesloLGS Nerd Font,11,-1,5,50,0,0,0,0,0
```

Merge only those keys into the existing `[General]` group if you edit the file
by hand. Keep the `[Colors:*]` groups produced by the selected `.colors` file;
do not replace the whole `kdeglobals` file. The serialized font weight `50` is
the legacy Qt value used by these ten-field strings.

## Merge and preview

1. Download the fragment for the surface you want to review and retain a copy
   of its current configuration. Merge only the listed appearance layer; do
   not replace launcher actions, notification config, lock settings, or service
   definitions.
2. Preview the Rofi theme in a one-off launcher window before changing the
   normal theme selection:

   ```sh
   rofi -show drun -theme "$PWD/examples/theme/neutral-slate.rasi"
   ```

3. For SwayNC and Gtklock, merge the CSS into the stylesheet path already used
   by that component, then preview through its normal owner-managed reload or
   isolated session. Do not alter the independent lock unit or authentication
   configuration to preview colors.
4. For Qt 5/6, place each palette under the corresponding `qt5ct/colors` or
   `qt6ct/colors` directory and select it through that settings tool. Restart a
   test Qt application to inspect focus, selected, disabled, and dialog states.
   Keep the existing platform styles and portal choices.
5. For KDE, install and merge the `.colors` file as described above, then confirm its `Colors:*`
   groups and the selected fonts in the existing `kdeglobals`. For Niri, merge
   the fragment into the current `layout` block and validate the full config
   before using the normal reload path.

Apply one surface at a time and review its active, inactive, focused, selected,
and disabled states. These files contain no input bindings, service startup,
power policy, session ownership, or application action changes.
