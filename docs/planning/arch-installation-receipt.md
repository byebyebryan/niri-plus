# Arch reference installation receipt

Execution date: 2026-10-28. **The corrected Arch walkthrough passed a separate
fresh-base replay.** It starts with installed Arch x86-64, an ordinary sudo
account and networking; it does not install the OS. The result is a locally
qualified guest reference, with explicit virtual-hardware limits. Public
publication, personal-fleet deployment and human acceptance remain separate.

## Scope and source provenance

The main route is [the Arch setup guide](https://dev.byebyebryan.com/niri-plus/setup/).
It begins from installed Arch and an ordinary sudo-capable account. The candidate input stager is
first-party checkout code, not part of the published component release. Its
candidate and published inputs remain separate:

| Input | Exact provenance |
| --- | --- |
| Candidate input stager | Commit `8133dd0ed69d50bd704c33ba5f3ed48001e0b59e`; SHA-256 `e753b0c4d74a617c90f97bd4e8bc2e83530552f1209d2a7224b0f5dbd84f71aa`. |
| Candidate input inventory | `tools/reference/inputs.json`; SHA-256 `abb054cfa3ea4683dbff225616dd619c3f2318da86c72b27ff1306110505d638`. |
| Frozen corrected guide candidate | Commit `a429c1ea2ea6239cb2a14340ee08ac2c5aa2f5c3`; `docs/setup.md` SHA-256 `8b5f6da0fdf0a12ecb19e99b3956f32057595f0a9179b45b73cc491853700096`; `docs/recipes/appearance.md` SHA-256 `b160f5e8fe2f54a3a689e624617e0e1f7841166c6eaa56b6c8c54a5fe8a77cb2`. |
| Authored SwayNC reference config | `examples/notifications/reference.json`; SHA-256 `da55b379747d5ac0208730354ebfd8901dc268ac8e5b5b717e81ee9243d15577`. This candidate file is not fetched from the older public example commit. |
| Candidate examples manifest | `examples/manifest.json`; SHA-256 `97ecc7c115985a909f113a91d9301d0b2e41ffb97c97af3b91b03c7d49ea7b2a`. |
| Published components | `0.3.1`, source commit `014a14241bd722186ae9248e71162e75cf7af7b1`; archive SHA-256 `868d9de46f54af9b9f563dd52cd94df9358fafaf9c9b33666c557c05d318a843`; manifest SHA-256 `de3e981f8bb76d2b4ccfbf7f2722e81fc9f73edf7b62de11cad55f7a209e7ed3`. |
| Independent identity | `design/identity.json`, SHA-256 `6dbb163103e911262b5c1a6b1dd8299863ea790f7a12e7fb264fe9603e8e2455`. |
| Public example snapshot | Repository commit `b62df460884b5a4d5e8c7eeb05c132a0b26814ae`; examples manifest SHA-256 `6919c539d34848f8587f1f3b2d2fb045372e1c2810bbffa9f1b6dc7db1a89222`; 34 explicitly listed files in the candidate inventory. |
| Shell dependency pins | `examples/terminal/pins.json`, SHA-256 `4a4c0dd16b17e48e3113e23d7e9e64a600f7f8dfe4d086d186e44290592bbd90`; the staged fetcher downloads four pinned upstream trees when explicitly run. |

The stager verifies the immutable component archive, its manifest and payload,
the independent identity, and the explicit public example inventory. It writes
an output provenance record and appearance previews into a fresh tree. It does
not read `tools/vm`, pilot receipts, private home files, or warmed shell caches;
it does not install packages, change normal configuration, or start services.
The first-party stager and authored notification config are unpublished
candidate checkout inputs, not 0.3.1 payloads.
The successful replay used the frozen candidate above. It was delivered as an
explicit first-party Git bundle (SHA-256
`768671adca66765a61582aab63c56bef5fa8cd3a4194a0730942e7227f659e93`),
not a private home or assembled pilot tree.

### Selected upstream builds and installed versions

| Item | Selected version or source |
| --- | --- |
| SDDM greeter input | Catppuccin SDDM `1.1.2`, Mocha Blue archive SHA-256 `a68fbed896d3066aec1fdaded561e8d20c855f0de4e193bdca4bc0d59ac1e333`; neutral appearance is derived from the independent identity. |
| SwayNC fork recipe | Recipe revision `cd1038d1c824f256ecb5a448d78df9f71b64850a`, archive SHA-256 `297852ede6f49cd9a2e75204d734807529e84b2dd0b01f6fc8789da4b53d9ff0`. |
| SwayNC fork source/package | Source revision `4114c9cd56f086e166253880d0c96c6c5212e4aa`, archive SHA-256 `8b69e2f47692a0dc53b00c5e9cf8c9df62c1295e5e7ee36acf16e40359f6bc83`; `swaync-bryan 0.12.6-15`. |
| Chrome | Arch recipe commit `f0071e0692f4545bcb3e0881ea60c031a9f99343`; installed Chrome `156.0.8078.47-1`. |
| VirtIO WLR compatibility candidate | Upstream xdg-desktop-portal-wlr commit `01171a150b705cf07066ebc0fb7e1ff537027bec`, archive SHA-256 `04ad0e4a7717265475fd394b614092d70909ff2089c08bb2b90adde9e8c436cd`; local package `0.8.2-1.3`. Patch hashes and recovery instructions are in the [conditional compatibility recipe](../../tools/vm/desktop/wlr-compat/README.md). |

Representative installed Arch versions on the successful fresh replay were Niri `26.04-1`,
SDDM `0.21.0-7`, Kitty `0.49.2-1`, Zsh `5.9.2-1`, Rofi `2.0.0-1`, Chrome
`156.0.8078.47-1`, KWallet `6.31.0-1`, `kwallet-pam 6.8.2-1`,
`polkit-kde-agent 6.8.2-1`, Fcitx5 `5.1.23-1`, PipeWire `1:1.6.10-1`, and
WirePlumber `0.5.18-1`. These rolling repository versions describe this guest,
not a promise about future Arch package transactions. The earlier
[desktop demonstration receipt](desktop-demonstration-receipt.md) records the
other selected application and media package versions.

## Integration findings before the final replay

The first guide candidate, `69008bdf79e7d88cbae4b1d5b0f490c93ebbf901`, returned
to guide correction when its `GTK_THEME` override left GTK4 pavucontrol light.
It was not accepted as a completed replay. The corrected candidate was frozen
at `a429c1ea2ea6239cb2a14340ee08ac2c5aa2f5c3`, then applied from another
fresh offline copy of `arch-base`, including matching fresh UEFI variables.

The useful corrections are now part of the written route:

- Native GSettings supplies theme, dark preference, fonts, icons and cursor.
  `GTK_THEME` stays unset; no extra GTK4 INI workaround is required.
- When audio packages arrive after the user manager is running, start the
  packaged PipeWire sockets and WirePlumber. Their native activation owns audio.
- The packaged polkit helper socket can similarly need a current-boot start;
  its packaged permissions are preserved.
- SDDM's existing PAM stack and the packaged KWallet initialization unit supply
  the login handoff. No custom PAM stack or copied wallet is required.
- Fcitx uses its packaged XDG autostart owner. Chrome and Kitty compose through
  native Wayland without legacy IME flags or a global `GTK_IM_MODULE`.
- First-use Powerlevel10k/gitstatus needs its own network fetch. A staged shell
  dependency tree does not imply an offline first Git prompt.
- Stock WLR fails in this VirtIO/VirGL guest. The documented conditional source
  recipe fixes the tested guest; it does not become the normal desktop backend.

## Final fresh-base replay

The base contained 184 packages, no Niri configuration and no staged component
or shell tree. The ordinary account followed the frozen source route. The
source export and public pinned downloads were the installation inputs: no
previous consumer configuration, wallet, prompt cache, private chezmoi or
pilot receipt was imported. Authored PDF/video task fixtures and private
observation tools were separately identified as lab inputs.

Package installation, source builds, manual profile adaptation, the conditional
network handover and the optional WLR branch were recorded in per-stage
transcripts. The successful replay required no repair outside the written
route. Earlier automation mistakes were corrected in observation tools or task
targeting; they did not change the guide or installed desktop implementation.

| Area | Native fresh-replay result | Limit |
| --- | --- | --- |
| Stock login | Before appearance and wallet setup, packaged SDDM accepted the ordinary guest password, started Niri, returned to the greeter on logout and accepted another login. | No autologin or default-target bypass. |
| Appearance and greeter | Derived the exact pinned upstream greeter from the independent identity, previewed its returned directory, installed the derived theme and then used the real themed login. Wrong password was rejected; correct password started Niri. Themed login worked after reboot and full power-off/start. Native GTK4 pavucontrol rendered dark using GSettings with `GTK_THEME` unset. | A rejection banner was not captured on SDDM; authentication rejection was confirmed by session state and PAM journal. Test mode alone was not treated as login acceptance. |
| Wallet | Unchanged distribution SDDM PAM plus the packaged initialization owner created/unlocked the guest wallet. Disposable store/lookup passed without another prompt; lookup passed after reboot/password login, then the secret was cleared. After cold power-on and final relogin, a new disposable store/lookup/clear passed again. Secret Service and KWallet portal had the same native owner. | Guest-only disposable secrets; no browser account, private wallet or GPG material. |
| Authorization | Actual KDE polkit prompt for harmless `pkexec /usr/bin/true`: Cancel returned 127; guest authentication returned 0. | No host action or package permission change. |
| Locking | Gtklock rejected a wrong password and unlocked correctly. Repeated lock and idle-service restart retained locker PID 3606. An explicit lock request targeting the SDDM Wayland session activated and unlocked another locker. | PAM rejection was allowed to finish before retrying; targeting the SSH session is not a graphical lock test. |
| Idle and session | Temporary five-second timeout produced DRM `Off`; a virtual Shift key restored `On`. Restored the exact 600-second policy. Restart cancellation preserved boot ID; explicit Restart rebooted. Explicit Shut down stopped QEMU, followed by a separate host start. | AC-only VM: no battery transition, physical lid/suspend, inhibition or physical display-wake acceptance. |
| Displays and input | One Kanshi owner changed the real virtual output from 1920×1080 scale 1 to scale 1.5 and back. One packaged Fcitx owner passed preedit, Escape cancellation, candidate Down/Up selection and Space commit. Kitty received `你好latin` at scale 1 and `中文latin` at 1.5. Chrome received `你好latin`; the second field received `中文你好` at 1.5 with its candidate popup following the field. | Real virtual keystrokes, no Unicode paste. Does not establish docking, physical hotplug/EDID or every toolkit. |
| Audio and feedback | Real ICH9 HDA sink/source with PipeWire/WirePlumber. Three-second 440 Hz tone reached ALSA PCM `RUNNING`; monitor captured 327680 bytes, RMS 6224.7, peak 10000. Up/down, output mute/unmute and source mute/unmute restored original values (40% output, unmuted); history counts stayed 0 before/immediately/after. | Guest sink/monitor evidence, not physical/SPICE audibility or microphone signal. No backlight device exists. |
| Browser and files | Normal Chrome first launch used its real terms/settings UI and stayed signed out; telemetry choice was verified. MIME defaults opened PDF in Chrome, PNG in Gwenview, MP4/WAV in mpv and ZIP in Ark. Ark extraction matched source bytes. Dolphin opened the downloaded Markdown through Kitty/Neovim. Native GTK portal picker selected that download; server upload hash matched `c2440ff35a67921e891877abc7f210c9c869ff38f2c5c973fcd319147b5a2275`. | Later CDP observations used a separately labeled disposable browser profile after the normal first-run gate; no real account. |
| Storage | Exclusively created a new 64 MiB guest-only image, positively identified serial `NIRI_GUIDE_FINAL`, formatted that image only, authenticated through the real KDE polkit prompt, mounted as the ordinary user, compared written/read bytes, unmounted and detached it. | Image retained; not physical USB hotplug acceptance. |
| Shell | Four pinned upstream dependencies staged manually. Cache was empty before the first Kitty Git prompt; that prompt fetched gitstatusd and loaded. Native Up/Enter repeated the command; Tab completed the partial directory path, verified by the resulting working directory. Account default stayed Bash; Kitty explicitly selected login Zsh. | No warmed cache import or offline-first-run claim. |
| Panel, launchers, clipboard | Actual SwayNC CPU/RAM and primary Ethernet/IP appeared; missing battery/Bluetooth/GPU cards hid. Owned notification appeared in history. Rofi launched Network/nmtui, Bluetooth/bluetoothctl, Audio/pavucontrol and Session. Clipboard restored exact multiline text and PNG bytes; Delete removed the item, default Cancel retained history, confirmed Clear emptied it. | Normal keyword search for Network also matched Chrome; name-only filtering selected the actual Network entry. Bluetooth has no adapter and its daemon hardware condition is unsatisfied. The configured 200-item cap was not stress-tested at 201 items. |
| Lifecycle | After cold sharing, confirmed Niri logout stopped Niri, graphical target, SwayNC, both clipboard collectors, idle/battery, polkit and Fcitx; Kanshi/Fcitx process counts fell to zero. Password relogin restored the owners, with exactly one Fcitx, Kanshi and SwayNC. Final normal Session Shut down stopped the accepted guest. | Native session evidence, distinct from site automation or physical-desktop acceptance. |

### Whole-monitor sharing and compatibility

Stock `xdg-desktop-portal-wlr 0.8.4-1` was tested under a bounded 512 MiB
memory limit and no swap. On this fresh guest it produced zero frames and
width zero, logged failure to create a GBM/PipeWire buffer and exited with
SIGSEGV (11). The earlier development run had a different abort signature;
these are recorded separately. No uncapped-stock or general-hardware failure
claim follows from this bounded guest observation.

Saved the exact stock package outside Pacman's cache (SHA-256
`85efdb0e0fcafea76a24c766b4022d6a2a0176bb132a597b9e8fd5bbc634cab8`).
The documented compatibility recipe was built afresh as the ordinary account;
its `0.8.2-1.3` package SHA-256 was
`efc5ea02d611b5a6d832559828319498b832a186b73af3d906efa85ef149fd99`.
It ran with normal `/usr/libexec/xdg-desktop-portal-wlr`, no TRACE flag and both
memory limits restored to infinity.

| Measurement | Before full power-off | After separate cold power-on |
| --- | --- | --- |
| Surface | Actual 1920×1080 monitor | Actual 1920×1080 monitor |
| Frame callbacks | 8 | 8 |
| Frame count | 59 → 67 | 58 → 66 |
| Media time | 3.011626 → 3.577138 s | 2.969453 → 3.499667 s |
| Sampled preview colors | 496 | 433 |
| After Stop | 0 live tracks, null preview stream, no capture/input video nodes | Same cleanup passed |

Chrome used native Wayland without `--disable-gpu`. The preview was scrolled
into view before measuring content. This is whole-monitor sharing only; no
per-window sharing or promotion of the guest workaround to personal hosts.

## Validation, focused evidence and recovery

Repository validation passed: 37 unit tests, zero generated-export drift,
31 isolated desktop checks and 81 terminal checks. Normal and portable site
builds each validated 20 pages, 115 files and 683 local HTML links. Each passed
690 browser checks across 20 routes at widths 375, 768, 1280 and 1600, with
JavaScript enabled/disabled and zero browser errors. The four unchanged clips
retained their hashed provenance; browser playback, seeking and static download
fallbacks are checked in the local review export. These site checks do not
substitute for the native task evidence above.

Three focused native stills appear in the [login](https://dev.byebyebryan.com/niri-plus/recipes/login/),
[locking](https://dev.byebyebryan.com/niri-plus/recipes/session/) and
[input](https://dev.byebyebryan.com/niri-plus/recipes/input/) recipes. Their exact
bytes, capture date/context and upstream attributions are in
[media provenance](../../assets/provenance.json) and
[license notes](../../assets/LICENSES.txt). The four earlier accepted clips and
the selected visual identity remain unchanged. Agent inspection is separate
from human visual/media approval.

The accepted guest is stopped, persistent and autostart-disabled. Its separate
`arch-guide` checkpoint retains disk, matching UEFI variables, domain XML and a
checkpoint receipt. Both source and checkpoint images passed `qemu-img check`;
copy hashes matched. Recovery copies the checkpoint into new working paths
while the owned domain is stopped; the stored XML records the original working
paths and must be adapted to those copies. Never boot the protected files as
writable disks.

- Disk SHA-256: `044c75c826d7c290d86f6a3d55cc62488f72d5b88492f7b319547b709eb75836`.
- UEFI SHA-256: `8ac19d17c0c943d39bd13bf71a936a4d86ab34fca56257e7a4b4d350ca157ee0`.
- XML SHA-256: `dbaa54a36809608424261092c0dd080d12fded1c91abbace78607ca5e747cc14`.

All 12 protected files across `arch-base`, `niri-plus` and `desktop-demo`
retained their pre-pass SHA-256 and size. The development and incomplete
first-replay disks/UEFI/XML remain separate. The new unmounted scratch image is
retained. Starship's NetworkManager, firewall, Docker and Tailscale service PIDs,
native Niri/SwayNC/swayidle/Kitty/349d PIDs, default route and resolver were
preserved. Free storage remained 117.5 GiB, above the 50 GiB floor. The owned
browser tunnel, fixture service and serial observation session were cleaned up;
shared report hosting remains available for review.

No public push, release, public-site rollout or personal-fleet apply occurred.
No physical audio/microphone, Wi-Fi/Bluetooth pairing, battery, backlight,
docking/lid/suspend or human approval is claimed. Ubuntu/Debian and new Rofi
controls remain deferred.
