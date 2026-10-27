# Reconcile reusable Niri Plus components

Planning origin: 2026-10-26. The direction is agreed: Niri Plus should own the
reusable custom desktop and shell pieces, chezmoi should consume them and supply
personal configuration, and established component repositories should retain
their implementation and release ownership. The contracts below record the
accepted scope; current producer and consumer status is summarized here.

## Current checkpoint status

| Checkpoint | Status | Evidence and remaining boundary |
| --- | --- | --- |
| A. Desktop source and bundle | Complete | Public desktop module and reproducible exports are included in the versioned bundle. |
| B. Desktop consumer | Complete | Deployed on Carbon, Starship and Snap; 16 shared files matched byte-for-byte, scoped repeats were no-ops, and services, processes and captured policy were preserved. |
| C. Shared shell candidate | Complete | Shared init/finish, prompt and dependency pins are published; the personal shim remains in chezmoi. |
| D. Shell consumer | Complete | Applied and PTY-qualified on all three hosts; repeat applies were no-ops and existing sessions were preserved. The cache verifier validates known `.zwc` headers/layouts and compares every loaded byte and mode with a fresh native Zsh compilation, normalizing only validated unused alignment padding. |
| E. Appearance reconciliation | Complete | The [0.3.0 producer record](../../data/components.json) pins the verified archive, appearance adoption revision and final consumer source revision. All three hosts converged across 35 scoped targets with zero drift; repeated runs made no writes. All 39 derived outputs per host matched the approved receipt, and all 45 pre-change/native comparisons passed. Six toolkit checks, four reviewed images and guarded greeter execution for all profiles passed with zero privileged-write requests. Native processes, service identities, packages and protected root files were preserved. |
| F. Public ownership map | Complete | The [component source map](../components.md) and [producer record](../../data/components.json) identify the canonical owners, immutable bundle, personal consumer boundary and deployment evidence. |

`data/setup.json` remains the dated record of the earlier desktop and utility
delivery. Current shared appearance qualification and rollout are recorded in
the [producer record](../../data/components.json).

## Outcome

Maintain each reusable implementation once. Build the public examples,
downloads, tests and deployed copies from that implementation. A change to a
shared helper or prompt should no longer require a separately edited public
copy and private implementation.

Keep the deployment familiar: existing commands, configuration paths, service
ownership and personal policy remain. The migration is about source ownership
and delivery; functional changes receive their own explicit review.

## Inspected baseline

- Public repository: `5f4653659a0ecc0d8d1299de0a6df39c962d8a01`.
- Chezmoi: `8e1309c086216be365ed5620536a7b7fe5fbbd94` on all three hosts.
- Carbon, Starship and Snap use Zsh 5.9.2. A read-only check found all four
  installed Zsh dependencies at the revisions in
  [the public pin manifest](../../examples/terminal/pins.json).
- Many desktop examples are exact copies of private managed helpers. The
  portable Zsh files are adaptations, not exact copies of the native setup.
- The active prompt bodies are still loaded from chezmoi's
  `.chezmoitemplates/niri-plus/legacy/p10k*.zsh`; the name is misleading for
  those active inputs. Kitty also reuses its legacy body for non-color settings.
- Appearance identity originates in [design/identity.json](../../design/identity.json),
  native adapters live in chezmoi, and frozen renders return to public examples.
  The selected canonical digest remains
  `6dbb163103e911262b5c1a6b1dd8299863ea790f7a12e7fb264fe9603e8e2455`.

Reinspect heads, worktree changes and host state before execution. These are
planning observations, not permission to overwrite later work.

## Ownership and migration inventory

| Piece | Current authoritative owner | Consumer boundary |
| --- | --- | --- |
| `desktop-power`, `desktop-session-ready`, `desktop-session-menu` | Niri Plus desktop module | Chezmoi supplies the captured policy and existing service wiring. |
| `notify-volume`, `notify-brightness`, `rofi-clipboard` | Niri Plus desktop module | Existing command names, tools, state paths and key bindings remain. |
| Generic idle/battery/lock unit bodies and utility desktop entries | Niri Plus desktop module | Chezmoi selects hosts, locker executable, dependencies, wants links and native drop-ins. |
| Zsh history/completion, agent detection, prompt, custom segments and ZLE watcher | Niri Plus shell module | A personal startup shim supplies paths, compatibility choices and CLI integrations. |
| Zsh upstream pins and opt-in fetcher | Niri Plus shell module/tools | One pin manifest; dependency staging stays separate from starting a shell. |
| Neutral Slate renderers and generic appearance merge logic | Niri Plus appearance module | Chezmoi selects identity, toolkit/profile and owned native keys. |
| SDDM pure derivation | Niri Plus appearance module | Root installation, system override and activation remain in chezmoi. |
| Kitty input/paste/glyph/session options and notification-label policy | Chezmoi initially | Appearance moves through the shared renderer; the small provider-specific notification hook remains an intentional private integration. |
| `.zshenv`, cloud/Android SDK setup, pyenv/kubectl integration, local defaults | Chezmoi | Personal and noninteractive environment setup is not exported into the generic core. |
| Actual Kanshi matches, Niri rules/binds, power values, input engines, MIME choices, packages and routes | Chezmoi | Public reference examples remain separately labeled portable choices. |
| SwayNC, SSH/Tmux/Agent Plus, Observer/Mesh, external displays | Existing repositories | Niri Plus documents and consumes their public contracts/releases. |

Launcher protocol changes belong in the relevant Rofi project. Do not import
its application implementation into Niri Plus merely because its binding is
part of this desktop. Native credentials, conversation state, clipboard/history,
pairings, dictionaries and hardware identifiers remain outside public artifacts.

## Public source layout

Implemented layout within the existing repository:

```text
components/
  desktop/       # command bodies, reusable units and desktop entries
  shell/         # init/finish, prompt, segments and dependency pin manifest
  appearance/    # pure renderers, generic merge logic and greeter derivation
scripts/         # bundle/export/check tools
design/          # existing canonical identity and retained design history
examples/        # generated current exports plus authored reference profiles
docs/            # story, guides, ownership and versioned adoption instructions
```

Use one component bundle and release version for these small modules. Modules
can be selected independently. The shell module must work on a Linux host
without Niri, a graphical session, wireless tools or a battery; missing optional
integrations must remain harmless. Do not introduce a new repository or a
desktop installation framework for these pieces.

The public and private ownership instructions identify Niri Plus as the source
for reusable modules; private wrappers contain personal integration.

## Bundle and chezmoi delivery contract

Publish a small deterministic first-party component archive with a version,
source commit and schema-1 manifest. The manifest lists modules, relative file
paths, SHA-256 values, executable modes, API version and prerequisites. Retain
upstream attribution/pins; third-party source trees are separate verified inputs.
Do not release a whole workstation configuration or embed host state.

The private selector `deployments/niri-plus-components.json` records
the exact published artifact URL, commit, archive/manifest digests and explicit
module admission for each host. Keep it independent from the existing
`deployments/niri-plus.json` identity pin and utility admission. Installing
shared code must not imply selecting a theme or enabling utility entries.

Initial admission covers only the existing Carbon/Starship/Snap cohort.
Desktop admission continues to require the known minimal Niri/GTK profile.
Unknown, DMS and KDE hosts retain their existing output. Shell-only use is a
supported module boundary, not authorization to enroll additional machines.

Delivery order:

1. Stage the reviewed archive under an immutable component/version directory
   in the user's Niri Plus data root. Verify archive, manifest and every payload
   file before making it eligible for consumption. Reject incomplete staging
   and unexpected replacements; retain previous versions.
2. Stage required upstream dependencies separately at exact pin revisions.
3. Render/diff the selected projection, then apply only reviewed native targets.

The stager must be callable independently of chezmoi's target rendering, so a
missing bundle cannot prevent the operation that supplies it. Once selected,
missing, unpublished or mismatched payloads make managed rendering/apply fail
with a useful staging error. Do not fetch code or run an installer while merely
rendering a file.

Keep deployed helpers and unit files as ordinary chezmoi-managed files at their
existing paths. Thin templates read verified bytes from the staged archive;
they do not maintain a second body of shared code. Chezmoi's
[absolute-path include](https://www.chezmoi.io/reference/templates/functions/include/)
supports this projection; a temporary-file probe confirmed it with the installed
version. Verify the manifest and selected file digest when reading the payload.
This keeps native diffs and byte comparisons useful.

In particular, keep `desktop-session-menu` and `desktop-session-ready` adjacent
under the existing bin directory: the menu resolves its helper relative to its
own file. Preserve the power helper's generated callback paths as well. A local
development override may exist only for isolated fixtures; production selectors
must consume published immutable artifacts.

## Shell reconciliation contract

The shell is the main behavior-sensitive part of this migration. Compare native
and portable versions before selecting the shared implementation. Record each
difference as a personal parameter, portability/testability improvement or
intentional behavior choice; do not choose either whole file blindly.

The shared shell entry points are `niri_plus_shell_init` and `niri_plus_shell_finish`,
with a computed, non-exported `NIRI_PLUS_SHELL_MODE=agent|human`. Source loading
defines the interface; initialization selects the mode and base setup. The
personal `.zshrc` explicitly returns in agent mode before its human-only hooks.
Finalization is harmless in agent mode and runs syntax highlighting after the
human CLI/widget integrations. This avoids treating a `return` inside a sourced
module as a return from its caller.

Preserve `ZSH_FORCE_FULL_PROMPT`/`ZSH_FORCE_SIMPLE_PROMPT`, prompt layout,
semantic ANSI indices, history behavior, key bindings, optional tools, watcher
cadence and descriptor/process cleanup. No provider authentication or native
conversation lifecycle moves into the shell module.

Known differences to settle explicitly:

- Native Zsh initializes history before its agent detection. The shared API
  computes mode first; `NIRI_PLUS_ZSH_AGENT_HISTORY=skip|legacy` keeps the
  behavior explicit. Public default `skip` leaves history uninitialized in
  agent mode; private compatibility selection `legacy` retains history
  initialization before returning in agent mode.
- The native history path and completion cache differ from the portable XDG
  choices. The personal shim supplies existing paths. Do not move, clear or
  rewrite history/completion state as part of extraction.
- Preserve personal Ghostty integration, SDK/tool initialization and editor/
  browser choices in the consumer layer. Keep syntax-highlighting registration
  after any integration that changes ZLE widgets.
- Bring the public proc/sys fixtures, safe read helper and watcher exit guard
  into the shared candidate with tests. Verify their intended native behavior;
  retain the selected color roles instead of carrying incidental initialization
  differences or string-replacing a live body named `legacy`.

CI portability note: Ubuntu's Zsh completion audit uses `getent` and `grep`.
Restricted shell fixtures expose those system helpers and copy the trusted
system `Completion` and `Misc` function trees into an owned mode-0700 path.
Fixture shells use only that `FPATH`; noninteractive checks reset it after
`zshenv`, while owned interactive checks use `-d` and reset it at the start of
their own `.zshrc`. The normal `compinit` security audit remains enabled. The
optional-tools case still omits unrelated tools and devices. Ubuntu Zsh 5.9
also reports missing optional sysfs reads on stderr, although the probes fail
safely and the shell check completes. The selected fleet's Zsh 5.9.2 rollout
was quiet; this CI-only observation did not change the released shell payload.

Keep prompt files at their existing managed paths where possible; a new shared
entry file can live alongside them. Existing shells, tmux clients and provider
sessions remain running. New-shell acceptance uses owned PTYs and later normal
Kitty use, not input injected into a working user session.

Unify dependency authority on the existing public pin manifest. All three hosts
currently match its four revisions, so the first adoption needs no plugin
upgrade. Stage pinned archive trees in an immutable dependency directory and
give the core its resolved plugin/theme roots. Stop refreshing the old floating
git externals only for admitted shell consumers; retain the old clones and
their local changes for recovery. Do not invoke the component/dependency
installer from shell startup. Preserve upstream Powerlevel10k's existing pinned
gitstatus binary/cache behavior; a first-use binary download is a separate
upstream boundary and must not be mislabeled as fully offline startup.

## Appearance and public export contract

Move pure color/style generation and greeter derivation into Niri Plus. Keep
host/profile selection, supported toolkit choices, native preference ownership
and root installation in chezmoi. Preserve desktop/terminal separation, schema-2
terminal roles, the current identity digest, Qt visited-link ownership, font
serialization, Rofi compatibility aliases and all non-appearance Kitty options.

Code and identity pins are independent. An explicit preparation step combines
a verified renderer with the reviewed identity and writes derived outputs into
a separate staging directory, with both inputs and output hashes recorded.
Templates then read verified outputs and merge only their declared native keys.
Rendering remains pure: no root writes, desktop actions or preference changes.

The first adoption must reproduce the current owned native outputs on all three
hosts, including Qt/KDE groups and the root greeter's derived files. Existing
SDDM installation/recovery and CSS-only SwayNC reload boundaries remain. No
SDDM restart, active-lock interruption or theme redesign belongs in this pass.

Generate current example/download files from these same modules. Retain existing
public URLs and useful GitHub-readable files: generated snapshots may remain
tracked, marked as generated in their manifest, with a CI regeneration check. Portable
profiles and historical specimens stay labeled and have explicit origins.
The two readiness-helper download locations must be emitted from one source.
Keep the existing opt-in shell fetcher's new-directory and startup-file contract.
Public builds must use repository source and declared inputs, without requiring
the private chezmoi checkout, a live desktop or the developer's home state.

## Execution checkpoints

| Checkpoint | Work | Required evidence before advancing |
| --- | --- | --- |
| A. Desktop source and bundle | Move unchanged reusable helpers, unit bodies and entries; add manifest/export/staging support and ownership docs. | Exact helper parity, isolated dispatch/cancellation/policy checks, helper-neighbour tests, deterministic archive and reproducible public exports. |
| B. Desktop consumer | Publish/verify the artifact, select desktop code explicitly, replace private bodies with verified includes and deploy scoped targets. | Excluded-host parity, missing/corrupt/unpublished rejection, zero native behavior delta, per-host recovery, scoped convergence and no-op repeats. |
| C. Shared shell candidate | Reconcile native/portable differences, add the init/finish contract and one upstream pin source; prepare the personal shim. | Headless human/agent matrix, native compatibility parameters, plugin/widget order, prompt/fixture parity, timer/FD cleanup, unchanged history paths and no implicit component installer. |
| D. Shell consumer | Stage exact dependencies, then qualify the shim/core on Carbon, Starship and Snap. | Complete payload before selection, owned new-shell/PTY acceptance, retained native sessions and old clones, scoped convergence/no-op repeats; normal Kitty/tmux/SSH follow-up recorded separately. |
| E. Appearance reconciliation | Move renderers/merge code and switch both public generation and private adapters to the shared source. | Current palette/geometry parity, native isolated GTK/Qt/Rofi/Kitty/SDDM evidence, safe owned-key merges and separately reviewed activation. |
| F. Final ownership cleanup | Update site/source maps, remove superseded active bodies and document the maintenance path. | Every current shared export regenerates from its owner; only frozen excluded-profile/fallback/history inputs remain duplicated; installed/public pins and boundaries are recorded. |

Treat these as separate reviewable checkpoints with bounded commits and artifact
versions. A later execution loop can cover several checkpoints, but must not
skip publication, consumer qualification or per-host evidence. Begin with A/B;
the shell is not the first live migration experiment.

## Fleet rollout, stop conditions and recovery

For each admitted group: reinspect source heads and worktrees, archive target
preimages and selected source/state, stage and verify the exact artifact, review
scoped status/diff/dry-run with `umask 022`, then apply Carbon, Starship and Snap
in that order. Capture process/service identities and the unrelated configuration
needed to prove this group's boundary. Preserve Snap's unrelated source work.

For unchanged desktop outputs, a source change may need no native write or
restart. Record installed and currently running versions separately rather than
restarting services just to refresh metadata. Any required activation is owned
by its existing reload group; manual locking remains independent of idle.

Stop for unexpected target or policy differences, incomplete staging, hash/API
mismatch, changed native work, broken input or prompt behavior, unexpected
migration-owned processes, unbounded probes, timer leaks, or an unsafe service/greeter action. Do not expand
the package/runtime/device cohort to make a check pass.

Rollback restores the previous selector and exact target preimages, retaining
old immutable bundles, dependency trees and frozen fallback inputs. Switching a
source pin alone is not proof of recovery: verify scoped output, new invocation
behavior and any previously activated group. Leave an active locker and ordinary
native work alone; root greeter rollback is separate. No automatic artifact or
state cleanup is included in the initial migration.

## Completion criteria

Shared desktop code, shell logic and appearance generation each have one public
authoring location. The private repository contains personal policy, projection,
selection and deployment rather than hand-maintained shared copies. Frozen
fallback inputs may remain for excluded profiles and recovery; do not delete
them while referenced. Public exports and the selected managed implementation
derive from the same versioned code and explicitly declared profiles.

Run appropriate module checks, the full private source suite, site build and
owned browser checks. Record published artifact proof, per-host scoped delivery,
repeat-apply behavior and preserved native state. Physical login, device,
scaling/docking and fresh-install acceptance stay explicitly separate from
source, package and isolated rendering evidence.

This document preserves the original contracts and rollout boundaries. The
source and host evidence now lives in the component map and producer record;
future acceptance updates should add evidence at the level actually observed.
