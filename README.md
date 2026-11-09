# Niri Plus

A personal Niri desktop shaped around Chrome, terminals, and coding agents.

**[Explore Niri Plus →](https://dev.byebyebryan.com/niri-plus/)**

Take [the tour](docs/tour.md), or explore the
[setup overview](docs/setup.md) for reference and explanation. For installation,
we recommend giving your agent the [detailed setup guide](docs/setup-agent.md).
The [component source map](docs/components.md)
explains reusable public code, portable exports and private consumer ownership.
Chezmoi remains the authority for personal machine configuration and deployment.

## Local development

Requires Python 3.11+ and Node.js for browser checks.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm ci
npx playwright install chromium
.venv/bin/python -B -m unittest discover -s tests -v
.venv/bin/python -B scripts/export-components.py --check
.venv/bin/python -B scripts/check-desktop.py
.venv/bin/python -B scripts/check-terminal.py
.venv/bin/python -B scripts/build.py --output /tmp/niri-plus-site
node scripts/check-browser.mjs /tmp/niri-plus-site
```

Choose a new empty output directory for each site build. To preview the public
project path locally, build into `/tmp/niri-plus-preview/niri-plus`, serve its
parent, then open `http://127.0.0.1:8000/niri-plus/`.

Published components 0.9.2 include an opt-in
[unified session screen](docs/recipes/session.md#optional-unified-session-screen).
Ctrl+Alt+Delete opens the action grid only when its portable profile is selected;
the published release catalog and numbered reference remain separate. The
current 0.4.3 Arch install target selects SwayNC 0.12.6-18 from fork release 1.
The [2026-11-08 qualification](docs/planning/reference-qualification-20261108.md)
completed 21 mapped routine native task groups through an independent fresh
replay and supplemental checkpoint-copy checks, including cold wallet lookup
and the conditional VirtIO monitor-sharing branch.
The VM suspend/resume check is waived for this qualification at Bryan's request.
Physical-device acceptance remains separate. Existing captures retain their
original package 17 provenance; the earlier 0.4.1 replay remains historical.
Managed-host rollout is recorded separately in [setup status](data/setup.json)
([dated receipt](docs/planning/swaync-reference-sync-20261107.md)). The
previous 0.4.1 setup guide remains available at
[source revision 4672016](https://github.com/byebyebryan/niri-plus/blob/4672016e7cfe4f4631b67209636b0720e9068784/docs/setup-agent.md).

Published [components 0.10.0](https://github.com/byebyebryan/niri-plus/releases/tag/components-v0.10.0) add an optional
[desktop-wide Close All helper](docs/recipes/desktop-utilities.md#optional-close-all).
It snapshots window IDs once and preserves application save dialogs. Its
Mod+Shift+Q profile is opt-in and leaves Mod+Q unchanged. Consumers verify the
immutable archive and select only the helper/profile beside their existing pins.

The build and module checks work offline after dependencies are installed. They
use declared repository inputs; they do not inspect or operate a desktop.

The 0.4.3 numbered Arch reference includes [direct Rofi controls](docs/recipes/rofi-controls.md).
They can also be adopted separately. Native binding tests need the system
Python with PyGObject/libnm/libsecret; environments without those bindings report
explicit skips. Run the separate required native gate on an equipped machine:

```sh
/usr/bin/python3 -B -m unittest discover -s tests -p 'test_controls_*.py' -v
```

The owned native Rofi, NetworkManager, secret-agent, Audio and BlueZ checkers in
`scripts/check-controls-*` and `scripts/check-rofi-controls-native` qualify
isolated clients/services. They are opt-in, have explicit prerequisites and
do not use physical devices as fixtures. Their results and remaining hardware
checks are recorded in the [implementation receipt](docs/planning/rofi-controls-implementation-receipt.md).

## Repository layout

- `docs/`: background notes, tour, architecture, setup, component ownership and recipes.
- `site/`: page layout, CSS, and small browser enhancements.
- `components/`: reusable desktop, shell and appearance sources.
- `components/metadata.json`: explicit bundle inputs, module prerequisites and
  generated public exports.
- `examples/`: portable profiles, generated downloads, historical examples and
  their source/hash manifest.
- `data/components.json`: immutable producer version, checksums and current
  consumer qualification status.
- `data/setup.json`: dated managed-source and personal deployment evidence.
- `assets/`: reviewed media, attribution and licenses.
- `scripts/` and `tests/`: site, archive, export and headless checks.
- `tools/vm/`: guarded Arch guest assembly, sample fixtures and native capture
  tools. VM definitions and original media stay outside Git; see the
  [desktop demonstration receipt](docs/planning/desktop-demonstration-receipt.md).

## Updating sources and examples

Edit shared code in its canonical `components/` module. Regenerate public
examples with `scripts/export-components.py --write`; keep authored portable
profiles and historical specimens separately labeled. Run the exporter in
`--check` mode before publishing.

Build a component bundle from a reviewed full commit with
`scripts/build-components.py`. Its archive is independent from the website
build, uses only declared inputs, and carries file hashes and modes in a root
manifest. Publish a new immutable version, record its archive and manifest
hashes in `data/component-releases.json`, then update the consumer's exact code
pin. Keep `data/components.json` pinned to the independently qualified baseline
until a new whole-reference qualification is recorded.
The [source map](docs/components.md) describes staging, separate identity and
utility selection, and scoped application. Shell startup does not install
components or fetch dependencies.

Keep public example provenance current in `examples/manifest.json`. Record
reused media in `assets/provenance.json`, retain licenses, and keep generated
site output and local environments untracked.

## Publishing

GitHub Actions checks and publishes the site from `main` through GitHub Pages.
The site build verifies local links, page metadata, public inventory and
example/media hashes. Browser checks cover responsive pages, keyboard behavior,
and use with JavaScript disabled. Component archives have their own immutable
release and SHA-256; publishing the site does not publish or select a machine
configuration.

The [Neutral Slate design](docs/design.md) and [contrast study](docs/design/contrast.md)
retain the selected desktop specimen and design history. The public page is the
main walkthrough; this README covers repository work and release maintenance.
