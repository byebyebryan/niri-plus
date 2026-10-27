#!/usr/bin/env bash
set -euo pipefail

require_niri_plus_arch_guest() {
    local guest_name vendor product

    if [[ ! -r /proc/sys/kernel/hostname ]]; then
        printf 'Refusing to run: kernel hostname identity is unavailable.\n' >&2
        return 1
    fi
    IFS= read -r guest_name </proc/sys/kernel/hostname || true
    if [[ "$guest_name" != "niri-plus-arch" ]]; then
        printf 'Refusing to run: expected guest hostname niri-plus-arch, got %s\n' "${guest_name:-<empty>}" >&2
        return 1
    fi

    if [[ ! -r /sys/class/dmi/id/sys_vendor || ! -r /sys/class/dmi/id/product_name ]]; then
        printf 'Refusing to run: QEMU DMI identity is unavailable.\n' >&2
        return 1
    fi
    vendor="$(tr -d '\000\r\n' </sys/class/dmi/id/sys_vendor)"
    product="$(tr -d '\000\r\n' </sys/class/dmi/id/product_name)"
    if [[ "${vendor,,}" != *qemu* || -z "$product" ]]; then
        printf 'Refusing to run: expected QEMU DMI, got vendor=%s product=%s\n' "$vendor" "$product" >&2
        return 1
    fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    require_niri_plus_arch_guest
    printf 'Guest identity verified: niri-plus-arch (%s / %s).\n' \
        "$(tr -d '\000\r\n' </sys/class/dmi/id/sys_vendor)" \
        "$(tr -d '\000\r\n' </sys/class/dmi/id/product_name)"
fi
