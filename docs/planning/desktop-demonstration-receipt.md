# Arch desktop demonstrations receipt

Execution date: 2026-10-28. This records work packages 0–4 / phases C–D of the
[demonstrations plan](demo-and-adoption-pass.md), following the
[2026-10-27 capture pilot](capture-pilot-receipt.md). Arch Linux x86-64 remains
the only reference target; Ubuntu/Debian are deferred for much later.

The staged guest now connects browser/files, terminal and on-demand information
workflows. The site contains a 62.1-second overview and three focused recordings.
These are real guest captures with local sample content. They establish the
bounded tasks below, rather than a complete installation or physical desktop.
Source, native guest, encoded media, site checks and human review are separate.

## Inputs and assembly

The working guest was cloned offline from the protected pilot checkpoint,
including its disk and UEFI variables. Its UUID, reserved MAC/address, SSH host
identity and working Niri session were checked after boot. Neither the clean
`arch-base` nor pilot-only `niri-plus` checkpoint was used as a writable disk.
The original domain definition and original working disk/variables were retained.

The public-input tuple remains:

| Input | Exact selection |
| --- | --- |
| Public starter/identity source | `b62df460884b5a4d5e8c7eeb05c132a0b26814ae` |
| Component bundle | `0.3.1`, source `014a14241bd722186ae9248e71162e75cf7af7b1` |
| Bundle SHA-256 | `868d9de46f54af9b9f563dd52cd94df9358fafaf9c9b33666c557c05d318a843` |
| Bundle manifest SHA-256 | `de3e981f8bb76d2b4ccfbf7f2722e81fc9f73edf7b62de11cad55f7a209e7ed3` |
| Independent identity SHA-256 | `6dbb163103e911262b5c1a6b1dd8299863ea790f7a12e7fb264fe9603e8e2455` |
| SwayNC package | `swaync-bryan 0.12.6-15` |
| SwayNC recipe | `cd1038d1c824f256ecb5a448d78df9f71b64850a` |
| SwayNC source | `4114c9cd56f086e166253880d0c96c6c5212e4aa` |
| Chrome AUR recipe | `f0071e0692f4545bcb3e0881ea60c031a9f99343` |

The independently pinned identity selects Crisper Neutral Slate/Clear Blue for
the desktop and pure-black Balanced+ for Kitty, with Noto Sans and Meslo.
The four shell dependency pins remain in the public shell dependency manifest;
no personal `.zshenv`, SDK hooks, history, credentials or chezmoi tree were copied.

The guarded incremental assembler lives in
[tools/vm/desktop](../../tools/vm/desktop/assemble-desktop.sh); its
[instructions](../../tools/vm/README.md) describe package, session and recovery
ownership. It renders appearance using the verified public component payload,
adds Dolphin/panel/clipboard binds, MIME defaults and utility entries, and records
25 ordinary managed files plus three exact session links. It refuses unknown
preimages before installing packages. The native capture helper is separate
from desktop assembly and only admits the owned QEMU `demo` guest.

Selected installed versions at capture:

| Component | Arch package version |
| --- | --- |
| Niri | `26.04-1` |
| Chrome | `156.0.8078.47-1` |
| Kitty / Zsh / Rofi | `0.49.2-1` / `5.9.2-1` / `2.0.0-1` |
| Dolphin / Gwenview / Ark | `26.08.2-1` |
| Neovim | `0.12.6-1` |
| Cliphist / libnotify | `1:0.7.0-2` / `0.8.9-1` |
| NetworkManager | `1.58.1-2` |
| PipeWire / WirePlumber | `1:1.6.10-1` / `0.5.18-1` |
| Portal frontend / GTK | `1.22.1-2` / `1.15.3-2` |
| WLR portal, VM compatibility build | `0.8.2-1.3`, explicit local recipe below |
| Mesa | `1:26.2.5-1` |
| Noto / Meslo | `1:2026.10.01-1` / `3.5.1-2` |

The assembly receipt retains the full installed package/input inventory and
preimages. Its original repository WLR entry (`0.8.4-1`) describes the core
assembly transaction; the later compatibility selection is recorded separately.
It must not be mistaken for a successful unmodified repository portal test.

## Task results

| Task | Observed result and limit |
| --- | --- |
| Browser download and files | Chrome downloaded the local Markdown sample. Dolphin opened it through the Neovim default in Kitty; an SVG opened through Gwenview. File-manager access and defaults were exercised without a private account. |
| GTK picker and upload | Actual `xdg-desktop-portal-gtk` chooser opened from Chrome. Portal D-Bus calls and successful response were observed. The receiver verified the original 252 bytes, SHA-256 `c2440ff35a67921e891877abc7f210c9c869ff38f2c5c973fcd319147b5a2275`. |
| Whole-monitor browser sharing | A real `getDisplayMedia` request produced a live 1920×1080 monitor track with advancing video frames using the explicit compatibility build. Stop ended the track, released the preview and removed the capture nodes. See the measured failure/fix below. This task is tested separately and is not shown in the clips. |
| Panel and notifications | `Mod+N` toggled the pinned native SwayNC panel. CPU/RAM and the actual NetworkManager Ethernet connection appeared; sample notifications were retained. Missing GPU, battery and Bluetooth cards hid naturally. The recorded values are actual guest observations. |
| Clipboard | `Mod+Y` restored exact text and PNG bytes through the native Rofi picker. Delete removed only the selected item. Cancel preserved history; confirmed Clear all emptied it. Both collectors are session-owned and the configured cap is 200; a 201-item capacity stress test was not performed. |
| Utility launchers | Network opened native `nmtui` against the connected Ethernet link; Audio opened Pavucontrol. Bluetooth opened `bluetoothctl`, but BlueZ skipped startup because the VM has no adapter. Session Restart opened a Cancel-first confirmation; cancellation retained Niri. No reboot/shutdown action, pairing or audio device acceptance is implied. |
| Terminal regression | A newly opened Kitty login/interactive Zsh loaded completion, autosuggestion and a nonempty prompt. A guest-only history sentinel survived a write/read check. Native recordings show command output and keyboard navigation. The final blank Kitty pixel stayed RGB 0 in the information still, decoded focused video and encoded overview. Neovim retains its application's own default colors. |
| Preimages and rerun | An unexpected Niri preimage was rejected before package work. An exact assembler rerun preserved all 25 targets and daemon PIDs. After the PATH correction, a final read-only check again matched all 25 file hashes/modes and three links. The core assembler was not rerun over the independently selected compatibility portal; a later explicit libnotify inventory declaration matches the already installed `0.8.9-1` package. |
| Session ownership | Niri logout/restart produced observed inactive states followed by new PIDs for SwayNC and both collectors. Required services start once with Niri and stop with its session. Final cold-boot results and checkpoint are recorded below. |

## Guest integration lessons

The cloud base used `systemd-networkd`, whereas the dashboard requires a real
NetworkManager PrimaryConnection. The guest-only handover preserved its DHCP
reservation, systemd-resolved stub and SSH recovery. All four networkd activation
sockets had to stop before its service; stopping only the conventional socket
allowed reactivation. Cloud network generation was disabled for this guest,
then NetworkManager owned virtual Ethernet with working DNS and HTTPS. This was
not a host networking migration and is not silently automated by the assembler.

Niri needed an explicit `~/.local/bin` prefix in its child environment. The
first trial exposed the missing helper lookup; the owning assembler was fixed,
its exact preimages restored, and the corrected assembly reapplied. The final
Niri child environment includes the helper path and GTK/Qt selections. A package
install or a source check alone would not have found this runtime failure.

### VirtIO WLR sharing compatibility

The repository WLR portal `0.8.4-1` negotiated a monitor track but delivered no
frames. Repeated buffer allocations eventually exhausted guest memory. Bounded
follow-up trials localized an exact format/modifier mismatch: GBM allocated
XRGB8888 with the LINEAR modifier (`0`), while Niri advertised XRGB8888 with the
implicit INVALID modifier (`0x00ffffffffffffff`). Exact-pair rejection triggered
reallocation before the first copied frame. Neither a software Chrome trial nor
`force_mod_linear` resolved it. Unmodified upstream `0.8.2` also failed.

The explicit [VM compatibility recipe](../../tools/vm/desktop/wlr-compat/README.md)
pins upstream commit `01171a150b705cf07066ebc0fb7e1ff537027bec` and checksums both
patches. On this rejected DMABUF pair, it selects the existing shared-memory
fallback before renegotiation. Dimension changes and SHM mismatches retain their
previous behavior; no unsupported pair is claimed as accepted. The trace patch
is diagnostic only unless TRACE logging is explicitly requested.

The resulting `0.8.2-1.3` package passed eight video callbacks with seven frame
advances and a real monitor surface. A bounded run stayed below 81 MiB peak;
a repeated normal run, after removing TRACE and the temporary 512 MiB limit,
stayed near 6.9 MiB current / 70.1 MiB peak. That normal run again advanced frames
and released the track and PipeWire capture nodes after Stop. Both the SwayNC
package (43 files) and this portal package (21 files) passed `pacman -Qkk` with
zero altered files.

This is a local VirtIO compatibility candidate, applied separately after core
assembly. It is not a public upstream release, a default component selection or
a personal-host deployment. The original repository package is retained for
recovery. Broader versions/renderers and cold-boot sharing repetition remain
future qualification; the later Arch guide must keep this conditional step
explicit rather than claiming the repository portal passed unchanged.

## Media and review

| Asset | Actual content | Measured output |
| --- | --- | --- |
| Overview | Browser/files, 12-second terminal excerpt, information/clipboard; hard cuts between accepted scenes | 62.100 s, 1863 frames, 30 fps |
| Browser/files | Download, Dolphin/default editor, native GTK picker and verified upload | 26.733 s, 802 frames, average `12045/401` fps |
| Terminal | Exact-byte reuse of the 2026-10-27 pilot: Chrome/local page and Kitty/Zsh/project command | 24.467 s, 735 frames, average `11025/367` fps |
| Information | Live panel/notifications, Rofi text and image restore, terminal byte checks | 23.367 s, 701 frames, average `21060/701` fps |

All clips are silent 1920×1080 H.264/yuv420p MP4s. The two new focused clips are
unaltered native recordings. Their posters are decoded frames (17 s for the
GTK picker, 4 s for the panel). The overview concatenates the entire browser
clip, terminal seconds 3–15, and entire information clip; it is re-encoded at
30 fps, CRF 18, limited range, with fast-start metadata. No text/telemetry is
composited, blurred, retouched or generated. Original takes, rejected trials,
receipts and logs stay outside Git. The accepted terminal file is byte-identical
to the protected pilot output. Per-file hashes, licenses, independent versions
and sample-content labels are in [asset provenance](../../assets/provenance.json).

The first browser take was rejected: damage-driven recording compressed idle
pauses and delayed recorder shutdown. The helper now requests continuous frames
with `--no-damage`; take two preserves the demonstrated pacing and decodes fully.
Asynchronous native picker dismissal also requires waiting before another Enter,
which otherwise opens a second dialog. Input is sent to the guest's virtual
keyboard, never the workstation desktop. Human viewer key grab/release and
human aesthetic/playback approval remain pending.

## Final verification and retained state

A final clean shutdown/start reached SSH and active Niri, SwayNC and both
clipboard collectors. There was exactly one SwayNC process and two `wl-paste`
collectors. NetworkManager and resolved were active, networkd inactive; the
reserved Ethernet address, DNS and HTTPS worked. Niri's new child environment
retained the helper PATH and GTK/Qt selections, and actual `Mod+D` launched
Dolphin from Rofi. All 25 assembly hashes still matched. Portal TRACE and runtime
memory caps were absent (`MemoryMax`/`MemorySwapMax` both infinity); sharing
itself was accepted before this cold boot rather than repeated afterward.

The guest was then shut down cleanly. The retained `desktop-demo` checkpoint
contains the stopped disk, UEFI variables, inactive domain XML, assembly receipt
and cold-boot receipt together. Disk SHA-256:
`67fa1174145413500aa5c9b1e7c25a8b91caefefc8ccc3b973287090af01ba8e`;
UEFI variables SHA-256:
`a7c55acadd982035e5653924c474f920254d9c6e16527a637085ba2273405edd`.
`qemu-img check` reported no errors. The working disk and original inputs remain
retained. All six disk/variables/XML hashes for the two protected earlier
checkpoints match their pre-work values. The domain remains persistent,
autostart-disabled and stopped; the retained lab network has autostart off.

Starship's NetworkManager, firewalld, Docker and Tailscale service PIDs match the
pre-work values. Its native Niri, SwayNC, swayidle, Kitty and notification-mirror
PIDs remain present; its DNS configuration and Wi-Fi default route match the
pre-work state. The temporary host-to-guest CDP tunnel and guest fixture/portal
monitor were stopped. No personal desktop was operated for acceptance.

The guest tooling is committed locally as `5bfd729` (`feat(vm): assemble and
exercise the Arch desktop`). Six focused assembler checks passed, along with
Python/Bash syntax and ShellCheck (only unresolved dynamic-source SC1091
excluded). A read-only helper `windows` invocation on Starship refused at the
exact hostname guard before Niri discovery or input. The compatibility package
was built and installed in the guest, with source/patch checksums verified.
Full FFmpeg decode passed for all four site MP4s. Targeted decoded RGB black
checks passed for the new information clip and the overview, supplementing the
unchanged pilot proof.

Final site gates passed on 2026-10-28: all 31 repository tests, the component export check (no changed exports), the desktop source check (31), the terminal source check (81), and whitespace validation. Standard and portable builds each validated 20 pages, 109 files and 665 local links. Both headless browser runs passed 690 checks across 20 routes at 375, 768, 1280 and 1600 pixels, with JavaScript enabled and disabled and zero browser errors; checks cover native video controls, no autoplay, MP4 range and seek, source/fallback/download/poster inventory, responsive layout and readable no-JavaScript text. Final local snapshots: standard `/tmp/niri-plus-reviewed-standard.I2nGIi`; portable `/tmp/niri-plus-reviewed-portable.vElfDQ`. Human playback and aesthetic review remain pending; no site publication or full-installation acceptance is implied.

## Remaining work

The next milestone is the wider Arch guide plus fresh-`arch-base` replay:
SDDM/password login, wallet/PAM, polkit, Gtklock/idle/power, Kanshi/input methods,
ordinary media/archive tasks and audio. Physical displays, Wi-Fi/Bluetooth,
backlight, suspend/lid and removable devices need their own hardware evidence.
Host reboot/firewall lifecycle and physical viewer grab/release also remain
separate. Rofi control design follows that guide, starting with Network; this
pass only exercised the existing utility entry points.

No remote push, release, public site deployment or fleet chezmoi apply is part
of this receipt. The local review snapshot is separate from public publication.
