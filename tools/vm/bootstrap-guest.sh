#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# This check deliberately precedes package, network, and filesystem changes.
source "$script_dir/guest-guard.sh"
require_niri_plus_arch_guest

if [[ ! -r /etc/os-release ]]; then
    printf 'Refusing to run: /etc/os-release is unavailable.\n' >&2
    exit 1
fi
# shellcheck disable=SC1091
source /etc/os-release
if [[ "${ID:-}" != arch || "$(uname -m)" != x86_64 ]]; then
    printf 'Refusing to run: expected x86_64 Arch Linux.\n' >&2
    exit 1
fi
if (( EUID == 0 )) || [[ "$(id -un)" != demo ]]; then
    printf 'Run this script as the ordinary demo user, not root.\n' >&2
    exit 1
fi
if ! command -v sudo >/dev/null 2>&1; then
    printf 'The demo user needs sudo access for guest package setup.\n' >&2
    exit 1
fi

sudo -v
guest_packages=(
    base-devel
    dbus
    ffmpeg
    fontconfig
    git
    grim
    kitty
    mesa
    mesa-utils
    niri
    noto-fonts
    noto-fonts-emoji
    python
    rofi
    ttf-meslo-nerd
    xdg-desktop-portal-gtk
    xdg-desktop-portal-wlr
    wf-recorder
    wtype
    xwayland-satellite
    zsh
)
printf 'Installing the pilot packages in the verified guest (full Arch upgrade included).\n'
sudo pacman -Syu --needed --noconfirm "${guest_packages[@]}"

if [[ "${1:-}" == "--packages-only" ]]; then
    printf 'Guest package transaction complete; downstream setup was not run.\n'
    exit 0
fi
if (( $# > 0 )); then
    printf 'Usage: %s [--packages-only]\n' "${BASH_SOURCE[0]}" >&2
    exit 2
fi

exec python3 "$script_dir/bootstrap_guest.py"
