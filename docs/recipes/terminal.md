# At home in the terminal

Kitty and Zsh support the keyboard driven work that moves between a laptop,
workstation, and remote hosts. This guide covers the Neutral Slate color
fragment and a portable shell core that you can install beside your existing
configuration.

The [desktop and terminal contrast study](../design/contrast.md) previews a
separate black terminal palette with clearer normal/bright pairs and moderate
color saturation. It is a proposal;
the fragment in this guide retains the currently selected appearance.

## Kitty: the everyday surface

My terminal uses MesloLGS Nerd Font at 11pt, no window decorations, explicit
Nerd Font symbol mappings, and Kitty's cursor trail. Pasted dangerous control
codes are replaced. Shift+Enter sends the existing CSI-u sequence for legacy
terminal modes, while applications using Kitty's keyboard protocol keep their
native behavior.

The generated [Neutral Slate Kitty fragment](../../examples/kitty/neutral-slate.conf)
contains only appearance options: a `#202326` background, warm off-white text,
a clear blue cursor, blue selection, and a coordinated 16-color ANSI table.
It does not change input, paste handling, glyph mappings, cursor trail, windows,
or shell behavior. The fragment is selected design material; its presence here
does not claim native deployment.

To inspect it in a separate Kitty window, layer it after your existing config:

```sh
kitty --config ~/.config/kitty/kitty.conf --config /path/to/neutral-slate.conf
```

The [Design page's palette](../design.md#palette) lists every ANSI slot and
role. Red maps to errors, green to success, yellow to warnings, blue to the
accent, violet and cyan are supplemental, and neutral slots map to canvas,
muted, secondary, and main text. Entries 16–255 retain Kitty's defaults;
applications' explicit RGB colors remain separately owned. Check default,
dim, bold, selected, ANSI, and full-screen tool output before adopting the
fragment.

## Zsh: portable core

The selected shell profile retains the working prompt shape and status, with
personal host setup and credentials removed.

| Part | Behavior |
| --- | --- |
| Location and Git | Host and current directory, branch and concise clean/modified/conflict state. |
| Prompt | Lean two-line Powerlevel10k prompt with transient history, Emacs keys, and distinct success/error prompt marks. |
| Right side | Time, CPU frequency/utilization, memory, Bluetooth, network, and battery when available. Wireless and battery probes cache for five seconds. |
| History and completion | Shared history in the user's XDG state directory, duplicate reduction, command verification, completion menu, and case-insensitive matching. |
| Editing | Up/Down substring history search, inline autosuggestions, and syntax highlighting loaded after widget integrations. |
| Navigation | Zoxide and fzf initialization when their commands are installed. |
| Agent tool shell | A recognized tool environment gets a hostname-only prompt and returns before history, plugins, custom probes, and the refresh watcher. Force the simple or full prompt with `ZSH_FORCE_SIMPLE_PROMPT` or `ZSH_FORCE_FULL_PROMPT`. |

The portable source files are [Zsh startup core](../../examples/terminal/zshrc),
[Powerlevel10k configuration](../../examples/terminal/p10k.zsh), and [custom
status segments](../../examples/terminal/p10k-custom-segments.zsh). The latter
use only Linux proc/sys interfaces and optional system commands; absent devices
hide their segments. The watcher refreshes only while ZLE waits for input and
closes its file descriptor on line completion or shell exit.

### Requirements and install

Use Zsh, Python 3.11 or later, a working TLS connection to GitHub codeload, and
MesloLGS Nerd Font installed in Kitty. The [fetcher](../../examples/terminal/fetch.py)
installs the four pinned upstream trees beside the portable configuration.
The file [pins and archive hashes](../../examples/terminal/pins.json) records
the immutable commit and SHA-256 for each tarball; [third-party notices](../../examples/terminal/THIRD_PARTY_NOTICES.md)
records license and attribution details. The selected versions follow the
existing public checkouts rather than a floating branch.

From a Niri Plus checkout, choose a new directory below your home directory:

```sh
python3 examples/terminal/fetch.py "$HOME/.local/share/niri-plus/zsh-neutral-slate"
```

The fetcher verifies HTTPS archives and SHA-256 before extraction. It refuses
an existing or symlink destination, installs only into a newly created leaf,
and does not edit `.zshrc`, `.zshenv`, `ZDOTDIR`, or your login shell. Review the
bundle, then source it manually from the shell file you choose:

```sh
source "$HOME/.local/share/niri-plus/zsh-neutral-slate/zshrc"
```

`fzf` and `zoxide` are optional. Without either command, the shell still starts
and their bindings are simply absent. The package that provides `nmtui`, the
Bluetooth prompt's system service, and graphical desktop utilities are covered
in the [common utility recipe](desktop-utilities.md). Powerlevel10k's pinned
tree includes `gitstatus` install metadata; on first use in a Git repository,
it may download an architecture-specific `gitstatusd` release binary and check
its SHA-256 against that pinned metadata.

To remove the bundle, first remove any source line you added and close shells
using it so the prompt watcher can stop. Check the exact destination printed by
the fetcher, then remove only that new directory. The XDG history and cache
directories live outside the bundle; keep or remove them separately if you
want to retain or discard shell state.

### Isolated verification

Run `python3 scripts/check-terminal.py` to check Zsh startup in a temporary
home, no-plugin/missing-tool behavior, the agent early return, fixture-backed
proc/sys status parsing, prompt watcher cleanup, plugin order, and Session
dispatch/cancellation. The check uses fake command shims and an isolated Unix
socket. It does not operate a live session or native agent shell.

Terminal rendering still needs a real Kitty window. Check Noto/Meslo fallback,
Latin and Chinese text, Nerd Font glyphs, tmux, SSH, full-screen tools, selection,
dim/bold output, and the ANSI colors on the target machine. The exported shell
configuration and actual native adoption remain separate checks.
