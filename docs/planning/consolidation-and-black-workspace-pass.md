# Desktop consolidation and black workspace pass

Status: execution authorized, 2026-10-29. The user approved this plan through a
Luna goal loop, including its publication and scoped fleet delivery. Sol owns
design, copy, integration and acceptance; Luna Max owns bounded technical
implementation and validation. Execution results are recorded separately from
the plan's required gates.

## Outcome

Bring the personal desktop, public explanation, recommended Arch installation
and demonstrations into alignment. Preserve the personal story: interactive
Chrome/Dolphin work beside keyboard-driven Kitty/Zsh and native coding agents,
with information and controls available on demand.

The user reports a grey desktop background and asks about pure black for OLED.
The recommendation is an opaque black workspace behind windows, retaining the
warm Neutral Slate application and control surfaces. This is a refinement of
the existing identity, with one maintained theme.

## Measured starting point

- Public source is `6a5e8dded00c68cc4f60856c2b9637051e7e5a6e`; private chezmoi
  source is `04173ad20affb63b2962492d8540d860a94f2fdc`. Both local worktrees were
  clean when planning began. Recheck all source and host state before execution.
- Components 0.4.0 are published from
  `5494554a53527a12f1042a6a742066ec2bb8280c`. The completed rollout records
  matching 22-target controls deliveries on Carbon, Starship and Snap, with
  fresh installed read-only callback/startup proof. Physical credential,
  wallet, audio and peripheral actions remain separate acceptance.
- The independent identity is schema 2, SHA-256
  `6dbb163103e911262b5c1a6b1dd8299863ea790f7a12e7fb264fe9603e8e2455`.
  Crisper Neutral Slate uses `canvas = #111213`; Balanced+ already uses a
  `#000000` terminal background.
- Starship's installed `~/.config/niri/config.kdl` explicitly sets
  `layout.background-color` to `#111213`. The chezmoi template and public
  appearance renderer both take this value from the shared `canvas` role.
  Changing that role globally would also affect Qt palettes and the website.
- No explicit overview backdrop is present in the selected Niri config.
  Niri owns it separately from the workspace background. See the official
  [layout background](https://niri-wm.github.io/niri/Configuration%3A-Layout.html#background-color)
  and [overview backdrop](https://niri-wm.github.io/niri/Configuration%3A-Miscellaneous.html#backdrop-color)
  documentation.
- The controls recipe and design page describe 0.4.0. Architecture/reference
  pages still describe older utility handoffs and adoption milestones.
  Historical implementation receipts retain candidate-era results.
- `data/components.json`, `tools/reference/inputs.json` and the reference
  recordings remain pinned to 0.3.1. The site currently requires recordings to
  match both the global producer record and the current identity exactly.
  This coupling must be resolved before changing the identity; old recordings
  cannot acquire a new identity or component version through metadata edits.

## Design contract

| Surface | Proposed result | Acceptance |
| --- | --- | --- |
| Empty workspace and gaps around windows | Opaque `#000000` | Native lossless capture has black interior background samples, including an empty workspace. |
| Overview backdrop and workspace transitions | Explicit charcoal `#111213` around black workspaces | Native all-black trial hid empty workspace boundaries; preserve those boundaries at normal and fractional scales. |
| Application/control surfaces | Existing warm Neutral Slate | Rofi, SwayNC, GTK/Qt and Dolphin keep their current surface and selection roles. |
| Terminal | Existing pure-black Balanced+ | All framing, sixteen ANSI values, typography and input/session behavior stay identical. |
| Login and locking | Existing neutral secure surfaces | Greeter core bytes/name, root installation and Gtklock appearance stay identical. |
| Website | Existing reading surfaces; black in desktop specimens | Show the actual workspace treatment without turning every page or card black. |

Add explicit selected color roles `workspace_background = #000000` and
`overview_background = #111213`, instead of redefining `canvas`. The native
all-black overview trial passed pixel/navigation checks but lost the visible
boundary of an empty workspace. Sol selected the charcoal surround at the
planned legibility review; retain that trial's receipt as historical evidence.
Validate both roles' RGB form.
Keep schema-2 identities usable: an identity without the workspace role retains
its prior canvas mapping, and one without the overview role emits no new
overview setting. Prove old-identity rendering parity rather than assuming it.

The public Niri appearance fragment and the private Niri projection must agree.
Update only the desktop specimen backgrounds that represent workspaces. The
palette page should name the workspace role separately from UI canvas/surfaces.
Check overview legibility before adopting its black backdrop; a concrete
navigation regression reopens that part of the design only.

## Work sequence and gates

### 1. Reconcile current status and historical evidence

Create a clear distinction between latest published components, the replayed
Arch reference and media capture inputs. Prefer a small explicit record of each
role over a release-management framework. Keep the old 0.3.1 reference selectable
until its replacement passes.

Update architecture, reference, component/source-map and utility descriptions
to explain direct Network/Audio/Bluetooth controls and retained advanced tools.
Keep Session and Clipboard behavior as currently delivered. Mark dated
implementation receipts as historical at their opening and link current status;
do not rewrite their original test claims as new results.

Adjust capture validation to verify each declared historical component/identity
against its frozen inputs and actual asset hashes. Freeze the existing identity
under an explicit historical path before changing its current source. Keep
labels/dates visible where older footage is embedded. Retain negative checks
for missing or mismatched pins; removing equality with the latest release must
not remove provenance validation.

Gate: current-state pages agree; old media bytes and original pins are unchanged;
normal and portable builds and the owned browser suite pass.

### 2. Implement and qualify the black workspace candidate

Own the roles in `design/identity.json`, validation/rendering in
`components/appearance/`, exports in `examples/` and the design/specimen
presentation in `site/` and `scripts/build.py`. Chezmoi owns only its selector,
snapshot, receipts and thin native projection; do not patch a deployed config
or frozen recovery body as the implementation.

Use an isolated native Niri session to check empty space, window gaps,
fullscreen exit, overview, workspace switching and fractional scaling. Inspect
lossless RGB samples away from borders, text and antialiasing. Keep compositor
pixel evidence distinct from a person's OLED/display observation.

Compare all derived outputs before/after. Expect only the Niri background
settings, desktop specimens and role/provenance metadata to change. Some JSON
outputs carry the entire role dictionary and may change without a visual change;
enumerate them explicitly. Require byte parity for terminal colors and shell
code, native UI styles, Qt/KDE palettes and greeter core assets. Fix unexpected
changes before publication.

Gate: backward compatibility, isolated native appearance, generated exports,
component/site tests and builds pass. Freeze a reproducible archive and source
commit. Use a new immutable component release, provisionally 0.4.1; never modify
the published 0.4.0 archive/tag. The revised identity has its own published pin.

### 3. Publish the reviewed tuple and deliver through chezmoi

Review the exact local/remote heads and changed paths. Publishing main also
publishes the site, so any intermediate presentation must describe its actual
reference/adoption state. Publish the component and independent identity only
after candidate qualification; verify direct downloads and immutable hashes.

Requalify the appearance receipt, preserve shell dependency pins and utility/
controls admission, and review every derived difference. Stage verified code,
shell dependencies and appearance before rendering on each host. The complete
22-target controls payload must remain valid even if only metadata changes.

Roll out Snap first, then Starship and Carbon, with scoped status/diff/dry-run,
preimages and a no-write repeat. Niri configuration reloads in place; preserve
native sessions, current locks, power policy, service ownership, network and
pairing state. This change needs no SDDM restart or root greeter update.

Gate: all three hosts have exact installed background settings and healthy
controls/startup paths. Keep any unavailable host pending rather than declaring
fleet completion. Recovery is the previous verified code/identity/receipt tuple
and scoped Niri preimage, with no unrelated source or target reset.

### 4. Close device acceptance through ordinary use

Run this alongside the documentation work when a local operator and suitable
hardware are available. Automated native interaction stays in owned isolated
fixtures or the unattended Snap pilot. Do not drive the attended desktop or
change its live devices as a test shortcut.

| Area | Task | Boundary |
| --- | --- | --- |
| Network | Exact saved-profile selection; personal Wi-Fi credentials; remember versus once; explicit retry/cancel; real Secret Service/wallet behavior | Use a noncritical connection with local recovery. Do not disrupt the sole SSH path or expose credentials in evidence. |
| Audio | Real output/microphone, independent defaults, volume steps and mute | Observe actual sound/input; virtual nodes and inventories alone do not establish it. Restore requested temporary changes. |
| Bluetooth | Suitable paired/spare peripheral, connect/disconnect, bounded discovery, pairing cancellation and explicit trust | Do not remove or unpair a working keyboard. Pairing and trust remain separate choices. |
| Appearance | Black idle workspace on Carbon/Starship; readable controls, overview and focus at everyday scales | Record human visual feedback separately from pixels and automated checks. |

Record passed, failed, unavailable or deferred with host/date and exact version.
A reproducible functional regression goes to its canonical component and needs
a new immutable fix release if necessary. Hardware absence does not pass a task,
and a VM result does not fill that evidence gap. Hardware-only gaps may remain
explicitly documented without blocking the VM reference or site work.

### 5. Replay the updated Arch instructions from a fresh base

Update the operational agent guide, focused recipes and public input inventory
to the reviewed published tuple, including all helpers/library/theme prerequisites
before the three direct-controls launchers. Keep `setup/` as the human overview
and navigation destination, with the recommended agent-guide link prominent at
the top; generate its plain Markdown form from the same operational source.

Use local Starship libvirt/QEMU and a new offline working copy of `arch-base`.
Preserve the accepted `arch-guide`, earlier demonstration and baseline disks,
matching UEFI variables and definitions. Use public inputs only, no private
chezmoi imports or warmed personal state. Keep one Arch guest running at a time
and the existing host network arrangement. Virtualization remains outside
chezmoi; useful guests/checkpoints remain persistent and autostart-disabled.

Follow the written route as an ordinary sudo account. Recheck SDDM password
login/reboot, wallet/polkit, locking/idle independence, Kanshi/Fcitx, browser/file
picker and defaults, sharing, shell, panel/clipboard/feedback, controls, logout
teardown and repeat login. Carry forward the conditional VirtIO WLR workaround
only if the new guest still requires it; never promote it to fleet defaults.

Exercise available Ethernet and virtual audio through the actual controls.
Verify understandable missing-Wi-Fi/Bluetooth states. Reuse owned native service
fixtures for their protocol paths; no guest radio or physical acceptance claim
follows from those fixtures. Correct failed instructions in their owner and
repeat affected gates; an implementation fix changes the release tuple and
requires requalification rather than silently repairing the frozen guest.

Gate: a dated fresh-base receipt, recovery checkpoint and task matrix establish
the new reference. Only then promote it as the numbered installation route.
Ubuntu/Debian, an OS installer/image pipeline and new features remain deferred.

### 6. Capture, review and publish the aligned site

Capture a concise native controls demonstration and a current black-workspace
still in the accepted Arch environment. Use real available Ethernet/audio facts;
wireless sample renderings, if useful, must be separately labeled fixtures.
No personal device names, accounts, secrets or notifications enter public media.

Review the existing overview for reuse versus replacement. Retain matching
footage with its original version/date labels; recapture scenes presented as
current when their workspace background or demonstrated behavior changed. Keep
original captures and checkpoints outside Git and record output/source hashes,
processing and any reused segments. Do not retag old footage as the new release.

Update home/tour/design/architecture/reference/setup together. Preserve the
personal story and concise human overview, with detailed installation steps in
the recommended agent guide. Review at narrow and desktop widths, keyboard-only,
JavaScript-disabled and native media playback/seek paths. Keep human media and
aesthetic acceptance distinct from browser checks.

Gate: required builds/checks pass, current claims match receipts, published
assets match reviewed bytes, and remaining physical/human gaps are explicit.

## Completion and reopening

Complete when the workspace refinement is delivered to all three selected
hosts, the current site consistently describes it and direct controls, and the
updated Arch route has its own fresh replay and correctly attributed media.
Report source, publication, installed, guest and human evidence separately.

Reopen only concrete failures: a device/workflow regression, illegible overview,
an instruction that cannot be followed, stale public claims, or changed pinned
inputs. Further palettes, new utility features, other distributions and expanded
virtualization are separate future decisions.
