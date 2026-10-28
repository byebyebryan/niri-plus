# Arch reference installation walkthrough and replay

Accepted execution plan, 2026-10-28. This expands phase E of the
[demonstrations plan](demo-and-adoption-pass.md). The
[desktop demonstration receipt](desktop-demonstration-receipt.md) is the
starting evidence. Execution was authorized through the Luna goal loop on
2026-10-28. Native results and final replay acceptance will be recorded in a
separate dated receipt; this plan is not an execution result. Public release,
site deployment and fleet application remain separate.

## Outcome and starting point

A reader with installed Arch Linux x86-64, an ordinary sudo-capable account,
working networking and package access can follow one ordered guide to the
reference Niri Plus desktop. The guide must work without a pre-existing Niri
session, private chezmoi, the capture pilot's receipt/tree, warmed shell caches
or personal credentials. OS installation/partitioning and image maintenance
remain outside the walkthrough.

Use [docs/setup.md](../setup.md) as the main site route and keep the focused
recipes as its detailed destinations. Each stage needs prerequisites, exact
inputs, commands, a visible result, a real verification task and recovery.
Keep manual choices explicit. Small reusable helpers are appropriate where
needed; a generic installer, VM orchestrator or package abstraction is not a
deliverable.

Keep the selected Neutral Slate/Clear Blue desktop, pure-black Balanced+
terminal and Noto/Meslo typography. Reference services remain SDDM, Niri,
Kanshi, Gtklock/swayidle, polkit-kde-agent, PipeWire/WirePlumber, GTK + WLR
portals, SwayNC, Cliphist and Fcitx5. Current Network/Bluetooth/Audio/Session
entry points remain as they are. Optional Plus tools and agent authentication
are outside core acceptance.

## Delivery sequence

Use three internal gates. Draft the guide first, investigate and integrate its
missing pieces on a disposable development copy, then replay the corrected
written route from a separate fresh base copy. Native experiments are not the
final replay. Progress between gates needs no additional permission once this
pass is authorized.

| Gate | Work | Exit condition |
| --- | --- | --- |
| E1. Guide candidate and recovery | Audit the existing recipes, package prerequisites, public inputs, account/network requirements and session/root ownership. Write an executable-by-hand Arch route and task checklist. Qualify a working clone of `arch-base`. | Every stage has a source, expected result and recovery; development copy boots with console/SSH access; protected checkpoints are unchanged. |
| E2. Missing desktop integration | Exercise login/wallet, authorization/locking/power, displays/input, audio/feedback and ordinary files/media. Recheck browser, information, clipboard and shell through the same written route. Fix the owning source and update the guide as findings arrive. | Every required task below has native evidence; VM-inapplicable hardware behavior is identified explicitly; no undocumented repair is accepted as a guide step. |
| E3. Fresh replay and delivery | Start again from a new `arch-base` copy and follow the corrected guide. Run reboot, logout/relogin and the task checklist. Integrate the qualified guide into the site, retain evidence and a separate checkpoint, and stop the VM. | The final route succeeds without repairs outside the guide; source/site gates pass; exact versions, results, limits and retained state are recorded. |

## E1: settle inputs and establish recovery

- Preserve `arch-base`, pilot `niri-plus`, `desktop-demo`, original media and
  the current stopped working disk. Use a new working disk and matching UEFI
  variables, with the owned domain definition captured before switching paths.
  Check storage headroom and retain the existing 50 GiB free-space floor.
- Run one guest at a time on Starship's existing local libvirt/QEMU network,
  reservation, graphics and console path. Verify base-copy identity, access
  and disk/variables provenance before modification. No hypervisor reinstall,
  host network changes, Docker changes, remote access or chezmoi lab integration.
- Record actual base package/network/login state. Fully upgrade the guest and
  reboot when needed before freezing the test baseline. Handle a networkd to
  NetworkManager handover explicitly, including activation sockets, cloud
  networking, DHCP/DNS and SSH/console recovery. Never run competing managers.
- Begin with published components 0.3.1, the independently pinned current
  identity, the pinned shell dependencies, SwayNC recipe/source, Chrome recipe
  and greeter archive. Record actual Arch package versions separately; rolling
  packages are not a promise of identical future binaries.
- Candidate guide/tools/fixtures may be staged as an explicit first-party
  source export, with commit/hash provenance and no private home or checkout
  extras. Label unpublished candidate inputs accurately. A shared-code fix
  belongs in its canonical module; release preparation and personal-host
  admission remain separate from local testing. Do not edit released payloads
  or private fallbacks to hide an upstream fix.
- Document first-party versus upstream licenses, explicit fetch/build steps,
  runtime prerequisites, helper PATH and user-manager/Wayland environment.
  Keep shell dependency staging separate from shell startup.

## E2: task contracts

| Area | Required native evidence | Boundary |
| --- | --- | --- |
| Login and greeter | Packaged SDDM/PAM password login to Niri works before theme installation. Derive and preview the selected greeter; install only into the guest, then qualify real login, logout and return to greeter. Inspect field/focus/error/font/cursor behavior. | Disable any exact lab autologin harness only if found; keep console/SSH recovery. Greeter test mode alone does not pass authentication. |
| Wallet and secrets | Use a guest-only KWallet reference setup and disposable secret. Verify intended login unlock, session environment handoff, native Secret Service/provider ownership and secret read after another login. Explain any required prompt or initialization. | This is a proposed guest reference choice matching the documented personal backend. Preserve distribution PAM defaults where possible; document any exact required changes/recovery. No real browser/account secrets, GPG imports, LUKS/autologin or authentication bypass. |
| Authorization | The selected polkit agent starts once with Niri. An owned harmless privileged action produces the actual graphical prompt; cancellation denies it, successful guest authentication permits it. | Sudo success or a mocked prompt is not polkit evidence. No host prompt or privileged host operation. |
| Manual locking and idle | Gtklock accepts the guest password, rejects/cancels an invalid attempt as applicable, and unlocks. Repeated lock requests retain one locker. Reload idle configuration while locked and prove the same locker remains active. Exercise the configured `loginctl` listener. | Use the independent lock service. No stopping a live locker to reload notifications, clipboard or idle policy. |
| Power and session | Choose and record the reference power policy explicitly. Use a temporary short timeout to test display-off/wake where the virtual output supports it; restore the normal policy. Verify menu cancellation and perform a guest-only confirmed reboot/shutdown during final lifecycle checks. | Capture exceptions are separate policy. No physical suspend/lid, battery transition or inhibition claims from an AC-only VM; the retained domain's suspend restrictions stay explicit. |
| Displays | Kanshi owns one real virtual-output profile, starts once, reloads cleanly, and retains a reachable screen after a supported mode/scale change. Check readable applications and restore capture mode afterward. | Virtual mode/scale evidence does not establish docking, physical hotplug, EDID matching or all laptop scales. |
| Input | Start one Fcitx5 owner. Compose disposable English/Chinese text in Chrome and Kitty; check preedit, candidate selection/cancellation, shortcut conflicts, position and glyph fallback, including a supported scale change. | Pasting Unicode or font display alone does not pass IME composition. Investigate actual app/protocol support before choosing flags or global environment overrides. |
| Audio and feedback | Play a deterministic guest sample through PipeWire/WirePlumber and verify the selected virtual sink and signal. Test a small volume/mute change, restore values, and confirm replaceable feedback stays out of notification history. Check source/microphone feedback only where a real guest source exists. | Guest sink/monitor evidence is separate from SPICE transport, physical speaker audibility and microphone capture. Missing backlight/radio hardware remains unavailable rather than simulated as live acceptance. |
| Ordinary files and storage | Open local PDF, image, audio/video and archive samples through the documented defaults; extract an owned archive and compare its file bytes. Repeat browser download/open/upload. Qualify UDisks mounting, sample read/write and safe unmount using a newly created disposable guest-only virtual disk if feasible. | Format only a new, positively identified lab image. No existing host or guest data disk. The virtual mount does not establish physical USB hotplug. |
| Existing core | Repeat SwayNC panel/history with actual available metrics; exact text/image clipboard restore, Delete/Cancel/Clear; Rofi application/utility launches; fresh Kitty/Zsh prompt, history and completion. | No new Network/BT/Audio Rofi controls and no authenticated remote/agent demo required. Radio/device tasks remain hardware checks. |
| Portal sharing | GTK picker uses the intended provider. Actual whole-monitor browser sharing advances frames and stopping releases the stream/nodes. Repeat after a cold boot. | Preserve GTK + WLR. Test the stock WLR route with bounded guest resource protection; apply the explicitly pinned VM compatibility recipe only for the demonstrated failure. Do not promote it to the default/fleet or claim per-window capture. |

The KWallet, input-method, virtual audio and output-power behaviors are
investigation points, not assumed results. Resolve failures within the owning
source/recipe. An unresolved required task prevents a complete Arch-reference
qualification claim. Record narrower progress honestly instead of relabeling
it as a passed full replay.

A change of compositor, terminal, secret backend, portal family or an additional
maintained external fork is a scope decision. Gather a bounded reproduction and
options before expanding into that work; do not silently change the reference
desktop to make a task pass.

For input methods, inspect the tested app/toolkit versions rather than copying
flags from an older guide. For wallet unlock, check both PAM and the session
startup handoff. Relevant upstream contracts are linked below.

## E3: replay rules and acceptance

1. Freeze a reviewable guide/source candidate and task checklist. Stage exact
   candidate/public inputs explicitly; start from a fresh offline clone of
   `arch-base`, not `desktop-demo` or the development disk.
2. Follow the written route in order using an ordinary guest account. Keep a
   transcript, package/input inventory, service ownership and target changes.
   No hidden pilot receipt, private chezmoi, undocumented commands or warmed
   user caches. Test an unwarmed first shell and document any first-use
   Powerlevel10k/gitstatus download; do not claim offline first-run behavior
   from a warmed shell.
3. Run the complete task matrix. Reboot into SDDM, password-login, exercise
   the core tasks and sharing, log out to observe service teardown, then log
   in again and verify one instance of each required owner.
4. Any required manual repair returns the candidate to E2. Incorporate the
   correction into its owner and the written route, then replay from a new
   base copy before claiming a successful installation walkthrough. Stop
   identical retries without new evidence; investigate the blocker instead.
5. Preserve exact preimages and restoration notes for privileged greeter/PAM
   changes, session units and native preferences. Checkpoint the accepted
   stopped guest as a separate `arch-guide` disk/UEFI/XML/receipt tuple. Verify
   the three protected earlier checkpoints remain unchanged. Keep the domain
   autostart-disabled and stop the guest when idle.

## Site, evidence and publication

- Make the main setup page clearly Arch-reference scoped, starting from
  installed Arch. Retain selective recipes and distinguish tested defaults,
  user choices, optional extensions and hardware follow-ups. Avoid duplicating
  implementation or making private chezmoi a prerequisite.
- Add a dated installation receipt with input versions, per-task results,
  necessary compatibility steps, recovery/checkpoint state and remaining
  limits. Keep credentials, wallet state and raw private logs outside Git;
  never type secrets through clipboard history or expose them in captures.
- Keep existing accepted clips and the current visual identity. Add only
  focused evidence needed for newly qualified login/lock/input/audio surfaces,
  or replace footage when shown behavior changes. A new full overview or
  large capture gallery is not required.
- Run appropriate module checks and the repository's required unit, export,
  desktop, terminal, build and browser gates. Review the normal and portable
  site paths, setup links and native media playback. Keep automated/agent
  review distinct from human visual, physical-viewer and device acceptance.
- Prepare local commits and a review preview. Public push/release/site rollout
  and personal fleet changes remain separate authorizations. Rofi controls
  design follows this milestone; Ubuntu/Debian remain deferred for much later.

## Completion checklist

- One ordered guide works from the stated installed-Arch baseline.
- All required native tasks and reboot/logout/relogin pass through that route.
- Required repairs are incorporated and the final fresh replay succeeds.
- Public inputs, local candidate provenance, versions and compatibility limits
  are inspectable without private configuration.
- Source/site/media checks pass; remaining physical and human checks are clear.
- The accepted guest/checkpoint and earlier recovery points are retained,
  Starship's host state is preserved, and the guest is stopped.
- No unrequested release, public-site deployment or fleet mutation occurred.

## Primary references for execution preflight

- [Niri session/systemd integration](https://niri-wm.github.io/niri/Example-systemd-Setup.html)
- [Niri's important session software](https://niri-wm.github.io/niri/Important-Software.html)
- [KDE's KWallet PAM and session handoff](https://github.com/KDE/kwallet-pam)
- [Fcitx5 Wayland application/toolkit integration](https://fcitx-im.org/wiki/Using_Fcitx_5_on_Wayland)
- Existing [login](../recipes/login.md), [session](../recipes/session.md),
  [input](../recipes/input.md), [files](../recipes/files.md),
  [feedback](../recipes/hardware-feedback.md) and [display](../recipes/displays.md)
  recipes. Recheck package/provider/PAM details on the actual tested Arch baseline.
