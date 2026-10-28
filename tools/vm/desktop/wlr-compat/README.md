# xdg-desktop-portal-wlr VM compatibility candidate

## Source and behavior

This local Arch recipe builds upstream xdg-desktop-portal-wlr commit
`01171a150b705cf07066ebc0fb7e1ff537027bec` (version 0.8.2) against the guest's
current libraries. The immutable GitHub archive SHA-256 is
`04ad0e4a7717265475fd394b614092d70909ff2089c08bb2b90adde9e8c436cd`. Package
`xdg-desktop-portal-wlr 0.8.2-1.3` keeps Arch's package name and portal
implementation provide, plus the local system portal defaults.

The two local patches are pinned in `PKGBUILD`:

- `trace-buffer-constraints.patch`, SHA-256
  `5e5d82645eb2e6e4eba23b472dc29b43e01a653da228c4a7fdcaef9349a43c0b`, prints
  actual GBM buffer dimensions, fourcc and modifier, then the advertised
  DMA-BUF pairs when xdpw rejects a pair.
- `fallback-unsupported-dmabuf.patch`, SHA-256
  `b719065f86a917de28ab633f82c4ee44035f5afec9a4863526b05893a354c10c`, keeps
  exact pair matching and switches this stream to the existing SHM formats
  only when dimensions still match and the actual DMA-BUF pair is not
  advertised. Size changes and SHM mismatches keep the existing behavior.

The trace found VirGL GBM returning a 1920x1080 XRGB8888 buffer
(`0x34325258`) with `DRM_FORMAT_MOD_LINEAR` (`0x0000000000000000`), while Niri
advertises the same fourcc with `DRM_FORMAT_MOD_INVALID`
(`0x00ffffffffffffff`). The exact pair check rejects that buffer before a frame
is copied.

## Guest result and scope

In the already assembled Arch VM, Chrome's whole-monitor share produced a live
1920x1080 track. The trace observed 8 video callbacks and 7 frame advances;
sampling found 80 distinct colors. xdg-desktop-portal-wlr kept the same PID for
30 seconds. Its measured `MemoryCurrent` maximum was 16.8 MiB and `MemoryPeak`
was 80.3 MiB. TRACE confirmed PipeWire buffer type `0 (4)` (SHM/MemFd). After
Stop, Chrome's `Video/Source` and `ChromeInput` nodes were removed. The retained
0.8.4 package and unpatched upstream 0.8.2 both failed this share test.

This result was recorded with temporary TRACE and per-unit resource-guard
overrides (`MemoryMax=512M`, `MemorySwapMax=0`). A second share pass then
passed with the TRACE drop-in removed, both memory limits restored to
`infinity`, and the package's normal `ExecStart`
(`/usr/libexec/xdg-desktop-portal-wlr`, no extra arguments). It again produced
a 1920x1080 monitor track with 8 video callbacks and 7 frame advances. Measured
`MemoryCurrent` was about 6.9 MiB and `MemoryPeak` about 70.1 MiB. Stop ended
the track and released the preview; `pw-dump` showed no remaining Video capture
or input nodes.

This records the tested screen-share path in this VM only. It is not a fresh
installation result, a full desktop acceptance, or a fleet/default adoption.
The desktop assembler does not select or install this candidate. Keep it as an
explicit VM compatibility step.

## Build, install and recovery order

Run the core desktop assembler first. It installs Arch's repository
`xdg-desktop-portal-wlr`; rerunning it can replace this local candidate with the
repository package. After every core assembler rerun, reinstall this candidate
explicitly if the VM share test needs it.

Run the assembler from the ordinary guest account:

```sh
bash /tmp/niri-plus-vm/desktop/assemble-desktop.sh
```

Before replacing the repository package, record its installed version and save
the exact package archive outside `/var/cache/pacman/pkg/`:

```sh
pacman -Q xdg-desktop-portal-wlr
```

Confirm the saved archive matches that installed version. If its archive is not
cached, obtain and save that exact version before continuing. Restore it with:

```sh
sudo pacman -U /path/to/saved-repository-package.pkg.tar.zst
```

The two package builds install the executable at different paths. The [Arch
repository package file list](https://archlinux.org/packages/extra/x86_64/xdg-desktop-portal-wlr/files/)
places it at `/usr/lib/xdg-desktop-portal-wlr`. This recipe leaves Meson's
`libexecdir` unset; its [built-in default](https://mesonbuild.com/Builtin-options.html)
is `libexec`, so the candidate uses `/usr/libexec/xdg-desktop-portal-wlr` and
its D-Bus service entry points there. Temporary runtime guards or TRACE
overrides must match the currently installed package path. Remove or restore
those overrides after the diagnostic, and check the service entry when
switching packages.

The runtime dependencies in `PKGBUILD` should already be installed so
`--rmdeps` removes only build dependencies. Build as the ordinary guest user
after the core assembler:

```sh
cd /tmp/niri-plus-vm/desktop/wlr-compat
makepkg --syncdeps --rmdeps
```

Save the repository recovery package before installing the candidate, then:

```sh
sudo pacman -U ./xdg-desktop-portal-wlr-0.8.2-1.3-x86_64.pkg.tar.zst
pacman -Q xdg-desktop-portal-wlr
```

The expected package query is `xdg-desktop-portal-wlr 0.8.2-1.3`. Keep the
same PipeWire, WirePlumber, Niri, Mesa, Chrome and resource cap during any
repeat trial. Afterward restore the saved repository package and its matching
service path/overrides.
