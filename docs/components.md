# Components and source ownership

Niri Plus keeps the small shared implementations used by this desktop in a
versioned public bundle. This page maps those sources to their downloadable
examples, identifies what remains personal configuration, and records the
current qualification state. It is a maintenance reference, not a workstation
installer.

The **published 0.4.0 direct-controls release** adds Network/Audio/Bluetooth helpers,
a shared controller and two additional appearance outputs, all listed in
`components/metadata.json`.
See the [release and installation recipe](recipes/rofi-controls.md) and
[implementation receipt](planning/rofi-controls-implementation-receipt.md).
It is installed through chezmoi on Carbon, Starship and Snap. The numbered Arch
reference remains 0.3.1 pending its next fresh-base replay; dated adoption
records below retain the release they qualified.
Direct-control desktop-entry downloads live under
`examples/desktop/direct-controls/`; the existing entries are frozen 0.3.1
baseline/recovery examples. Downloadable wrappers require the complete sibling
`lib/niri_plus_controls` package.

## Public source and example map

| Module | Canonical source at the 0.3.1 producer revision | Public examples and downloads | Consumer boundary |
| --- | --- | --- | --- |
| Desktop | [`components/desktop/`](https://github.com/byebyebryan/niri-plus/tree/014a14241bd722186ae9248e71162e75cf7af7b1/components/desktop) | [`desktop-session-ready`](../examples/desktop/desktop-session-ready), [`notify-volume`](../examples/feedback/notify-volume), and [`desktop-power`](../examples/session/desktop-power) | Chezmoi supplies host admission, power policy, package choices and existing service wiring. The two session-readiness downloads come from one source. |
| Shell | [`components/shell/`](https://github.com/byebyebryan/niri-plus/tree/014a14241bd722186ae9248e71162e75cf7af7b1/components/shell) | The [Zsh starter](../examples/terminal/zshrc), [init module](../examples/terminal/init.zsh), and [opt-in fetcher](../examples/terminal/fetch.py) | Chezmoi keeps the personal startup shim, SDK and tool setup, local defaults and history/cache paths. The shared shell also works headlessly without Niri or Wayland. |
| Appearance | [`components/appearance/`](https://github.com/byebyebryan/niri-plus/tree/014a14241bd722186ae9248e71162e75cf7af7b1/components/appearance) | The [Rofi theme](../examples/theme/neutral-slate.rasi), [SwayNC stylesheet](../examples/theme/swaync.css), [Kitty fragment](../examples/kitty/neutral-slate.conf), and standalone [SDDM preview helper](../examples/login/derive-theme.py) | Chezmoi selects the identity and native keys, merges owned preferences, selects machines and owns root installation. |

`components/metadata.json` at the [producer revision](https://github.com/byebyebryan/niri-plus/blob/014a14241bd722186ae9248e71162e75cf7af7b1/components/metadata.json)
declares the bundle inputs, public exports and module prerequisites. The
generated files keep their existing public paths. Their source and hashes are
recorded in the [example manifest](../examples/manifest.json). Portable profiles
remain authored for their intended audience; historical specimens remain
identified as history. Neither is silently regenerated from a selected native
profile.

The appearance module returns desktop, terminal, font and role outputs from the
schema-2 identity. Its color code and the identity pin are separate inputs. The
SDDM preview helper is a standalone generated file: it can be downloaded and
run with an unpacked pinned theme and identity without the Niri Plus checkout.
The root installer and activation stay with the private consumer.

## Personal and independent owners

Private chezmoi owns Bryan's `.zshrc` integration, personal environment and
policy, host and utility admission, selected native preferences, monitor
matches, device routes, and privileged greeter installation. Shared code is
staged as ordinary files at their existing targets. Shell startup never
downloads or installs the component bundle. The pinned shell dependency fetcher
is an explicit separate operation.

Shell dependency staging pins upstream text separately from the first-party
release. Powerlevel10k can create nine known `.zwc` runtime caches. The private
verifier checks each cache's single-file header and layout, then compares every
loaded byte and mode with a fresh native Zsh compilation. It normalizes only
the validated 0–3 unused alignment bytes at the end of each endian half, and
rejects extra caches or changes to loaded code, metadata or mode. This preserves
upstream cache behavior without embedding third-party files in the component
release.

Established projects keep their implementation and release authority:

| Project | Owns |
| --- | --- |
| [SwayNC fork](https://github.com/byebyebryan/SwayNotificationCenter) | Notification behavior, dashboard widgets, activation and packaging. Niri Plus provides an appearance stylesheet and assembly guidance. |
| Rofi Plus pickers: [SSH](https://github.com/byebyebryan/rofi-ssh-plus), [Tmux](https://github.com/byebyebryan/rofi-tmux-plus), [Agent](https://github.com/byebyebryan/rofi-agent-plus) | Each picker owns its action protocol, launcher arguments and implementation. Niri Plus documents how to connect them to the desktop. |
| [Agent Observer](https://github.com/byebyebryan/agent-observer) and [Mesh Plus](https://github.com/byebyebryan/mesh-plus) | Runtime observation, peer and transport contracts. Desktop admission does not grant routes or move their state into this bundle. |
| [Niri](https://github.com/niri-wm/niri), [Kanshi](https://github.com/emersion/kanshi), [ESP32-RLCD](https://github.com/byebyebryan/esp32-rlcd), and [349d](https://github.com/byebyebryan/esp32-349) | Compositor and output-profile behavior, or independent display and notification-mirror firmware. This repo does not select a machine's monitor matches or hardware routes. |

## Immutable bundle and independent selections

The [release catalog](../data/component-releases.json) records immutable
published tuples independently of the installation reference and recordings.
The latest published release is 0.4.0; the black workspace refinement is being
qualified as a separate release. Historical recordings keep their original
component tuple and retained identity source in
[media provenance](../assets/provenance.json), with their capture date and
component version beside the player.

The 0.3.1 Arch reference producer record is [`data/components.json`](../data/components.json).
It pins one small deterministic archive, its source commit and manifest hash:

- Version: `0.3.1`, API version `1`
- [Release archive](https://github.com/byebyebryan/niri-plus/releases/download/components-v0.3.1/niri-plus-components-0.3.1.tar.gz)
- Source commit: [`014a14241bd722186ae9248e71162e75cf7af7b1`](https://github.com/byebyebryan/niri-plus/tree/014a14241bd722186ae9248e71162e75cf7af7b1)
- Archive SHA-256: `868d9de46f54af9b9f563dd52cd94df9358fafaf9c9b33666c557c05d318a843`
- Root `manifest.json` SHA-256: `de3e981f8bb76d2b4ccfbf7f2722e81fc9f73edf7b62de11cad55f7a209e7ed3`

Adoption can start from a repository clone or from the reviewed release URL and
digests above. A consumer verifies the archive, manifest and every listed file
before staging it. It then selects modules explicitly and reviews their normal
managed targets. The bundle does not contain machine policy, native credentials,
third-party source trees or personal host state.

The release pin is separate from other inputs and choices:

- The appearance identity is pinned by its own SHA-256 in `design/identity.json`.
- Utility entries and the machines allowed to receive them are selected by
  private chezmoi independently from bundle publication.
- Shell plugin revisions live in `components/shell/pins.json`; explicit
  dependency staging is separate from sourcing Zsh.
- Host profiles and native settings remain consumer decisions. Publishing a
  module does not select it on a machine.

## 0.3.1 shell maintenance acceptance

The portable helper's redirection diagnostic regression was introduced in the
[adaptation at `4d4066b`](https://github.com/byebyebryan/niri-plus/commit/4d4066b1916cf49e14d146cd4ef1a337c7e9e5da).
Carbon normal Kitty use exposed missing optional sysfs reads on stderr even
though the probes failed safely. Release `components-v0.3.1` fixes that Zsh
redirection boundary; it changes only `components/shell/p10k-custom-segments.zsh`
among 27 bundle files and was verified against two deterministic builds.

The producer and consumer checks require quiet missing/empty/unterminated reads
and an energy-only battery result of 75%, 10.0W and `3:00`. Host sysfs probes
and owned full-prompt PTYs passed on Carbon, Starship and Snap. Each host had
zero drift across all 35 selected targets, preserved 34 other targets, seven
protected files, 25 protected root files and eleven service identities, and
repeat applies made no writes. Captured process identities remained intact
(Carbon 11, Starship 14, Snap 34). Carbon's temporary trial was removed while
the installed prompt already matched the official payload; the user confirmed
normal Kitty use of the trial with those same bytes. Starship and Snap changed
only the selected prompt target. Snap's pre-existing package-manifest edit and
installed package state were preserved.

Appearance source and identity did not change in 0.3.1, and all 39 derived
output records per host remain byte-identical to the approved 0.3.0 receipt.
The six toolkit checks, four reviewed images and 45 pre-change/native
comparisons remain historical 0.3.0 evidence. For 0.3.1, shell staging
reverified the existing dependency pins and all known present Powerlevel10k
caches on each host; no plugin revision changed. The full consumer suite reran
synthetic cache layout/tamper checks and guarded greeter checks for three
profiles with zero privileged-write requests. No new toolkit, image or physical
qualification was run. Carbon's normal use is recorded for the corrected
prompt; normal new Kitty/tmux/SSH use elsewhere and physical device acceptance
remain separate follow-ups. Consumer shell adoption is revision
`c8e058ed491b63b734c591c6dcff2d21ede7f03e`; the final consumer source and
documentation revision is `43d84fe54a8b07c405fc4461fda5fa14f605043e`.

## 0.3.1 adoption checkpoint

| Module | Evidence at this checkpoint |
| --- | --- |
| Desktop | Deployed and converged on Carbon, Starship and Snap. Sixteen shared files matched byte-for-byte; scoped repeat runs made no writes and preserved services, processes and captured policy. |
| Shell | The 0.3.1 quiet-read correction is deployed and PTY-qualified on all three hosts; see the maintenance acceptance above for fixture results, scoped target preservation and repeat behavior. |
| Appearance | Original qualification remains at adoption revision `9f2bf9689d27a5698c25c0e604a835b5370b0624` under producer 0.3.0. Its 39 outputs remain identical in 0.3.1; toolkit and image evidence remains historical. The 0.3.1 guarded greeter checks requested zero privileged writes. |

These dated checkpoints are distinct. The 0.3.1 consumer source revision is
`43d84fe54a8b07c405fc4461fda5fa14f605043e`; it follows shell adoption revision
`c8e058ed491b63b734c591c6dcff2d21ede7f03e`. The earlier desktop delivery in
[`data/setup.json`](../data/setup.json) remains its dated record; it does not
stand in for qualification or rollout of the current shared appearance
consumer. The same rule applies to source parity, package verification and
normal-use or physical acceptance: each is recorded at the evidence level it
actually covers.

## Maintenance path

1. Edit the canonical owner under `components/`, keeping personal policy and
   independent project behavior with their current owners.
2. Regenerate public component examples with
   `python3 scripts/export-components.py --write`, then run
   `python3 scripts/export-components.py --check`, the module tests and focused
   headless checks.
3. Build the explicitly listed inputs with
   `python3 scripts/build-components.py --output NEW_DIR --source-commit FULL_COMMIT`.
   Review the deterministic archive and root manifest before publishing a new
   immutable version.
4. Update the exact consumer code pin and prepare verified derived files. Review
   the scoped status, diff and dry run before applying only selected targets.
5. Record per-host convergence, repeat behavior and preserved native state
   separately from isolated rendering or physical acceptance.

Public builds and checks use repository source and declared inputs. They do not
need the private chezmoi checkout. There is no broad distribution installer;
portable guides and explicit, reviewable consumer steps remain the adoption
path.
