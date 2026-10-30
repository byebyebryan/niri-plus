# Black workspace and desktop consolidation receipt

Recorded 2026-10-29; fresh-reference and media results added 2026-10-30 UTC.
This implements the [consolidation plan](consolidation-and-black-workspace-pass.md).
Components 0.4.1 and the selected identity are published, and the scoped update
is installed on Carbon, Starship and Snap. The fresh-Arch reference is qualified
and checkpointed. Capture and publication checks are recorded separately below.

## Selected appearance

The Niri workspace is opaque `#000000`; its overview surround is `#111213`.
The surround keeps empty black workspace tiles visible. Warm Neutral Slate
application surfaces, Clear Blue focus, Balanced+ terminal framing and all
sixteen ANSI values remain unchanged. Login and lock surfaces retain their
existing colors.

An all-black overview trial hid the empty workspace boundary. The selected
charcoal surround passed native normal/fractional-scale navigation and primary
visual review. Lossless captures established black workspace interiors, empty
workspaces, window gaps, fullscreen return and overview transitions. These are
software-capture checks; OLED/display and human aesthetic acceptance remain
separate.

Schema-2 identities without the optional workspace role retain the prior canvas
mapping; those without the overview role emit no new overview setting. Old
identity native Niri projections matched byte-for-byte for all three profiles.

## Published inputs

| Input | Verified value |
| --- | --- |
| Components | 0.4.1, API 1; 44 files: 33 desktop, 7 shell, 4 appearance |
| Code source and release tag target | `317658ee7913bb58536f6ec1b2575043a9494449` |
| Archive SHA-256 | `0940e0803c84bc6e1cb941ea4074f14a02db0d124bd8c1c676c3375147427d11` |
| Manifest SHA-256 | `30e1ad903fb74d7ee17b74f9f037cdc3ce2224d7538f5096668360aff9b504a4` |
| Independent identity source | `f6d2ed05f0a855ab5ba884d6bc84f71e50d98ba2` |
| Identity SHA-256 | `3fc1f9deef2bf7f4c377b34c452dcd965ac0e6dc5dcd96768ddbc6538321c563` |
| Verified derived receipt SHA-256 | `328c7746468661d2c8539c99cb6381ff1961f7fcd05890a6afcdee2098a1452b` |

Two archive builds were identical. Direct public downloads, the remote tag,
GitHub release asset digest, every payload hash and mode, and the independent
identity source member were verified. The [release catalog](../../data/component-releases.json)
retains 0.3.1 and 0.4.0 unchanged.

There are 41 derived outputs. Thirty-six are byte-identical to 0.4.0. The five
changed outputs are `niri-neutral-slate.kdl`, `controls-appearance.json`,
`identity.css`, `roles.json` and `theme.json`. Eleven native application and
terminal styles are unchanged. Shell source, dependency pins and the accepted
compiled-cache receipt are unchanged. The greeter remains
`niri-neutral-fe1a7a554ed6` with identical core bytes.

## Installed consumer

Chezmoi code/identity adoption is `30c3559b5d69021bd47f5dabd75df33e61480218`;
the completed documentation/source revision is
`ec2b35f583d2ceed466b14b7bb1ee55046113b02`. The public
[managed setup record](../../data/setup.json) and
[component record](../../data/components.json) contain the independent producer,
identity and consumer selections.

| Host | Verified native targets | Actual writes | Repeated scoped apply | Installed read-only controls |
| --- | --- | --- | --- | --- |
| Snap | 23 | Niri config and controls appearance metadata | No writes | Passed |
| Starship | 23 | Niri config and controls appearance metadata | No writes | Passed |
| Carbon | 23 | Niri config and controls appearance metadata | No writes | Passed |

Delivery staged the complete 22-target controls payload before the Niri
projection. All four fresh installed wrappers passed protocol/callback/cancel
checks, native compositor PATH/Python GI and desktop-entry checks. Scoped status
and diff were empty afterward. Thirty-eight protected home files per host,
73/75/75 root files and 8/6/5 native process identities were preserved, as were
package state, providers, network routes, pairings, power policy and active
sessions. No service restart, package change or root greeter write was needed.
Snap's 19 and Carbon's two unrelated source edits were preserved.

Real Wi-Fi credentials/wallet compatibility, physical output/microphone,
Bluetooth peripheral operations and human OLED/visual review remain normal-use
follow-ups. The installed read-only checks do not claim those results.

## Fresh Arch reference

The 0.4.1 reference passed on 2026-10-30 UTC, starting from a new offline copy
of installed Arch Linux x86-64 with 184 packages and an ordinary sudo account.
The run used the published 44-file bundle, independently pinned identity and
31 public examples. The stopped, accepted state is preserved as
`arch-reference-0.4.1`, with matching disk, EFI variables, inactive domain
and reviewed task matrix. Both source and checkpoint image checks passed;
all 17 files in the earlier base/reference/demo checkpoints retained their
original size and SHA-256. Autostart remains disabled.

### Guide findings and exact inputs

The initial reviewed guide was commit
`7903048f008f98673b8b323dfa7e1342b8cb38c7`, SHA-256
`3c56f1a8077e1c8dcb8c442b3d22632a4c705f26d4a35e981224d6f1d9de2010`.
The execution record retains these public amendments and the affected checks:

| Revision | Correction | Verification |
| --- | --- | --- |
| `7903048` | Use the single `qt5ct` platform-theme name for both installed Qt versions. | A separate development attempt found Qt6ct's warning with the combined name. The accepted run began again from a fresh base; native Qt5/Qt6 plugins, fonts and palette passed without that warning. |
| `e47fbbf` | Move user-local launcher PATH setup before its first use. | Applied during stage 6 of the run; real Niri-spawned Rofi/helpers and later fresh/cold logins resolved the installed commands. |
| `e31c57b` | Start packaged audio units before testing controls; distinguish the retained legacy entries from direct controls. | Native socket/service owners, direct entries and virtual output actions passed. The three legacy entries were kept out of the selected stage. |
| `bcaccd7` | Check PAM initialization completion and native wallet operation. | The short-lived initializer exited 0 with `Result=success`; Secret Service/portal owners and disposable store/read passed without another password prompt. PAM stayed unchanged. |

This is a fresh-base run with reviewed guide amendments and repeated affected
gates. The code, identity and public-example pins in the published-input table
stayed fixed. The promoted guide names the same input inventory as
`tools/reference/inputs.json`; the earlier inventory is retained under
`tools/reference/history/inputs-0.3.1.json`.

The execution review also caught two omitted installation steps in the lab
runner: Session's helper and the hardware-feedback helpers/bindings. Their
existing guide commands were completed and their native tasks tested before
the accepted checkpoint. No first-party implementation or release pin changed.

### Native task matrix

| Area | Observed result | Boundary |
| --- | --- | --- |
| Login and appearance | Stock SDDM password login/logout/relogin before theming; themed password login after changes, restart and cold start. Native GTK, Qt5/Qt6, Rofi and Kitty use the staged appearance; workspace is black with a charcoal overview. | Compositor/image evidence; physical/OLED review remains separate. |
| Browser and files | Ordinary signed-out Chrome first run; PDF in Chrome, image in Gwenview, audio/video defaults in mpv. Native GTK upload returned the exact downloaded PDF bytes. Ark extraction matched the archive's README bytes. | Public disposable samples and actual app paths. |
| Storage and authorization | Native polkit Cancel denied and authentication allowed. A newly created 64 MiB serial-mapped scratch disk passed authorized UDisks mount, user write/read/hash comparison and unmount. | Scratch was detached and retained; no existing disk was formatted. |
| Wallet | Real password login initialized KWallet; disposable store/read and retained lookup after cold login matched without a second password prompt. Test secret cleared. | Basic Secret Service/PAM proof; real NM credential/schema compatibility remains a device follow-up. |
| Locking and idle | Invalid input kept one Gtklock alive; correct input unlocked it. Repeated lock kept one process. Idle reload preserved the active locker. The session's normal lock request worked. | Selected power policy retained; physical suspend/resume remains separate. |
| Panel and clipboard | Fresh-login panel showed live CPU/RAM and Ethernet/IP; missing cards hid. Exact text/PNG restore, selected Delete, Cancel-first Clear and confirmed Clear passed. | Guest readings and owned sample clipboard only. |
| Network controls | Real connected `eth0`, saved profile and IPv4 details; named action cycling, Back and Cancel worked. NetworkManager handover retained the original address, DNS and HTTPS, with rollback armed first and cancelled after verification. | Guest-only cloud-init/networkd handover; Wi-Fi hardware absent. |
| Audio controls and feedback | Output 40%→45%→40%, mute/unmute, input helper mute/unmute at 100%, all restored. Output volume keys and transient banners worked; expired feedback left history count zero. | Virtual mic-key injection did not toggle input; that key path is unverified. Backlight absent; brightness helper/binds installed. |
| Playback | Actual ICH9 HDA playback reached ALSA RUNNING and produced nonzero monitor signal; volume/mute baseline restored. | Physical/SPICE audibility and microphone signal unverified. |
| Displays and input | One Kanshi owner changed scale 1→1.5→1 and restored config. Native Pinyin preedit, cancellation, selection and committed `你好latin` passed in Kitty and Chrome at fractional scale. | Virtual output; physical docking/hotplug/EDID not exercised. |
| Terminal | Four pinned shell trees verified; new Kitty used installed Zsh, first prompt fetched gitstatusd, history and completion worked. An actual public-sample Git branch appeared in the prompt. | Account login shell stayed Bash; no private shell/cache import. |
| Monitor sharing | Native Entire Screen capture advanced frames with the documented VirtIO compatibility package, including after cold start. Stop released the exact owned PipeWire nodes/link. | Monitor-only; conditional guest package described below. |
| Lifecycle | Cancel-first Restart preserved boot ID; confirmed Restart changed it and returned to themed login. Normal logout stopped Niri/Fcitx/Kanshi/SwayNC and graphical targets; relogin restored one owner each. Final Session Shut down powered off the guest. | Same guarded domain/disk/EFI/NIC; autostart disabled. |

### Tested packages and VirtIO sharing

| Component | Recorded package version |
| --- | --- |
| Niri / SDDM / Rofi | `26.04-1` / `0.21.0-7` / `2.0.0-1` |
| Chrome / Kitty / Zsh | `156.0.8078.47-1` / `0.49.2-1` / `5.9.2-1` |
| Qt selectors | `qt5ct 1.9-2`, `qt6ct 0.11-9` |
| SwayNC fork / Gtklock / Cliphist | `0.12.6-15` / `5.0.0-1` / `1:0.7.0-2` |
| PipeWire / WirePlumber | `1:1.6.10-1` / `0.5.18-1` |
| NetworkManager / GTK portal | `1.58.1-2` / `1.15.3-2` |
| Fcitx / KWallet / KWallet PAM | `5.1.23-1` / `6.31.0-1` / `6.8.2-1` |

Stock WLR `0.8.4-1` created a running stream but delivered zero frames in this
VirtIO guest. Native Stop released its nodes. The existing
[conditional compatibility recipe](../../tools/vm/desktop/wlr-compat/README.md)
was then built from upstream commit `01171a150b705cf07066ebc0fb7e1ff537027bec`,
source archive SHA-256
`04ad0e4a7717265475fd394b614092d70909ff2089c08bb2b90adde9e8c436cd`.
The local `0.8.2-1.3` package SHA-256 is
`9c6f9e958f34653ba8c6bae38562b4a077da3b1c57d9f05b7c5f2d0e79dd42fb`.
Its normal user/D-Bus activation matched the new binary, with no drop-ins.

The native preview reached frames 120→540 and a later stop at 918. After full
power-off/start and password login, a new capture reached 120→240 and stopped
at 450. Both stops ended tracks and removed their exact source/input nodes and
link while the normal backend remained available. The stock recovery package
is retained, SHA-256
`85efdb0e0fcafea76a24c766b4022d6a2a0176bb132a597b9e8fd5bbc634cab8`.
This compatibility selection is local to the guest; fleet portal defaults were
preserved.

The accepted checkpoint disk SHA-256 is
`686a1604b028d5af27ee8252b1dae45ebbd8d1531f5ee7e5327a154056fe4299`;
matching EFI variables SHA-256 is
`a7c55acadd982035e5653924c474f920254d9c6e16527a637085ba2273405edd`.
The working copy is used separately for capture. Hardware-only and human
acceptance remain explicit follow-ups.

## Media and publication

The [current controls recording](../../assets/demo-controls.mp4) and
[desktop still](../../assets/arch-reference/black-workspace-041.png) were captured
on 2026-10-30 from the accepted reference's separate working copy. The native
output was 1920×1080 at scale 1. Chrome shows the public Niri Plus Story page;
Kitty/Zsh shows the clean `public-sample` branch of
`octocat/Hello-World` at `7fd1a60b01f91b314f59955a4e4d4e80d8edf11d`.
The recording opens Audio, inspects its device details, adjusts volume and mute,
restores the original settings, then inspects the connected Ethernet link in
Network and returns to the desktop. Wi-Fi and Bluetooth hardware are absent.

The 35.4-second silent H.264 High/yuv420p MP4 is the original recorder output,
with no cuts, overlays, compositing or reused footage. Its SHA-256 is
`f587e58d6dac06e60efd72d7f970c036bdd04173b4141a7ad1e614e2d9bc95aa`.
Full decode passed without errors: 1,062 decoded frames, measured average rate
`5315/177`. The container lists 1,063 packets/frames with the final packet
flagged discard. TV range was requested and logged by wf-recorder, while
ffprobe reports `color_range=unknown`; no later color conversion was applied.
The native PNG poster was captured during the same take. Recorder/tool versions,
all output hashes, processing, exact source pins and review states are in the
[media record](../../assets/provenance.json).

The clip and still use components 0.4.1 and the retained black-workspace identity.
The browser's public page was separately verified against source
`45e8144e26533b6519fceddfa00647088697aab5`. The four earlier desktop clips
remain byte-identical, labeled with their original 0.3.1 component tuple,
retained identity and capture dates. Neither those recordings nor the new clip
shows monitor sharing; its independent warm/cold checks are described above.
Two unsuccessful recording trials are retained privately outside Git.

Sol reviewed the native still and sampled frames across the full sequence.
Full decode passed; the final site also checks native playback, seeking,
responsive layout and static fallbacks before publication. Human playback and
physical OLED/aesthetic acceptance remain pending.

The final normal and portable builds each contain 23 pages, 152 files and
824 checked local links. Each passed 764 owned browser checks across widths
375, 768, 1280 and 1600, with interactive and JavaScript-disabled paths and no
browser errors. The source suite ran 88 tests with three native-GI modules
delegated to the explicit system-Python gate; desktop checks passed 31 and
shell checks passed 85. Component exports matched their sources. Publication
uses the checked main revision through GitHub Pages; direct served-byte
verification is retained with the deployment evidence.

The final shell gate also exposed a race in its own interactive test harness:
it accepted an intermediate prompt before the transition had finished. Submitting
each fixture phase as one compound command removed that ambiguity. The delayed
transition reproducer and all 85 shell checks passed. No published component
code or release bytes changed for this test correction.
