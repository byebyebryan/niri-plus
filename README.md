# Niri Plus

A personal Niri desktop shaped around Chrome, terminals, and coding agents.

**[Explore Niri Plus →](https://dev.byebyebryan.com/niri-plus/)**

Read [the story behind the setup](docs/story.md) for the personal workflow and
motivations, [take the tour](docs/tour.md), or start with the
[setup guide](docs/setup.md). The [project brief](docs/planning/project-brief.md)
preserves the original context and proposals.

The existing chezmoi source manages Bryan's machines. Component implementations
and releases remain in their own repositories.

## Local development

Requires Python 3.11+ and Node.js for the owned browser checks.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm ci
npx playwright install chromium
.venv/bin/python -B -m unittest discover -s tests -v
.venv/bin/python -B scripts/build.py --output /tmp/niri-plus-site
node scripts/check-browser.mjs /tmp/niri-plus-site
```

The output must be empty. Choose a new directory for each build, or remove only
your previous generated output. To preview with the site's project path, build
to an empty `/tmp/niri-plus-preview/niri-plus`, then serve its parent:

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory /tmp/niri-plus-preview
```

Open `http://127.0.0.1:8000/niri-plus/`. The build works offline once dependencies
are installed. It does not contact desktop runtimes or inspect the current host.

## Repository layout

- `docs/`: readable story, tour, architecture, setup recipes, and reference.
- `site/`: layout, presentation enhancements, CSS, and browser interactions.
- `examples/`: portable configuration, frozen helpers, and a source/hash manifest.
- `data/setup.json`: dated managed-source selections and personal policy context.
- `assets/`: reviewed application renders, attribution, and media provenance.
- `scripts/`: builder, owned headless browser checks, and social-image renderer.
- `tests/`: build and publication-boundary checks.
- `docs/planning/`: project brief and v1 delivery record; excluded from the site.

## Updating content and assets

The website uses the same Markdown as GitHub. The `niri-plus` enhancement comments
surround readable fallbacks that the builder upgrades into visual controls.
Keep both representations useful. Update the route map in `scripts/build.py`
when adding pages.

Record every reused image's source, license, and SHA-256 in
`assets/provenance.json` and retain `assets/LICENSES.txt`. The desktop walkthrough
is an illustration. The Rofi image uses fictional data in the real renderer;
SwayNC screenshots use an isolated native session. Their captions describe the
differences. Fresh daily-desktop recordings remain a future addition.

Update `examples/manifest.json` when intentionally changing an example. Keep
adaptations distinguishable from copied helpers. Refresh `data/setup.json` from
reviewed source selections rather than claiming a fresh-machine installation.
Regenerate the original social graphic with `node scripts/render-social.mjs`.

## Publishing

`.github/workflows/pages.yml` checks and publishes `main` with GitHub Pages.
Pages uses the GitHub Actions build type. The project inherits the portfolio
domain and needs no project CNAME or DNS change.

The build checks local links and anchors, metadata, public file inventory, and
media/example hashes. Browser checks cover nine pages at four widths,
keyboard operation, motion preferences, and reading without JavaScript. To save
local captures, set `NIRI_SCREENSHOTS=/absolute/directory` for the browser check.
Keep generated output and captures untracked.
