# A day between two halves

My desktop follows what I'm doing: interacting with the web, building in a
terminal, or returning to work somewhere else. These are the small routines
that shaped it.

## Explore the workflow

<!-- niri-plus:workbench -->
The illustrated walkthrough has four scenes: browser and files, terminals and
agents, notifications and clipboard, and work across hosts. Each scene explains
the action, its keyboard entry point, and the components involved. It uses
fictional content to show the workflow; it is not a recording of a live session.
<!-- /niri-plus:workbench -->

## Browser and files

Chrome handles browsing, reading, transactions, and web applications for both
work and personal life. Dolphin and graphical file pickers belong here too:
opening a download or choosing a file to send should feel ordinary.

Niri gives the browser room, then lets me return to a terminal without navigating
a stack of overlapping windows. My preference for terminal operations still
leaves plenty of useful work for the mouse.

**Try the pieces:** start with [the base desktop](setup.md#start-with-a-working-niri-session)
and its portal and file-dialog checks.

## Terminals and agents

Kitty is the terminal. Native coding agents stay responsible for their own
conversations and authentication. Agent Plus provides an entry point into
dedicated TUI windows: open one, return to one, or request another window.

![Actual Agent Plus Rofi rendering with fictional local and remote environments and sample window titles](../assets/agent-plus.png)

*Actual Rofi rendering with sample environments and windows and a preview theme.
No live sessions are shown. The installed Rofi theme controls its appearance.*

I like commands and configuration that I can inspect, repeat, and ask an agent
to work with. That same preference connects coding, troubleshooting, and system
management.

**Try the pieces:** [Agent Plus](https://dev.byebyebryan.com/fleet-plus/projects/agent-plus/)
and the [launcher reference](reference.md#launchers).

## Information when I want it

There is no permanent bar. `Mod+N` opens SwayNC for notifications and system
information. The custom panel brings CPU, RAM, active NVIDIA GPU information, network,
connected Bluetooth devices, and battery information into one place.

<!-- niri-plus:panel -->
[View the native panel rendering](../assets/panel.png), captured in an isolated
test session using the fork's default theme. Wireless and GPU values are sample
data; CPU/RAM readings are local. There is no battery card on this hardware.
<!-- /niri-plus:panel -->

The details matter: metrics refresh while the panel is open, missing hardware
cards hide, and battery estimates follow the reported charge limit. Volume and
brightness keys show brief replaceable feedback. Clipboard history is a separate
Rofi picker on `Mod+Y`, with text and images kept in their original form.

**Try the pieces:** [notifications](recipes/notifications.md) and
[clipboard history](recipes/clipboard.md).

## Work that can move between machines

A laptop is an entry point to work on other hosts. `Mod+S` opens SSH Plus and
`Mod+G` opens Tmux Plus. Their filters and named actions keep access close to
the keyboard. Agent Plus uses `Mod+A` to reach native agent windows.

Remote access is configured explicitly. Installing a picker does not grant
access to another computer or require the entire observation stack.

**Try the pieces:** [Fleet Plus](https://dev.byebyebryan.com/fleet-plus/start/)
explains the independently useful projects and their prerequisites.

## About the demonstrations

The interactive walkthrough is an illustration based on the documented desktop
bindings. The Agent Plus image comes from the real Rofi renderer with sample
data. Neither shows private browser activity or live agent conversations.

The [media record](../assets/provenance.json) identifies the sources. A full
recording of the daily desktop is a future addition; the current edition uses
the walkthrough, source-backed recipes, and the application rendering above.
