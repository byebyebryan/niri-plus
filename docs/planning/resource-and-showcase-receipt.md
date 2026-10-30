# VM resource observation and current showcase receipt

Recorded 2026-10-30 UTC against the
[approved resource/showcase plan](resource-and-showcase-pass.md). Sol owns the
storyboard, design, copy, integration and acceptance. Luna Max handles the
bounded guest measurements and native capture mechanics.

This pass reuses components 0.4.1, the independently pinned black-workspace
identity and the accepted installed-Arch working guest. The
[previous receipt](black-workspace-receipt.md) records that release, its fresh
reference and scoped delivery to Carbon, Starship and Snap. This pass does not
change the component bundle, selected identity or managed host configuration.

## Measured scope

The resource observation runs inside the existing Arch QEMU/VirtIO guest with
4 vCPUs and 8 GiB assigned, at 1280×800, scale 1. No physical-host desktop
baseline is taken. Host load is context for contention; guest figures do not
establish laptop battery use, physical GPU/display behavior or workstation
resource requirements.

The guest enters through its normal SDDM password login. Chrome displays the
public Niri Plus Story page and Kitty/Zsh opens the clean `public-sample`
branch of `octocat/Hello-World` at
`7fd1a60b01f91b314f59955a4e4d4e80d8edf11d`.

The small private collector reads CPU ticks from `/proc` at 1 Hz and samples
PSS every ten seconds. It identifies processes by PID plus start time, keeps
declared desktop owners distinct from Chrome, Kitty/Zsh and the sampler, and
records process/unit membership and PSS-read coverage. CPU 100% means one guest
vCPU. Short-lived processes between samples can be missed; the launcher phase
supports cleanup and observed responsiveness, not precise launch latency or
complete transient CPU accounting. Memory values describe the recorded cohort,
not every service needed by the OS.

No recording/encoding runs during the resource phases. No desktop settings,
service configuration, networks, radios or physical devices are changed for the
measurement. Missing hardware remains absent.

The run retained 394 samples over approximately 394 seconds, including two
launcher cycles. The table shows duration-weighted mean CPU from the retained
per-process tick deltas and consecutive monotonic sample times. First and
cross-phase intervals are excluded. The original collector's aggregate CPU
field is not used: review found that its denominator omitted collection work.
The raw ticks/timestamps support the corrected analysis without another run.

| Phase | Wall-time target | Core mean CPU, one vCPU | Core sampled 1-second peak | Readable core PSS median |
| --- | --- | --- | --- | --- |
| Initial quiet | 60 s | 0.10% | 1.00% | 233.8 MiB |
| SwayNC open | 30 s | 0.45% | 2.00% | 256.4 MiB |
| SwayNC closed | 60 s | 0.12% | 2.00% | 255.6 MiB |
| Quiet after first launcher cycle | 60 s | 0.08% | 1.00% | 257.7 MiB |
| Quiet after second launcher cycle | 60 s | 0.10% | 1.00% | 257.7 MiB |

The core cohort includes Niri/Xwayland, SwayNC, Kanshi, Fcitx, clipboard
collectors, idle/battery helpers, authorization and selected portal/audio
processes. Chrome, Kitty/Zsh, the sampler and unassigned system services stay
separate. One core member, the polkit agent, has unreadable PSS; the memory
column sums only readable members, with that omission in every reading.
Nothing substitutes summed RSS for missing PSS. This is not a total OS or
complete desktop memory figure.

For comparison within the final quiet phase, the separately attributed mean
CPU observations were Chrome 0.00%, Kitty 0.03%, Zsh and its descendants 0.39%,
and the sampler 1.37% of one vCPU. A 0% median at the collector's one-tick
resolution does not mean a process performs no work. The sampler's own
activity and the short window limit interpretation of very small values.
Guest steal was zero outside settle; the settle peak was 0.248% of total
guest CPU ticks. Host load was retained as context, without a host benchmark.

All eight launcher/clipboard/Audio/Network opens across the two cycles had a
Rofi process observation; final quiet had none. The only new running user unit
was `pipewire-pulse.service`, activated normally by Audio. Other declared
running units were retained, with no duplicate process identities in either
census. These checks support cleanup, not a complete accounting of every
short-lived helper.

SwayNC PSS rose from 32.6 MiB before its first open to 57.3 MiB at the end.
The later quiet readings remained stable. CPU returned to the initial quiet
range after close; memory did not return to its pre-open figure. This short
observation found retained state rather than continued growth through the
repeat, and does not establish long-run leak freedom. No optimization or
component change followed from the result.

Raw samples, action/phase logs, exact cohort/census, read coverage, source hashes
and corrected analysis are retained in the dated resource-showcase evidence
directory outside Git. The sample JSONL SHA-256 is
`1be1114d3199b4e9ff73696b56bc584bb31168572cbb1f356dbdf7e554daf2df`.

## Current native overview

The overview follows the two halves of the desktop: browser and ordinary file
interaction beside terminal work, with information and controls available on
demand. The selected appearance and normal gaps remain intact. The accepted
35.4-second controls clip and current desktop still are reused unchanged.

The accepted overview is one continuous 82.433333-second, silent native take at
1920×1080, scale 1. It enters and leaves Niri overview, downloads a public
Markdown sample in Chrome, opens it from Dolphin in the registered Nvim
handler, selects the original file through the GTK chooser and uploads it.
The local fixture confirms the same 252 bytes and SHA-256:
`c2440ff35a67921e891877abc7f210c9c869ff38f2c5c973fcd319147b5a2275`.
It then shows real Git output, SwayNC's available guest metrics, restoration of
an owned text clipboard sample, Audio's default device state, and the original
Story/Kitty pair. No sharing request or audio setting change occurs.

The public MP4 equals the raw capture, SHA-256
`4a78cfa72a3d704f0cbd6416434dd90ad6d90c7fef99ad11cafa63a44c6fae35`.
There are no cuts, overlays, time stretching or composited actions. Full decode
passes with 2473 frames; the container reports 2474. The stream has nominal
cadence `30/1` and average-rate field `74220/2473`; decoded frames divided by
container duration is 30.0 per second. TV range was requested and the encoder
log reports `yuv420p(tv)`, while ffprobe has no explicit color-range field.
No later color conversion was applied.

Sol reviewed decoded frames at their encoded timestamps, including Nvim at
22 seconds, the clipboard picker at 52 seconds and Audio at 58 seconds.
A whole-frame blackdetect check found no interval of at least 0.20 seconds with
at least 99.9% of pixels below the 10% luma threshold. This is a blank-frame
check, not a display calibration. Failed rehearsals and a rejected take remain
private evidence and are not the published media.

The poster is an unedited native pre-take rehearsal PNG of the same opening
scene, rather than a decoded movie frame. Its SHA-256 is
`863107cf7db9740113bbd0f7aa0c4d2c2b1aae9622a888aafadfba5f99d543af`.
Exact source, fixture, package and media records are in
[asset provenance](../../assets/provenance.json).

### Current capture procedure

Use the accepted working guest, checking its guarded domain/disk identity,
installed bundle and identity before login. Keep the normal theme, gaps and
application sizes. Stop the sampler, prepare public/local scene content and
rehearse without recording. Temporarily select the advertised 1920×1080 mode
through the guest's existing Kanshi profile; retain its exact preimage.
The recorder is wf-recorder 0.6.0-2 with FFmpeg 2:9.0.2-2, started as a
single owned transient user unit with this command:

```sh
wf-recorder --file /tmp/niri-plus-overview.mp4 --codec libx264 \
  --framerate 30 --pixel-format yuv420p --codec-param color_range=tv
```

Stop only that recorder with SIGINT and wait for clean exit. Transfer the
original bytes, compare guest/local hashes, run full decode/probe and inspect
encoded scene frames. Retain logs and trials outside Git. Restore the exact
Kanshi preimage and original 1280×800 runtime mode, stop the owned fixture
server and verify the unchanged 40% output/100% input, both unmuted. Do not
rerun the historical `tools/vm/` assembler for this current reference.

The rehearsal found one small prerequisite gap: this reference had Git but no
`less`, so an ordinary interactive `git log` could not start its default pager.
The guide now includes `less`, and the terminal recipe explains the choice.
Capture uses the normal per-command `git --no-pager log` form; no package or
persistent pager configuration was changed in the guest or checkpoint. This is
a later instruction correction, not another fresh-base replay claim.

The guest has none of the SSH Plus, Tmux Plus or Agent Plus launchers installed.
Their optional insert is deferred: no agent authentication, remote endpoint or
integration setup was added to create this recording. The core overview does
not claim an agent conversation or remote connection. Those workflows retain
their explanations and labeled sample rendering on the Tour.

The four earlier recordings are moved to the
[earlier-recordings page](../tour-earlier.md), with their original component
0.3.1 tuples, retained identity, capture dates and bytes. They remain reachable
from the relevant Tour sections. No old recording is relabeled as current.

## Checks and preservation

Local validation passed: 88 source tests with three native-GI skips, unchanged
component exports, 31 desktop contract checks and 85 terminal checks. Normal
and portable builds each produced 24 pages, 156 files and 870 checked local
links. Each browser run passed 813 checks across 23 routes and four viewport
widths, with zero browser errors. Coverage includes all six players' metadata,
keyboard play/pause, seeking, poster loading and direct MP4 access, plus narrow
layouts, reduced motion and JavaScript-disabled reading.

Sol reviewed the current Tour and earlier-recordings layout at desktop and
narrow widths. The home demo link leads to the new overview; the focused
controls clip remains on Tour. Setup navigation still opens the human overview
with its prominent recommended agent-guide link. All prior asset records,
clip records and corresponding media bytes are unchanged. Component/identity
inputs, the personal Story and the private chezmoi repository are unchanged.

Exact commit, CI/Pages outcome and served-byte parity are recorded separately
in the final publication evidence. Those checks establish site publication,
not a new component release, host deployment or physical-device qualification.

The accepted reference checkpoint and all earlier checkpoints remain separate
from the mutable capture working disk. The final audit records their hash/size
checks, the unchanged inactive domain definition, normal Session shutdown and
autostart disabled. Human playback/OLED acceptance and physical device issues
remain ordinary-use follow-ups.
