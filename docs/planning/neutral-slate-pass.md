# Neutral Slate implementation and site plan

Neutral Slate is the selected Niri Plus identity. Keep its reviewed palette,
Noto Sans UI, and MesloLGS Nerd Font terminal typography. Graphite Blue remains
a recorded alternative for later; this pass maintains one theme.

The pass should produce a coherent daily desktop, portable reference material,
and a visual Design page showing the theme in use. The public presentation
should concentrate on appearance, interaction, and setup. Keep palette selection
history in internal design notes.

## Fleet delivery checkpoint - 2026-10-25

The selected Neutral Slate appearance was delivered from consumer
`46ab3eb4d44efe71c9cd7815a59f959742a5103c`, using producer
`4d4066b1916cf49e14d146cd4ef1a337c7e9e5da` and canonical identity SHA-256
`0c9135b5d22f796e076c1373cddf57ad0d947d1b7feb80b4f1c3f0b3f4f19b1c`. The
rollout completed Carbon, Starship, then Snap. All three scoped passes ended
with zero file and hook differences; repeat applies were no-ops. Niri, Kitty,
SwayNC, and native sessions remained in place. The root-owned SDDM theme is
installed at `/usr/local/share/sddm/themes/niri-neutral-ab2469ae2948`.

New login/unlock appearance, application visuals, device/backlight behavior,
and docking checks remain for normal use. The Design page's labeled specimens
do not claim those checks. The sanitized receipt is
[`design/evidence/neutral-slate-fleet-delivery.json`](../../design/evidence/neutral-slate-fleet-delivery.json);
it excludes process identifiers and session contents. Website publication is a
separate step.

## Implementation checkpoint - 2026-10-24

The source/reference pass is implemented locally. This checkpoint covers
stages 1-4 and the isolated portion of stage 5. Host adoption and public
publication remain separate steps.

| Area | Current evidence |
| --- | --- |
| Identity and site | Selected Neutral Slate, Noto/Meslo assets, visual Design gallery, palette/type specimens and generated Kitty export. |
| Native source | Opt-in chezmoi adapters for Niri, Rofi, SwayNC, Gtklock, GTK/Qt/KDE, Kitty and derived SDDM. No hosts selected. |
| Terminal and utilities | Portable Zsh core with four pinned archives; Network, Bluetooth, Audio and Session examples and recipes. |
| Source/native checks | Full chezmoi suite; three-host renders and baseline parity; native GTK/Qt/Rofi/Kitty checks and SDDM test mode. |
| Remaining acceptance | Normal desktop adoption, physical devices/scaling/login/unlock/resume, accepted daily-desktop captures and public publication. |

The private consumer records the exact identity SHA-256 in
`deployments/niri-plus.json`, with `enabledHosts: []` and unpublished source
metadata. Templates preserve the previous output while unselected. No live
apply, session restart, commit, push or public site publication is part of this
checkpoint. The durable preview receipt is recorded in
`design/evidence/neutral-slate-source-pass.json`.
[Open the source-pass preview](http://starship:8787/reports/9f609b9f397475c80a17eca07a42fcf6a0b9537d2d3b707f08ba2ab097cda777/design/).
It includes an isolated native-render appendix and was checked from Carbon.

The remaining sections preserve the implementation contract and rollout gates.

## Fleet rollout planning checkpoint - 2026-10-25

Snap, Starship and Carbon have been inspected for the next deployment pass.
All have the required fonts/packages and no managed drift on the existing theme
targets. Theme admission remains empty. The canonical private procedure is in
chezmoi `docs/niri-plus-neutral-slate-rollout.md`: separate utility admission,
reload SwayNC CSS in place, publish an immutable producer commit, then perform
scoped delivery on Carbon, Starship and Snap in that order. Bryan is using Carbon
and wants to start there, with ordinary issues/gaps fixed during adoption rather
than waiting for complete qualification. Keep per-host owned settings/root
preimages and distinguish installed, active-session and physical acceptance.
Carbon is the first feedback surface; all three hosts remain delivery targets.
Disruptive automated GUI tests still belong on unattended Snap. This checkpoint
adds planning only; no host has adopted the theme.

## Selected identity

Use Neutral Slate as reviewed, without adding Graphite Blue accents in advance.
Judge focus and selection in native surfaces before making further adjustments.

| Role | Value |
| --- | --- |
| Canvas | `#151719` |
| Surface | `#202326` |
| Raised surface | `#2b3034` |
| Input | `#191c1f` |
| Border | `#535d66` |
| Main text | `#efefec` |
| Secondary text | `#b9bec3` |
| Muted text | `#9ba4ab` |
| Accent and text on accent | `#b3c9dd` / `#151b20` |
| Focus | `#d0e2f1` |
| Selection and selected text | `#35434f` / `#efefec` |
| Success, warning, error | `#b8c9a4` / `#ddbb80` / `#e5a09b` |
| Login and lock surface, input, button | `#202020` / `#303030` / `#d0d0d0` |

Noto Sans uses 11pt regular UI text, 10pt secondary text, and 13pt medium group
titles. Retain the 48pt lock clock in regular weight and check native rendering.
Meslo remains 11pt, with the existing Nerd Font symbol mappings. Source Han Sans
CN remains the CJK fallback. The website shares the font families and palette,
with larger type and spacing appropriate for reading.

Keep Breeze Dark icons, explicit Breeze cursors at 24 logical pixels, square
outer windows, 4px gaps and focus ring, the existing Niri column widths, and the
4/8/12/16/24/32 spacing scale. Keep the proposed 96% owned-overlay opacity,
opaque application interiors, small internal control/card corners, and flat
backgrounds without adding blur. These values still require native review.

Kitty needs a Neutral Slate terminal extension. Map its background/foreground,
cursor, selection, ANSI blue, and semantic red/green/yellow directly from these
roles. Complete the remaining ANSI slots and bright variants as a bounded
terminal specimen in stage 1; the existing Slate Blue ANSI table is not the
selected terminal palette. Preserve input, paste, glyph maps, cursor trail,
existing sessions, and independently owned editor/agent RGB themes.

## Baseline corrections completed in stage 1

The following described the pre-pass source and have now been corrected together:

- `design/identity.json` still has `selected_candidate: null`, Slate Blue as
  its working direction, and the earlier terminal extension.
- `scripts/build.py` and its checks name the Slate Blue Kitty fragment.
- `site/style.css`, `site/identity.html`, and font export inputs assume Inter.
- The public Design page draft, terminal guide, home feature, and root README
  still describe Slate Blue.
- Review builders assume an unselected proposal and must distinguish selected
  design, generated specimens, and deployed appearance.

Retain `design/identity.json` as the one canonical identity input. Select
`neutral-slate` there during implementation; emit only the selected profile in
the public `data/identity.json`. Keep historical candidates available to internal
comparison tools without offering runtime theme switching.

The Niri Plus committed baseline is
`45881d7b4d4f01625c3391aa1dbdf7745d2dbfb9`, with local site/design changes from
this conversation. Preserve them. The inspected chezmoi HEAD is
`d4d780be4a336ac66d248128563300bf501645ba`; its worktree was clean. The desktop
audit originated at `861861eaa3ff67ca65ce4577318fd52135917620`. The later commit
changes Observer deployment diagnostics, which stay outside this pass. Refresh
heads, scoped source/deployed differences, and selected artifacts before work.

## Stage 1 Align the selected reference

Update the canonical selection, complete the terminal extension, and retarget
the public projection, generated appearance fragments, review defaults, labels,
tests, and Noto font assets/licenses together. Remove hardcoded palette names
and UI font assumptions where they can disagree with the selected profile.
Use a selected-profile field or generated values rather than a runtime theme
framework.

Prepare `examples/kitty/neutral-slate.conf`, update its manifest/provenance, and
verify it with Kitty's native configuration parser. Retain older immutable
reports and identify old example files as historical if kept. Do not leave the
current setup guide pointing at the earlier theme.

Produce one consistent set of Neutral Slate specimens: browser beside Kitty,
Rofi applications and Plus actions, SwayNC cards/notifications, hardware
feedback, Dolphin/file chooser, login/lock, and Fcitx text. Include selected,
focused, empty, error, long-name, unknown-value, and missing-hardware states.
Check the terminal's default, dim, bold, selected, and ANSI text, including
extended colors and representative full-screen tools.

**Completion:** the selected profile and every current specimen/export agree;
theme names, fonts, assets, and terminal values have no stale Slate Blue
assumptions. Exact-theme/native acceptance is still tracked separately.

## Stage 2 Make Design a permanent visual part of the site

Keep `/design/` in main navigation and linked prominently from the home page.
Use a short introduction such as: “Neutral Slate brings warm charcoal surfaces,
readable type, and pale blue focus to the browser and terminal desktop.”

Build the page around these sections in this order:

| Section | What visitors see and do |
| --- | --- |
| Desktop overview | A large browser/terminal composition establishing the two halves, focus, window geometry, and absence of a permanent bar. |
| Surface gallery | Inspect Launch, Information, Terminal, and Login/lock. Show real-sized details, including selected rows, named actions, transient feedback, and empty/unavailable states. |
| Palette | Labeled role swatches with hex values: canvas/surfaces/text, accent/focus/selection, and semantic status colors. |
| Typography and details | Noto UI, Meslo terminal, Latin/CJK text and glyph samples, spacing, icons/cursor, and a close view of focus/selection. |
| Use the theme | Component mapping and links to the selected identity, appearance fragments, prerequisites, setup, and the terminal recipe. |

Use one theme throughout the page and site. Palette comparisons, the selection
story, and a theme switcher do not belong in this visitor flow. Explain native
toolkit variations briefly beside the relevant surface. Place deeper ownership
and compatibility details in the architecture/reference guides.

Show useful behavior: a picker filter/selected action, a terminal prompt and
selection, panel hardware presence/absence, and replacement feedback. Keep all
illustration controls local to the page. Native keys, device operations, and
authentication remain demonstrations rather than real desktop actions.

Label mockups and isolated native samples at their point of use. Replace or
supplement them with accepted native captures in stage 6. Keep captions concise;
the page should show the desktop rather than narrate the implementation process.
Retain readable static content without JavaScript, keyboard controls, reduced
motion, responsive layouts, and working source/example links.

Update `site/home.html`, `docs/design.md`, `site/identity.html`, site styles and
enhancements, `docs/recipes/terminal.md`, architecture/setup/reference links,
asset/license manifests, and the builder/check inventory. Keep the README
operational. Do not rewrite the personal story.

**Completion:** a visitor can see Neutral Slate across the common surfaces,
understand focus and feedback, inspect the palette/type, and reach usable setup
material without reading the selection history.

## Stage 3 Prepare native component configuration

Use the existing [component implementation map](../design/implementation-plan.md)
for ownership and source paths. Prepare small groups with independent reload
and rollback boundaries:

| Group | Work |
| --- | --- |
| Applications | Supported GTK/Qt dark appearance, Noto UI and Meslo fixed-font roles, icon/cursor ownership, Dolphin and file-dialog integration. |
| Niri and launchers | Canvas/focus/cursor, Rofi theme, Plus selected rows and action styling; retain layout, binds, and native picker contracts. |
| Information and feedback | SwayNC typography/cards/notifications and volume/brightness appearance; preserve data, timing, replacement, and history semantics. |
| Terminal and prompt | Kitty appearance and Zsh semantic prompt/suggestion colors, preserving terminal/shell behavior and native provider ownership. |
| Lock and login | Gtklock appearance through its independent service; separate root-owned SDDM derived theme/font/cursor changes. |

Chezmoi consumes a reviewed, immutable Niri Plus archive and its canonical
selected profile, with URL and checksum updated together. Avoid copying another
hand-maintained palette into private data. Host policies, local application
preferences, runtime artifacts, pairing, and display selections stay separately
owned. Unknown hosts receive no new effects.

Keep the current GTK3/Libadwaita and Qt style boundaries. Use supported settings
and scoped owned styles. An application that cannot accept an exact color
receives a documented native variation, rather than an unsupported global theme
override.

**Completion:** scoped source/config validation and isolated native specimens
match the selected identity. Review exact chezmoi diff/dry-run before delivery;
no live change is implied by source preparation.

## Stage 4 Complete the terminal and common utility reference

Extract a portable Zsh core with Powerlevel10k configuration/custom status,
history, completion, autosuggestions, substring search, syntax highlighting,
fzf, zoxide, and the lightweight agent-shell path. Pin and attribute upstream
plugins/theme first. Keep cloud SDKs, personal provider/fleet configuration,
history, and credentials outside the portable core. Document optional development
integrations separately.

Check isolated shell startup, missing optional tools/devices, plugin order,
history/completion, prompt refresh cost and cleanup, and the agent-tool early
return. Then qualify glyph/CJK rendering, tmux, SSH, and full-screen tools in
owned terminal windows. The public recipe should include real files,
dependencies, installation, verification, and removal, not just a description.

Complete the already scoped common entry points as a separate functional group:
Network via Kitty/nmtui, Bluetooth via Kitty/bluetoothctl plus a pairing guide,
Audio via pavucontrol, and a small Session picker. Make BlueZ/bluez-utils,
pavucontrol, and UDisks2 dependencies explicit for selected hosts where needed.
Reuse existing lock, quit confirmation, suspend, and power behavior; confirm
restart/shutdown and preserve cancellation. These entry points use Mod+D.

Retain the panel's status/subscription contract and existing hardware-key
helpers. Keep the Starship volume trial scoped. Do not expand SwayNC into a new
settings application. Document the remaining capability roster, including
SDDM, Kanshi, swayidle, Gtklock, portals, input, and authorization, as part of the
complete reference.

**Completion:** the terminal core is portable and the common utility paths are
documented, discoverable, and checked independently of appearance changes.

## Stage 5 Qualify and adopt by component and host

Use the [verification matrix](../design/verification.md). Source checks,
isolated native rendering, session use, and physical acceptance remain separate.
Preserve current power, auto-lock, lid, wallet/PAM, native agent state, fleet
routes, notification mirrors, and active sessions.

Adopt on Carbon first, then Starship and Snap. Carbon is Bryan's current working
desktop, so apply small appearance batches and use normal-use feedback. Ordinary
visual defects and untested states can be fixed during adoption; they do not
require holding usable components off the other hosts. Finish with delivery on
all three and an explicit list of remaining checks or restored components.

Start disruptive GUI trials on unattended Snap. Check Starship's ultrawide
and Carbon's 1.5-scale laptop context in appropriate normal-use windows. Include
keyboard and mouse focus, long labels/CJK, portal/file dialogs, audio/backlight,
hardware-present/absent states, docking, and normal login/lock/resume paths.
Do not restart Niri or SDDM, interrupt a locker, or force suspend/logout to
preview a theme.

Stop a component group for a broken input/action path, unreadable native state,
missing dependency, unexpected source/preimage, or unrelated drift. Restore only
that group's reviewed source/configuration preimage. Keep root greeter recovery
separate from user appearance recovery.

If focus is actually hard to distinguish, record the surface and state before
making a small Neutral Slate focus/selection adjustment. Do not silently switch
to Graphite Blue or reopen the entire palette choice.

**Completion:** record exactly which component/host combinations passed and
which physical checks remain pending. Other hosts do not inherit acceptance.

## Stage 6 Capture and publish the experience

Capture sample browser/file work, terminals/agents, launchers, the information
panel, clipboard, hardware feedback, and appropriate normal-use login/lock and
laptop views. Use owned fixture content and keep media provenance explicit.
Add short task demonstrations and concise setup recipes to the site.

The public Design page can present labeled specimens before desktop adoption;
only accepted native evidence changes its captions to describe the deployed
setup. Publish website changes as their own reviewed result. Run the site build,
link/inventory/hash checks and owned browser checks, then verify the deployed
revision and served assets. Check report/preview access from Carbon as well.

**Completion:** site source, downloads, media, component versions, and claims
agree. The finished presentation shows the selected experience and how to use
it; historical alternatives stay in internal notes.
