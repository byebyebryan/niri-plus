# Desktop verification and capture plan

This plan separates design review, source checks, isolated native evidence,
and actual desktop/hardware acceptance. No live device/network/lock/power tests
were performed to create the design package.

## Evidence stages

| Stage | Evidence | What it does not establish |
| --- | --- | --- |
| Design board | Comparable candidate mockups, semantic values, readable states, documented action paths. | Native implementation, actual login, device actions or deployed appearance. |
| Source/static | Explicit packages and ownership, valid rendered Niri/INI/JSON/CSS as applicable, selected artifact hashes, source checks. | Native application rendering or session/hardware behavior. |
| Isolated native | GTK/Qt font/style samples and later component fixture renders in private displays/buses. | Normal desktop or physical-device acceptance. |
| Session use | Real app/picker/notification/input behavior in a controlled normal-use window. | Other hosts, unattended suspend, or physically observed greeter/scale behavior. |
| Per-host physical | Normal login/unlock, docking, screen sharing, audio/input choice, AC/battery and suspend/resume checks. | Unexercised devices or different deployment tuples. |

## Host matrix

| Context | Common acceptance | Specific cases |
| --- | --- | --- |
| Starship | Browser/files, terminals, launchers, panel, clipboard, app/portal appearance, input, auth and normal login/lock. | Ultrawide scale 1, no internal battery, external brightness path, current per-app volume trial. |
| Snap | Same reference paths; disruptive automation only while unattended and using owned resources. | Internal/external/home/work/dual-output profiles, AC/battery behavior, applicable GPU state, greeter/locker and normal-use trial. |
| Carbon | Same reference paths, checked separately. | Internal fractional scale 1.5, dock transitions, CJK/preedit/candidates, backlight, battery/charge limits and resume. |

Candidate boards are checked at normal and fractional device scales. That is a
useful rendering exercise, not a physical legibility or mixed-output proof.

## Representative journey and expected results

1. **Login:** normal password login enters Niri, the wallet behaves as before,
   the expected services are present, and no competing shell/notifier starts.
2. **Displays:** normal internal/external/dock transitions choose the expected
   Kanshi profile and retain a usable screen and readable controls.
3. **Browser/files:** download/open sample PDF/image/video/archive, use a file
   chooser and default applications, and share/stop sharing sample content in a
   browser call.
4. **Keyboard work:** navigate columns/workspaces, open/return to an owned
   terminal/agent and configured test host/session, and retain native input,
   cancellation, action selection, and focus.
5. **Information/actions:** see correct primary network, connected Bluetooth,
   battery and available GPU state; use the documented utility entry points.
   Test no-hardware, unknown-value, disconnected, long-name and hidden-return
   states through fixtures before live hardware trials.
6. **Feedback:** volume/mute/microphone/brightness show the right value and
   replaceable progress popup, without notification history. Small live trials
   restore the previous device values.
7. **Clipboard/capture:** restore original sample text/image bytes; delete only
   owned entries; cancel destructive history actions; capture owned windows.
8. **Input/auth:** verify English/CJK typing, preedit/candidates, native focus,
   and an owned harmless authorization path. Never record passwords or private
   input history.
9. **Lock/power:** verify manual lock/unlock and independent locker lifetime,
   then normal-use idle/inhibition, source changes, display-off, and suspend/
   resume according to each host's existing policy. Never force these actions
   in an attended working session merely to obtain a screenshot.

## Visual review checklist

Compare the shared UI font and size hierarchy, terminal role, CJK/symbol
fallbacks, tabular numeric alignment, icon/cursor family and size, focus/selection,
disabled/error states, density, geometry, and opacity on real backgrounds.

Pay attention to pointer transitions between compositor space, Chrome, Dolphin,
Rofi, and greeter/lock. Check GTK and Qt dialogs for readable palettes and
matching file rows. Native control differences are accepted where the identity
specification names them; unsupported global CSS is not the fallback.

## Captures after adoption

- An overview of the real browser/terminal arrangement, including column
  navigation, application rules, and the absence of a permanent bar.
- Browser download/open/upload and the supporting file/portal applications.
- Rofi applications and Plus pickers with their actual managed theme.
- Personal SwayNC panel plus normal/critical/transient notifications and hardware
  feedback, with hardware availability explained.
- Login and lock appearance through an appropriate normal-use capture method.
- A laptop view showing meaningful fractional-scale and dock differences.

Use sample sites/files/conversations/device aliases. Preserve source revisions,
license/provenance and whether a capture is native, staged, or illustrated.
Native fixture data and mockups never become unlabeled daily-desktop footage.

## Source implementation checkpoint - 2026-10-24

The selected profile, public specimens, typography assets and terminal extension
now agree. The source pass adds the portable shell/utility bundle and prepares
opt-in private native adapters. No host is admitted to the new theme.

Source evidence includes the full chezmoi check suite, byte-for-byte unselected
output parity for three known hosts and an unknown host, rendered Niri validation,
Qt5/6 palette and INI checks, publication/hash rejection, and safe stubbed
Session actions. Isolated native evidence covers GTK3 locker-style controls,
GTK4 SwayNC stylesheet parsing, Qt6 Breeze widgets/font, Rofi theme/menu,
Kitty configuration parsing, and the derived greeter in SDDM test mode.
The native checks use private displays/settings/buses and perform no real
session, authentication, radio, audio or power action.

The terminal bundle passed isolated startup/status/watcher checks and an actual
four-archive install in a temporary home. Kitty glyph/CJK rendering, tmux/SSH,
full-screen tools, actual utility launches, normal lock/login and physical host
acceptance remain open. These source and fixture results do not qualify a host.

## Original design package acceptance

The current package is complete as a reviewable recommendation when its 22
capabilities, selected Neutral Slate profile, terminal extension, native
limitations, implementation map and capture plan agree; the review board works by keyboard and without
JavaScript; all intended assets/links are present; and current public-site
output is unchanged.

Neutral Slate is selected. Update the token selector, font/export assumptions,
public specimens and recipes together under the
pass in `docs/planning/neutral-slate-pass.md`. Native and per-host
acceptance remain independent of that selection.

## Terminal additions after color feedback

Include the full Kitty ANSI/cursor/selection palette and Zsh prompt semantics in
the appearance checks. Isolate shell startup and agent markers, optional plugin
absence, history/completion and prompt watcher cleanup before any native trial.
Then verify glyph/CJK input, dim and extended colors, tmux, remote shells and
full-screen tools in owned windows. The public terminal guide is source-derived;
its existence is not acceptance of a portable shell bundle.
