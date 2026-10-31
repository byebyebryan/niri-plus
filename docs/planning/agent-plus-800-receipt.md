# Agent Plus 800p capture receipt

The Tour's “Terminals and agents” section now uses a native full-desktop
1280×800 PNG, with the installed Neutral Slate Rofi theme over Chrome and Kitty.
The previous 1120×421 standalone blue-theme preview remains retained under its
original filename, hash, source and license; it is no longer the Tour image.

## What was captured

Agent Plus's production `_render` function generated its documentation sample
frame from public source commit `0230ce9288598842f5e8a6affc4593f332ba2d8a`
(version 0.15.0a17). The clean checkout matched the public main head at capture.
The frame was transferred to the guarded Arch guest and emitted by a temporary
read-only script-mode callback. Native Wayland Rofi rendered it with the normal
installed configuration and launcher key options. No preview color/font theme
was substituted. The foreground rows are fictional hosts, environments and
window titles, as labelled beside the image.

This is a production presentation-frame sample. The full Agent Plus runtime
is absent from this guest: no host discovery, provider authentication, live
agent session, window-opening or remote action is exercised. Existing producer
runtime qualifications remain separate. Chrome displays the public Story;
Kitty shows real Git output from the clean guest-only Hello-World sample.

The unedited grim PNG was captured at `2026-10-31T01:12:09.446704+00:00`,
from Virtual-1 at 1280×800@74.994, scale 1. Exact transferred PNG bytes are used;
no crop, resize, compositing, annotation or retouching was applied.

- PNG SHA-256: `a0ab6d4759a73990d6dbb3c435ce1549498c483e64512979dd0bc14f21fb3417`
- Production sample-frame SHA-256: `3c5f2c4c5b1444ec716f7d77ebc27f1f1213449fbe07b80dddbfc521c84cce6c`
- Producer preview script SHA-256: `9df19f4d3c53f0fe6279714fae3b89aa5e461cafe29f9617ffdedad9d8f5dc9a`
- Producer Rofi module SHA-256: `d592674c20509558132072940b1d4e9e59590134e5bdfcf2cdfe8961c17c5af8`
- Installed Rofi configuration SHA-256, unchanged before/after: `acf04989ee275cb47c88262da6c57f3ee7a447690216687dbf7266af30c1685a`

## Preservation and review

Components remain 0.4.1; the independent identity remains
`3fc1f9deef2bf7f4c377b34c452dcd965ac0e6dc5dcd96768ddbc6538321c563`.
Niri/Kanshi configuration hashes and the package inventory match the reference.
The owned callback/frame files were removed, Rofi exited through native Cancel,
and the guest shut down normally. All 21 protected file hashes/sizes match
preflight. Inactive XML remains
`e4bcf9f070d00a9fa3470ca8d4b458ffd34755f59135f81c64c433b8bc8fdf73`;
network/domain identity is unchanged and autostart remains disabled. Audio is
unchanged at output 40%, input 100%, both unmuted. No fleet deployment occurs.

Primary visual review passed. All 89 source tests passed (3 optional GI checks
skipped in the local venv). Normal and portable builds each contain 24 pages,
168 files and 941 validated local links. Both owned browser runs passed 1,105
checks across 23 routes at widths 375, 768, 1280 and 1600 with zero browser
errors, including full-frame geometry and full-size targets for both inline
captures. Native video playback/seeking, keyboard controls, reduced motion and
JavaScript-disabled content remain covered. `git diff --check` passed.

A rendered-Tour audit found all eight image elements (six stills plus two video
fallback posters) at 1280×800. Neither old inline image is used there. The old
Agent Plus asset/record and every video provenance record are unchanged.
Human review of this final page remains pending.

Local evidence: `/home/bryan/.local/state/niri-plus-lab/agent-plus-800-20261031T010941Z`.
Full source and file attribution is retained in `assets/provenance.json`.
