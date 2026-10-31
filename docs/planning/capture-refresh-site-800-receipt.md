# Current-site desktop capture receipt

This receipt records the fresh 1280×800 staged Arch media used by the current
Tour, Design page, controls recipe, and workflow gallery. The overview shows
the Niri Plus homepage in Chrome beside Kitty; the separate controls take shows
Audio and Network. The current captures replace the former Git-manual scene.
All ten earlier video records and all existing media bytes remain retained in
the archive and asset inventory.

## Browser source and guest scope

The guest displayed a prebuilt Niri Plus site export from source commit
`4e6bf087b2005f5c6f2ce7b79c53b803d66e819a`. A temporary loopback static server
served the exact 182-file snapshot at `http://127.0.0.1:8766/`; its total size
was 29,588,249 bytes. The browser page title was
“A desktop for the way I work — Niri Plus”. Its captured `index.html` was
14,368 bytes with SHA-256
`70451ac6222c1ea46ac362021e661ad88f07cce7e92997b9cc62e54ed6a58743`; the
source inventory confirmed the served snapshot matched. Chrome used a fresh,
signed-out temporary profile at 125% page zoom. The guest output was
1280×800 at compositor scale 1; the component bundle, package set, Niri
configuration and Kanshi configuration stayed on their captured 0.4.1
reference values.

Kitty showed a clean `octocat/Hello-World` checkout at commit
`7fd1a60b01f91b314f59955a4e4d4e80d8edf11d`. Its local file fixture used the
unchanged `tools/vm/desktop/sample_server.py` source, SHA-256
`757f1392d979e639b1878162e01d516c8ae5fb57b8b0b901ab0d87a7c71f44ee`. The
252-byte sample SHA-256 was
`c2440ff35a67921e891877abc7f210c9c869ff38f2c5c973fcd319147b5a2275`; upload
confirmation compared bytes in memory. These sample and fixture details do not
represent an authenticated user, provider session, fleet state, or deployment.

## Qualified recordings

Both takes are continuous, silent native `wf-recorder` captures at 30 fps,
H.264 High/yuv420p. Full decode and whole-frame black detection passed.
FFmpeg copy-faststart remuxing preserved each compressed video stream without
re-encoding, cropping, overlays, timing changes, or color conversion. The
container frame count includes one final discard packet beyond decoded frames.

| Clip | Duration | Decoded / container frames | Raw capture SHA-256 | MP4 SHA-256 | H.264 stream SHA-256 |
| --- | ---: | ---: | --- | --- | --- |
| `desktop-site-800` | 54.033333 s | 1,621 / 1,622 | `14a35b37dc209880dc38bfe15e738d9703b76b54feca6f4836a0a73b5e325cd9` | `43f3fc41805ed910e833bec2cb24c3b5cc546b56343a253ceacde0584c19f634` | `baca001f49fbcb10ec946cc50f18f21aad28befead4e0dcf66d8af58292251a3` |
| `controls-site-800` | 35.000000 s | 1,050 / 1,051 | `c7b76fe1cd7ca9ee423f1dd6a22d537f05a8873ff5f20d0436f92c98d999b52b` | `09765b3002f89c9893734f49e03e149585c14aa08135d79adf5a5845991e865b` | `d6f225329dea8444195be6d7e13121f76f4aeb71f0e47bb481a6986c1452fda4` |

The overview ran from `2026-10-31T02:52:02.601779Z` to
`2026-10-31T02:52:59.106057Z`. Primary-reviewed encoded-PTS links start at
browser 0, terminal 35, panel 40, and controls 50 seconds. The controls take
ran from `2026-10-31T02:53:07.417348Z` to `2026-10-31T02:53:43.466441Z`; primary
reviewed frames at 16, 21, and 31 seconds. Native capture times are recorded in
`assets/provenance.json`.

## Fresh stills and licensing

The eight destination files derive from fresh unedited native captures; six
distinct images were captured, and none is extracted from a video. The opening
image is byte-identical at its three intended destinations.

| Destination | Captured UTC | SHA-256 |
| --- | --- | --- |
| `assets/workflow-browser-site-800.png` | `2026-10-31T02:52:03.819432Z` | `814752bc98611ffbb900577ad300b303e4125af52a9697068759b1aa10e783df` |
| `assets/arch-reference/desktop-site-800.png` | `2026-10-31T02:52:03.819432Z` | `814752bc98611ffbb900577ad300b303e4125af52a9697068759b1aa10e783df` |
| `assets/demo-desktop-site-800.png` | `2026-10-31T02:52:03.819432Z` | `814752bc98611ffbb900577ad300b303e4125af52a9697068759b1aa10e783df` |
| `assets/workflow-terminal-site-800.png` | `2026-10-31T02:52:38.610579Z` | `7616c8949914db67cedda952d7d73f3d067647b2ce9457eeb210431c0616e651` |
| `assets/workflow-panel-site-800.png` | `2026-10-31T02:52:42.989002Z` | `918679c615c680a808a96e2eb5d42cf80026d7f48bd5487ce02b418b77d101fe` |
| `assets/workflow-controls-site-800.png` | `2026-10-31T02:52:53.653573Z` | `ed42a6b38cdb1d6cfd3b8fa1512b597bed800d6704485702ffc96319e17d6152` |
| `assets/demo-controls-site-800.png` | `2026-10-31T02:53:11.418649Z` | `53bfe0c347170af20483a61dcbcb0a46634f4764be77d7546b72da3d76213034` |
| `assets/agent-plus-site-800.png` | `2026-10-31T02:54:03.439206Z` | `e58b7301749ca5d3f3fe033575005e041e51861afa9fca350482489fe0f43dbd` |

The original capture media uses the repository MIT terms, except the overview
recording and panel still, which include the SwayNC fork interface and retain
its GPL-3.0-only attribution to Erik Reider and contributors. Those media
notices do not relicense the Niri Plus site source, SwayNC source, other
software interfaces, or fonts. The Agent Plus image uses the production
presentation renderer pinned to
[`rofi-agent-plus` commit `0230ce9288598842f5e8a6affc4593f332ba2d8a`](https://github.com/byebyebryan/rofi-agent-plus/tree/0230ce9288598842f5e8a6affc4593f332ba2d8a),
with fictional documentation rows. It does not depict an installed Agent Plus
runtime, provider discovery, authentication, live session, or remote action.

## Review and preservation

Primary visual review passed for the fresh native stills and representative
encoded frames. Human playback and aesthetic acceptance remain pending. The
combined source/build/browser integration gate passed on 2026-10-31:

- All 28 build contract tests passed.
- Normal and portable builds each validated 25 pages, 193 files and 960 local
  links.
- Each build passed 1,329 owned Chromium checks across 23 routes at 375, 768,
  1280 and 1600 pixels, including playback, seeking, current image paths,
  complete frames, Story redirects and JavaScript-disabled presentation.
- All 39 prior asset records and bytes, and all ten prior video records, were
  retained unchanged.

Luna prepared the scene and handled media/site integration. The primary
completed the recording-helper corrections, qualified captures, native cleanup,
preservation audit and final integration review.

After normal guest shutdown, the VM preservation audit passed: all 21
protected file hashes and sizes matched; inactive domain XML hash
`e4bcf9f070d00a9fa3470ca8d4b458ffd34755f59135f81c64c433b8bc8fdf73` was
unchanged; autostart remained disabled; package, Niri and Kanshi pins were
unchanged; and output/audio remained 1280×800 at scale 1, output 40%, input
100%, both unmuted. Cleanup receipts confirm the original download preimage and
clipboard history were preserved, the owned fixture and temporary profile were
removed, the loopback server stopped, and owned ports 8765, 8766 and 9222 were
absent. The VM is shut off.

This is staged-guest media evidence only. It does not claim physical-device,
provider-runtime, component-release, identity-release, fleet, or deployment
acceptance. Human playback and aesthetic acceptance remain separate from the
completed site integration checks.
