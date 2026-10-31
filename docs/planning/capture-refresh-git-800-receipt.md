# Git documentation capture refresh receipt

## Scope and outcome

This refresh replaces the retired Story page in the current home workflow
gallery, Tour, Design reference image, controls recipe, and Agent Plus still.
The earlier videos, posters, file records, clip records, capture inputs, and
qualification limits remain in the archive. The public Story redirect and
private notes remain unchanged.

Chrome shows the official Git project's static `git-status(1)` reference
manual at <https://git.github.io/htmldocs/git-status.html>, beside the existing
clean public Hello-World checkout in Kitty. The sample repository is
`octocat/Hello-World` at `7fd1a60b01f91b314f59955a4e4d4e80d8edf11d` on the
`public-sample` branch. A local loopback fixture serves a 252-byte public
sample and confirms uploaded bytes in memory; its endpoint is
`http://127.0.0.1:8765`. The browser uses a fresh signed-out temporary profile.
No account, provider, runtime, component, identity, color, package, device, or
desktop configuration changes were made for this capture.

The browser document's captured HTML hash is
`a21d07f7aca697cd0a2c185d945e0e2998dd714015e0a312a623c32d2d8dd5e9`
(`70,499` bytes). Its title is `git-status(1)`; the `NAME` and `DESCRIPTION`
anchors were present. The Git project and contributors retain attribution for
the reference manual. The Git website identifies reference-manual content as
imported from the Git project and available under its GPL terms; the Git
project's default is GPL-2.0-only unless a file states otherwise. See
[`git-status.adoc`](https://github.com/git/git/blob/master/Documentation/git-status.adoc),
[Git's license file](https://github.com/git/git/blob/master/COPYING), and
[the Git website's source notes](https://git-scm.com/site.html). These upstream
terms apply to the depicted manual, not to the original capture-media notices
or independent application interfaces and fonts. The inspected upstream
`COPYING` file was 18,765 bytes with SHA-256
`5b2198d1645f767585e8a88ac0499b04472164c0d2da22e75ecf97ef443ab32e`.

The Agent Plus image is a separate native still of the production
presentation-frame renderer, pinned to
[`rofi-agent-plus` commit `0230ce9288598842f5e8a6affc4593f332ba2d8a`](https://github.com/byebyebryan/rofi-agent-plus/tree/0230ce9288598842f5e8a6affc4593f332ba2d8a).
It contains fictional documentation rows. No Agent Plus runtime, provider
discovery, authentication, live session, or remote action is shown.

## Qualified recordings

Both recordings are continuous native 1280×800, scale-1 captures at 30 fps.
They are silent H.264 High/yuv420p streams. Full decode and whole-frame
black-detection checks passed. FFmpeg faststart remuxing changed the MP4
container only; the compressed video stream hashes match, with no re-encode,
crop, overlay, time change, or color conversion. The final container packet is
flagged discard, so the decoded frame count is one less than the container
count.

| Current clip | Duration | Decoded frames | Raw capture SHA-256 | Published MP4 SHA-256 | H.264 stream SHA-256 |
| --- | ---: | ---: | --- | --- | --- |
| `desktop-git-800` | 58.666667 s | 1,760 | `5118f162fa8514afbc31a073f402eca4db70041e166dad0693e450f1996d05ad` | `57e87c761f5c65476caaf0c861d04caa574ece0b1d230864a57ec0bcec2b0982` | `a1af888c7ebd473ad7c67f5bdddaab94e9d6c7daf6b86d453b04562bbe7c07a5` |
| `controls-git-800` | 36.000000 s | 1,080 | `9eda57ee6d4b8fdd399aed9e607066850bcabb1cb7611af52da3553470024b86` | `8d672a09823a23241f689845a21d913a15f454bb66d0b4ae1a16107a17bba8d3` | `b418f883fa350b1dad70dd031e5195553bdc3b5f6232c25d23c62eb8c7d136d6` |

The overview take ran from `2026-10-31T01:41:39.261202Z` through
`2026-10-31T01:42:39.106641Z`; its reviewed encoded-PTS links start at browser
0, terminal 38, panel 43, and controls 53 seconds. Primary visual review
checked the native stills and representative encoded frames, including those
watch points; the retired page is absent and the complete desktop remains in
frame. The captures use the staged environment at repository baseline
`0b461c35275ba203e401f3d4c86e2cc7c41b29ee`; the desktop component and identity
pins remain the same measured 0.4.1 tuple recorded in the media inventory.
The controls take ran from `2026-10-31T01:43:03.838884Z` through
`2026-10-31T01:43:41.427284Z`; decoded frames at 16, 21, and 31 seconds were
reviewed. The loopback fixture log records successful GET and POST requests,
with in-memory byte comparison.

## Native stills and licensing

The eight new still/poster destinations come from fresh native captures; none
is extracted from a video. The opening capture is copied byte-for-byte to its
three separately inventoried destinations.

| Destination | Captured UTC | SHA-256 |
| --- | --- | --- |
| `assets/workflow-browser-git-800.png` | `2026-10-31T01:41:40.483222Z` | `4fb077111842b32f49ba011c878fd8c42492d39641f782dc083071d0b0ca635d` |
| `assets/workflow-terminal-git-800.png` | `2026-10-31T01:42:19.011942Z` | `4d3edbad899ba88f6119fa0bbfff87d2b8945e319724df593cbe3a69e777463f` |
| `assets/workflow-panel-git-800.png` | `2026-10-31T01:42:23.404184Z` | `69bea795aa5a4b981531c39e28d978ce6c277bafee76b7b342a32037491e3cfa` |
| `assets/workflow-controls-git-800.png` | `2026-10-31T01:42:32.873447Z` | `bada27552776353fc3bdd17dbfed67c28b3d70e3cf089ba457abdc9a61ca6e67` |
| `assets/arch-reference/desktop-git-800.png` | `2026-10-31T01:41:40.483222Z` | `4fb077111842b32f49ba011c878fd8c42492d39641f782dc083071d0b0ca635d` |
| `assets/demo-desktop-git-800.png` | `2026-10-31T01:41:40.483222Z` | `4fb077111842b32f49ba011c878fd8c42492d39641f782dc083071d0b0ca635d` |
| `assets/demo-controls-git-800.png` | `2026-10-31T01:43:07.875731Z` | `fe1239f62024bc5cd91c77eac562164378d740936b943807d7df12be703aa36a` |
| `assets/agent-plus-git-800.png` | `2026-10-31T01:44:20.840436Z` | `6f47c09877edd40fa0952381ee54f2d871724b1c01a45136d2f73f0d5efb04f6` |

The opening poster is a separately captured MIT-licensed original still and
contains no SwayNC interface. The overview recording and panel still retain
the existing SwayNC GPL-3.0-only attribution and exact fork/recipe/source tuple.
The other new original capture assets are MIT-licensed, except for the panel
still. Those notices cover the original capture media; they do not relicense
the Git manual, SwayNC source, other application interfaces, or fonts. See
[`assets/LICENSES.txt`](../../assets/LICENSES.txt) and
[`assets/provenance.json`](../../assets/provenance.json) for attribution,
component and identity pins, source/output hashes, and per-file terms.

## Review and preservation status

Primary visual review of the native and representative encoded frames passed.
Capture, source-hash, full-decode, black-detection, and stream-preservation
checks passed. The combined repository gate passed on 2026-10-31:

- 111 unit tests, with three optional GI tests skipped in the virtual environment;
- component-export parity, 31 isolated desktop checks and 85 terminal checks;
- normal and portable builds, each with 25 pages, 182 files and 939 local links;
- 1,293 owned Chromium checks per build across 23 routes at 375, 768, 1280 and
  1600 pixels, including native video playback/seeking, current-image paths,
  responsive frames, Story redirects and JavaScript-disabled presentation;
- exact retention of the eight old clip records and 29 old asset records/bytes.

Luna handled site/media integration and regression checks; the primary handled
native capture, preservation, scene review and final integration acceptance.
Additive parallel away-mode source work is preserved in the repository; the
captured guest remains on its unchanged 0.4.1 tuple. No away-mode deployment or
runtime action was part of this refresh. Human playback and aesthetic
acceptance remain pending.

The VM postflight preservation audit passed after normal shutdown. All 21
protected file hashes and sizes match; inactive domain XML hash
`e4bcf9f070d00a9fa3470ca8d4b458ffd34755f59135f81c64c433b8bc8fdf73` is
unchanged; autostart is disabled; package, Niri and Kanshi pins are unchanged;
the output remains 1280×800 at scale 1; audio remains output 40%, input 100%,
both unmuted. The domain is shut off. Cleanup receipts confirm the loopback
fixture stopped, clipboard cleared, sample preimage restored, owned frame data
removed, and temporary browser profile deleted with no owned Chrome processes
remaining.

The two new videos are the current Tour players. The historical archive route
displays the previous eight video/poster pairs with their original bytes,
records, and qualification limits. Other earlier stills remain in the asset
inventory; they are not additional archive players. No physical-device,
provider-runtime, component-release, identity-release, or fleet-acceptance
claim is made by this media-only refresh.
