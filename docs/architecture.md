# Small pieces with clear jobs

Niri owns the windows and navigation. A few selected applications and session
services fill in the rest of the desktop. The arrangement reflects how I work
and how I prefer to maintain it.

<!-- niri-plus:architecture -->
Chrome and Dolphin serve browser and file interaction. Kitty and native coding
agents serve terminal work. Niri arranges their windows. Rofi provides launchers;
SwayNC provides notifications and system information. Session services handle
clipboard collection, automatic idle policy, manual display-away, locking,
authorization, and battery monitoring. Chezmoi owns my configuration and
deployment. The optional away latch has its own session service and does not
add another automatic idle or suspend policy.
<!-- /niri-plus:architecture -->

## The desktop layer

| Job | Current choice | Why it belongs |
| --- | --- | --- |
| Windows and navigation | Niri | Scrolling columns, workspaces, overview, and keyboard navigation. |
| Browser and files | Chrome and Dolphin | Interactive web work, downloads, and graphical file operations. |
| Terminal and shell | Kitty, Zsh, Powerlevel10k, fzf, zoxide | Terminal work, prompt/status, history/completion, directory navigation, and dedicated coding-agent windows. |
| Applications and pickers | Rofi and Rofi Plus | Find applications, hosts, tmux sessions, agent windows, and clipboard items. |
| Common utilities | Direct Rofi Network, Audio and Bluetooth controls; Session helper | Search devices and run explicit actions; open native advanced settings when needed. Session retains lock, logout and power actions. |
| Notifications and information | SwayNC fork | Notification history and a panel of system information, available on demand. |
| Clipboard | Cliphist and wl-clipboard | Collect text and images; a Rofi picker restores the original item. |
| Locking | Gtklock | Manual locks through an independent user service. |
| Idle and power | swayidle and desktop-power | Explicit display, suspend, and battery policy per machine. |
| Manual display-away | Optional `desktop-away` companion | A user-entered latch keeps displays off during unattended work; it leaves automatic idle and suspend policy with their existing owners. |
| Authorization | polkit-kde-agent | Graphical authorization prompts when an application needs them. |
| Login and outputs | SDDM, Kanshi | Display-manager login theme and independent monitor profiles. |
| Portals and input | xdg-desktop-portal, Fcitx5, Niri input | File/screen integration, input methods, and compositor-owned keyboard/touchpad behavior. |

## Keep changes independent

The user services start with the Niri session and stop with its graphical
session. Idle policy, notification reloads, and clipboard configuration have
separate lifetimes. Manual locking has its own service, so an idle-policy reload
does not stop an active locker.

The panel only refreshes its metrics and wireless subscriptions while open.
NVIDIA GPU reads wait for cached runtime activity. Closing it cancels the outstanding
work. This behavior is part of the fork, beyond what a CSS theme can express.

The [direct controls](recipes/rofi-controls.md) use NetworkManager, the existing
audio server and BlueZ without adding a startup daemon. Their current/default
device marker is independent of keyboard selection. The [Session helper and
baseline utility entries](recipes/desktop-utilities.md) remain separate from
session policy. UDisks2 and polkit
authorize removable-drive access; external monitor brightness is separate from
the laptop backlight controls.

The [manual display-away recipe](recipes/away-mode.md) describes the separate
opt-in latch. Normal video and presentation inhibitors remain with the existing
session policy; once explicitly latched away, the companion deliberately
ignores application inhibitors while correcting display wakeups.

The [Arch walkthrough](setup.md) connects each owner to its installation
and recovery guide, including display profiles, login, power services, input
methods and default applications.

## Configuration that an agent can inspect

Most routine investigation and system management happens through commands and
configuration. The useful properties are concrete: a service has an owner, a
configuration has a source, and a change can be reviewed before it is applied.
That fits both working at the keyboard and asking an agent for help.

In my setup, chezmoi manages the machines. It selects packages, configuration,
release pins, and session wiring. The [setup guide](setup.md) presents portable
examples without requiring my personal deployment system.

## Where the projects live

| Owner | Responsibility |
| --- | --- |
| [Niri Plus](https://github.com/byebyebryan/niri-plus) | This desktop story, assembly guides, reusable desktop/shell/appearance modules, and generated public examples. See the [component source map](components.md). |
| Private chezmoi source | My personal environment, machine and utility admission, policies, native preference projection, and deployment. |
| [SwayNC fork](https://github.com/byebyebryan/SwayNotificationCenter) | The panel implementation, activation behavior, and fork packaging. |
| [Rofi SSH Plus](https://github.com/byebyebryan/rofi-ssh-plus), [Rofi Tmux Plus](https://github.com/byebyebryan/rofi-tmux-plus), [Rofi Agent Plus](https://github.com/byebyebryan/rofi-agent-plus) | Each picker owns its launch contract, action behavior, and implementation. |
| [Agent Observer](https://github.com/byebyebryan/agent-observer), [Mesh Plus](https://github.com/byebyebryan/mesh-plus) | Runtime observation and peer/transport contracts; their state and route selection stay separate. |
| [Niri](https://github.com/niri-wm/niri), [Kanshi](https://github.com/emersion/kanshi), [ESP32-RLCD](https://github.com/byebyebryan/esp32-rlcd), [349d](https://github.com/byebyebryan/esp32-349) | Compositor/output-profile behavior and independent display/notification-mirror firmware. |
| [Fleet Plus](https://dev.byebyebryan.com/fleet-plus/) | Cross-project presentation and guidance for the optional tools. |

The external tools and displays are optional integrations. The browser,
terminal, and basic desktop remain understandable without them. The source map
shows which public downloads come from shared modules and which decisions stay
in private chezmoi or the independent projects.

## A short resource observation

A controlled 4-vCPU/8-GiB Arch guest observation measured the selected core
session processes at about 0.10% of one vCPU while quiet, 0.45% with SwayNC open,
and 0.12% after it closed. Two launcher cycles left no Rofi process in final
quiet. The [dated resource receipt](planning/resource-and-showcase-receipt.md#measured-scope)
defines the process cohort, readable-memory coverage and sampling limits.
These are short guest observations; applications and the collector are
attributed separately, and physical laptop/GPU/battery behavior is outside them.

## A shared visual identity

The [design guide](design.md) presents Neutral Slate's warm UI surfaces,
Clear Blue focus, the black workspace refinement, Noto Sans UI, Meslo terminal
type and the surface gallery. It links to the
generated [identity export](../data/identity.json) and
[Kitty appearance fragment](../examples/kitty/neutral-slate.conf).
[Kitty and Zsh](recipes/terminal.md) are part of the reference workflow. The
design specimen and machine adoption remain separate states.
