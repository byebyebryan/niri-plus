# Niri Plus desktop design pass

Current selection: **Neutral Slate**. The
[Neutral Slate implementation and site plan](neutral-slate-pass.md) supersedes
the open-decision and candidate-exploration steps below. The retained text
records the original planning phase.

Planning draft, 2026-10-24. This pass defines the desktop experience and its
identity before configuration changes. The [desktop review](desktop-review.md)
is the current baseline; the [personal story](../story.md) explains the work the
desktop needs to serve.

The goal loop has produced a [complete design review package](../design/README.md)
with a 22-capability map, three visual candidates, native reference samples,
recommended identity, implementation map, and verification/capture plan.
The original recommendation was Graphite Blue. Bryan subsequently reviewed the
Slate Blue blend and selected Neutral Slate. Follow the current pass for the
selected identity, visual site presentation, and implementation sequence.

## Direction already established

Niri Plus is an opinionated personal desktop experience built on an existing
Linux distribution. It should account for common daily desktop use, with
particular attention to browsing, development, terminals, agents, and remote
work. The project owns an understandable experience, public reference material,
and presentation of how the pieces belong together.

Treat the desktop as a whole: entering the session, using applications and
files, seeing system state, taking common actions, and leaving or resuming work.
An independently implemented utility can be a first-class part of that whole.

The name is settled. Building an operating system, adding a package manager,
maintaining an arbitrary-distribution installer, and supporting specialized
workstation uses such as printing are outside this pass. Desk displays and
other specialized integrations remain optional extensions.

The current Niri setup is a working foundation. The review will identify
existing choices to retain, gaps to fill, and bounded improvements. Existing
applications are the baseline, not an assumed roster that must be replaced.

## Decisions still open

The following are starting proposals, not adopted design choices:

| Decision | Starting proposal | What will settle it |
| --- | --- | --- |
| Visual exploration | Develop the current charcoal/blue direction; compare alternatives at a bounded scale. | Bryan's preferred exploration range and side-by-side specimens. |
| Reach into development tools | Include terminal framing, background, typography, selection, and common chrome; permit intentional syntax-palette differences. | Decision about desktop-only, framing, or full editor/palette alignment. |
| Theme variants | Establish one coherent primary theme first. | Chosen visual direction and desired light/dark support. |
| Neutral login and lock screens | Consider retaining the shared neutral palette as an intentional variation. | Compare the greeter and locker alongside the rest of each candidate. |
| Shared data ownership | Niri Plus defines the public identity; chezmoi remains responsible for machine deployment. | Choose one canonical source and a practical consumption/export path before implementation. |

## The capability map

For every row, record the current component, visible state, path to take an
action, configuration owner, hardware variation, and a representative check.
Mark gaps explicitly. A status display does not by itself establish an action
path, and a command can be an intentional interface.

| Area | Daily outcomes to cover | Current components to evaluate |
| --- | --- | --- |
| Login and session | Log in, choose Niri, enter a usable session, lock/unlock, log out, suspend, restart, and shut down. | SDDM, Niri session, Gtklock, user services, logind. |
| Windows and displays | Navigate, resize, find work, use multiple monitors, dock/undock, and retain readable scale. | Niri rules and bindings, Kanshi, output profiles. |
| Browser and files | Browse, download/open files, pick files to send, view PDFs/images/media, handle archives, and use common file operations. | Chrome, Dolphin, Gwenview, Ark, mpv, MIME defaults, portals; removable-media behavior to check. |
| Terminal and development | Open/return to terminals and agents, maintain useful input and notifications, and reach work on another host. | Kitty, native agent TUIs, shell/tmux/editor interfaces, Rofi Plus, SSH. |
| Connectivity | See Wi-Fi/Ethernet and Bluetooth state; reach a clear path for connecting, selecting a network, pairing, and disconnecting devices. | SwayNC status cards, NetworkManager, BlueZ, existing command/native utility interfaces. |
| Audio and display controls | Change volume/brightness, mute output/microphone, see feedback, and reach output/input selection when needed. | Hardware bindings, notify-volume, notify-brightness, WirePlumber, applicable SwayNC controls. |
| Clipboard, capture, and alerts | Retrieve text/images, manage history, take screenshots, respond to notifications, and share the screen in browser calls. | Cliphist, Rofi picker, Niri capture, SwayNC, portals. |
| Power and availability | See battery/charging information, understand AC/battery behavior, preserve inhibition, and recover from display-off/suspend. | SwayNC cards, UPower, swayidle, desktop-power, captured host policy. |
| Input and authorization | Type normally, switch input methods, read candidate windows, authorize an operation, and use existing secrets integration. | Keyboard/input settings, Fcitx5, polkit agent, PAM/KWallet. |

Advanced settings can continue to use commands and agents. We will decide which
frequent actions deserve a shortcut, picker, or native graphical entry point.
This does not imply adding a replacement all-in-one settings application.

## Design principles to evaluate

Use the personal workflow as the test for each principle:

- Make browser interaction and keyboard work equally comfortable.
- Keep repeated actions predictable, with visible focus and clear cancellation.
- Offer information when needed, with restrained transient feedback.
- Make configuration understandable and repeatable for both the owner and
  agents working on the system.
- Keep the desktop readable on a laptop as well as an ultrawide display.
- Give missing hardware, unavailable readings, and errors clear representations.
- Use shared visual cues while allowing native toolkit controls and appropriate
  typography for different roles.
- Keep maintenance proportionate to a personal setup.

## Sequence and deliverables

### 1 Establish the desktop brief

Complete the capability map and distinguish the personal reference setup from
portable adaptations. Identify common paths that are merely undocumented and
those that actually need an implementation decision.

Record the working contexts: Starship's ultrawide, laptop internal displays and
fractional scale, and supported home/work external-display arrangements. Keep
host-specific output and power choices separate from shared identity.

**Result:** a short desktop brief, a complete capability map, and an explicit
list of open functional decisions. Resolve scope before adding features.

### 2 Compare complete visual directions

Prepare two or three bounded candidates at the exploration range Bryan chooses.
Each candidate combines palette, typography, geometry, and density. Use the
same representative content and states for each so the comparison is useful.

Each comparison board should show:

- SDDM and Gtklock, including password, focus, and error states.
- A browser next to a terminal, plus Dolphin and a file chooser.
- The application launcher and one Rofi Plus picker with filter, selected row,
  named actions, and an empty or error state.
- The notification panel, a normal notification, a critical alert, and volume
  and brightness feedback.
- Input-method text and candidate presentation where relevant.

Use realistic normal-length and long labels, English/CJK samples, symbols,
unknown values, and hardware-present/absent states. Compare normal logical size
and fractional-scale presentation. Evaluate perceived text size and density;
the different toolkits do not express every size in the same units.

Use local comparison boards and isolated native previews where supported.
Label mockups as mockups. The boards do not modify or establish acceptance of
the running desktop. A candidate with poor native-toolkit fit should expose
that limitation before it is chosen.

**Result:** comparable visual specimens and a decision record describing the
selected direction, intentional exceptions, and the reasons for the choice.

### 3 Specify the chosen identity and interactions

Write down exact values and behavior after choosing a direction:

| Part | Decisions to specify |
| --- | --- |
| Palette | Base/raised surfaces, primary/secondary/disabled text, borders, accent, focus, selection, warning, error, and success roles. |
| Typography | UI and monospace families, fallbacks and glyph coverage, body/title/secondary sizes, weights, and numerical alignment. |
| Geometry | Spacing scale, control height, padding, border widths, corners, panel/dialog sizing, and window decoration policy. |
| Surfaces and effects | Opacity, shadows, blur, and the desktop background or wallpaper approach. |
| Icons and cursors | Families, sizes, fallback behavior, and ownership across compositor, applications, and greeter. |
| Feedback | Transient versus retained messages, urgency, replacement behavior, progress, and empty/unavailable states. |
| Interaction | Launch/navigation conventions, activation/cancel behavior, focus indication, filtering, action selection, and mouse equivalents. |
| Motion | Appropriate feedback/transitions, readability, reduced-motion behavior where supported, and resource-cost constraints. |
| Site identity | Shared colors, typography, wordmark treatment, and presentation language, adapted for reading and instruction. |

Preserve the Rofi Plus action-cycle contract and native widget behavior. For
example, Tab selects a named action in a Rofi Plus picker, while Tab traverses
controls in the notification panel. Coherence means these contexts are clear;
it does not require assigning every widget the same keys.

Address actual GTK3, GTK4/Libadwaita, Qt5, Qt6, and application capabilities.
Identify supported settings, small owned styles, and deliberate native
differences. Do not assume a single stylesheet or theme package controls them.

**Result:** a compact identity and interaction specification with explicit
component exceptions. Font names and semantic palette values are decisions,
not placeholders left for an implementation agent to invent.

### 4 Map the specification to implementation

For every component, classify the change as retain/document, configure, fix an
integration gap, or evaluate a replacement. Record the source owner, target
files, dependencies, reload/session boundary, and verification required.

Choose a single canonical home for reusable identity values. Decide how the
public reference and private deployment consume the same decisions without
separately maintained palettes. Start with the simplest practical data/config
arrangement; add generation only where it meaningfully reduces drift.

Niri Plus owns the experience specification and public reference. Chezmoi owns
host deployment. Component repositories retain implementation and releases;
Fleet Plus retains its ecosystem guidance. Root-owned SDDM configuration and
user-session settings require different delivery and recovery procedures.

Keep existing power, automatic-lock, lid, wallet/PAM, native provider, and fleet
transport choices intact unless a separately identified functional change is
selected. Hardware-card behavior and the Starship volume trial retain their
existing scope while the design is evaluated.

**Result:** a bounded implementation backlog, in dependency order, with the
smallest source changes, per-host verification, and rollback boundaries.

### 5 Prepare the review and presentation plan

Use the following complete journey as the verification and capture sequence:

1. Login and enter Niri; establish outputs and scale.
2. Browse, download/open a file, choose a file to send, and exercise screen
   sharing.
3. Work in terminals and agents, then reach or return to work on another host.
4. Use applications, clipboard, SSH/Tmux/Agent pickers, notifications, system
   status, hardware controls, input methods, and authorization.
5. Lock/unlock, change power source, dock/undock, and resume through the normal
   usage paths appropriate to each host.

Prepare a matrix for shared behavior, host variation, and expected outcomes.
Distinguish source/static checks, isolated native rendering, actual session
behavior, and physical laptop/display acceptance. A mockup or running service
does not complete the later checks.

Plan disruptive GUI trials on unattended Snap. Starship's daily session and
Carbon's laptop/scaling behavior can be reviewed in appropriate normal-use
windows. Do not force logout, locking, display power, suspend, or a greeter
restart while preparing the design.

The eventual site update should explain the complete component map, the chosen
appearance and its rationale, actual daily workflows, and how to assemble the
parts. Show the actual setup and label portable alternatives at their point of
use. Refresh native captures and recordings only after the relevant desktop
changes are accepted.

**Result:** a concrete verification matrix, capture list, and site-content map.

## Completion boundary

The design pass is ready to hand to implementation when:

- Every core daily task has an owner and a defined interaction path, with
  implementation gaps scoped and optional deferrals identified.
- One chosen visual direction is recorded across the representative surfaces;
  native exceptions are deliberate and explained.
- Palette, font roles, geometry, icons/cursors, and interactions are specific
  enough to implement without inventing another design.
- Hardware differences and scaling contexts have planned checks, with evidence
  levels kept distinct.
- Canonical identity ownership and the public/private consumption path are
  settled.
- The implementation backlog and presentation plan are concrete and bounded.

Open core decisions prevent declaring the design settled. The outcome of this
planning step is documentation; it does not select a final palette, deploy a
theme, change components, or republish the current site. Implementation follows
the selected design as a separate phase.

## First decisions for the next step

Set the exploration range and the reach into development-tool appearance. Then
complete the capability map and prepare comparable visual directions. The
existing audit supplies the source baseline; it is not the chosen identity.
