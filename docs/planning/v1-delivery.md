# Niri Plus v1 delivery

V1 presents Bryan's Niri desktop through the personal story, an illustrated
workflow tour, native component renders, and portable setup recipes. It keeps
the two halves of daily work visible: Chrome and graphical file interaction,
and terminals and agents for building and operating things.

## First edition scope

Nine public pages cover the overview, story, tour, architecture, setup,
notifications, clipboard, session services, and reference. The story remains in
the first person. Guides are readable Markdown and feed the same site build.

The tour has four keyboard-operable scenes. It is explicitly illustrated. The
Agent Plus image uses the real Rofi renderer with fictional environments. The
SwayNC images use the selected native fork in an isolated session, with fixture
wireless/GPU data and local CPU/RAM readings. Captions identify their limits.
The original images and provenance are retained.

Nine example files include a portable Niri configuration, portal preferences,
clipboard collection and selection, readiness checking, manual locking, and
fork notification configuration/theme. Every example has a recorded hash and
origin. Private chezmoi configuration stays private; public recipes include
their required helper files.

## Decisions for this edition

- Python and pinned MarkdownIt produce a static site; small CSS/JavaScript
  enhancements supply the interactive presentation.
- The canonical checkout is `~/code/niri-plus` and the GitHub repository is
  `byebyebryan/niri-plus`.
- GitHub Pages publishes under `https://dev.byebyebryan.com/niri-plus/`,
  inheriting the existing portfolio domain. No new DNS or project CNAME is used.
- Component implementation and releases remain with their existing owners.
- Portable examples have explicit scope and do not apply configuration on build.
- Clipboard, notification, and session recipes can be followed independently.
- Source selections are dated; they do not claim a clean-machine installation.

## Local verification

On 2026-10-24:

- Seven build tests pass, covering complete output, broken links, attributed
  media and example changes, unexpected output, nonempty output preservation,
  and isolation of private/personal configuration.
- The build checks nine pages, 31 public files, and 218 local links/anchors.
- 262 owned Chromium checks pass across widths 375, 768, 1280, and 1600,
  including keyboard scene switching, reference filtering, reduced motion,
  skip navigation, and reading with JavaScript disabled. No browser errors.
- Desktop and mobile renders were visually inspected, including the homepage,
  personal story, tour, and architecture.
- The Niri example passes `niri validate`; the Python helpers and notification
  JSON parse. These syntax checks do not start desktop applications.
- Seventeen external navigation destinations resolve successfully.
- A source-based content review corrected build prerequisites, portal ordering,
  notifier activation, private source links, and hardware support descriptions.

The GitHub workflow repeats the build and browser checks before Pages delivery.
Remote branch parity, workflow success, and served artifact bytes are verified
separately at publication.

## Published edition

The [first publication](https://github.com/byebyebryan/niri-plus/actions/runs/40125177001)
passed on 2026-10-24 from site source `9ef2c5f361ed76c5804e8567cfca026fb94ac61f`.
All 30 served pages/assets/examples match the reviewed build byte for byte;
`.nojekyll` is a build-control file excluded from HTTP comparison.

An owned headless browser verified the public homepage, scene interaction,
navigation to the personal story, and keyboard-reference filtering, with no
browser errors. The [publication record](v1-publication.json) preserves URLs,
artifact hashes, and these checks. Later changes to this nonpublic planning
record do not change the recorded site artifact.

## Remaining acceptance and media work

The daily desktop still needs a representative real-session recording. Current
media demonstrates the workflows through an illustration and isolated native
application renders. It does not show private browsing or conversations.

The recipes have source, syntax, and site verification. Installing the complete
setup on a clean machine, hardware-specific power behavior, authentication,
screen sharing, and physical lock/suspend behavior require target-machine
acceptance. The public session example covers manual locking; the private
per-host battery/power orchestrator is not distributed as a universal default.
