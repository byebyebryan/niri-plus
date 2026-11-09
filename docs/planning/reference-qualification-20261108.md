# Arch reference qualification 20261108

The numbered components 0.4.3/SwayNC 0.12.6-18 installation and 21 mapped
routine native task groups completed through an independent fresh replay and
later checkpoint-copy supplements recorded below. Additional
virtual suspend checks returned from the kernel but failed graphical recovery.
Bryan subsequently waived this particular VM check as a qualification blocker,
reporting no corresponding issue in ordinary daily use. The recorded failure
remains retained and is not marked passed. The routine-task checkpoint is
stopped, with autostart disabled and a clean read-only disk check. Optional
selections were assessed separately on copies of that checkpoint. The
[0.4.1 replay](black-workspace-receipt.md#fresh-arch-reference) and the scoped
[0.4.3 and package 17 checks](swaync-reference-sync-20261107.md) retain their
original dates and scope.

This pass keeps the numbered reference and the three optional selections
independent. It does not consolidate releases or change personal machine
selection or deployment. Chezmoi retains that authority.

## Frozen inputs

The public guide checkout is
[`40077f8dbd96b2aac4ab05e64cfe7a813e6353c6`](https://github.com/byebyebryan/niri-plus/tree/40077f8dbd96b2aac4ab05e64cfe7a813e6353c6).
The [reference inventory](../../tools/reference/inputs.json) selects 44
component payloads and 31 public example files. The authored notification
profile is a separate reviewed input from that guide checkout.

| Input | Exact selection |
| --- | --- |
| Components | 0.4.3, producer `07cf4a393314c195ace7e66d162f21d3a2f73136` |
| Component archive SHA-256 | `146b4d4b81dac3804b5836348045b5b89a8fa3c62719b643a90302da8346d87a` |
| Component manifest SHA-256 | `31a30ac9f11dcb4182e9b0c26e5c33ca741bdb28a2c1a195f298db8ea79dd79b` |
| Identity SHA-256 | `c4d61361a61dcd900e23c07d01f02ebe6b326529ccd144e86c7460d672ea1e5e` |
| Authored notification profile SHA-256 | `c40e8a0cbf1327c87b5b713b6c68ba3d0462dff654d7b51d1bd58333bdf79543` |
| SwayNC | `swaync-bryan 0.12.6-18`, source `7e0ea67572a5c98412572c1ef3eb6920354fa1d6` |
| SwayNC recipe | `8998ab49dc71e2c1353d5518cd8cd30191f41d18` |

The [SwayNC pin](../../tools/reference/swaync-pins.json) also records the recipe
and source archive hashes. The development guest built the package through
ordinary `makepkg`; its local package SHA-256 is
`7e73e7101e7e0ca2f80941cda71488e9368f8a5fb34cb0c0e53a0a439aac92a9`.
That hash identifies this guest build, not the separately released package.

## Development results

| Area | Observed result |
| --- | --- |
| Base and staging | Untouched installed Arch base, 184-package baseline, full upgrade and reboot into `7.2.14-arch1-1`; public checkout, component archive, identity and example hashes verified. |
| Login | Stock SDDM login, wrong-password rejection, logout and relogin passed before theming. Derived-theme preview, themed reboot and password login passed. The packaged PAM file remained unchanged. |
| Appearance | Native black workspace and charcoal overview pixels matched the selected colors; Rofi, Gtklock, KDE polkit and Kitty surfaces were inspected. |
| Authorization and wallet | Native polkit Cancel returned 127 and authentication returned 0. Disposable Secret Service store and lookup passed after a real password login. After full power-off/start and another password login, lookup matched without another prompt. The fixture secret was then cleared and lookup returned absent. |
| Locking | Wrong input retained the locker; correct input unlocked it. Repeated lock and idle-service restart retained the same locker process. The graphical session's normal `loginctl` lock request passed. |
| Idle | A temporary five-second timer produced DRM Off, native input restored On, and the exact original 600-second policy was restored. |
| Sidebar | Package 18 passed package integrity, live CPU/RAM, inline DND, cards, reopen and unchanged daemon ownership. Ethernet and IP appeared after NetworkManager took ownership. |
| Clipboard | Exact multiline text and PNG restoration, selected Delete, Cancel-first Clear and confirmed Clear passed with owned samples. Final sample history was empty. |
| Network | Documented handover retained address, route, resolver, DNS and HTTPS. Rollback was armed first and cancelled after verification. Direct device details, Back and Cancel passed. |
| Files and browser | Image, PDF, text and archive defaults and extracted-byte comparison passed. Ordinary Chrome first run used the Rofi entry, accepted terms, stayed signed out and saved metrics reporting as disabled through native settings. The download screenshot shows Done and 606 B; its actual file digest was not retained. Native GTK upload displayed the expected text digest. |
| Terminal | New Kitty used Zsh, fetched pinned `gitstatusd` from a clean cache, displayed Git status, recalled history, completed a path and exited. Account login shell remained Bash. |
| Audio | Direct Details/Back/Cancel, volume and mute restoration passed. The replay notes record mpv playback, ALSA and PipeWire monitor RUNNING state and nonzero monitor PCM; the raw WAV and standalone metrics receipt were not retained. Native volume/mute keys produced transient toasts and left history empty. |
| Displays and input | One Kanshi owner applied scale 1→1.5→1, restoring configuration according to the replay notes. QEMU seat-input events exercised Pinyin preedit, cancellation and candidate selection. Chrome screenshots show `你好latin` at both scales. Kitty's matching committed text is recorded in replay notes without a retained per-scale result file. These are injected guest input events, not physical-device acceptance. |
| Storage | Newly created serial-verified 64 MiB FAT16 scratch devices passed native UDisks Cancel/authentication, user write/read/hash comparison, unmount and detach. Images were retained. |
| Sharing and lifecycle | The conditional portal candidate passed live capture and native Stop, including after full power-off/start. Cancel-first Restart, confirmed Restart, logout teardown and password relogin passed. Final native Session shutdown reached a stopped, autostart-disabled domain; the read-only disk check found no errors. |

## Findings and corrected execution

The staging path is now assigned once before the stager and reused by later
commands. An existing or failed output must be retained while a new path is
chosen.

Full-mode shell fetching does not produce `receipt.json`; that file belongs to
dependency-only mode. The first development transcript fetched successfully
but checked the wrong output. Its log was retained. A continuation verified the
existing full bundle and four pinned dependencies before creating the shell
shim; the corrected fresh transcript does not repeat that mistake.

Niri can close its IPC connection after accepting quit. Teardown and return to
the greeter were checked directly. KDE's packaged polkit agent exited 255 when
that compositor connection closed; no agent process remained, and the next
password login restored one successful active agent. No exit-code suppression
was added.

The VM exposes DRM connector power state but not the protocol used by `wlopm`.
The idle check was repeated using the actual DRM state. Clipboard fixture
filter and focus mistakes were corrected and retained separately from the
successful run; they did not require a component change.

## VirtIO sharing comparison

The uncapped stock WLR 0.8.4 attempt displayed Entire Screen but aborted before
a stream or frame was observed. WLR dumped core with SIGABRT at `wl_array_add`
and `data is non-NULL with zero alloc`; Chrome's main process dumped core with
SIGTRAP. The service journal reported a 7.1G memory peak. The captured
`app.slice` peak was 7,876,804,608 bytes, with `oom_kill=2` and local
`oom_kill=0`. There was no pre-attempt counter baseline, so those existing kills
are not attributed to this attempt.

The exact stock archive was saved for recovery, SHA-256
`85efdb0e0fcafea76a24c766b4022d6a2a0176bb132a597b9e8fd5bbc634cab8`.
The existing [conditional recipe](../../tools/vm/desktop/wlr-compat/README.md)
was built from its pinned upstream source and patches; its local package
SHA-256 is `2b60b234e8ef4546f6b741dd5ee23ae6df8d570ffd90d658ac3fcd9afd350f4c`.
It ran as 0.8.2-1.3 using the normal packaged service, without drop-ins or
memory caps. Frames advanced 1303→1397, and Chrome's native Stop ended the same
track and removed the WLR source and Chrome input nodes.

After full power-off/start, the actual Wayland route repeated this result:
frames 1064→1123, a live 1920×1080 monitor, and native Stop ending that track
and removing both nodes. An earlier cold launch used XWayland/X11 capture;
its frames bypassed the selected WLR path and were excluded. Browser backend
and actual PipeWire provider nodes were checked before accepting the repeat.
The comparison does not establish the precise DMA-BUF cause or qualify other
capture modes, physical devices or fleet portal choices.

The independent fresh stock attempt used the ordinary uncapped service with
an external observer that stopped its exact process after sampled memory
crossed 512 MiB. The observed peak was 566,194,176 bytes. Initially the page
reported no track; after native Stop it reported an already-ended monitor track
with zero frames. This was an observer intervention, separate from the
development guest's natural crash. No advancing stock frame was observed.

The fresh guest independently built the same pinned candidate, local package
SHA-256 `1a5b8162ff3afad8f4b44786b99ac0efc682d47bf84e06c06d3a058a95bdc54f`.
Warm frames advanced 81→140 and cold frames 285→343. Each native Stop ended
the same track and removed both video nodes and their exact capture link.
The service used its normal command, without drop-ins or memory caps. A
process-observer assumption about Chrome's coalesced `argv[0]` was corrected;
the saved frame and graph evidence was retained, without repeating the stream.

## Independent fresh replay

The fresh guest started from a separate standalone copy of the untouched
installed Arch base and EFI variables. Its live baseline contained 184
packages, no Niri package and no Niri configuration. Full upgrade and reboot
passed into `7.2.14-arch1-1`, with a changed boot ID. All numbered installation
stages passed, including public staging of all 44 payloads, source builds,
stock and themed password gates and the corrected full-mode shell fetch.

The fresh native pass has also completed sidebar, clipboard, network controls,
polkit, wallet store/lookup, locking, idle timing, first terminal, ordinary
Chrome first run, native GTK upload and file defaults. Browser download matched
the 606-byte PDF SHA-256
`27768d289b11d768c8d3b5808e6696d74a02cce83d9aa65b4bca98884c51ca42`;
upload matched the 83-byte text SHA-256
`80dacdd030e5dcf6cb8fe9ec3c21fb495918ebb222711dcff4e3ed9b91fdeba9`.

The fresh audio replay saved contemporaneous mpv, ALSA RUNNING and PipeWire
monitor observations, plus the actual captured WAV. Independent review of that
file confirmed stereo signed 16-bit PCM at 44.1 kHz, 311,296 frames, 478,432
nonzero samples, RMS 4386.4729 and peak 7071. Its SHA-256 is
`9769b3cc9a4cbddb48bfbb89c5f42c321d98aeb016369d8a09295756ab3d089f`.
The initial harness failures and its incorrect 48 kHz assumption are retained
separately. Output/input remained 0.40/1.00; native volume and mute feedback
expired without adding history. This is virtual signal proof, separate from
audibility or physical microphone acceptance.

Native QEMU seat-input events produced preedit, cancellation, candidate
selection and exact `你好latin` in Chrome and Kitty at scales 1 and 1.5.
Both retained Kitty result files have SHA-256
`d40be4a49c2ae3dfa8a7bb216de0986fe59f0841202cc40d70f00210fffe4f57`.
Kanshi's original bytes, mode, owner, group, atime and mtime were restored and
one owner returned to scale 1. Linux ctime necessarily advanced on rewrite.
The native MP4 default opened the exact fixture in mpv and rendered a frame.

A new serial-verified 64 MiB FAT16 image passed native UDisks/polkit mount,
83-byte write/read/hash comparison, unmount and detach. The image is retained.
Cancel-first Restart was cancelled with Enter and preserved the boot ID;
confirmed Restart changed it. Full shutdown/start and actual password login
returned the retained wallet fixture without another prompt. The exact secret
was cleared and its private token file removed. Logout stopped every intended
session owner; password relogin restored one of each. The owned fixture server
was stopped after PID/UID/command/start-time checks, with port 8765 clear.

Final package integrity reported SDDM 251/0, SwayNC 43/0 and the conditional
WLR package 21/0 files altered. No user units were failed. Final native Session
shutdown stopped the guest. Its disk SHA-256 is
`87ccc0bdd4f4dd3ec21b52ba0ec025f8180b999fbf221bc84356b622079493ba`;
EFI variables SHA-256 is
`46f840d6f8946800fa3f266d060bd39b120788dad9756c6018984a02b87ba203`.
The read-only `qemu-img check` found no errors, and autostart remains disabled.

The development and fresh guests use distinct UUIDs and separate lab networks.
Every fresh SSH payload checks the actual guest DMI UUID as well as the host's
domain, disk and firmware identity before performing the requested operation.

## Optional selections

All three public archives and full manifests are verified. Only the listed
files are selected. Four standalone copies of the routine-task core checkpoint
isolate Away, the screen, Close All and their combination. A fifth plain-core
copy separates the suspend rendering control from all optional selections.

| Extension | Release and selected payloads |
| --- | --- |
| Away | 0.5.0, producer `4c79ff18cc12152ce072c000bf00131fc2efda15`; helper and user unit only. |
| Session screen | 0.9.2, producer `41ed699a7c0b95be7a7e51c29409d14f19a9b98a`; menu, readiness and countdown helpers, plus the optional binding. |
| Close All | 0.10.0, producer `ef37cb145230e85bb70dd3d3a1aba4fe2b67ead9`; helper and optional binding only. |

The [release catalog](../../data/component-releases.json) retains each exact
archive and manifest hash. These full optional-release bundles are not selected
over the core 0.4.3 controls and appearance. Automatic idle and suspend policy remain
independent of the manual Away latch and session screen.

The first screen prerequisite check stopped before changing helpers or the
binding because the core's GTK4 layer-shell package does not provide GTK3's
`GtkLayerShell` namespace. The optional recipe now explicitly installs Arch's
`gtk-layer-shell` and checks the GTK3 namespace before adoption.

### Installed Away

The Away-only copy passed the optional shortcut latch, explicit resume,
QEMU seat-input resume through the permissionless input-only backend, stop
while latched restoring On, and restart returning normal with one owner.
A forced Niri display wake without input returned success and advanced the
controller's correction count from 0 to 1 under the same PID; the journal
recorded correction. The 25 ms external DRM observer did not catch a transient
On sample, so this does not prove a visible panel flash.

A real mapped GTK Wayland idle inhibitor held the display On for 7.57 seconds
under the temporary five-second ordinary idle timeout. A separate post-close
Off observation was not retained in that attempt; normal uninhibited Off has
its own core receipt, and the later same-session supplement below closes the
release-sequence gap. A new real inhibitor while manual Away was latched left the display
Off without a locker. Explicit resume, inhibitor cleanup and exact original
policy restoration passed. Logout and password relogin returned normal with
one controller; final native core Session shutdown stopped the copy.

### Installed Close All

The Close All copy passed a dry-run snapshot and one ordinary close request per
snapshot ID across two workspaces. The requested IDs exactly matched the
snapshot; no request failed or was skipped. The application created another
window and its Save/Cancel dialog after that snapshot; neither was targeted.
Native Cancel preserved the exact unsaved editable buffer, and native Save
wrote 37 bytes with SHA-256
`ae1b8f37414445fc6884b43b618818cd1668a94b1303364058e6dee476089a47`.
The actual Mod+Shift+Q binding delivered an ordinary delete request to a
separate owned window. Mod+Q remained unchanged and the final empty dry run
returned no IDs.

GTK's application-modal dialog retained one clean window despite an accepted
close request. That is allowed: Close All requests closure once, and applications
control save dialogs and final closure. An initial harness incorrectly required
immediate disappearance; its events, cleanup and saved text are retained. The
corrected replay manually closed the remaining fixture after Save, without
adding a helper resnapshot or forced termination. These checks used one virtual
output; physical multi-output behavior remains a human gate.

### Installed screen and VM suspend check

On the screen-only copy, real Ctrl+Alt+Delete opened an inert grid. All six
choices started a five-second timer and could be cancelled directly to the
desktop. Re-entry retained one pending request and timer. Reopening remembered
the selection without starting another timer. Keyboard navigation, unchanged
boot/policy and normal unlocked display state passed.

Actual Display off and Lock expiry passed, including changing countdown digits,
DRM Off, input resume, real Gtklock readiness before blanking, rejection of the
menu shortcut while locked, wrong-password retention and correct-password
unlock. The first authentication observer typed during PAM's failure delay;
a corrected wait and field clear demonstrated ordinary unlock without any PAM
change.

The native VM suspend/resume check is waived as a blocker at Bryan's request.
Its recorded result remains a failure. With the VM's original firmware capabilities,
the real screen action completed kernel s2idle, but Niri IPC timed out and the
display remained Off after input resumed the kernel. Niri's main thread was
observed waiting on a DMA fence while its user cgroup was unfrozen. One scoped
S3 capability comparison also resumed the kernel and failed graphical recovery;
the original VM definition was restored. A clean-boot trial with no Wayland
screenshot client before or during sleep reproduced the published-helper failure.

An experimental helper hid and synchronized the layer surfaces before suspend.
Its isolated UI checker passed, but a clean-boot native trial still completed
kernel suspend without IPC/display recovery. The experiment was rejected, its
patch and evidence retained privately, and canonical source and generated
exports restored byte-for-byte. Published helper bytes were restored on the
extension copies before their remaining action checks. No suspend workaround,
driver, firmware or personal policy change is adopted by this result.

The screen copy also passed actual five-second Log out, Restart and Shutdown.
Logout returned to the real greeter and password login restored one of every
intended owner; Restart changed the boot ID; Shutdown stopped the exact guest.
The first logout observer scanned every runtime socket directory and found a
committed record for the dead compositor. The helper scopes state to socket
identity. The corrected observer found no current-session request; retained
greeter, journal and owner evidence support the action without a repeat or
component change.

### Isolated screen proof

The source helpers match the selected immutable optional payloads. The owned
nested-Niri session-screen checker passed 30 GUI checks with inert lock, logout
and power endpoints. The default timer visibly rendered 5, 4, 3, 2 and 1 before
dispatch at 5.086 seconds. All six action routes, direct cancellation to the
desktop, remembered selection requiring fresh activation, keyboard traversal,
refusal handling and constrained-scale layout passed. Private process groups
were cleaned up and the protected host process baseline was unchanged.

The 21 isolated Away checks also passed. These fixture and GUI results are
separate from installed-extension results, the VM check waiver and physical-panel
acceptance.

### Combined selection

The combined copy retained the same core and independently selected only Away,
the screen and Close All. All installed helper and binding hashes matched the
selected release payloads after restoring the published suspend helper. The
original power policy hash was unchanged. Grid cancellation, inert remembered
selection, actual Display off and Lock, and the controlled Close All fixture
passed together; Save/Cancel and post-snapshot preservation retained the same
semantics as the separate Close All copy. Actual five-second Logout, Restart
and Shutdown also passed, including complete owner teardown, password relogin,
changed reboot ID and the final stopped guest. Native suspend/resume is covered
by the same VM check waiver; the combined result does not mark it passed.

### Plain-core render control

A final standalone core copy had one ordinary GTK window mapped before direct
native suspend, without the optional helpers, layer surfaces or an application
idle inhibitor. Normal core inhibitors were retained. No Wayland capture client
ran before or during sleep. Kernel success advanced 0→1 under the same boot,
Niri retained its PID, IPC returned 0 and DRM reported On. The app consumed a
new AFTER nonce, updated its title through IPC and logged the update.

The required fresh-frame proof did not pass: one bounded post-resume `grim`
returned 124 and zero bytes. The GTK draw observer also lacked the Cairo GI
converter, so no draw count or actual AFTER pixels were accepted. This control
establishes kernel, IPC and application-update behavior, not successful visual
recovery or an observed physical-panel freeze. It does not isolate the cause of
the screen copy's stronger IPC/display failure. Its normal OS shutdown also
hung after the guest agent exited. After more than two minutes, the primary
verified UUID, disk and EFI identity, stopped only this disposable copy from the
hypervisor and obtained a successful read-only QCOW2 check. This is recovery
from a failed test, not a successful native shutdown observation.

An earlier idle plain-core control on the eventual combined copy also returned
IPC and On. A later new-frame capture stalled before another candidate suspend
was confirmed, making that candidate trial inconclusive. Its normal shutdown
then hung; only that exact owned copy was stopped from the hypervisor after
identity checks, and its read-only disk check passed. Those recovery receipts
and all failed observations remain retained. The final five-action combined
checks used a clean boot and the published helper.

### VM check waiver and reopening

Bryan requested skipping this particular VM check after reporting no
corresponding problem in ordinary daily use. This removes the native VM
suspend/resume check as a blocker for this qualification pass. The previous
failures, recovery receipts and rejected experiment remain preserved; the
exception does not convert them into a pass or change runtime behavior. The
controlled physical-host checklist remains pending. No further VM suspend trial
is required in this pass.

Reopen investigation if an actual daily-use incident is reported or Bryan
explicitly requests a VM graphics investigation. Any future controlled retest
should use the same published helper bytes and record a controlled runtime or
platform change. Require an exact kernel success-counter increment,
unchanged boot ID, responsive IPC, and a newly rendered ordinary GTK frame
captured after resume. An idle IPC response or the host's stale VGA screenshot
is insufficient. Keep this virtual result separate from physical panel, input,
lid and power-button acceptance. Do not carry the rejected layer-surface patch
forward as a fix.

### Consolidation boundary

The complete 0.10.0 archive shares 41 payloads, including modes, with 0.4.3.
It changes `components/appearance/render.py`, `components/appearance/sddm.py`
and the Session menu, and adds six optional helper, binding and service paths.
It therefore cannot replace the qualified appearance input wholesale.

The user-waived VM suspend/resume check no longer blocks this qualification.
A subsequent consolidation remains a separate review and can retain
the 0.4.3 appearance renderers together with the accepted optional selections.
That requires a new immutable release tuple and a separate consumer review;
the existing archives must not be overwritten. Chezmoi continues to own which
files and policies each machine selects and when it adopts the new tuple.

## Supplemental gap review, 2026-11-09 UTC

A review found missing retained observations within two of the original task
groups and one optional Away sequence. The bounded follow-up uses a new
standalone copy of the stopped fresh core checkpoint, preserving the original
fresh guest and its receipts. It retains the exact core 0.4.3/SwayNC 0.12.6-18
installation; these are checkpoint-copy supplements, not another untouched-base
installation replay. The VM suspend/resume waiver remains in effect.

### Notification action and application focus

A controlled GTK/Gio application sent an action-bearing notification through the
real SwayNC owner. A native QMP click on its visible button produced the
application callback, mapped its previously hidden window, and made GTK report
that window active. Niri independently reported the matching PID and title
focused. The app then closed normally. No direct focus command or injected
notification-action signal supplied the result.

The first observer pause let the toast expire before the click. Its no-callback
result is retained as a timing-limited attempt. The corrected harness captured
and clicked in one running call: the callback followed notification creation by
about 1.23 seconds. A nonessential logger API mismatch also stopped an earlier
attempt before any notification was sent. These do not replace the accepted
native callback/focus observations.

### Ordinary audio default-handler launch

Niri-spawned `xdg-open` opened the original `sample.wav` through the configured
`audio/x-wav` default, `mpv.desktop`. The exact fixture was 480,044 bytes with
SHA-256 `d340b18b059f0aee21a5eba95471cacf10f9f6282c9155eb2a2bb6f2c659ee9b`.
The observed executable was `/usr/bin/mpv`, with the exact fixture in its argv
and the normal desktop pseudo-GUI option. The matching window and process were
gone after ordinary close. This closes the default-route evidence gap; the
previous direct mpv playback and captured PCM retain their separate scope.

### Ordinary inhibitor release

After the core-only notification and audio checks, the same copy selected only
the verified Away 0.5.0 helper and unit, with no binding or Niri configuration
change. Manual Away remained false. A real mapped GTK Wayland idle inhibitor
held DRM On through an 8.204-second quiet interval while the ordinary idle owner
used a five-second timeout. No seat input was sent during that hold.

Closing only that owned app normally removed its window and process. Without
further input, ordinary idle produced DRM Off at the 4.998-second sample after
close. Manual Away stayed false, with no reblank corrections. A native injected
key restored On. The original 410-byte policy, SHA-256, mode, owner, group,
atime and mtime were restored; ctime necessarily advanced. One normal idle
owner again used 600 seconds, with the locker inactive and no fixture windows.

The follow-up used a private, hashed copy of an existing protocol XML to build
the inhibitor fixture with the guest's existing tools; no package transaction
or product source change was required. An earlier setup attempt encountered
normal display blanking after its 600-second idle period, before the temporary
policy was applied. The corrected attempt woke the owned guest first and
verified the already-installed exact Away payloads rather than overwriting them.

### Review dispositions

| Review item | Disposition for this pass |
| --- | --- |
| Notification callback and application focus | Verified through the native card action, GTK active state and matching Niri focus. |
| Ordinary audio default-file route | Verified through `xdg-open`, actual mpv executable/argv and normal close. |
| Inhibitor release back to normal idle | Verified in the same session, followed by exact policy restoration. |
| Notifications recipe qualification link | Updated to this record; earlier media retain their package 17 dates. |
| Controlled multi-output and physical-device checks | Deferred from this pass; the human checklist remains pending. |
| Release consolidation and consumer adoption | Deferred to a separate immutable-tuple and consumer review. |

### Scope explicitly deferred from this pass

Controlled multi-output and physical-device acceptance are deferred. The owned
nested GUI checker and current guest each expose one output, so focused-monitor
backdrops, hotplug/docking and physical peripherals remain on the separate human
checklist. They are not new product failures or completed hardware tests.

Release consolidation is also deferred. The accepted core and optional
selections remain independent, and a full 0.10.0 pin jump would change
appearance inputs. A new immutable tuple and consumer review remain separate
work; chezmoi retains personal admission and deployment. The current pass does
not publish or deploy that composition.

## Physical acceptance

Bryan owns these pending checks on the selected physical target. Record the
host, package tuple, actual device and result for each applicable row. Restore
the original device settings after testing.

| Area | Physical observation still required |
| --- | --- |
| Login and lock | Readability, focus, scaling, password rejection and unlock on the actual panel. |
| Displays and input | Internal/external outputs, dock and hotplug recovery, fractional scale and native IME candidate placement. |
| Audio | Audible speaker/headphone output, microphone signal, routing and hardware keys. |
| Brightness | Internal backlight and supported external DDC/CI behavior, including restoration. |
| Radios | Available Wi-Fi and Bluetooth pairing, connection, headset routing and reconnect; actual Wi-Fi credential persistence and wallet handoff. |
| Storage and files | Actual removable-device mount/eject and controlled browser download/open/upload with native handlers. Format only a newly authorized disposable device. |
| Sharing | Controlled whole-monitor capture with advancing frames, Stop cleanup and repeat after a full cold start. |
| Power | Idle, lock, physical wake, suspend/resume, lid and power-button behavior under the selected policy. |
| Optional Away and screen | Focused-monitor grid and other-monitor backdrops; visible countdown and cancellation, unlocked Display off, Lock then blanking, real input and panel return, ordinary inhibitors outside Away, and wake correction while Away is latched. |
| Optional Close All | Owned disposable windows across the actual workspaces and outputs, one dry-run snapshot, native Save/Cancel behavior and preservation of windows created after the snapshot. Never use ordinary working windows. |

## Preservation and qualification outcome

The old reference VM, package 17 working VM, original Arch-base disk and EFI
variables remain preserved. New development and replay domains use standalone
copies with distinct UUIDs. The existing lab network was temporarily started
for development, and a new dedicated network isolates the fresh replay. The
existing network configuration and the user's native desktop are preserved.

The numbered installation and 21 mapped routine core task groups, including
the checkpoint-copy supplements, cold sharing/wallet,
Away, Close All and the screen's five non-suspend actions are accepted within
the stated virtual scopes. Their combined selection passed the same non-suspend
behavior. The native VM suspend/resume check is user-waived for this pass,
with its recorded failures retained. The 12-item private physical-host checklist
remains entirely pending; no controlled physical suspend qualification is claimed.

Eight owned domains are retained stopped with autostart disabled. The retained
reference domains, original source images and historical media are compared
against the seven-file/two-domain preservation baseline. The existing network
returns to its original inactive state with unchanged configuration; the new
owned fresh network is stopped and undefined, with recovery XML retained.
Private raw logs, failed attempts, screenshots, selected-input preimages,
per-task receipt hashes and stopped disk/EFI checkpoints remain under the dated
qualification artifact trees. They are recovery/evidence artifacts, not bundle
inputs.

Final source checks passed: 190 virtualenv tests (three GI module skips), all 74
system-Python controls tests, unchanged component exports, 44 desktop checks
and 85 terminal checks. The unchanged helpers also retain 21 isolated Away
tests and 30 isolated native screen checks. Normal and portable site builds and
the owned responsive/browser checks validate this documentation candidate;
those checks do not operate the user's native desktop. Historical screenshots
and recordings retain their original provenance and dates.

This record covers the qualification and its supplements, including the explicit
user waiver for the native VM suspend/resume check. Publishing it updates the
documentation and site. Component source, published component releases and pins,
and personal fleet configuration retain their existing selections; release
consolidation remains separate. Chezmoi retains personal selection and deployment
authority.
