# Setup overview

Niri Plus is a desktop for browsing and building: Chrome and Dolphin on the
interactive side, Kitty and Zsh at the keyboard, with Niri arranging both.
This overview is for reference: it explains what the setup includes and the
choices to make. For installation, we recommend working with an agent using
the detailed guide linked below.

## Set up with an agent

**The recommended way to install Niri Plus is with an agent.** Give it the
guide, let it inspect your machine, and work through the choices together.

[Set up with an agent](setup-agent.md)

Share the guide or its [plain Markdown version](../setup/agent.md) with your
agent. Ask it to inspect your current setup, work through your choices, and
report what it verified. For one component, use a [focused recipe](setup-agent.md#focused-recipes).

## What you get

- **A coherent desktop:** warm Neutral Slate surfaces, Clear Blue focus,
  a pure-black workspace, Noto/Meslo fonts and a separate Balanced+ terminal palette.
  [See the design](design.md).
- **Tools on demand:** Rofi for apps and utilities, SwayNC for notifications
  and system information, Cliphist for text/image history. No permanent bar.
- **Everyday desktop support:** login, locking, displays, audio/brightness
  feedback, files, network/Bluetooth entry points, input methods and
  whole-monitor sharing.

The numbered Arch install target selects components 0.4.3 with SwayNC
0.12.6-18 from fork release 1. Its authored reference profile selects the unified
information panel at width 448, full height, with zero margins, individual
notifications, a bold clock and inline Do Not Disturb control.
Managed-host rollout evidence remains separate in
[setup status](../data/setup.json).

The 0.4.3 reference includes [direct Rofi controls](recipes/rofi-controls.md)
for Network, Audio and Bluetooth. Native tools remain available for deeper
settings and recovery. The [stateful illustration](../design/rofi-controls/index.html)
explains the shared action and status presentation with sample devices.

Manual display-away is a separate, opt-in extension from components 0.5.0. It
does not change the numbered reference's 0.4.3 selection or automatic power
policy; see the [away-mode recipe](recipes/away-mode.md) after the reference is
complete.

The [unified session screen](recipes/session.md#optional-unified-session-screen)
is another opt-in extension in published components 0.9.2: Ctrl+Alt+Delete opens
Lock, Display off, Suspend, Log out, Restart and Shut down. Selecting one starts
a cancellable countdown that confirms the action automatically at expiry.
It is separate from the published component selections and the reference's
acceptance evidence.

The published 0.10.0 Close All helper and profile remain a separate opt-in;
the numbered reference keeps its existing Mod+Q behavior.

## Starting point

Start with **installed Arch Linux x86-64**, a regular sudo account, working
networking and the [reviewed source](setup-agent.md#inputs-and-working-directory).
On an existing desktop, merge into your configuration and keep console or SSH
recovery access. Ubuntu/Debian guides are deferred.

## The setup at a glance

| Stage | Result | Agent steps |
| --- | --- | --- |
| Base session | Niri, Kitty, Rofi and portals; a working stock SDDM password login. | [Packages and first login](setup-agent.md#3-install-the-first-session-packages) |
| Appearance and apps | The selected theme across desktop, terminal and greeter; Chrome and file defaults. | [Appearance, browser and files](setup-agent.md#5-add-the-reference-appearance-and-browser-files) |
| Everyday controls | Dashboard, clipboard, Network/Bluetooth/Audio/Session launchers and brief hardware feedback. | [Notifications and utilities](setup-agent.md#6-install-the-selected-notification-and-clipboard-paths) |
| Session services | Wallet unlock, authorization, locking and an explicitly chosen power policy. | [Wallet and session ownership](setup-agent.md#7-wire-wallet-policy-and-authorization-services) |
| Your workflow | Actual display profiles, input languages, audio, Kitty and the pinned Zsh setup. | [Displays, input and terminal](setup-agent.md#8-add-display-input-audio-and-shell-workflows) |
| Check the whole system | Native tasks, reboot, logout/relogin, sharing and a recovery record. | [Verification and handoff](setup-agent.md#9-replay-the-task-checklist-and-recover-cleanly) |

After the reference, optionally stage the manual display-away companion from
its independent 0.5.0 pin. This branch is separate from the reference's
required acceptance and from the desktop's automatic idle/suspend policy.

## Make it fit your machine

Choose your monitor names/scales and input languages. Review browser defaults,
existing network/login/secret providers, and which optional Plus tools you
actually want. Remote and authenticated agent integrations are separate additions.

Pay particular attention to **power and locking**. The reference example turns
displays off after ten minutes, suspends on battery after thirty minutes, and
has automatic locking and AC suspend disabled. Choose those settings for your
own use; the [session details](setup-agent.md#7-wire-wallet-policy-and-authorization-services)
keep manual locking independent of idle-policy reloads.

## What has been checked

The dated 0.4.3/SwayNC 0.12.6-17 reference passed scoped fresh-Arch staging,
package installation, stock and themed password/cold login, sidebar/DND lifecycle,
clipboard and direct-controls checks. New native videos and stills show the
selected sidebar, with inputs and limitations in the
[dated receipt](planning/swaync-reference-sync-20261107.md). Package 18 retains
package 17's byte-identical runtime paths (`src/`, `data/`, `meson.build`,
unchanged `meson_options.txt`, `man/`); the pin reset is not a new full
fresh-Arch or physical replay. The last complete task
replay used 0.4.1 and is preserved in its
[dated installation receipt](planning/black-workspace-receipt.md#fresh-arch-reference).
Sharing, wallet, IME, suspend and physical-device tasks were not relabelled as
new results in this focused sync. Recheck the full guide on a new target.
