# Desktop design review

Selected direction: **Neutral Slate**. The
[implementation and site plan](../docs/planning/neutral-slate-pass.md) records
the work sequence; the canonical selection, terminal mapping, site export, and
selected review-board default now agree. Graphite Blue and the Slate Blue blend
remain design history rather than supported runtime themes.

These are design references for the complete Niri Plus desktop. They are not
active desktop configuration. The public design guide and generated identity
projection expose only the selected profile. Historical comparison reports and
planning evidence remain separate and unchanged.

Start with [the desktop brief](../docs/design/desktop-brief.md), then read the
[selected identity](../docs/design/identity.md),
[implementation map](../docs/design/implementation-plan.md), and
[verification plan](../docs/design/verification.md).

`identity.json` contains historical explorations and the selected Neutral Slate
profile, with `selected_candidate` and `working_direction` both set to
`neutral-slate`. One theme is targeted initially; additional palettes are
deferred. The public site build reads this source for its colors, specimens,
downloadable identity, and Kitty fragment. `capabilities.json` distinguishes
managed behavior, locally available tools, and planned work, including Kitty and
Zsh.

The review board lives under `board/`. Build a dedicated export with:

```sh
.venv/bin/python design/build-review.py --output /tmp/niri-plus-design-review
node design/check-review.mjs /tmp/niri-plus-design-review
```

The output must be empty. The export contains only intended review assets.
Normal site builds include only their explicit identity/font projection. Mockups are labeled and do
not operate the desktop. Native widget samples, where included, are isolated
reference renders rather than captures of the daily session.

## Focused palette comparison

Compare Graphite Blue, Neutral Slate, and the Slate Blue blend side by side:

```sh
python3 design/build-comparison.py --output /tmp/niri-plus-palette-comparison
```

The export consumes the same `identity.json`, synchronizes four representative
surface groups, and can hold the UI font constant or show the original font
proposals. It includes exact color roles, calculated contrast pairs, and bundled
font provenance/licenses. These are design mockups; comparison does not add
supported runtime themes or select/deploy a palette.
