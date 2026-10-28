# At home in the terminal

Kitty and Zsh support the keyboard driven work that moves between a laptop,
workstation, and remote hosts. This guide covers the Neutral Slate color
fragment and a portable shell core that you can install beside your existing
configuration.

The selected terminal palette is **Balanced+ on pure black**, independent of
the desktop's warm charcoal surfaces. The
[contrast study](../design/contrast.md) retains the compared alternatives and
marks the selected sample.

## Kitty: the everyday surface

My terminal uses MesloLGS Nerd Font at 11pt, no window decorations, explicit
Nerd Font symbol mappings, and Kitty's cursor trail. Pasted dangerous control
codes are replaced. Shift+Enter sends the existing CSI-u sequence for legacy
terminal modes, while applications using Kitty's keyboard protocol keep their
native behavior.

The generated [Neutral Slate Kitty fragment](../../examples/kitty/neutral-slate.conf)
contains only appearance options: a fully opaque `#000000` background, warm
off-white text, a clear blue cursor, blue selection, and the Balanced+ ANSI table.
It does not change input, paste handling, glyph mappings, cursor trail, windows,
or shell behavior. The fragment is selected design material; its presence here
does not claim native deployment.

To inspect it in a separate Kitty window, layer it after your existing config:

```sh
kitty --config ~/.config/kitty/kitty.conf --config /path/to/neutral-slate.conf
```

The [Design page's palette](../design.md#palette) lists every ANSI slot and
role. Red maps to errors, green to success, yellow to warnings, blue to the
blue family, violet and cyan are supplemental, and neutral slots are chosen
for terminal work. These values are independent of desktop color roles.
Entries 16–255 retain Kitty's defaults;
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
| History and completion | Shared history in the user's XDG state directory, duplicate reduction, command verification, completion menu, and case-insensitive matching. The personal caller can provide its existing history and compdump paths. |
| Editing | Up/Down substring history search, inline autosuggestions, and syntax highlighting loaded after widget integrations. |
| Navigation | Zoxide and fzf initialization when their commands are installed. |
| Agent tool shell | A recognized tool environment gets a hostname-only prompt and skips history, completion, plugins, custom probes, and the refresh watcher by default. The private compatibility option retains history initialization before returning in agent mode. Force the simple or full prompt with `ZSH_FORCE_SIMPLE_PROMPT` or `ZSH_FORCE_FULL_PROMPT`. |

The portable [Zsh starter](../../examples/terminal/zshrc) sources the shared
[init API](../../examples/terminal/init.zsh), initializes the shell, returns
for agent mode, and finalizes the human shell. The API file only defines
`niri_plus_shell_init` and `niri_plus_shell_finish` when sourced. Private
callers can put their own integrations between those calls and explicitly
return from their `.zshrc` when `NIRI_PLUS_SHELL_MODE` is `agent`.

The core derives `NIRI_PLUS_ZSH_HOME` from the location of `init.zsh`. Its
default plugin root is `NIRI_PLUS_ZSH_HOME/plugins`; the theme root defaults to
the same directory, with Powerlevel10k below `powerlevel10k/`. Set
`NIRI_PLUS_ZSH_PLUGIN_DIR` and `NIRI_PLUS_ZSH_THEME_DIR` to use a staged
dependency tree. The portable history and completion defaults use XDG state and
cache paths. Callers can override them with `NIRI_PLUS_ZSH_HISTORY_FILE` and
`NIRI_PLUS_ZSH_COMPDUMP` without moving existing data.

`niri_plus_shell_pre_init` is an optional function hook for integrations such
as Ghostty. It runs for human shells after history setup and before completion
and plugins. The finalizer runs optional zoxide/fzf initialization and loads
syntax highlighting last, after caller integrations that may change ZLE widgets.

The [Powerlevel10k configuration](../../examples/terminal/p10k.zsh) and
[custom status segments](../../examples/terminal/p10k-custom-segments.zsh)
retain the selected semantic ANSI roles and prompt layout. Proc/sys roots can
be replaced in isolated fixtures, and the quiet reader plus guarded watcher
shutdown keep missing hardware and closed pipes harmless. These probes use
Linux interfaces and optional system commands; absent devices hide their
segments. The watcher refreshes only while ZLE waits for input and closes its
file descriptor on line completion or shell exit.

### Native and portable choices

| Difference | Shared-core choice |
| --- | --- |
| Native Zsh initializes history before agent detection; the shared API computes mode first. | `NIRI_PLUS_ZSH_AGENT_HISTORY=skip` is the portable default. The personal compatibility setting `legacy` retains history initialization before returning in agent mode. |
| Native history and completion paths differ from the portable XDG defaults. | `NIRI_PLUS_ZSH_HISTORY_FILE` and `NIRI_PLUS_ZSH_COMPDUMP` let the caller retain both existing paths. The core does not migrate either file. |
| Ghostty, SDK, kubectl, pyenv, editor, and browser setup exists only in the personal startup. | Ghostty can use the pre-init hook. Other personal integrations stay in the caller between init and finish. |
| Native prompt source uses fixed proc/sys paths and the watcher does not guard a failed worker write. | The shared source keeps the portable fixture roots, quiet single-value reads, and worker exit guard. Defaults still read `/proc` and `/sys`; five-second hardware/network caching and the one-second refresh cadence remain. |
| Native prompt source has raw ANSI values that the managed templates map to the selected palette. | The shared prompt keeps the rendered semantic roles: blue path, green success, yellow warning, red error, and the selected neutral/connected roles. |

`NIRI_PLUS_ZSH_AGENT_HISTORY` accepts only `skip` or `legacy`. `NIRI_PLUS_SHELL_MODE`
is recomputed by `niri_plus_shell_init` and remains a non-exported shell variable.

### Requirements and install

Use Zsh, Python 3.10 or later for the opt-in fetcher, a working TLS connection
to GitHub codeload, and MesloLGS Nerd Font installed in Kitty. The [fetcher](../../examples/terminal/fetch.py)
installs the four pinned upstream trees beside the portable configuration.
The file [pins and archive hashes](../../examples/terminal/pins.json) records
the immutable commit and SHA-256 for each tarball; [third-party notices](../../examples/terminal/THIRD_PARTY_NOTICES.md)
records license and attribution details. The selected versions follow the
existing public checkouts rather than a floating branch.

The main walkthrough exports `SOURCE` as the verified examples tree. Choose a
new directory below your home directory and run the staged fetcher manually:

```sh
ZSH_BUNDLE="$HOME/.local/share/niri-plus/zsh-neutral-slate"
python3 "$SOURCE/examples/terminal/fetch.py" "$ZSH_BUNDLE"
```

The fetcher verifies HTTPS archives and SHA-256 before extraction. It refuses
an existing or symlink destination, installs only into a newly created leaf,
and does not edit `.zshrc`, `.zshenv`, `ZDOTDIR`, or your login shell. Review the
bundle, then source it manually from the shell file you choose:

```sh
source "$ZSH_BUNDLE/zshrc"
```

For a fresh account with no `.zshrc`, create a small user-owned source shim. If
one already exists, inspect it and merge only the `source` line; do not replace
its other integrations:

```sh
ZSHRC="$HOME/.zshrc"
if [ -e "$ZSHRC" ] || [ -L "$ZSHRC" ]; then
  printf '%s\n' "Inspect and merge this line into $ZSHRC:"
  printf 'source "%s/zshrc"\n' "$ZSH_BUNDLE"
else
  install -Dm600 /dev/stdin "$ZSHRC" <<EOF
source "$ZSH_BUNDLE/zshrc"
EOF
fi
```

The reference keeps Bash as the account login shell and starts Zsh only in
Kitty. Merge this line into the existing Kitty config; the appearance recipe
already shows it with the font and palette entries:

```conf
shell /usr/bin/zsh --login
```

New Kitty windows then read the `.zshrc` shim and start a Zsh login shell. If
you want Zsh for every terminal and console login instead, make that a separate
account-level choice with `chsh -s /usr/bin/zsh`; log out and back in to test it.
The guide's reference route does not change the account shell.

To stage only pinned dependencies for a separately selected shell core, use
the fetcher's `--dependencies-only` mode with another new destination:

```sh
python3 "$SOURCE/examples/terminal/fetch.py" --dependencies-only \
  "$HOME/.local/share/niri-plus/zsh-plugins-0.2.0"
```

That leaf contains `plugins/` with all four pinned trees, `pins.json`,
third-party notices, and `receipt.json`. Receipt schema 1 records the SHA-256
of the exact pins file, each project's commit and archive digest, and a sorted
`files` list. Regular-file records include path, mode, and SHA-256; symlink
records include path, link target, and the target-string SHA-256. The receipt
does not include a self-hash. The fetcher never merges or replaces an existing
leaf and does not copy shell startup or prompt files in this mode.

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
