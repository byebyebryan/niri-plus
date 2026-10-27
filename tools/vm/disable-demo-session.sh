#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
source "$script_dir/guest-guard.sh"
require_niri_plus_arch_guest

if (( EUID == 0 )) || [[ "$(id -un)" != demo ]]; then
    printf 'Run this recovery script as the ordinary demo user, not root.\n' >&2
    exit 1
fi

profile_source="$script_dir/session/demo.bash_profile"
profile_target="$HOME/.bash_profile"
dropin_source="$script_dir/session/getty@tty1.service.d/20-niri-plus-demo.conf"
dropin_target="/etc/systemd/system/getty@tty1.service.d/20-niri-plus-demo.conf"
recovery_directory="$HOME/.local/state/niri-plus-vm/recovery"
state_path="$recovery_directory/bash_profile.state.json"
backup_path="$recovery_directory/bash_profile.preimage"
arch_profile_sha256=e149407c2bee17779caec70a7edd3d0000d172e7e4347429b80cb4d55bcec9c2

for path in \
    "$HOME/.local" \
    "$HOME/.local/state" \
    "$HOME/.local/state/niri-plus-vm" \
    "$recovery_directory"; do
    if [[ -L "$path" ]]; then
        printf 'Refusing to follow a symlink in recovery state: %s\n' "$path" >&2
        exit 1
    fi
done
if [[ ! -d "$recovery_directory" ]] || [[ "$(stat -c '%u:%a' "$recovery_directory")" != "$(id -u):700" ]]; then
    printf 'Bash profile recovery directory is missing or has unexpected ownership/mode.\n' >&2
    exit 1
fi
if [[ -L "$state_path" || ! -f "$state_path" ]] || [[ "$(stat -c '%u:%a' "$state_path")" != "$(id -u):600" ]]; then
    printf 'Bash profile recovery record is missing or unsafe: %s\n' "$state_path" >&2
    exit 1
fi
profile_state="$(python3 - "$state_path" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    state = json.load(stream)
if state.get("schema_version") != 1 or state.get("state") not in {"absent", "arch-skel"}:
    raise SystemExit("unsupported Bash profile recovery record")
if state["state"] == "arch-skel":
    if state.get("sha256") != "e149407c2bee17779caec70a7edd3d0000d172e7e4347429b80cb4d55bcec9c2" or state.get("mode") != 0o644:
        raise SystemExit("Arch skeleton recovery record does not match its pinned preimage")
elif "sha256" in state or "mode" in state:
    raise SystemExit("absent-profile recovery record contains unexpected preimage data")
print(state["state"])
PY
)"

if [[ "$profile_state" == arch-skel ]]; then
    if [[ -L "$backup_path" || ! -f "$backup_path" ]] || [[ "$(stat -c '%u:%a' "$backup_path")" != "$(id -u):600" ]]; then
        printf 'Preserved Arch skeleton profile is missing or unsafe: %s\n' "$backup_path" >&2
        exit 1
    fi
    if [[ "$(sha256sum "$backup_path" | cut -d ' ' -f 1)" != "$arch_profile_sha256" ]] || ! cmp -s -- "$backup_path" "$script_dir/session/arch-skel.bash_profile"; then
        printf 'Preserved Arch skeleton profile preimage changed.\n' >&2
        exit 1
    fi
elif [[ -e "$backup_path" || -L "$backup_path" ]]; then
    printf 'Unexpected Bash profile preimage exists for an originally absent profile.\n' >&2
    exit 1
fi

profile_needs_restore=1
if [[ ! -L "$profile_target" && -f "$profile_target" ]] && [[ "$(stat -c '%a' "$profile_target")" == 644 ]] && cmp -s -- "$profile_source" "$profile_target"; then
    :
elif [[ "$profile_state" == arch-skel && ! -L "$profile_target" && -f "$profile_target" ]] && [[ "$(stat -c '%a' "$profile_target")" == 644 ]] && cmp -s -- "$backup_path" "$profile_target"; then
    profile_needs_restore=0
elif [[ "$profile_state" == absent && ! -e "$profile_target" && ! -L "$profile_target" ]]; then
    profile_needs_restore=0
else
    printf 'Refusing to restore over an unrelated changed profile: %s\n' "$profile_target" >&2
    exit 1
fi
dropin_present=0
if sudo test -e "$dropin_target" || sudo test -L "$dropin_target"; then
    if sudo test -L "$dropin_target" || ! sudo cmp -s -- "$dropin_source" "$dropin_target"; then
        printf 'Refusing to remove a changed systemd drop-in: %s\n' "$dropin_target" >&2
        exit 1
    fi
    dropin_present=1
fi

if (( dropin_present )); then
    sudo rm -- "$dropin_target"
    sudo rmdir --ignore-fail-on-non-empty "$(dirname -- "$dropin_target")"
fi

if (( profile_needs_restore )) && [[ "$profile_state" == arch-skel ]]; then
    replacement="$(mktemp "$HOME/.bash_profile.niri-plus-restore.XXXXXX")"
    cp -- "$backup_path" "$replacement"
    chmod 0644 "$replacement"
    if ! cmp -s -- "$profile_source" "$profile_target"; then
        rm -f -- "$replacement"
        printf 'Bash profile changed during recovery; refusing replacement.\n' >&2
        exit 1
    fi
    mv -fT -- "$replacement" "$profile_target"
elif (( profile_needs_restore )); then
    rm -- "$profile_target"
fi

sudo systemctl daemon-reload
sudo systemctl reset-failed getty@tty1.service
sudo systemctl restart getty@tty1.service
rm -- "$state_path"
if [[ "$profile_state" == arch-skel ]]; then
    rm -- "$backup_path"
fi
rmdir --ignore-fail-on-non-empty "$recovery_directory"
printf 'Restored the exact pre-setup Bash profile and removed only verified Niri Plus tty1 lab files.\n'
