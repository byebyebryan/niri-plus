# Components and source ownership

Niri Plus keeps the small shared implementations used by this desktop in a
versioned public bundle. This page maps those sources to their downloadable
examples, identifies what remains personal configuration, and records the
current qualification state. It is a maintenance reference, not a workstation
installer.

## Public source and example map

| Module | Canonical source at the 0.3.0 producer revision | Public examples and downloads | Consumer boundary |
| --- | --- | --- | --- |
| Desktop | [`components/desktop/`](https://github.com/byebyebryan/niri-plus/tree/975eab393d2c4e920448eda888d2dc8f0242b396/components/desktop) | [`desktop-session-ready`](../examples/desktop/desktop-session-ready), [`notify-volume`](../examples/feedback/notify-volume), and [`desktop-power`](../examples/session/desktop-power) | Chezmoi supplies host admission, power policy, package choices and existing service wiring. The two session-readiness downloads come from one source. |
| Shell | [`components/shell/`](https://github.com/byebyebryan/niri-plus/tree/975eab393d2c4e920448eda888d2dc8f0242b396/components/shell) | The [Zsh starter](../examples/terminal/zshrc), [init module](../examples/terminal/init.zsh), and [opt-in fetcher](../examples/terminal/fetch.py) | Chezmoi keeps the personal startup shim, SDK and tool setup, local defaults and history/cache paths. The shared shell also works headlessly without Niri or Wayland. |
| Appearance | [`components/appearance/`](https://github.com/byebyebryan/niri-plus/tree/975eab393d2c4e920448eda888d2dc8f0242b396/components/appearance) | The [Rofi theme](../examples/theme/neutral-slate.rasi), [SwayNC stylesheet](../examples/theme/swaync.css), [Kitty fragment](../examples/kitty/neutral-slate.conf), and standalone [SDDM preview helper](../examples/login/derive-theme.py) | Chezmoi selects the identity and native keys, merges owned preferences, selects machines and owns root installation. |

`components/metadata.json` at the [producer revision](https://github.com/byebyebryan/niri-plus/blob/975eab393d2c4e920448eda888d2dc8f0242b396/components/metadata.json)
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

The current producer record is [`data/components.json`](../data/components.json).
It pins one small deterministic archive, its source commit and manifest hash:

- Version: `0.3.0`, API version `1`
- [Release archive](https://github.com/byebyebryan/niri-plus/releases/download/components-v0.3.0/niri-plus-components-0.3.0.tar.gz)
- Source commit: [`975eab393d2c4e920448eda888d2dc8f0242b396`](https://github.com/byebyebryan/niri-plus/tree/975eab393d2c4e920448eda888d2dc8f0242b396)
- Archive SHA-256: `7ac7ca4494826c37e364343838681320dfa759e8a12969f07c4200f10be75d1d`
- Root `manifest.json` SHA-256: `f10fceaa07eb4e9d62e0afef9fe8339bfab09c34d8c9528db962ea4d9e67bf76`

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

## Current adoption status

| Module | Current evidence |
| --- | --- |
| Desktop | Deployed and converged on Carbon, Starship and Snap. Sixteen shared files matched byte-for-byte; scoped repeat runs made no writes and preserved services, processes and captured policy. |
| Shell | Deployed and qualified on all three hosts. Owned full-prompt PTY checks passed on each; scoped repeats were no-ops and existing sessions were preserved. |
| Appearance | Applied at adoption revision `9f2bf9689d27a5698c25c0e604a835b5370b0624`; the final verified consumer source revision is `e8a11e79b3009bebf1d931c5d3e64982692e2f25`. All three hosts converged across 35 scoped targets with zero drift; repeat runs and the greeter hook made no writes. All 39 derived outputs per host matched the approved receipt byte-for-byte, and all 45 pre-change/native comparisons passed. Native process counts (8/8/9), eleven service identities per host and package state were preserved; 25 protected root-owned files retained bytes, modes, owners and mtimes. Six isolated toolkit checks, four reviewed images and guarded greeter execution for all three profiles passed with zero privileged-write requests. No SDDM restart was needed. |

These checkpoints are distinct. The earlier desktop delivery in
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
