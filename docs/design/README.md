# Desktop design plan and review material

**Neutral Slate is selected.** Use Noto Sans UI, MesloLGS Nerd Font terminal,
and the reviewed Neutral Slate palette. Keep Graphite Blue as a documented
alternative for later; maintain one theme initially.

Start with the [Neutral Slate implementation and site plan](../planning/neutral-slate-pass.md).
It defines the selected values, coordinated source promotion, permanent visual
Design page, native component work, Zsh/utility reference, host validation, and
capture/publication sequence.

The public Design page should show how the theme looks and works: desktop
composition, common surfaces and states, palette, typography, and setup links.
Keep selection history and comparisons in these internal notes.

Existing site drafts and immutable previews still show the preceding Slate Blue
experiment. Stage 1 updates the token selector, terminal extension, Noto assets,
labels, exports and checks together. This planning update does not change the
running desktop or published website.

## Review material

- [Desktop brief](desktop-brief.md) and [22-capability catalog](../../design/capabilities.json).
- [Selected identity specification](identity.md), including palette, typography, native boundaries, and interactions.
- [Implementation map](implementation-plan.md), including Kitty and Zsh ownership/extraction.
- [Verification and capture plan](verification.md).
- [Review-board source and build instructions](../../design/README.md).

The [original three-direction review](http://starship:8787/reports/9b9e5a20085fc2e33ee54390df3b568657392135bdc85c8731b0afdfcc07d3aa/)
is an immutable historical snapshot, with its
[original verification receipt](../../design/evidence/review-result.json).
Its Graphite Blue recommendation predates Bryan's feedback and the Slate Blue
refinement. These snapshots predate the final Neutral Slate selection; the
existing source board still includes the earlier blend until stage 1 is
implemented.

## Remaining acceptance

Follow the Neutral Slate pass, then qualify the native component and per-host
adoption groups. The site and comparison mockups do not establish deployed
appearance or physical acceptance. Shell plugin/theme revisions and attribution
must be fixed before exporting a reproducible public shell bundle; personal
history, cloud configuration, fleet routes and credentials stay outside it.

The common utility entries, package admissions, power/authentication policies,
and hardware-trial boundaries retain their existing proposed implementation
scope. Publishing source/site changes is separate from deploying the desktop.

## Focused three-palette comparison

The [side-by-side comparison](http://starship:8787/reports/7e40d91689056e08e4ad00e6c91c2ec1a0ed7920247808d0b0d2ea5f344a5ae6/)
compares Graphite Blue, Neutral Slate, and Slate Blue with synchronized surfaces
and a same-font mode. It consumes the canonical tokens and retains the one-theme
implementation scope. See the [delivery/check receipt](../../design/evidence/three-palette-comparison.json).
