# More definition, the same warmth

A design study for Neutral Slate: clearer desktop surfaces and states, with a
separate pure-black terminal palette. Both use the existing Noto Sans UI and
Meslo terminal fonts.

**Selected · 26 October 2026.** Crisper Neutral Slate is the desktop palette;
Balanced+ on pure black is the terminal palette. The
[current design](../design.md) and downloadable appearance examples now use
that selection. This comparison retains the earlier baseline and alternatives.
The later pure-black workspace and charcoal overview surround are shown in
the current design; the desktop specimens here compare UI surface palettes.

<!-- niri-plus:contrast -->
## Desktop comparison

Compare the delivered Neutral Slate palette with a crisper proposal. The
proposal deepens the neutral base, separates raised surfaces more clearly,
strengthens important boundaries, and makes status colors more distinct.
Quiet separators have their own color so every card does not need a bright
outline. The warm off-white main text, font choices, geometry, and neutral
login/lock colors remain the same.

## Terminal comparison

Compare Balanced, Balanced+, Rich, and Vivid, all on black. The two intermediate
samples lean further toward Vivid while preserving normal/bright separation.
The preceding Balanced and Vivid endpoint color values remain unchanged.
Use “Middle two” to compare just the new samples. The earlier “Black background only”
changed only the original terminal background; it did not include the crisper
desktop colors. All three are ANSI palettes, with different color values.

Black resolved much of the perceived haze in the first comparison. The refined
proposal kept moderate rose, sage, gold, blue, violet, and teal hues. The current
samples add more color: Balanced+ starts 40% toward Vivid, and Rich starts 70%
toward it, using sRGB-channel blends. Normal colored entries are then deepened
only where needed to keep at least 1.45:1 luminance contrast with their bright
partners. That threshold is a design guard for these samples, not an
accessibility criterion. Equal-weight text samples expose pairs such as 01/09.

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

For the terminal, compare Balanced+ and Rich against the unchanged endpoints.
The original muted-on-black palette remains in the preceding reports and
source baseline. Check Zsh, Git diffs,
tmux, SSH, agent output, and full-screen
tools. Faint attributes, entries 16–255, explicit RGB, and application-owned
backgrounds need their own checks. Browser font rendering and screenshots cannot
settle how this feels on Carbon and Starship's OLED monitors.

The selected values are promoted into the canonical identity and appearance
adapters. Chezmoi delivery and native/physical acceptance are recorded
separately; comparison controls never apply a desktop theme.

## Source and earlier comparisons

- [Study values and calculated contrast pairs](../../data/contrast-study.json).
- [Current selected identity](../../design/identity.json).
- [Balanced terminal comparison](http://starship:8787/reports/376a029fc8312346709e56932645850827798d0eebb36460b9e601383130d10d/design/contrast/): the original-on-black, Balanced, and Vivid specimens before the two intermediate samples.
- [First desktop/terminal comparison](http://starship:8787/reports/f3e6bea2450fd01eb9e567a1413ad47b4a89fc9a988cb9a2b6049371b3b75990/design/contrast/): the preceding grey, black-only, and vivid specimens, before the balanced refinement.
- [Earlier accent comparison](http://starship:8787/reports/0dabd4987bc03a94302f2501b0aabc998312ad3bea50bb47bd458f814925a52d/): the preceding Clear Blue decision, before the desktop/terminal split.
- [Font provenance and licenses](../../assets/fonts/provenance.json).
- [Control and state contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html). The calculated pairs are design aids, not a native accessibility conformance result.
