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

The 0.4.1 reference includes [direct Rofi controls](recipes/rofi-controls.md)
for Network, Audio and Bluetooth. Native tools remain available for deeper
settings and recovery. The [stateful illustration](../design/rofi-controls/index.html)
explains the shared action and status presentation with sample devices.

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

The reference passed a fresh installed-Arch VM replay. The [installation
receipt](planning/black-workspace-receipt.md#fresh-arch-reference) records the results and the VM's
VirtIO sharing workaround; physical hardware and human acceptance remain
separate. See the [component source map](components.md) for release and
personal-host deployment status.
