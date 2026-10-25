# Niri Plus desktop brief

Desktop reference plan, 2026-10-24. Neutral Slate is selected. Niri Plus is a complete everyday desktop built from
selected Linux components, shaped around browser interaction and terminal,
development, agent, and remote-host work. The [personal story](../story.md)
remains the explanation for that emphasis.

## Experience and scope

The desktop should be understandable from login through daily work to locking,
leaving, and resuming. Common tasks have explicit owners and reachable action
paths. Status belongs on demand; advanced configuration can remain in commands
and agent-assisted work. The browser and graphical file workflow are first-class
parts of the experience.

The reference includes login, windows/displays, files and default applications,
terminals, Wi-Fi/Ethernet/Bluetooth, audio and brightness, clipboard, capture,
notifications, power, input methods, authorization, and existing secrets
integration. Printing, specialized hardware, and external desk displays remain
optional topics. There is no new operating system, package manager, or generic
installer in this design.

## Proposed reference roster

| Responsibility | Reference choice |
| --- | --- |
| Login and session | SDDM with the standalone greeter; niri-session and session-scoped user services. |
| Windows and displays | Niri with the existing fixed-width/application rules; Kanshi with host-specific profiles. |
| Browser and files | Chrome, Dolphin, Gwenview, Ark, mpv, and explicit MIME defaults. |
| Terminals and development | Kitty, native coding-agent TUIs, Zsh/Powerlevel10k, fzf, zoxide, editor/tmux tools, and Rofi Plus. |
| On-demand desktop information | The pinned SwayNC fork and its native dashboard; no permanent bar. |
| Network management | NetworkManager status in the panel; a Network launcher entry opening Kitty with nmtui. |
| Bluetooth management | BlueZ status in the panel; a Bluetooth launcher entry opening a dedicated bluetoothctl terminal and a pairing guide. |
| Audio | Existing hardware-key helpers and WirePlumber; pavucontrol as the common Audio entry for device/stream choices. |
| Brightness | Existing internal-backlight helper; external monitor controls and optional explicitly qualified DDC. |
| Clipboard | Cliphist and the existing text/image Rofi picker. |
| Locking and power | Gtklock, swayidle, desktop-power, UPower, existing logind policy; a small proposed Session picker. |
| Input and authorization | Fcitx5, the native polkit agent, retained PAM/KWallet integration, and the actual portal profile. |

The three utility launcher entries and Session picker are proposed additions.
They are not installed by this pass. The common Audio entry does not expand the
Starship per-application SwayNC trial to other machines.

## Daily capability contract

The [capability catalog](../../design/capabilities.json) contains 22 outcomes.
Each records the current path, proposed reference path, implementation gap,
owner, hardware variation, and an acceptance task. Its status distinguishes
managed configuration, locally available tools, and planned integration.

NetworkManager already supplies nmcli/nmtui. BlueZ's bluetoothctl, pavucontrol,
and UDisks2 are present on Starship but are not explicit entries in the managed
desktop package manifest. Supporting them as reference capabilities requires
deliberate package admission and per-host checks, not an inference from local
availability.

The proposed utility entries keep the workflow small:

- **Network:** `kitty -e nmtui`. Inspect and change connections through the
  existing NetworkManager interface. The SwayNC card stays a primary-link status
  view.
- **Bluetooth:** `kitty -e bluetoothctl`. Pair/connect/disconnect through the
  existing interactive client and documented steps. The panel stays a connected
  device/battery view; no unimplemented pairing controls are depicted as real.
- **Audio:** `pavucontrol`. Use native device/stream controls, retaining wpctl
  for direct operations and the current hardware-key feedback.
- **Session:** a bounded Rofi helper offering Lock, Logout, Suspend, Restart,
  and Shut down. Reuse native Niri quit confirmation, confirm restart/shutdown,
  and keep the selected lock-before-suspend policy. Cancellation and dispatch
  receive isolated checks before any live trial.

No new modifier bindings are required for those entries: `Mod+D` remains the
discoverable common entry. Existing Mod+N/Y/S/G/A and hardware keys retain their
roles.

## Shared identity and deliberate variations

[Neutral Slate](identity.md) is selected, with its reviewed palette, Noto Sans
UI, Meslo terminal, explicit cursor ownership, and
consistent density and focus cues. Neutral login/lock surfaces remain an
intentional variation.

Native GTK/Qt controls, browser content, and syntax colors retain appropriate
differences. The shared identity governs desktop surfaces, font roles, icons,
cursors, selected controls, and feedback. It does not promise that every native
application or website accepts an arbitrary custom palette.

## Preserve the working behavior

Keep the current window/launcher contracts, native provider ownership, directional
host access, hardware-card lifetimes, clipboard retention, and session service
boundaries. Keep the current per-host output and power policy as data.

The captured personal policy remains display-off after ten minutes, battery
suspend after thirty minutes, no automatic AC suspend, no automatic locking,
and no lock-before-suspend. These values are personal choices and remain labeled
as such in public instructions.

## Evidence and completion

This proposal uses the shared configuration and the scoped Starship audit.
Command presence is not cross-host or behavioral acceptance. Native widget
samples show supported styles/fonts in isolation; candidate boards are labeled
mockups. The [verification plan](verification.md) retains those distinctions.

The design work is ready for review with the selected identity, complete action
map, exact token definitions, implementation steps, and a verification/capture
plan. The color direction is settled; coordinated source promotion and native/
per-host acceptance remain in the next pass. Kitty and Zsh are explicit reference components; only one
theme is targeted initially.
