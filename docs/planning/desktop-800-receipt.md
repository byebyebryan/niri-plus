# Native 800p showcase receipt

The current Tour, home workflow gallery and Design still use native 1280×800
capture at scale 1. Complete frames preserve the browser/terminal context;
no crop or image enlargement is applied. Page contents remain in a collapsible
left sidebar, with a bounded wider content column. Earlier qualification
screenshots and all six earlier videos retain their original dimensions,
provenance records and bytes in the recording archive.

## Capture and media checks

Two fresh continuous, silent takes were recorded with wf-recorder 0.6.0-2,
libx264, yuv420p, CRF 18, medium preset and a 30 fps target. The overview
started at 2026-10-30T23:57:40Z; controls started at 23:59:31Z and ended on
2026-10-31 UTC. The guest stayed in its preferred 1280×800@74.994 mode at scale 1.

| Clip | Duration | Decoded frames | Average frame rate |
| --- | --- | --- | --- |
| desktop-800 | 58.0 s | 1740 | 30/1 |
| controls-800 | 36.0 s | 1080 | 30/1 |

Both complete FFmpeg decodes passed. Whole-frame blackdetect found no interval
of at least 0.20 seconds with at least 99.9% of pixels below 10% luma.
Representative encoded frames were reviewed for files, chooser, terminal,
panel, clipboard, volume/mute and Ethernet. Action timestamps are a separate
wall-clock log and are not claimed as exact encoded presentation timestamps.
TV range was requested; ffprobe has no explicit color_range field.

MP4 faststart remuxing moves the index ahead of the media for browser delivery.
This is stream-copy only: raw and output container hashes differ, while the
compressed H.264 stream hashes match. No re-encoding, color conversion, cuts,
overlays, compositing, time changes or reused footage were applied.

Posters are separate unedited grim PNGs captured during each take. The four
workflow stills and Design still reuse the accepted 2026-10-30 native 800p trial
byte-for-byte; they are independent captures, rather than decoded video frames.
Their separate timestamps and hashes are recorded in assets/provenance.json.

## Native interactions

The overview downloads the owned 252-byte Markdown sample, opens it through
Dolphin in Nvim, then selects it with Chrome's GTK chooser. The loopback fixture
confirms an exact-byte upload, SHA-256
`c2440ff35a67921e891877abc7f210c9c869ff38f2c5c973fcd319147b5a2275`.
Git output comes from the clean public Hello-World sample at
`7fd1a60b01f91b314f59955a4e4d4e80d8edf11d`. SwayNC shows real guest
CPU/RAM/Ethernet readings. Clipboard restores the owned public sample text.
No screen-sharing request is activated.

The controls take inspects Audio Details, adjusts output 40% → 45% → 40%,
mutes/unmutes, and displays Ethernet details without changing connectivity.
Every audio transition is independently checked with pactl; final output is
40%, input 100%, both unmuted. One unsuccessful preliminary controls take was
retained locally and excluded; it made no audio changes.

## Source and preservation

Components remain 0.4.1 at `317658ee7913bb58536f6ec1b2575043a9494449`,
with archive SHA-256
`0940e0803c84bc6e1cb941ea4074f14a02db0d124bd8c1c676c3375147427d11`.
The independent identity remains
`3fc1f9deef2bf7f4c377b34c452dcd965ac0e6dc5dcd96768ddbc6538321c563`.
The SwayNC fork pin, package inventory, Niri config and Kanshi config match the
accepted reference. This changes presentation media and layout only.

The guarded working guest was shut down normally after stopping the owned
fixture and recorder. All 21 protected file SHA-256 hashes and sizes match
preflight. The inactive XML remains
`e4bcf9f070d00a9fa3470ca8d4b458ffd34755f59135f81c64c433b8bc8fdf73`;
network/domain identity is unchanged and autostart remains disabled.
The six prior video/poster bytes and clip records match the published baseline.

Local evidence: `/home/bryan/.local/state/niri-plus-lab/desktop-800-20261030T234656Z`.
The earlier still trial is `low-resolution-trial-20261030T224118Z` in that lab.

## Site validation and delivery

Validation passed: 89 unit tests (3 optional GI checks skipped in the local
venv), 31 isolated desktop checks, 85 terminal checks, and unchanged component
exports. Normal and portable builds each contain 24 pages, 166 files and 938
validated local links. Both owned browser runs passed 1,085 checks across 23
routes at widths 375, 768, 1280 and 1600, including all eight clips, actual
playback/seeking, uncropped gallery frames, sidebar keyboard interaction,
reduced motion and JavaScript-disabled behavior, with zero browser errors.
`git diff --check` passed.
This receipt is a local candidate; it is not a Pages publication or a new
component/identity release. Physical Wi-Fi, Bluetooth, display/OLED and audio
acceptance remain separate, as does human review of the finished page/videos.

desktop-800 output SHA-256: `6fc730cfd4badf7198c02829f2dbb60e6f1406acdbd868e229eb8821e378bf75`.
Raw capture SHA-256: `f79b831d4607bbf6bdf7eb645bb06f2affaa9aca451cc5e80cd6afb50360e92b`.

controls-800 output SHA-256: `9345998c3497b8b246700cfd77813fedde796d60a38bea1af1ea1a1f15d39c0e`.
Raw capture SHA-256: `ef996fd6228a1a7d1ef8e748423f206593a13365cb04daec3b95f8b0fc0d3fc2`.

## Information section follow-up

The Tour's “Information when I want it” section now uses the same complete
native 1280×800 SwayNC desktop capture as the workflow gallery. It fills the
content column and links to the original image. This replaces the older
isolated panel rendering in that section, whose crop styling conflicted with
the prose image width. The fixture image and its provenance remain retained.
Browser checks at all four widths verify native aspect ratio, frame alignment,
full content width and the full-size target. No new capture or VM operation was
needed; the accepted 800p image bytes and provenance are unchanged.
