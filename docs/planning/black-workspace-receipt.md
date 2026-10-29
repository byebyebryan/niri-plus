# Black workspace and desktop consolidation receipt

Recorded 2026-10-29. This implements the [consolidation plan](consolidation-and-black-workspace-pass.md).
Components 0.4.1 and the selected identity are published, and the scoped update
is installed on Carbon, Starship and Snap. Fresh-Arch replay and current capture
results will be recorded here before the installation reference is promoted.

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

The final frozen replay is in progress from a new offline copy of the installed
Arch base. It uses public inputs, an ordinary sudo account and stock SDDM
password login before theming. Existing reference/demo/base checkpoints remain
protected, and the VM is autostart-disabled. The operational route is still
0.3.1 until the 0.4.1 task matrix and recovery checkpoint pass.

The first development attempt found that Qt6ct warns when
`QT_QPA_PLATFORMTHEME=qt5ct:qt6ct`. Native Qt5 and Qt6 plugin/palette probes
showed that the single `qt5ct` name selects the matching installed plugin for
both versions while preserving colors and fonts and removing that warning.
The public recipe was corrected; managed hosts already used the single name.
The final replay starts from a fresh base with the corrected frozen recipe.

## Media and publication

The four earlier desktop clips remain byte-identical, labeled with their
original 0.3.1 component tuple, retained identity and capture dates. Current
controls media and a black-workspace still are pending the accepted replay.
Human playback review remains separate from automated browser/media checks.
