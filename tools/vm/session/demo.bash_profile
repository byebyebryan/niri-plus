# Lab-only console start for the retained Niri Plus reference guest.
if [[ "$(tty 2>/dev/null || true)" == /dev/tty1 && -z "${WAYLAND_DISPLAY:-}" ]]; then
    exec niri-session -l
fi

[[ -f ~/.bashrc ]] && . ~/.bashrc
