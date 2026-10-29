# Set up Niri Plus

Niri Plus is a desktop for browsing and building: Chrome and Dolphin on the
interactive side, Kitty and Zsh at the keyboard, with Niri arranging both.
Adopt the reference desktop or use a few pieces. The [agent setup guide](setup-agent.md)
holds the commands, verification and recovery details.

## What you get

- **A coherent desktop:** warm Neutral Slate surfaces, Clear Blue focus,
  Noto/Meslo fonts and a separate pure-black Balanced+ terminal palette.
  [See the design](design.md).
- **Tools on demand:** Rofi for apps and utilities, SwayNC for notifications
  and system information, Cliphist for text/image history. No permanent bar.
- **Everyday desktop support:** login, locking, displays, audio/brightness
  feedback, files, network/Bluetooth entry points, input methods and
  whole-monitor sharing.

## Before you start

Start with **installed Arch Linux x86-64**, a regular sudo account, working
networking and the [reviewed source](setup-agent.md#inputs-and-working-directory).
On an existing desktop, merge into your configuration and keep console or SSH
recovery access. Ubuntu/Debian guides are deferred.

## The setup at a glance

| Stage | Result | Detailed instructions |
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

## Set it up with an agent

Send your agent the [agent setup guide](setup-agent.md) with this request:

> Help me set up Niri Plus on this Arch machine using this guide. Inspect the
> current setup first and preserve my configuration and recovery access. Ask
> about display, input and power-policy choices, then work through the stages
> and report what was verified and what still needs my input.

A [plain Markdown guide](../setup/agent.md) is also available for agents that
prefer text. Both versions of the detailed guide come from the same source.
For a single component, jump to its [focused recipe](setup-agent.md#focused-recipes).

## What has been checked

The reference passed a fresh installed-Arch VM replay. The [installation
receipt](planning/arch-installation-receipt.md) records the results and the VM's
VirtIO sharing workaround; physical hardware and human acceptance remain
separate. See the [component source map](components.md) for release and
personal-host deployment status.
