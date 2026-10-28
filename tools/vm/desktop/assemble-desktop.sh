#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# Refuse the workstation or any guest other than the retained Arch VM before
# Python, sudo, package, network, service, or home actions are attempted.
# shellcheck disable=SC1091
source "$script_dir/../guest-guard.sh"
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
if (( $# > 0 )); then
    printf 'Usage: %s\n' "${BASH_SOURCE[0]}" >&2
    exit 2
fi

exec python3 "$script_dir/assemble_desktop.py"
