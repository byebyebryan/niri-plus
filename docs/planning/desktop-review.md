# Desktop coverage and coherence review

Reviewed on 2026-10-24 against Niri Plus v1 and the current managed desktop
source. The first edition covers selected workflows and integrations well, but
does not yet describe the complete desktop from login through daily use and
session teardown.

This pass inspected the shared source for Starship, Snap, and Carbon and the
running configuration on Starship. Laptop behavior and visual transitions still
need a normal-use review. No desktop configuration, packages, services, or site
publication were changed.

## How much v1 presents

| Part of the setup | Current site coverage | Missing material |
| --- | --- | --- |
| Niri | Window/navigation explanation and a portable starting configuration. | Actual fixed column sizes, application rules, scaling rationale, and their relationship to the displays. |
| Kanshi | Named in the architecture and setup guidance. | Output profiles, docking transitions, internal/external display choices, scale and refresh-rate decisions. |
| SDDM | Not included in the public desktop guide. | Login/session entry, standalone theme, relation to Gtklock, and the system-level ownership boundary. |
| Gtklock | Manual-lock recipe, service example, readiness helper, and policy explanation. | The actual configured clock/password form and the stylesheet matching SDDM. |
| swayidle and desktop-power | Ownership and personal timeout choices are explained. | The full AC/battery behavior, resume and inhibition behavior, and the private helper's orchestration. |
| SwayNC | Substantial panel/notification explanation, fork recipe, config/CSS examples, and native fixture captures. | The complete personal panel in its actual theme, hardware-key feedback helpers, and host-specific volume trial. |
| Rofi and Rofi Plus | Workflow coverage, keys, and links to component guides. | Shared launcher theme and the visual relationship between applications, clipboard, SSH, Tmux, and Agent pickers. |
| Clipboard | Collector and picker recipe with self-contained helpers. | Appearance in the normal desktop and the image workflow in a real recording. |
| GTK, Qt, and application appearance | Mentioned; only SwayNC's custom stylesheet is bundled. | GTK3 theme, Libadwaita dark preference, Qt5/Qt6 styles and palettes, Dolphin integration, fonts, icons, and cursors. |
| Browser and file interaction | The personal workflow and portal checks are described. | Actual browser appearance and the file-open, upload, archive, image, and default-application experience. |
| Portals, authorization, and secrets | Basic prerequisites and portable portal example. | The actual GTK/WLR/KWallet profile and how it differs from the generic upstream-oriented example. |
| Terminal environment | Kitty and native-agent use are explained. | Terminal appearance and useful integration details, plus the boundary with shell, tmux, editor, and remote-host configuration. |
| Input methods | Fcitx5 is named in architecture. | Input switching, candidate-window appearance, and fractional-scaling behavior. |

The site needs a complete account of the desktop's components and choices before
its setup instructions can serve as a faithful recreation of the personal
environment. Portable recipes can remain a separate path for adopting pieces.

## What is already integrated

The source gives the core desktop services clear owners. Minimal services follow
the graphical session; manual locking has an independent service; notification,
clipboard, and idle configuration have separate reload boundaries. Rofi Plus
pickers share action and cancellation conventions. This is useful system design
to explain alongside appearance.

The visual baseline already has several deliberate connections:

- SDDM uses a pinned standalone Qt6 theme, derived into a neutral charcoal/gray
  palette. Gtklock repeats that palette, uses Noto Sans, and presents a native
  password form.
- GTK3 selects `adw-gtk3-dark`; GTK and the settings portal request dark
  appearance. GTK and Qt select `breeze-dark` icons.
- Qt5 uses Fusion, Qt6 uses Breeze, and both have explicit Breeze Dark palettes.
  Dolphin independently selects BreezeDark so its application scheme and Qt
  palette agree.
- Rofi and SwayNC use charcoal surfaces, blue selection/focus accents, and Inter.
- Niri requests frameless/square window geometry, uses a black background and
  blue focus ring, and gives the browser and terminals explicit widths.
- Kitty has a frameless Material Darker palette and MesloLGS Nerd Font. Neovim
  selects Tokyo Night; those are separate terminal/editor appearance choices.

Different toolkit styles and different terminal typography can be intentional.
The review should settle their roles and shared visual cues before deciding
which differences need changes.

## Concrete gaps to review

### Appearance has several sources

GTK/Qt choices live in desktop data, while Niri, Rofi, SwayNC, Gtklock, the SDDM
derivation, Kitty, and Neovim hold their own visual choices. The setup has a
recognizable dark/blue direction, but no documented contract for surface colors,
accents, density, radii, typography, icons, and cursors.

Current examples include Niri focus blue `#7fc8ff`, Rofi/SwayNC accent blue
`#42a5f5`, neutral lock/login controls, and several nearby dark background colors.
These are candidates for an explicit palette with intentional exceptions, not
evidence that every component should receive an identical stylesheet.

### Typography needs defined roles

Starship's GTK settings select Noto Sans 10. Rofi selects Inter 11; SwayNC
selects Inter with 15px notification text. SDDM and Gtklock select Noto Sans 11;
Kitty selects MesloLGS Nerd Font 11.
Qt5ct/Qt6ct currently have explicit appearance choices but no font section.

Choose the intended application/UI font roles, size scale, and terminal font
role. Then compare the perceived size and density across components and laptop
scaling. A separate monospace face is an expected part of this desktop.

### Cursor ownership needs confirmation

Starship's GTK settings select `breeze_cursors` at size 24. The managed minimal
Niri configuration has no explicit cursor block; the system `default` cursor
theme inherits Adwaita. The SDDM override has no explicit cursor selection.

That is an ownership gap to investigate, not a proven visible mismatch. Check
pointer transitions across applications, compositor space, and login/lock, then
make the intended theme and size explicit where needed. Niri has a supported
[cursor configuration](https://niri-wm.github.io/niri/Configuration:-Miscellaneous.html#cursor)
that also sets cursor environment variables for spawned applications.

### The public example and personal profile need separate explanations

The managed profile routes file dialogs/settings through GTK, screen capture
through WLR, and secrets through KWallet. V1's public portal example chooses
GNOME screencasting following upstream Niri guidance. Its portable Niri example
uses proportional widths, while the actual desktop uses fixed widths and
application-specific sizing.

Those adaptations belong in a clearly explained generic starting path. Add a
separate description of the actual personal profile and why each choice exists.
Screen-sharing behavior still needs to be checked in the browser workflow.

### Legacy naming obscures current ownership

Rofi loads a static theme named `dms-blue` and the launcher arguments refer to
its `dms-*` tokens. Some portal/preferences comments still describe DMS ownership
after its retirement. The chezmoi README also describes the former shell.

Those names do not establish a running DMS dependency. Any cleanup should keep
rollback inputs and coordinated theme-token references intact. Document current
ownership first; rename only where the maintenance benefit is clear.

## Starship evidence from this pass

- Niri, SDDM, SwayNC, desktop idle/battery services, authorization, and both
  clipboard collectors are active. Gtklock's service is inactive, as expected
  outside an active manual lock.
- Kanshi is running. The active ultrawide output is 5120 by 1440 at scale 1.
  Shared source also defines laptop, home, work, and dual-monitor profiles.
- The installed SDDM selection is the root-owned derived neutral theme; its
  override chooses Noto Sans 11 and disables custom/login backgrounds.
- GTK and GSettings agree on the dark preference, application/icon choices,
  Noto Sans font, and Breeze cursor settings. Qt provider variables are present
  in the user manager; Qt/Dolphin select their managed styles and palettes.
- MIME defaults send web/PDF to Chrome, directories to Dolphin, images to
  Gwenview, and plain text to the terminal Neovim entry.
- A scoped chezmoi diff of the inspected desktop configuration is empty.
  Unrelated status entries were preserved.

These checks establish configuration and running-service evidence. They do not
establish visual consistency, a successful password login/unlock, docking,
inhibition, suspend/resume, or equivalent live state on the laptops.

## Proposed next review and presentation scope

Use one walkthrough of the actual desktop as the review sequence:

1. Login, enter Niri, and establish displays and scale.
2. Open Chrome, download/open a file, choose a file to send, view an image, and
   check screen sharing.
3. Open terminals and agents, switch hosts, and compare navigation and focus.
4. Open each Rofi picker, clipboard history, the notification panel, and an
   authorization dialog.
5. Check manual lock/unlock and the chosen display, power, and resume behavior
   during an appropriate normal-use window.

Capture the appearance decisions as a small specification: palette and accent
roles, UI and monospace typography, density, icons/cursors, window geometry,
and deliberate exceptions. Prefer supported toolkit dark/style preferences;
[Libadwaita](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/styles-and-appearance.html)
and Qt do not share a single theme mechanism.

Classify findings as existing choices to document, concrete inconsistencies to
fix, and optional experiments. Keep source changes and per-host deployment as
separate steps after that review.

Niri Plus can then present the complete component map, a dedicated appearance
guide, and a login-to-work walkthrough. Kanshi, SDDM, the actual locker styling,
and the AC/battery behavior should become visible parts of the personal setup.

## Source pointers

The private chezmoi source at revision
`861861eaa3ff67ca65ce4577318fd52135917620` contains desktop data, Kanshi
profiles, the SDDM installer/external, GTK/Qt modifiers, Niri layout/rules, Rofi
and SwayNC styles, Gtklock configuration, and desktop-power/session services.
The inspected Niri Plus edition is
`45881d7b4d4f01625c3391aa1dbdf7745d2dbfb9`.
