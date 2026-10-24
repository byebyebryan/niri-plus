# Small pieces with clear jobs

Niri owns the windows and navigation. A few selected applications and session
services fill in the rest of the desktop. The arrangement reflects how I work
and how I prefer to maintain it.

<!-- niri-plus:architecture -->
Chrome and Dolphin serve browser and file interaction. Kitty and native coding
agents serve terminal work. Niri arranges their windows. Rofi provides launchers;
SwayNC provides notifications and system information. Session services handle
clipboard collection, idle policy, manual locking, authorization, and battery
monitoring. Chezmoi owns my configuration and deployment.
<!-- /niri-plus:architecture -->

## The desktop layer

| Job | Current choice | Why it belongs |
| --- | --- | --- |
| Windows and navigation | Niri | Scrolling columns, workspaces, overview, and keyboard navigation. |
| Browser and files | Chrome and Dolphin | Interactive web work, downloads, and graphical file operations. |
| Terminals | Kitty | Terminal work and dedicated native coding-agent windows. |
| Applications and pickers | Rofi and Rofi Plus | Find applications, hosts, tmux sessions, agent windows, and clipboard items. |
| Notifications and information | SwayNC fork | Notification history and a panel of system information, available on demand. |
| Clipboard | Cliphist and wl-clipboard | Collect text and images; a Rofi picker restores the original item. |
| Locking | Gtklock | Manual locks through an independent user service. |
| Idle and power | swayidle and desktop-power | Explicit display, suspend, and battery policy per machine. |
| Authorization | polkit-kde-agent | Graphical authorization prompts when an application needs them. |
| Outputs and integration | Kanshi, portals, GTK/Qt configuration, Fcitx5 | Monitor profiles, file dialogs, appearance, and input methods. |

## Keep changes independent

The user services start with the Niri session and stop with its graphical
session. Idle policy, notification reloads, and clipboard configuration have
separate lifetimes. Manual locking has its own service, so an idle-policy reload
does not stop an active locker.

The panel only refreshes its metrics and wireless subscriptions while open.
NVIDIA GPU reads wait for cached runtime activity. Closing it cancels the outstanding
work. This behavior is part of the fork, beyond what a CSS theme can express.

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
| [Niri Plus](https://github.com/byebyebryan/niri-plus) | This desktop story, demonstrations, assembly recipes, and public examples. |
| Private chezmoi source | My managed configuration and deployment selections. The portable examples are included in Niri Plus. |
| [SwayNC fork](https://github.com/byebyebryan/SwayNotificationCenter) | The panel implementation, activation behavior, and fork packaging. |
| [Fleet Plus](https://dev.byebyebryan.com/fleet-plus/) | Shared presentation and cross-project guidance for the SSH, Tmux, Agent, Observer, and Mesh tools. |
| Individual component repositories | Their implementations, releases, detailed installation guides, and public contracts. |

The fleet tools and external displays are optional integrations. The browser,
terminal, and basic desktop remain understandable without them.
