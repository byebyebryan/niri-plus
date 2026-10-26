# Niri Plus identity

**Selected identity: Neutral Slate. One theme for the initial reference.**

The [contrast study](contrast.md) previews the next revision: distinct desktop
and terminal palettes within this identity. The split is agreed; the exact
proposal values remain under review. This specification records the current
selected baseline until that review is complete.

Use the reviewed warm charcoal/off-white surfaces, Clear Blue accent,
Noto Sans UI, and Meslo terminal. Graphite Blue is retained as a future
alternative. The public design presentation should show these choices in use.

The selected candidate and complete terminal ANSI mapping live in
[identity.json](../../design/identity.json). The site builder projects that
single selection into [public identity data](../../data/identity.json), site
colors, typography specimens, and a [generated Kitty fragment](../../examples/kitty/neutral-slate.conf).
The identity is selected as a design; none of this establishes deployed
appearance.

## Palette roles

| Role | Selected value |
| --- | --- |
| canvas | `#151719` |
| surface | `#202326` |
| raised | `#2b3034` |
| input | `#191c1f` |
| border | `#535d66` |
| text | `#efefec` |
| secondary | `#b9bec3` |
| muted | `#9ba4ab` |
| accent | `#83b8f5` |
| accent ink | `#151b20` |
| focus | `#a6ceff` |
| selection | `#2b425b` |
| selection text | `#efefec` |
| warning | `#ddbb80` |
| error | `#e5a09b` |
| success | `#b8c9a4` |
| secure surface | `#202020` |
| secure input | `#303030` |
| secure button | `#d0d0d0` |

Use focus, selected-row fill, and visible control boundaries to distinguish the
active operation. Preserve semantic status colors with labels and the existing
rules for unknown values and absent hardware. Keep authentication surfaces
neutral. Start with the reviewed values and judge native legibility before
adjusting them.

## Typography

| Role | Neutral Slate choice | Implementation interpretation |
| --- | --- | --- |
| Ordinary UI | Noto Sans, 11pt, regular | Native family name must resolve explicitly; browser specimens must use the selected packaged Noto weights. |
| Secondary UI | Noto Sans, 10pt | Keep long device names readable and ellipsize with a full-name tooltip. |
| Group titles | Noto Sans, 13pt, medium | Use restrained hierarchy rather than large dashboard headings. |
| Lock clock | Noto Sans, 48pt, regular | Preserve the existing clock scale while joining the UI family. |
| Terminal | MesloLGS Nerd Font, 11pt | Retain current glyph behavior and explicit Nerd Font symbol mappings. |
| CJK fallback | Source Han Sans CN | Verify preedit, candidate windows, mixed Latin/CJK labels, and browser/terminal input. |
| Numbers | Tabular where supported | Preserve stable percentage width, two-digit padding, and ETA alignment. |

At 96 DPI, 11pt corresponds to about 14.67 CSS pixels. That is a conversion for
specimens, not a command to paste the same number into every toolkit. Compare
perceived size under native scale and the laptops' fractional scale.

The terminal extension maps background, foreground, cursor, selection, and the
full sixteen ANSI slots to the selected identity. Red, green, and yellow retain
error, success, and warning roles; blue follows accent/focus. Subdued violet and
cyan fill the other colored slots, while neutral slots follow canvas, muted,
secondary, and main text. Zsh prompt roles follow those meanings; extended
colors, syntax highlighting, and suggestions need native review.
Explicit RGB editor/provider syntax remains independently owned. See the
[terminal and Zsh guide](../recipes/terminal.md) for the current workflow,
source/extraction boundary, and acceptance tasks.

## Geometry and effects

- Preserve 4px Niri gaps, square tiled windows, the 4px focus ring, fixed width
  presets 960/1280/1600/1920, 960px terminal columns, and 1600px browser columns.
- Use a spacing scale of 4/8/12/16/24/32 logical pixels. Target 32px ordinary
  shell controls, with native toolkit exceptions checked for perceived density.
- Keep outer shell windows/panels square. Use a small 3px control radius and
  4px internal-card radius where the component supports it.
- Preserve the 448px notification panel and Rofi's 52em launcher width, with
  viewport constraints on smaller logical displays.
- Proposed owned-overlay opacity is 96%; native application interiors remain
  opaque. Judge this against the current more translucent overlays in native
  previews before adoption.
- Use a flat canvas initially, no new wallpaper dependency, blur, or ambient
  animation. Existing motion is evaluated separately; this pass does not change
  Kitty's cursor trail or Niri's animation behavior.

## Icons and cursor

Retain Breeze Dark icons. Use 16/22/24px roles according to context, rather than
scaling one bitmap. Make `breeze_cursors` at 24 logical pixels explicit across
Niri, GTK, Qt/environment paths as needed, and SDDM. Verify scaling and pointer
transitions; the current source gap is not a proven visible mismatch.

## Interaction and feedback

Keep Rofi Plus's existing Up/Down row selection, Tab/Shift+Tab action cycling,
Enter activation, and Escape/Ctrl+G cancellation. Keep native focus traversal
in panel controls and preserve their own keys. Focus remains visible in both
keyboard and mouse workflows.

Hardware feedback remains replaceable, transient, silent, and 1.5 seconds long,
without entering history. Normal notifications retain their current timeout
and sender rules; critical alerts remain until dismissed. Battery/tooltips and
hardware availability keep their existing semantics. Visual redesign is not a
reason to change them.

## Native implementation limits

GTK3 uses the current adw-gtk3-dark baseline. Libadwaita follows supported dark
appearance/accent mechanisms. Qt5 uses Fusion; Qt6 uses Breeze, with explicit
palettes and application scheme choices. Do not install global unsupported CSS
or assume an exact shell hex value can be imposed on every application.

Native applications should agree on dark preference, font roles, icon/cursor
families, dialog ownership, and selection/focus character. Small native color
and widget differences are accepted and documented. Web content and provider
application internals remain under their respective owners.

The isolated native samples demonstrate actual GTK3/Qt6 widgets and typography.
They are reference samples, not proof that the complete proposed theme is
implemented or that real greeter, lock, portal, or authorization flows work.
Comparison compositions illustrate the visual roles; they do not require
rewriting the native greeter, locker, file chooser, or application layouts.

## Public identity and deployment ownership

Niri Plus should own the versioned public identity values and reference assets.
Chezmoi should pin a reviewed Niri Plus archive or raw identity artifact and
project the selected values into owned configuration. Host-specific policy and
application-local preferences stay private and separately owned.

Start with a small token file and component adapters where repeated values
justify them. Do not introduce a theme service, package manager, runtime theme
daemon, or monorepo migration. The [implementation plan](implementation-plan.md)
specifies the proposed adoption boundary.
