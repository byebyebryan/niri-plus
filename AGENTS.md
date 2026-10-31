# Niri Plus

This repository owns the presentation, personal story, desktop assembly guides,
and reusable first-party modules under `components/`. Preserve the first-person
story in `docs/story.md` as background notes; the standalone Story page is
retired from the site. Niri Plus owns these shared modules and their public
bundle format; independent projects retain their own implementation and release
authority. Chezmoi remains the authority for Bryan's personal machine selection,
configuration, and deployment.

`components/metadata.json` is the explicit input inventory and version source for
the component bundle. Generate current component examples with
`scripts/export-components.py`; retain authored portable profiles and historical
examples separately. Build artifacts with `scripts/build-components.py` from
the listed repository files only. Do not put personal policy, host state, or
third-party trees in this bundle.

Use `rtk` for shell commands. The site is generated from Markdown and small
HTML/CSS/JavaScript enhancements. Keep Markdown useful on GitHub. Label sample
renderings and illustrations at their point of use. Never present them as a
recording of the live desktop.

Run the build and owned browser checks before delivery. Do not test by operating
the user's desktop, notifications, clipboard, locks, or native agent sessions.
Keep generated output, local environments, and browser captures untracked.

Use Conventional Commits and review the staged file list. Publishing and remote
changes must stay within the user's authorized task.
