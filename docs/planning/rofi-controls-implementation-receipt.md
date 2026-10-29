# Direct Rofi controls implementation receipt

Status: local 0.4.0 candidate under integration, 2026-10-29. No component
release, public-site deployment, personal chezmoi selection or fleet apply has
been performed in this pass.

The [design plan](rofi-controls-pass.md) and
[pre-implementation review](rofi-controls-design-review.md) define the scope.
The native proof selected the documented fixed-view fallback: Open/Details on
the list, then a pinned target with its own action strip. No Rofi fork or
per-highlight subprocess hook is used.

Current source includes Network, Audio and Bluetooth controls, temporary
native credential/pairing agents, generated appearance outputs, bundle inputs,
tests and owned native checkers. Session, Clipboard, notification cards,
power/locking, independent Plus pickers and the terminal palette retain their
existing implementations.

## Integration evidence

- Native Rofi 2.0.0 on private Xvfb: masked credential handoff, fixed actions,
  stable duplicate selection, pending completion, inline Audio and Escape.
  Final candidate rerun and installed-bundle proof are still pending.
- Real NetworkManager 1.58.1/libnm in private mount/network/UTS namespaces:
  14 checks passed, including virtual Ethernet activation, accepted-versus-active,
  targeted cancellation, another adapter retained, and stale daemon rejection.
  Host routes/resolver and captured NetworkManager/Docker/Tailscale/Niri/SwayNC/
  idle/349d service PIDs matched before and after.
- Native NM agent on a private root-owned D-Bus peer: 19 checks passed for
  registration/coexistence, scoped GetSecrets, storage policy, request-new/retry,
  Save/Delete, failures, cancellation, explicit and connection-loss retirement.
  Its activation callback is synthetic; the real wired proof is separate.
- Real PipeWire/Pulse virtual devices with policy-only WirePlumber: 23 checks
  passed for independent defaults, repeated volume, channel balance, mute,
  amplification limits, replaced node identity and missing-service handling.
- Private BlueZ protocol, pairing, native Wayland, final bundle/site gates and
  source review remain in progress. They are not passes at this point.

## Boundaries

These fixtures do not qualify physical Wi-Fi credentials/rfkill/removal, actual
speaker/headset/microphone behavior, or real Bluetooth adapters, keyboards and
pairing. Human visual and physical acceptance remain separate. No host network
owner, power service, notification owner, active lock or native session is used
as a test fixture. The retained Arch guests and checkpoints remain untouched.
