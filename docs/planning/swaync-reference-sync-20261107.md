# SwayNC reference and showcase sync, 2026-11-07

This pass selects the already published components 0.4.3 and SwayNC 0.12.6-17
for the numbered Arch reference and current showcase. It does not publish a new
component release or change personal fleet policy. The maintained SwayNC fork
branch is `niri-plus`; immutable source and recipe pins remain independent.

## Inputs and preserved evidence

The component archive is built from `07cf4a393314c195ace7e66d162f21d3a2f73136`,
archive SHA-256 `146b4d4b81dac3804b5836348045b5b89a8fa3c62719b643a90302da8346d87a`,
manifest SHA-256 `31a30ac9f11dcb4182e9b0c26e5c33ca741bdb28a2c1a195f298db8ea79dd79b`.
All 44 payloads and modes are verified by the reference stager. The identity is
independently pinned to `c4d61361a61dcd900e23c07d01f02ebe6b326529ccd144e86c7460d672ea1e5e`;
the public examples use the same immutable source commit, with manifest SHA-256
`86cb3c932bb4652dc1c476c6b36ddc9a3bb069fa2456e55ae855753dc9182b6d`.

The reviewed checkout supplies the authored notification profile separately:
SHA-256 `c40e8a0cbf1327c87b5b713b6c68ba3d0462dff654d7b51d1bd58333bdf79543`.
It selects width 448, full-height fit, zero margins, individual notification
cards and `information`, `title`, `notifications` widgets. The information
surface shares notification-card styling, with bold time/plain date and paired
primary-interface identity, Signal/IP and upload/download details.

SwayNC recipe `c6eeafb4ded51afc0a5f9a3d092fb1d4a86d0662` has archive SHA-256
`f733190593dac14a9bbf47f286ed23b8681b80d53f5c88282a6d873f87a02d5a` and selects
source `3d4458262c23ac66820cbb7a63b171bab1053ae8`, archive SHA-256
`11d591899424a1cdc6a627c53f2b2aab3a91e56fa1ff390ba0d4878806e832e6`.
The ordinary-user makepkg build installed `swaync-bryan 0.12.6-17` in the owned
reference guest. The existing package/source release is unchanged.

The previous reference input inventory and authored profile are retained
byte-for-byte under `tools/reference/history/*-0.4.1.json`. Previous setup and
component records are retained under `data/history/*-0.4.1.json`. All twelve
previous video records and their media bytes remain unchanged; the two prior
homepage recordings move to Earlier recordings. Historical identities and the
legacy VM assembly pin remain frozen. New captures use a retained sidebar
identity under `design/history/neutral-slate-sidebar.json`.

## Owned reference validation

Validation uses a new disposable libvirt domain `niri-plus-swaync-sync-20261107`,
a standalone copy of the immutable 184-package installed-Arch checkpoint and a
separate EFI variables file. The existing desktop guest remains shut off.
A full Arch upgrade, foundation install and actual published-input staging
passed before appearance/config installation. No private machine configuration,
wallet, browser profile, notification history or agent session was imported.

Stock SDDM password login, logout/relogin, theme preview and installation, and
password login after reboot passed with the distribution PAM stack unchanged.
The new kernel is `7.2.14-arch1-1`; Niri is `26.04-1`, SDDM `0.21.0-7`, Chrome
`156.0.8078.47-1`. The normal reference account remains `demo`, with an ordinary
Bash login shell and Kitty's explicitly selected Zsh login command. Chrome used
its real first-run flow: lab-only terms accepted, default-browser selection
retained, usage statistics disabled and account left signed out.

NetworkManager took over the clone's single Ethernet interface from networkd
using the documented recovery timer. DNS, route and outbound HTTPS passed;
networkd is inactive and resolved remains the DNS owner. No Wi-Fi, Bluetooth,
NVIDIA GPU or battery hardware is supplied. The panel shows real guest CPU/RAM,
Ethernet address and measured network rates, with missing hardware sections hidden.

The installed profile and rendered CSS match the staged hashes. Full-height
attachment, matching information/card surfaces, equal clock/date columns and
separate cards from one sample app were inspected against the black terminal.
DND toggles through its actual UI and returns to false. Closing/reopening the
panel works without replacing the daemon. Installed Audio and Network entries
open the retained direct controls and native Details pages.

Native clipboard checks passed exact text and PNG restore through the installed
picker, Delete, Cancel with unchanged history and confirmed Clear on owned
samples. Panel reopen retained PID 652 and its service invocation, with DND
restored to false. No CSS loading errors or daemon crash occurred. Two pairs
of GTK surface-position assertions were logged during discarded capture setup;
the accepted takes and final lifecycle check completed with the same daemon.
These runtime warnings are retained in the lab journal for fork follow-up.

Capture qualification, preservation and site checks are recorded below. This is a scoped refresh of the changed
installation/login/sidebar/control path. The earlier complete 0.4.1 task replay,
including whole-monitor sharing, remains a dated independent record. This pass
does not relabel old sharing, wallet, IME, suspend or physical-device evidence
as a new complete replay. Human playback and physical display acceptance remain separate.

## Current media

The accepted videos are continuous, silent native `wf-recorder` takes at
1280×800, compositor scale 1 and Chrome page zoom 125%. Chrome's application menu
was visually checked at 125% before recording. Both use H.264 High/yuv420p,
30 fps. Full decode and full-frame black detection passed with
`d=0.20:pix_th=0.10:pic_th=0.999`; no black intervals were found. Copy-faststart
remuxing preserved each compressed stream without re-encoding, cropping,
overlays, timing changes or color conversion. The final discard packet explains
the one-frame difference between container and decoded counts.

| Clip | Seconds | Decoded / container frames | Raw SHA-256 | Output SHA-256 | H.264 stream SHA-256 |
| --- | ---: | ---: | --- | --- | --- |
| `desktop-sidebar-800` | 33.900000 | 1017 / 1018 | `4118557c8ee85d10bc2f69f3e01c4235a50dc6c5a1c726d0542e233791417143` | `3493f4ad2b8e314fc2de60a34c8a0a1caf758841a073218de64a4bfcdd2456a1` | `55cf0c45d029c4f2802f013eb3fab5117ded8aa1c855cb7750a20420cef5d071` |
| `controls-sidebar-800` | 23.033333 | 691 / 692 | `f684d7da2db0ef0f2f80bbae4df6a9c954184d8de269328c645be3e7b5ad787e` | `51251a8ba37e07cd5d65c64873dd4f6b5e1f5fcb8f851751a21a4d6f2098183b` | `5566a77ec3a493dd4d46fb5df2c9e4747a8defb505f7176d1fc125d8301e0be3` |

The overview covers terminal work, time and system/network readings, individual
same-app notification cards, DND on/off restoration, panel reopen and Audio.
Its reviewed encoded-PTS links start at 0, 6, 11 and 29 seconds. The controls take
shows installed Audio/Network entries and their native Details pages. These
menus are invoked through their installed desktop entries with `gtk-launch`;
normal Mod+D application-list selection was checked separately. New clips do
not claim the archived volume/mute adjustment sequence or browser file tasks.

Seven new PNG destinations derive from five independent, unedited native
`grim` stills; the opening still is copied byte-for-byte to the poster,
workflow browser and Design-page destinations. No poster is a decoded video
frame. The new overview video and panel still retain GPL-3.0-only SwayNC
attribution; the opening poster and remaining original capture media use MIT.
Independent software, fonts and depicted source keep their own terms.

Chrome displays a frozen portable export of published main commit
`4672016e7cfe4f4631b67209636b0720e9068784`, served on guest loopback port 8766.
All 203 transferred file hashes matched the built inventory; index.html SHA-256
is `b22fc72ae02554b02a42ddb76b564a0afb8a0b64e00e4a4ca213bbbb1548bf4c`.
The browser stays signed out and Kitty shows clean `octocat/Hello-World` commit
`7fd1a60b01f91b314f59955a4e4d4e80d8edf11d`. This public browser content is
independent of the current desktop component/package tuple. Exact capture
UTCs, source versions, native measurements, hashes and separate review states
are in [media provenance](../../assets/provenance.json).

Primary visual review passed for the full-frame native stills and representative
encoded scenes. Human playback and aesthetic acceptance remain pending.

## Integration and preservation

The previous 49 asset records and their bytes, all 12 prior clip records and
both historical data snapshots were checked unchanged. Media package tuples
use retained pins, so a future selected reference pin cannot rebind these clips.

The new guest shut down normally. The original domain remained shut off; its
inactive XML matched SHA-256
`e4bcf9f070d00a9fa3470ca8d4b458ffd34755f59135f81c64c433b8bc8fdf73`.
The immutable base disk, base EFI and previous final 0.4.1 disk matched their
pre-run SHA-256 values. Original network XML is unchanged and the initially
inactive lab network was returned to inactive. The new standalone disk and EFI
are retained for recovery; neither guest has autostart enabled.

The installed profile/Niri/Kanshi/policy hashes were checked unchanged after
capture, DND is false, owned clipboard history returned to its initial empty
state, no recorder remained and the owned loopback server stopped. Guest logs,
staging receipts, raw captures, encoded-frame checks and preservation records
remain under the task's local lab state directory. No user desktop operations,
personal consumer writes or host service restarts were performed.

The reference stager's 10 contract tests passed, including exact 0.4.3 archive
reconstruction, all 44 payloads, authored profile/hash and frozen 0.4.1 history.
Component export check found no changes; desktop 44 checks, shell 85 checks and
all 74 native-binding controls tests passed. Final local integration passed: 190 source tests (three unavailable-bindings
skips covered by the separate 74-test native run), 30 focused build contracts,
normal and portable builds of 25 pages/220 files/1040 local links, and 1372
owned Chromium checks per build across 23 routes at 375/768/1280/1600px, with
JavaScript enabled and disabled and zero browser errors. Checks include all 14
players, seeking/ranges, current media paths, complete frames, responsive
contents and historical reachability.

Luna prepared documentation, reference-stage tests and media/browser contract
updates. The primary owned immutable-reference contracts, fresh VM setup,
native qualification/capture, provenance, preservation, history-test corrections
and final integration review. The optional 0.5.0 Away parity test now explicitly
compares its original 0.4.1 baseline; it does not pretend that archive contains
the later 0.4.3 sidebar backport. Publication follows [PR2](https://github.com/byebyebryan/niri-plus/pull/2)
and its [Actions checks](https://github.com/byebyebryan/niri-plus/actions/workflows/pages.yml).
Those live records identify the resulting source commit and Pages deployment;
local acceptance above is independent.
