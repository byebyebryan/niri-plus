# Neutral Slate contrast pass

Design scope, 2026-10-26. The user has accepted separate desktop and terminal
palettes within one identity. Daily use revealed two issues: a grey terminal
background is undesirable on Carbon and Starship's OLED displays, and softened
colors make terminal output and some desktop states feel hazy.

## Prepared comparison

- Current desktop against one crisper warm-neutral proposal, using the same
  Noto fonts, geometry, content, and connected/warning/error states.
- Balanced, Balanced+, Rich, and Vivid, all on black, using identical Meslo
  type, prompts, diffs, and output. The middle two can be viewed together.
- Equal-size, equal-weight normal/bright pair text, including 01/09, with
  calculated within-pair luminance separation.
- All sixteen ANSI colors, normal versus bright blue, selected text, and two
  illustrative faint levels. An explicit RGB sample stays constant.
- Exact desktop/terminal values and calculated opaque sRGB contrast pairs.
- Public comparison page plus a portable HTML report from the same source.

The first comparison established that black resolves much of the haze; the
remaining priority is separation within a color family. The balanced proposal
keeps moderate color character and gives each normal entry a lighter bright
partner. The vivid candidate remains a reference, rather than the preferred
direction in that comparison. Further feedback leans closer to Vivid, so the
current study adds two intermediates starting at 40% and 70% sRGB-channel blends.
Normal entries are deepened where needed to retain at least 1.45:1 pair
separation. This is a design guard, not an accessibility target. Both endpoints
remain unchanged. The grey and muted-on-black baselines remain in earlier
immutable reports and the exported source baseline.

`design/contrast-study.json` owns the proposal, tied to the current
`design/identity.json` SHA-256. The builder rejects a mismatched baseline. Its
black-only terminal experiment changes only the background color. Its original
ANSI values are independent of the crisper desktop proposal. The crisper
desktop distinguishes important control borders from quiet separators; its
login/lock colors remain the selected baseline.

## Acceptance and promotion

Browser review must confirm correct colors, matched fonts and content,
responsive layouts, keyboard operation, state/view controls, and useful reading
without JavaScript. Unit checks protect the selected identity and downloadable
Kitty fragment from accidental proposal adoption. Retain generated exports and
browser captures outside the checkout.

Human comparison and physical OLED acceptance remain open. Native overlays,
GTK/Qt widgets, terminal faint attributes, 256-color output, application-owned
RGB/backgrounds, tmux, SSH, and agent/full-screen tools require review before
fleet adoption.

Selection is a later step. Promote the accepted desktop and terminal values to
the canonical identity and update adapters/examples together. Publish an
immutable producer, then plan scoped chezmoi delivery to the selected hosts.
This design pass performs no live desktop changes, package actions, or fleet
rollout.
