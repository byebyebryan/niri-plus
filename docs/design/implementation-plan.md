# Desktop implementation map

Neutral Slate is selected. Follow `docs/planning/neutral-slate-pass.md` for the
current sequence and site scope.
This component map supplies ownership and delivery boundaries alongside the
[selected identity](identity.md) and [desktop brief](desktop-brief.md).
The local source pass is implemented; see the checkpoint in the pass plan.
The published v1 site and deployed desktop configuration remain unchanged.

## 1 Freeze the selected design and preserve the baseline

Use Neutral Slate as reviewed, with Noto Sans UI and Meslo terminal typography.
Promote the selection and complete its terminal ANSI/prompt roles together. Capture
the exact Niri Plus and chezmoi revisions, scoped status/diff, active sessions,
selected immutable components, and per-host configuration preimages before
deployment. Preserve unrelated dirty work and existing native sessions.

The original desktop audit baseline is chezmoi
`861861eaa3ff67ca65ce4577318fd52135917620`; the current inspected source is
`d4d780be4a336ac66d248128563300bf501645ba`; the published Niri Plus v1 baseline
is `45881d7b4d4f01625c3391aa1dbdf7745d2dbfb9`. Recheck those before implementation.

## 2 Establish one public identity source

Retain `design/identity.json` as the canonical input, select `neutral-slate`, and
export the single selected profile to public `data/identity.json`. Keep its
version and source provenance explicit. Candidate variants stay in design
history rather than silently becoming supported runtime themes.

Chezmoi pins the reviewed public artifact through its external-selection
mechanism, with URL/checksum together. Add a small template boundary for shared
identity data and project values only into owned configuration. Avoid maintaining
a second hand-copied palette in private data and another in the site.

A commit-pinned archive is sufficient initially. A package/release system is not
required merely to carry a small identity file. Site colors and examples consume
the same selected definitions when that publishing phase is reached.

## 3 Apply the identity through existing component boundaries

All paths in the source column below are relative to the private chezmoi source.
They identify ownership. The pass checkpoint records prepared source; live
adoption is separate.

| Component | Proposed work and source | Delivery and verification boundary |
| --- | --- | --- |
| Niri | Retain layout/rules/binds; add explicit cursor choice; map focus/canvas from selected identity. `dot_config/niri/config.kdl.tmpl`, local rules, shared binds. | Validate rendered config for all hosts. Review reloadable changes separately from session startup. No forced Niri restart. |
| Kanshi | Retain per-host output policies and profile decisions. `dot_config/kanshi/config`. | Document scale/refresh/profile rationale. Test real docking separately; do not rewrite profiles as part of palette work. |
| GTK3/4 | Retain dark baseline, select shared UI typography/icons/cursors through existing managed preferences and settings. GTK modifiers and desktop-preference hook. | Preserve unrelated INI/dconf preferences. Use supported native settings; inspect newly launched apps. |
| Qt5/6 and Dolphin | Retain Fusion/Breeze and matched palettes; add explicit general/fixed font roles where supported; retain portal dialogs and Dolphin scheme. Qtct/KDE/Dolphin modifiers. | Native palette/font probes plus actual app/chooser views. Preserve application preferences. |
| Rofi and pickers | Apply shared font, surfaces, selection, geometry, icons; preserve named-action tokens/launch arguments as a coordinated change. `dot_config/rofi/` and shared binds. | Isolated picker-state checks first. Legacy dms token rename is optional and must update every consumer together. |
| SwayNC | Map selected owned CSS; retain configuration, panel semantics and Starship volume-trial admission. `dot_config/swaync/`. | Native isolated fixtures first; a scoped notification reload later. Preserve idle, active locking, pairing and mirror state. |
| Hardware feedback | Retain 5% steps, limits, replacement and history rules; export helpers and prerequisites. `notify-volume`, `notify-brightness`. | Syntax/owned-dispatch checks, then small reversible hardware trials. No external-monitor DDC behavior inferred from laptop keys. |
| Gtklock | Apply shared UI font/cursor relationship while retaining neutral form and independent service. `dot_config/gtklock/`, lock unit/readiness helper. | Isolated appearance where possible, then deliberate manual lock/unlock. Never stop an active locker through idle/theme reload. |
| SDDM | Carry the selected font/cursor into the root-owned derived theme, retaining neutral colors and existing PAM/scaling. SDDM external and installer template. | Review exact root target/preimage and derived assets. Verify during a normal password login; never restart SDDM to preview. |
| Kitty | Retain Meslo/glyph maps/native input/paste behavior; map background, foreground, cursor, selection, and the full ANSI table from the shared identity. `dot_config/kitty/kitty.conf`. | Parse the generated appearance fragment and use owned sample windows. Review extended colors, dim text, full-screen tools, tmux and remote shells. Preserve sessions. |
| Zsh and prompt | Export a portable core from `dot_zshrc`, `dot_config/zsh/p10k.zsh`, and `p10k-custom-segments.zsh`; separate optional SDK/provider integrations from `dot_zshenv` and `dot_zshrc`. Map prompt states to shared semantic ANSI roles. | Pin/attribute upstream plugin/theme revisions before export; preserve source implementations. Check startup, light agent path, history, completion, watcher cleanup, optional tools and absent hardware. Do not ship personal history or cloud/fleet state. |
| Input/authorization | Align supported font/fallback/cursor choices; preserve engines and native auth ownership. Fcitx, portal, polkit and environment inputs. | Test sample input and harmless owned prompts. No PAM/wallet/provider-auth migration. |

## 4 Make common utility entry points explicit

Add a small set of desktop entries under the managed applications directory:

- **Network:** Kitty running `nmtui`; dependency remains NetworkManager.
- **Bluetooth:** a dedicated Kitty `bluetoothctl` terminal plus the maintained
  pairing guide; admit BlueZ/bluez-utils explicitly on selected desktop hosts.
- **Audio:** `pavucontrol`; admit it as an explicit supporting utility rather
  than relying on its incidental presence.
- **Session:** one small Rofi helper with the scoped Lock/Logout/Suspend/Restart/
  Shut down contract in the brief. Reuse native confirmation where available;
  isolate dispatch tests and preserve per-host suspend/locking policy.

Declare UDisks2 explicitly for the supported removable-drive capability. Confirm
service/package ownership before extending the manifest. No new tray, panel
backend, pairing daemon, or always-running control collector is proposed.

Do not add Wi-Fi/Bluetooth mutation controls to the SwayNC fork in this phase.
Its status cards keep their read/subscription contract. A future native GUI
pairing tool is a separate optional UX experiment if the terminal path proves
uncomfortable in real use.

## 5 Qualify and deploy in bounded groups

Prepare sources, public-reference provenance, rendered templates, and scoped
diff/dry-run before a deployment request. Preview using isolated test resources.
Disruptive GUI trials belong on unattended Snap. Review Starship and Carbon in
appropriate normal-use windows; keep source evidence distinct from live
acceptance on each host.

Group changes by their reload boundary: app/desktop appearance, Rofi and helper
entries, notification CSS, locker appearance, and root greeter assets. Preserve
the independent notification, clipboard, idle, and locker lifetimes. Do not
bundle network, auth, provider, or fleet changes into a theme rollout.

Stop a group if its source/provenance differs from the reviewed artifact,
required dependencies are absent, an unrelated replacement is encountered,
or a verification result violates the selected contract. Retain the current
accepted selection and preimages; do not keep applying adjacent changes to
make the group pass.

Rollback restores that group's source selection and reviewed configuration
preimages through a scoped path. Root greeter rollback is separate from user
theme rollback. No broad package purge, rollback-file deletion, session killing,
or immutable-artifact overwrite belongs to this work.

## 6 Present design and accepted behavior

The selected theme belongs on a permanent visual Design page: browser/terminal
composition, surface gallery, palette/type samples, focus/selection states, and
setup/download links. Keep palette-selection rationale and comparisons in
internal notes. Clearly distinguish specimens from accepted native captures. Keep one
theme; historical directions do not become supported choices. After desktop
acceptance, update the exact personal profile and utility recipes. Refresh native
captures and a
representative daily-work recording, using sample content and explicit media
provenance.

Publish the website in a separate reviewed change. Its own build/browser/served-
byte checks do not replace desktop acceptance. Component source/releases and
private host deployment remain independently owned.
