# xdg-desktop-portal-wlr VirtIO compatibility candidate

This is a local Arch package candidate for a specific whole-monitor sharing
failure in a VirtIO/VirGL guest. It is not part of the normal Arch desktop
installation route, a new portal backend, or a general replacement for the
distribution package. On a physical desktop or a guest where the stock portal
works, keep the repository package.

## Source and behavior

The recipe builds upstream xdg-desktop-portal-wlr commit
`01171a150b705cf07066ebc0fb7e1ff537027bec` (version 0.8.2) against the
installed Arch libraries. The immutable GitHub archive SHA-256 is
`04ad0e4a7717265475fd394b614092d70909ff2089c08bb2b90adde9e8c436cd`. The
resulting package is `xdg-desktop-portal-wlr 0.8.2-1.3`; it keeps Arch's package
name and portal implementation provide.

The two local patches are pinned in `PKGBUILD`:

- `trace-buffer-constraints.patch`, SHA-256
  `5e5d82645eb2e6e4eba23b472dc29b43e01a653da228c4a7fdcaef9349a43c0b`, records
  the actual GBM buffer dimensions, fourcc and modifier, plus the advertised
  DMA-BUF pairs when xdpw rejects a pair.
- `fallback-unsupported-dmabuf.patch`, SHA-256
  `b719065f86a917de28ab633f82c4ee44035f5afec9a4863526b05893a354c10c`, keeps
  exact pair matching and uses the existing SHM formats only when dimensions
  still match and the actual DMA-BUF pair is not advertised. Size changes and
  SHM mismatches keep the existing behavior.

In the guest, VirGL supplied a 1920x1080 XRGB8888 buffer
(`0x34325258`) with `DRM_FORMAT_MOD_LINEAR` (`0x0000000000000000`), while Niri
advertised that fourcc with `DRM_FORMAT_MOD_INVALID`
(`0x00ffffffffffffff`). The exact pair check rejected the buffer before a frame
was copied.

## Latest guest result and limits

The Arch 0.8.4 repository package under the guest's existing 512 MiB unit cap
created a live 1920x1080 Chrome track but produced zero frames and width zero;
the provider later aborted while handling a non-null zero-sized allocation.
The host showed no OOM event. Treat this as a VirtIO guest observation, not a
claim about other machines or an uncapped stock package.

After installing the compatibility candidate with its normal service command,
no TRACE flags, and no memory limit, Chrome displayed a live 1920x1080 monitor
preview. The capture recorded eight callbacks and frame advances from 291 to
298 over 42.10–42.57 seconds, with 608 sampled colors. Portal memory peaked at
79.9 MiB (`MemoryCurrent` 16.1 MiB). Stopping the share ended all tracks; a
`pw-dump` check found no capture or input nodes left behind. This confirms the
tested guest capture path only. It is not fresh-install, physical-device, fleet,
or full-desktop acceptance.

For Chrome's preview check, scroll the preview into view before judging its
image. An off-viewport preview can show a black canvas even while media frame
counters advance. Chrome 156 passed without `--disable-gpu`; the observed test
used the native Wayland route `--ozone-platform=wayland` only.

## Optional Arch walkthrough branch

The main [Arch walkthrough](https://dev.byebyebryan.com/niri-plus/setup/agent/) installs Arch's repository
portal as part of its package group. Use this candidate only if a VirtIO/VirGL
guest reproduces the exact whole-monitor failure above. It is built from the
reviewed checkout and is not downloaded from the pilot guest or its cache.

Keep a console available. Save the exact currently installed repository package
outside Pacman's cache before replacing it. If that exact archive is not
available, stop and obtain the matching package before continuing:

```sh
REPOSITORY_VERSION="$(pacman -Q xdg-desktop-portal-wlr | cut -d' ' -f2)"
REPOSITORY_ARCHIVE="/var/cache/pacman/pkg/xdg-desktop-portal-wlr-${REPOSITORY_VERSION}-x86_64.pkg.tar.zst"
test -r "$REPOSITORY_ARCHIVE"
RECOVERY="$HOME/.local/share/niri-plus/recovery"
install -Dm644 "$REPOSITORY_ARCHIVE" "$RECOVERY/$(basename "$REPOSITORY_ARCHIVE")"
```

Build the candidate as the ordinary account from this checkout's existing
recipe. The main guide exports `NIRI_PLUS_CHECKOUT`; no desktop assembler or
pilot path is needed:

```sh
WLR_CANDIDATE="$NIRI_PLUS_CHECKOUT/tools/vm/desktop/wlr-compat"
(
  cd "$WLR_CANDIDATE"
  makepkg --verifysource
  makepkg --syncdeps --rmdeps
)
WLR_PACKAGE="$WLR_CANDIDATE/xdg-desktop-portal-wlr-0.8.2-1.3-x86_64.pkg.tar.zst"
pacman -Qip "$WLR_PACKAGE"
```

Review the package metadata, then install the exact built archive:

```sh
sudo pacman -U "$WLR_PACKAGE"
pacman -Q xdg-desktop-portal-wlr
```

Use the portal through Chrome's ordinary whole-monitor sharing flow. Keep the
package's normal `ExecStart` (`/usr/libexec/xdg-desktop-portal-wlr`), avoid
TRACE/runtime resource overrides, and verify that the preview is live. If the
stock package works or the candidate does not fix the exact failure, restore
the saved repository package:

```sh
sudo pacman -U "$RECOVERY/$(basename "$REPOSITORY_ARCHIVE")"
pacman -Q xdg-desktop-portal-wlr
```

The Arch repository package installs its executable at
`/usr/lib/xdg-desktop-portal-wlr`; this candidate's Meson default installs at
`/usr/libexec/xdg-desktop-portal-wlr`. The package carries its matching D-Bus
service entry. Do not leave service overrides from another package path in
place when switching back.

## Retained capture-pilot route

The old retained-guest workflow remains optional for that specific guest. Its
desktop assembler installs the repository portal package, so a rerun replaces
this candidate; reinstall it afterward only if the retained VM share test still
needs it. The regular Arch walkthrough above does not call the assembler or
depend on `/tmp/niri-plus-vm`.
