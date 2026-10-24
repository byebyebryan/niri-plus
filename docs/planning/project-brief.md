# Niri Plus project brief

Captured on 2026-10-24.

Niri Plus will record and present Bryan's daily Linux desktop: a Niri setup
refined around browser use, terminal work, and coding agents. Its purpose is to
show the experience, explain how the pieces fit together, and help others adopt
the parts that suit their work.

The [personal story](../story.md) presents the workflow and motivations in Bryan's
voice. Use it as the starting narrative for the site and future presentation
copy.

The name and personal scope are settled. The site structure, example packaging,
and first edition below are proposals to refine before implementation.

## Project intent

- Repository name: `niri-plus`; display name: **Niri Plus**.
- Bring the desktop's story, configuration references, and custom integrations
  into one understandable place.
- Give demonstrations, presentation, and instruction substantial attention.
- Keep the maintenance effort appropriate for a personal setup. Building and
  supporting a Linux distribution is outside the intended scope.
- Explain a setup fitted closely to its owner's work, including the reasons for
  its choices and the compromises another person might make differently.

## How Bryan uses the desktop

The desktop serves two main halves of daily computer use: Chrome for interactive
work on the internet, and terminals for tinkering, building, and working with
agents. Both support personal activities and work.

### Chrome and graphical interaction

Chrome is the more interactive, mouse-heavy side of the workflow. It covers
browsing websites, consuming information, making transactions, and using web
applications for both personal and work tasks.

This browser activity continues to drive the need for a comfortable graphical
desktop and ordinary file-management tools. Opening a downloaded file or picking
one to send is naturally a graphical interaction. Dolphin and file dialogs have
a useful role in that workflow even though routine system management usually
happens in a terminal or through an agent.

### Terminals and building

Bryan enjoys terminal life and spends much of his remaining computer time
tinkering, coding, and building things there. The appeal includes:

- Keyboard control. Mechanical keyboards are a hobby, and keyboard interaction
  is a valued part of using the computer.
- Explicit, repeatable operations, with a similar appeal to infrastructure as
  code.
- Low resource overhead.
- Flexibility across hosts, including moving between laptops, servers, and
  workstations and working remotely.

### Agents and system management

AI and coding agents are central to how Bryan works. Terminal commands,
inspectable configuration, and text-based operations make it easier for an agent
to help investigate something, make a change, or take over a task.

This is a major reason for moving away from DMS. A visual settings interface
previously offered an appealing way to configure the system. Today, asking an
agent to investigate or adjust something is often preferable to searching
through graphical settings manually. Small, understandable services and explicit
configuration fit that preference.

The desktop still needs to make browser interaction and routine graphical file
tasks comfortable. The agent workflow explains the preferred way to operate and
maintain the system.

## How the setup arrived here

KDE was Bryan's desktop for years and later remained available as a backup after
the move to Niri. That backup went unused and has now been removed. Niri has
become the desktop Bryan wants to use daily.

The surrounding setup evolved through DMS and then toward a smaller collection
of selected services and custom integrations. The SwayNC fork and Rofi Plus
tools are important parts of that work. The current arrangement reflects
ongoing refinement for actual use.

## Proposed presentation approach

Lead with how the desktop supports these two halves of work. Introduce tools
through a task and then explain their implementation and setup.

For each important workflow, connect four things: a real demonstration, the
reason for the design, how the integration works, and instructions for adopting
it. The browser and graphical file workflow should appear alongside terminal and
agent work in the overview and tour.

Explain the integration details that a screenshot cannot convey: notification
focus, service lifetimes, panel refresh behavior, image clipboard preservation,
and the ability to reload one service without disturbing another. Show the
parts of those details that affect normal use, with deeper explanations linked
from the demonstration.

## Proposed site structure

| Area | Content |
| --- | --- |
| Overview | Introduce the personal workflow, show a real desktop recording, and provide clear paths to the tour and setup guide. |
| Desktop tour | Demonstrate browser and file interaction, window navigation, terminals and agents, launchers, notifications, clipboard, and remote work. |
| How it works | Map components and service ownership; explain design choices and the custom integrations. |
| Set it up | Provide prerequisites, an ordered assembly guide, focused recipes, verification steps, and troubleshooting. |
| Reference | Document key bindings, relevant package groups, component links, configuration examples, and a dated working combination. |
| Evolution | Explain the KDE, DMS, and current Niri periods, including choices that were revised and the reasons for doing so. |

Use an expressive overview and readable deeper pages. Guide content should remain
useful as ordinary repository documentation as well as on the website.

## Proposed component coverage

| Part of the experience | Components and explanation |
| --- | --- |
| Browser and files | Chrome, Dolphin, downloads, file selection, and the desktop integration that makes those tasks comfortable. |
| Windows and navigation | Niri layout, columns, sizing, workspaces, overview, key bindings, and multiple monitors. |
| Terminals and agents | Kitty, native coding-agent TUIs, and the way terminal operations support both manual and agent-assisted work. |
| Launching and returning | Rofi application launching, SSH Plus, Tmux Plus, and Agent Plus as used from the desktop. |
| Notifications and system information | The SwayNC fork, notification actions and focus, history, panel cards, and hardware-dependent behavior. |
| Clipboard and quick feedback | Cliphist, the Rofi clipboard picker, screenshots, volume, brightness, and mute feedback. |
| Session and power | Gtklock, swayidle, authorization, display power, battery handling, and session-scoped services. |
| Desktop integration | Kanshi, GTK and Qt appearance, portals and file dialogs, and input methods. |
| Optional extensions | Remote-host integrations and external notification or dashboard displays, with links to their owners. |

Cover the components actually used. Hardware-dependent features and host-specific
choices should be identified where they appear.

## Proposed repository contents and ownership

Niri Plus would own:

- Site source and the guide content used to build it.
- Demo recordings, screenshots, and capture notes identifying what they show.
- Focused public configuration examples with their dependencies and helpers.
- A dated record of relevant component versions, source revisions, environment,
  and known limitations.
- Small tools for building the site, checking links, and checking examples.

The README should provide a compact entry point, a prominent site link once
published, repository layout, and maintenance and publishing instructions.

Existing responsibilities remain separate:

| Owner | Responsibility |
| --- | --- |
| Chezmoi | Authoritative configuration and scoped deployment for Bryan's machines. |
| Component repositories | Implementation, releases, contracts, and detailed component installation and reference documentation. |
| Fleet Plus | Shared presentation and guidance for the SSH, Tmux, Agent, Observer, and Mesh ecosystem. |
| Niri Plus | The daily desktop experience, design explanation, and recipes for assembling its integrations. |

Show the Rofi tools in the context of desktop use and link to Fleet Plus and
component documentation for depth. Public examples derived from chezmoi should
identify their source revision and adaptations. The exact mechanism for keeping
those examples current remains open.

## Proposed instruction scope

Start with an experienced Linux user who is new to this particular setup, and
target Arch or EndeavourOS first.

Provide two complementary ways to use the material: add one feature to an
existing Niri session, or assemble the documented desktop in stages. For each
stage, explain prerequisites, the files involved, how to verify the result, and
how to undo the change.

Include the browser, file manager, portals, authorization, and appearance in the
desktop assembly guide. Make power and locking policies explicit choices.
Document personal conventions separately from necessary integration steps.

Begin with inspectable instructions and examples. A general installer,
cross-distribution support, and a new configuration deployment system are not
part of the proposed first edition.

## Proposed first edition and demonstrations

Start with one desktop overview recording, four focused demonstrations, the
component map, and a guide through the basic desktop. The evolution page can
begin with a concise account of the main transitions.

The four focused demonstrations could cover:

1. **Browser and files:** download and open a sample file, then select a file to
   send through a browser interface.
2. **Building in terminals:** navigate between terminal work and a coding agent,
   including a representative investigation or configuration task.
3. **Information and small actions:** use the panel, return through a
   notification, and retrieve clipboard content.
4. **Work across hosts:** use SSH, Tmux, or Agent Plus to reach or return to work
   on another host.

The overview should establish Niri navigation and show how the browser and
terminal sides fit together. Use visible key hints and explanations where they
help a visitor understand an action. Real session recordings should carry the
experience; diagrams can explain relationships and service behavior.

Fresh media of the current desktop is needed. Existing component documentation
provides useful background, while the desktop assembly narrative and public
examples still need to be developed.

## Open decisions

- Exact page outlines, visual direction, and demo capture list.
- How much configuration to provide as portable examples, and how to keep it
  aligned with chezmoi without creating competing sources of truth.
- The precise starting environment and checks required before calling the full
  setup guide reproducible.
- Which remote-host and display integrations belong in the first edition.
- Site framework, hosting, and URL. A static site and GitHub Pages are candidates.
- The maintenance routine for refreshing media, examples, and the working
  configuration record as the desktop evolves.

## Existing source map

- Desktop configuration and deployment:
  `~/.local/share/chezmoi`, especially `docs/desktop-deployment.md`,
  `.chezmoidata/desktop.yaml`, and the Niri, SwayNC, Rofi, and systemd inputs.
- SwayNC fork: `~/code/SwayNotificationCenter`.
- Rofi components: `~/code/rofi-ssh-plus`, `~/code/rofi-tmux-plus`, and
  `~/code/rofi-agent-plus`.
- Ecosystem presentation: `~/code/fleet-plus` and
  [the Fleet Plus site](https://dev.byebyebryan.com/fleet-plus/).
- General portfolio: `~/code/devlog` and
  [dev.byebyebryan.com](https://dev.byebyebryan.com/).
