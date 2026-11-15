# SwayNC reference release 2 supplement — producer release 2026-11-14

The current public Arch selection pairs components 0.4.3 with SwayNC fork
release `niri-plus-2`, package `swaync-bryan 0.12.6-20`. This records producer
provenance and the qualification boundary; it does not change component
metadata, identity or utility pins, generated exports, or the authored
notification profile.

| Producer input | Exact selection |
| --- | --- |
| Public release | [`niri-plus-2`](https://github.com/byebyebryan/SwayNotificationCenter/releases/tag/niri-plus-2) |
| Runtime package | `swaync-bryan 0.12.6-20` |
| Source revision | `96a2a9c4574e26fc6d6839a0e19d506a7638898e` |
| Source archive SHA-256 | `68f1cfa73eb79e344589fb2b1d62d04bb282034910f6118e366a979c5c256658` |
| Arch recipe revision | `d2a4bc709b7ea77567ca50fac9b1001088f90815` |
| Recipe archive SHA-256 | `ffcd5dbc373e062a82ec0daee3be5ae35385bfb1e73c0569c141801ca848ab0c` |
| Stable consumer selector | `3146eee089db444c76a5a1ed2d12abed85900e61` |
| Producer host receipt | `4cafaebe306453e1fbb8fbd7483db7b060bedf48` |

The release and exact package pin are retained in
[`tools/reference/history/swaync-pins-0.12.6-20.json`](../../tools/reference/history/swaync-pins-0.12.6-20.json).
The producer receipt reports stable package 20 on Starship and Snap; Carbon
was offline-pending. The earlier Nov7 package-18 host evidence remains dated in
[`data/history/setup-20261107.json`](../../data/history/setup-20261107.json).

## Native checkpoint-copy qualification — passed 2026-11-15

The primary guest result was observed at `2026-11-15T08:43:38.861166+00:00`.
Final preservation completed at `2026-11-15T08:44:29.933481+00:00`, which is the
qualification timestamp recorded in the current route metadata. The Nov14 date
in this receipt's filename is the producer-release date; native checks occurred
the following day.

The guest was a standalone stopped copy of the accepted package-18 core using
the public Niri Plus source at
`40077f8dbd96b2aac4ab05e64cfe7a813e6353c6`. This bounded supplement tested the
SwayNC package and session integration; it is not a fresh OS installation or a
replay of the 21 package-18 task groups.

### Build and installation

The pinned public recipe and source archives passed SHA-256 verification, and
`makepkg --verifysource` passed. The successful clean build used
`makepkg --syncdeps --rmdeps --noconfirm` after earlier interactive prompt
attempts reached EOF. `--noconfirm` was an unattended-harness adaptation; the
public installation guide remains interactive. The build passed all five Meson
tests: schema validation, history retention, network data, system data and
dashboard data. Its own 43 build dependencies were removed by `--rmdeps`. After
the earlier prompt attempts, a separate plain `pacman -R` transaction removed
their exact 43-package dependency set and restored the pre-build baseline; no
recursive orphan pruning or guest-wide upgrade was used.

The VM-built package archive SHA-256 is
`3c4f744fb6c317c2378dc180d9271bddf5ac88bcb0b4c71c59061a044e6416f4`. The
installed executable SHA-256 is
`a82d39b9baf7db5bc56c89bf02c536cac5558ab49bed9827bda6955d0eddf57b`, matching
the producer's binary receipt. The independent package archive hash differs
from the canonical archive; no cause is inferred from that difference.

### Native results

- A real SDDM password login started Niri without autologin or PAM changes. The
  packaged `swaync.service` owned the notification bus with exactly one process.
  Native `Mod+N` opened the panel, and its DND control changed false → true →
  false.
- With the public profile's retention keys absent (effective 0/0), a 1000 ms
  popup expired while the history card remained available and the daemon kept
  advertising `persistence`. The card was then closed and the history count
  returned to zero.
- With a temporary ordinary limit of 2 seconds and critical limit of 0, two
  notifications appeared immediately. After 3 seconds the ordinary entry was
  removed once with `NotificationClosed` reason 1; the critical entry remained
  in history and `GetNotification`. The daemon omitted `persistence` while the
  override was active.
- An action popup configured for 120 seconds remained visible after 81.749
  seconds with the control center closed and only critical history remaining.
  A guarded native QMP click invoked the real Gio action callback, focused its
  Niri window, closed the notification with reason 2 and normally closed the
  owned fixture.
- The original profile and stylesheet bytes were restored, with their original
  owner, mode, mtime and inode. Reads advanced atime and restoring the profile
  changed ctime. After restoration, DND was false, history was empty and
  `persistence` was advertised again.
- A normal power-off/start changed the boot ID. After verifying the SDDM
  greeter, a second real password login returned to Niri with exactly one
  SwayNC process matching both the service MainPID and notification-bus owner.
  The loaded binary, package, profile and stylesheet hashes matched; history
  was empty, DND was false and `persistence` was available. The primary captured
  and reviewed the native `Mod+N` panel, then closed it.

### Cleanup, failures and limits

Final preservation passed at `2026-11-15T08:44:29.933481+00:00`. The guest is
shut off with autostart disabled; read-only `qemu-img check` reported no errors.
All 10 retained domain states/definitions and 20 older disk/EFI metadata records
were unchanged. The lab network was restored inactive with persistent XML
unchanged.

Initial automation errors were harness-only. Early package-build prompt
attempts reached EOF before the inspected dependency transaction was completed.
The first worker cold-login attempt sent input before confirming the SDDM
greeter and used an invalid `busctl` verb; the primary repeated the login after
checking greeter readiness and passed. The first action-popup attempt used the
normal 30-second timeout and expired before the screenshot/click sequence. A
later harness assertion expected callback name `focus` in the D-Bus action
array, which exposes `app.focus`; the corrected guarded attempt passed. These
errors were retained and were not counted as product failures or passes.

This qualification does not claim a fresh OS installation or a full replay of
the 21 package-18 task groups. Package-20 suspend was not tested; the VM
suspend/resume waiver remains specific to package 18. Physical-device and
multi-output acceptance remain separate. The optional Xvfb private-bus source
lifecycle harness was not run because `/usr/bin/Xvfb` was unavailable; it was
not required for this actual-service guest qualification.

The prior [2026-11-08 qualification](reference-qualification-20261108.md)
remains explicitly tied to package 18. Its 21 task groups and VM suspend/resume
waiver do not transfer to package 20. The package-20 supplement remains a
checkpoint-copy qualification, not full fresh-reference acceptance. The
authored profile still omits both retention properties and inherits the fork
defaults of unlimited history; the guide documents those options and keeps
personal chezmoi policy separate.
