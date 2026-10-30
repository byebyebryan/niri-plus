# Manual display-away trial

This unpublished, opt-in companion lives in a separate Niri Plus worktree.
It is not in the released 0.4.1 component bundle. Personal host admission and
checksum-verified installation remain in chezmoi. No published pin is changed.

`desktop-away run` observes physical USB/Bluetooth/i8042/I2C keyboard, mouse
and touchpad devices without grabbing them or saving input events. A private
runtime socket accepts `away`, `resume` and `status` commands. Manual away
powers monitors off and corrects later application/hotplug wakeups, polling
DRM state every 250 ms with corrections limited to two per second. A brief
flash is possible because correction happens after a wake. Unknown DRM state
gets an off request; it is never accepted as proof of darkness.

Only new physical key/button presses or pointer movement clear the latch.
Shortcut releases/repeats, old buffered input, virtual uinput devices, audio
jack events, connection changes and SSH/CDP activity cannot clear it. Hotplug
opens newly connected input nodes promptly; the initial Bluetooth wake key
can still precede node discovery, requiring another input. No new access
rules or input-group membership changes are installed.

Normal mode does not act on display power, so the existing idle owner and
application inhibitors remain effective. Stopping the companion while away
restores normal display power. A new session starts in normal mode. The
manual-off client falls back to ordinary DPMS off if its controller is down.
Remote recovery is `desktop-away resume` or stopping `desktop-away.service`.

Validation: `python3 scripts/check-desktop-away.py` uses decision tests and
an isolated daemon with a fake compositor. Live acceptance must separately
verify an actual Chrome extension interaction and screenshot with DRM off,
application-triggered wake correction, and real physical input return.
Physical panel acceptance is distinct from the kernel's DRM power report.

## Local validation, 2026-10-30

Seventeen isolated tests passed. The producer built 160 files/24 pages with
904 local links, and its existing isolated browser suite passed 1,007 checks.
Starship's managed binding and companion unit validated; its existing idle,
locker, notification and compositor services retained their original identities.
Snap, Carbon and an unknown host rendered exactly their prior bindings.

Chrome extension navigation, two clicks and fresh standard screenshots worked
with the display reporting DRM Off and the latch remaining armed. An explicit
application-style power-on was corrected back to Off in 0.306 seconds. Real
Lofree mouse input released the first trial. Human panel confirmation is
recorded separately in the private deployment receipt.

A screenshot with an explicit crop timed out after five seconds with DRM Off.
The ordinary `tab.screenshot()` path then succeeded, including a fresh capture
after another click. Prefer the standard screenshot path during this trial;
compatibility with every capture mode is not established. The owned test tab
was closed to release its capture/debugger state.
