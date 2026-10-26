# More definition, the same warmth

A design study for Neutral Slate: clearer desktop surfaces and states, with a
separate pure-black terminal palette. Both use the existing Noto Sans UI and
Meslo terminal fonts.

**Refined proposal · 26 October 2026.** The desktop/terminal split and black
terminal background are the agreed direction; these exact colors are under
review. The
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

Compare the original ANSI colors on black, a balanced proposal on black, and
the preceding vivid reference on black. The earlier “Black background only”
changed only the original terminal background; it did not include the crisper
desktop colors. All three are ANSI palettes, with different color values.

Black resolved much of the perceived haze in the first comparison. The refined
proposal keeps moderate rose, sage, gold, blue, violet, and teal hues. Deeper
normal entries and lighter bright partners make pairs such as 01/09 easier to
distinguish. Equal-weight text samples expose those differences directly.

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

For the terminal, compare the balanced middle with the original colors on
black, using the vivid version as a reference endpoint. Check Zsh, Git diffs,
tmux, SSH, agent output, and full-screen
tools. Faint attributes, entries 16–255, explicit RGB, and application-owned
backgrounds need their own checks. Browser font rendering and screenshots cannot
settle how this feels on Carbon and Starship's OLED monitors.

If selected, promote the reviewed values into the canonical identity, update
the component adapters and examples, then deliver through chezmoi. This study
does not change those deployment inputs.

## Source and earlier comparisons

- [Study values and calculated contrast pairs](../../data/contrast-study.json).
- [Current selected identity](../../design/identity.json).
- [First desktop/terminal comparison](http://starship:8787/reports/f3e6bea2450fd01eb9e567a1413ad47b4a89fc9a988cb9a2b6049371b3b75990/design/contrast/): the preceding grey, black-only, and vivid specimens, before the balanced refinement.
- [Earlier accent comparison](http://starship:8787/reports/0dabd4987bc03a94302f2501b0aabc998312ad3bea50bb47bd458f814925a52d/): the preceding Clear Blue decision, before the desktop/terminal split.
- [Font provenance and licenses](../../assets/fonts/provenance.json).
- [Control and state contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html). The calculated pairs are design aids, not a native accessibility conformance result.
