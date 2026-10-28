# Displays and docking

Kanshi owns output profiles in this setup. On the current Arch package there is
no packaged user service, so the single startup owner is Niri's
`spawn-at-startup` entry. Niri owns windows and workspaces; changing the
connected displays should leave those workflows intact. The
personal profiles include an ultrawide at scale 1, Carbon's internal panel at
scale 1.5, and laptop home/work combinations. Connector names, available modes
and monitor identities are machine-specific.

## Inspect the outputs

The main walkthrough installs `kanshi`. Inspect the outputs from a terminal
inside Niri:

```sh
niri msg outputs
```

Record the connector, advertised mode, scale and logical position you want.
The [Kanshi configuration manual](https://man.archlinux.org/man/kanshi.5.en)
describes connector and manufacturer/model matching. Connector names may change
through a dock; a model pattern can be more useful, but publishing a personal
serial number is unnecessary.

## Adapt the profiles

The [profile skeleton](../../examples/displays/kanshi.conf) has a specific
two-display profile followed by an internal-only fallback. For a fresh account,
install that staged file only when the target does not exist, then replace its
output names, mode, scale and positions before starting Kanshi:

```sh
KANSHI_CONFIG="$HOME/.config/kanshi/config"
if [ -e "$KANSHI_CONFIG" ] || [ -L "$KANSHI_CONFIG" ]; then
  printf '%s\n' "Inspect and merge the staged profile into: $KANSHI_CONFIG"
else
  install -Dm644 "$SOURCE/examples/displays/kanshi.conf" "$KANSHI_CONFIG"
fi
```

Its `1280,0` position is an example: a 1920-pixel-wide panel at scale 1.5
occupies 1280 logical pixels. Calculate from your actual mode.
On a desktop without an internal panel, replace both profiles with the outputs
that exist there. Keep at least one display enabled in each usable profile.

My managed desktop uses fixed Niri column-width presets of 960, 1280, 1600 and
1920 logical pixels, with Kitty/agent windows starting at 960. The portable
[Niri example](../../examples/niri/config.kdl) uses proportional widths so it is
useful on unfamiliar displays. Output scaling and column width are separate
choices; the former also affects application readability.

## Start one owner

Merge this top-level statement into Niri's existing config only if Kanshi is not
already started by another hook or user service:

```kdl
spawn-at-startup "kanshi"
```

That starts it on the next session. For a first trial, run `kanshi` from an
owned terminal in the existing Niri session and keep that terminal available.
Use `kanshictl reload` after later configuration edits. Check a normal dock,
undock and reconnect, including the internal-only fallback. See
[Niri's output configuration](https://niri-wm.github.io/niri/Configuration:-Outputs.html)
for compositor output controls and temporary recovery adjustments.

If a trial profile is wrong, stop that trial Kanshi process, restore its previous
configuration, and use the current Niri output controls to recover a reachable
display. Do not run competing profile managers. Profile matching and real
display transitions still require acceptance on the target hardware.
