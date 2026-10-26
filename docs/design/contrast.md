# More definition, the same warmth

A design study for Neutral Slate: clearer desktop surfaces and states, with a
separate pure-black terminal palette. Both use the existing Noto Sans UI and
Meslo terminal fonts.

**Proposal · 26 October 2026.** The desktop/terminal split is the agreed
direction; these exact colors are under review. The
[current design](../design.md) and downloadable setup examples retain the
delivered Neutral Slate · Clear Blue palette.

<!-- niri-plus:contrast -->
## Desktop comparison

Compare the delivered Neutral Slate palette with a crisper proposal. The
proposal deepens the neutral base, separates raised surfaces more clearly,
strengthens important boundaries, and makes status colors more distinct.
Quiet separators have their own color so every card does not need a bright
outline. The warm off-white main text, font choices, geometry, and neutral
login/lock colors remain the same.

## Terminal comparison

Compare the current terminal, the current ANSI colors on pure black, and
stronger ANSI colors on pure black. The black-only version isolates the effect
of the background change. Stronger colors draw on the previous Material Darker
terminal family, with separate normal and bright entries.

Prompts, Git diffs, ordinary output, status messages, selected text, all sixteen
ANSI slots, and faint text use identical sample content. An explicit RGB sample
stays the same in every version; terminal ANSI changes do not recolor it.

All specimens are HTML/CSS illustrations with fictional values. They do not
operate desktop controls or establish native rendering or OLED acceptance.
<!-- /niri-plus:contrast -->

## Review in daily use

Judge the desktop's selected row, keyboard focus, input boundary, secondary
labels, and success/warning/error states together. The proposal uses opaque
panels; the specimens use a flat background so desktop content behind them does
not bias the comparison. A native translucent-overlay comparison remains useful.

For the terminal, compare black-only before deciding whether the stronger ANSI
table is necessary. Check Zsh, Git diffs, tmux, SSH, agent output, and full-screen
tools. Faint attributes, entries 16–255, explicit RGB, and application-owned
backgrounds need their own checks. Browser font rendering and screenshots cannot
settle how this feels on Carbon and Starship's OLED monitors.

If selected, promote the reviewed values into the canonical identity, update
the component adapters and examples, then deliver through chezmoi. This study
does not change those deployment inputs.

## Source and earlier comparisons

- [Study values and calculated contrast pairs](../../data/contrast-study.json).
- [Current selected identity](../../design/identity.json).
- [Earlier accent comparison](http://starship:8787/reports/0dabd4987bc03a94302f2501b0aabc998312ad3bea50bb47bd458f814925a52d/): the preceding Clear Blue decision, before the desktop/terminal split.
- [Font provenance and licenses](../../assets/fonts/provenance.json).
- [Control and state contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html). The calculated pairs are design aids, not a native accessibility conformance result.
