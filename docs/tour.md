# A day between two halves

My desktop follows what I'm doing: interacting with the web, building in a
terminal, or returning to work somewhere else. These are the small routines
that shaped it.

## Native reference demo

The current overview follows browser and file work, a native terminal, and
information and controls on demand. It runs in the staged Arch reference with
the pure-black workspace, warm Neutral Slate surfaces and Balanced+ terminal.
The videos use native **1280×800 at scale 1**, with the full desktop in view.
The content is public sample material; device readings come from the guest.

<!-- niri-plus:demo-desktop-800 -->
Move between Chrome and Kitty, open a downloaded file, choose one to send,
and use the panel, clipboard and Audio before returning to work.
<!-- /niri-plus:demo-desktop-800 -->

The [earlier recordings](tour-earlier.md) retain their original inputs, capture
dates and resolution, including the previous 1080p overview and controls.

## Explore the workflow

<!-- niri-plus:workbench -->
Explore real captured moments: browser and files, terminal work, the system
panel, and Audio controls. Each 1280×800 capture keeps the full desktop visible.
Open the original frame or watch the scene in the native recording.
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

The [earlier browser/files recording](tour-earlier.md#browser-and-files) shows
the full download, default-application and native file-chooser sequence.

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

The [earlier terminal recording](tour-earlier.md#terminal-and-browser) shows
the original guest sample check and column navigation.

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

The [earlier information/clipboard recording](tour-earlier.md#information-and-clipboard)
shows the full text/image restore, Delete, Cancel and confirmed Clear sequence.

**Try the pieces:** [notifications](recipes/notifications.md) and
[clipboard history](recipes/clipboard.md).

## Device controls

Network, Audio and Bluetooth use Rofi's search, named actions and separate
device state. The focused recording shows actual Ethernet and virtual audio
beside Chrome and Kitty. Wi-Fi and Bluetooth hardware are absent in the guest.

<!-- niri-plus:demo-controls-800 -->
Open Audio, inspect device details, adjust and restore its volume/mute state,
then inspect the connected Ethernet link in Network.
<!-- /niri-plus:demo-controls-800 -->

## Work that can move between machines

A laptop is an entry point to work on other hosts. `Mod+S` opens SSH Plus and
`Mod+G` opens Tmux Plus. Their filters and named actions keep access close to
the keyboard. Agent Plus uses `Mod+A` to reach native agent windows.

Remote access is configured explicitly. Installing a picker does not grant
access to another computer or require the entire observation stack.

**Try the pieces:** [Fleet Plus](https://dev.byebyebryan.com/fleet-plus/start/)
explains the independently useful projects and their prerequisites.

## About the demonstrations

The workflow explorer uses independent, unedited native 800p stills captured
before the new recordings; its watch links open the related scenes.
The identity gallery remains illustrative. The Agent Plus image is a real Rofi rendering with sample data, and the SwayNC image
is an isolated native rendering with its fixture values labelled separately.
The recordings show actual software in staged Arch guests with public sample
content. The current videos and stills use native 1280×800 capture at scale 1, keeping
the full desktop visible. The [six earlier videos](tour-earlier.md) retain their
original 1920×1080 frames, source inputs and bytes. The earlier terminal clip reuses
its accepted pilot. Whole-monitor browser sharing is not shown in any clip.
Sharing is checked separately and recorded
in the relevant receipt; both reference guests needed the conditional
[WLR compatibility package](../tools/vm/desktop/wlr-compat/README.md).
Read the [800p capture receipt](planning/desktop-800-receipt.md),
the [previous showcase receipt](planning/resource-and-showcase-receipt.md),
the [reference and controls receipt](planning/black-workspace-receipt.md)
or the [earlier demonstration receipt](planning/desktop-demonstration-receipt.md).
The [media record](../assets/provenance.json) lists versions, measurements,
source and output hashes, fixture labels, processing and separate review status.

Human playback and aesthetic review remain pending and separate from the
automated browser checks.
