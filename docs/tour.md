# A day between two halves

My desktop follows what I'm doing: interacting with the web, building in a
terminal, or returning to work somewhere else. These are the small routines
that shaped it.

## Native reference demo

The reference demonstration uses a staged Arch guest and public sample content.
The overview combines the full browser/files and information clips with a
12-second excerpt from the earlier terminal pilot. Each clip identifies its
source scene and any reused footage. These are staged VM demonstrations, not
recordings of my daily desktop or evidence of a full-installation qualification.

<!-- niri-plus:demo-overview -->
Watch the staged Arch desktop move between browser and terminal work, with
information and clipboard tools available on demand.
<!-- /niri-plus:demo-overview -->

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

**Try the pieces:** start with [the base desktop](setup-agent.md#3-install-the-first-session-packages)
and its portal and file-dialog checks.

<!-- niri-plus:demo-browser-files -->
The staged guest downloads a public Markdown sample and SVG, opens them through
Dolphin with the guest's Neovim default and Gwenview, then selects the original
Markdown file in Chrome's native GTK upload chooser. The sample page reports
the received byte count and hash.
<!-- /niri-plus:demo-browser-files -->

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

<!-- niri-plus:demo-terminal -->
The reused pilot clip shows a local Chrome sample page beside Kitty and Zsh,
including a guest-guarded project check and keyboard navigation. It is the
terminal/browser scene, not the later full desktop demonstration.
<!-- /niri-plus:demo-terminal -->

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

<!-- niri-plus:demo-information -->
The staged guest shows SwayNC's actual CPU, RAM and Ethernet readings; absent
GPU, battery and Bluetooth cards hide on this VM. The Rofi clipboard picker
restores exact public sample text and image, deletes one selected item, keeps
history on Cancel, and clears it only after confirmation.
<!-- /niri-plus:demo-information -->

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

The interactive walkthrough and identity gallery remain illustrations. The
Agent Plus image is a real Rofi rendering with sample data, and the SwayNC image
is an isolated native rendering with its fixture values labelled separately.
The recordings show actual software in a staged Arch guest with public sample
content. The terminal clip is byte-identical to the accepted earlier pilot; it
is not a fresh scene from the later demonstration. Whole-monitor browser
sharing is not shown in any clip. It passed separately with an explicit WLR
compatibility package in this VM only; the core assembler and fleet defaults do
not select that package. Read the [guest demonstration receipt](planning/desktop-demonstration-receipt.md)
and its [WLR compatibility note](../tools/vm/desktop/wlr-compat/README.md).
The [media record](../assets/provenance.json) lists versions, measurements,
source and output hashes, fixture labels, processing and separate review status.

Human playback and aesthetic review remain pending and separate from the
automated browser checks.
