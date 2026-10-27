# Shared Niri Plus custom Powerlevel10k status segments.
# Right prompt: time, cpu, memory, bluetooth, network, battery.
# Shared utils: semantic colors, circle/wifi/battery gauge icons.
# Segments split into detection (data + status) and rendering (icon + color + p10k segment).

# EPOCHSECONDS is provided by zsh/datetime and lets the slow probes below use
# monotonic-ish wall-clock deadlines without spawning `date` from the prompt.
zmodload zsh/datetime 2>/dev/null

# Probe state survives between prompt renders.  A failed/absent probe is cached
# too, so missing hardware and optional commands do not cost a process per tick.
typeset -gi __p10k_bt_cache_until=0 __p10k_bt_cache_available=0
typeset -gi __p10k_net_cache_until=0 __p10k_net_cache_available=0
typeset -gi __p10k_bat_cache_until=0 __p10k_bat_cache_available=0
typeset -gi __p10k_color=252
typeset -g __P10K_SYS_PREV_TOTAL= __P10K_SYS_PREV_IDLE_ALL=
typeset -gi __P10K_CPU_SMOOTH_PCT=-1

# --- ANSI 0-15 color constants ---
# p10k only recommends its own names for 0-7 (black/red/green/yellow/blue/magenta/cyan/white).
# For 8-15 it uses xterm names (maroon/lime/navy…) which aren't intuitive, so we define our own.
typeset -gri \
  C_BLACK=0           C_RED=1           C_GREEN=2         C_YELLOW=3 \
  C_BLUE=4            C_MAGENTA=5       C_CYAN=6          C_WHITE=7 \
  C_GRAY=8            C_BRIGHT_RED=9    C_BRIGHT_GREEN=10 C_BRIGHT_YELLOW=11 \
  C_BRIGHT_BLUE=12    C_BRIGHT_MAGENTA=13 C_BRIGHT_CYAN=14 C_BRIGHT_WHITE=15

# --- Semantic color palette ---
# Each segment's _detect_* helper sets a __p10k_*_status to one of these levels.
# Renderers call _p10k_color_for "$status" to get the right color index.
#
#   info      – neutral / informational (time)          → secondary (7)
#   normal    – healthy / all good                      → bright white (15)
#   connected – active network/Bluetooth connection    → cyan (6)
#   inactive  – powered but idle                        → bright black (8)
#   charging  – actively charging                        → green (2)
#   warning   – degraded but not urgent                → yellow (3)
#   error     – something is off / disabled             → red (1)
#   critical  – urgent, needs attention                 → bright red (9)
function _p10k_color_for() {
  local level="$1"
  case "$level" in
    info)      __p10k_color=7 ;;
    normal)    __p10k_color=15 ;;
    connected) __p10k_color=$C_CYAN ;;
    inactive)  __p10k_color=$C_GRAY ;;
    charging)  __p10k_color=$C_GREEN ;;
    warning)   __p10k_color=$C_YELLOW ;;
    error)     __p10k_color=$C_RED ;;
    critical)  __p10k_color=$C_BRIGHT_RED ;;
    *)         __p10k_color=15 ;;
  esac
  # Keep stdout for isolated helper tests; renderers use the global to avoid a
  # command substitution (and its fork) on every prompt refresh.
  print -r -n -- "$__p10k_color"
}

# --- Icon utilities ---
# Circle gauge by percentage (0–100), retained as a renderer utility for
# optional status visuals.  The active CPU/memory renderers use fixed icons and
# padded percentages to avoid gauge churn and width jitter.
function _circle_gauge() {
  local pct="${1:-0}" level
  (( pct < 0 )) && pct=0
  (( pct > 100 )) && pct=100
  level=$(( pct * 8 / 100 ))
  case "$level" in
    0) print -r -n '󰄰' ;;
    1) print -r -n '󰪞' ;;
    2) print -r -n '󰪟' ;;
    3) print -r -n '󰪠' ;;
    4) print -r -n '󰪡' ;;
    5) print -r -n '󰪢' ;;
    6) print -r -n '󰪣' ;;
    7) print -r -n '󰪤' ;;
    *) print -r -n '󰪥' ;;
  esac
}

# Wi‑Fi strength icon from RSSI (dBm). Empty or invalid -> generic icon.
function _wifi_icon() {
  local rssi="$1" level=0
  if [[ -n "$rssi" && "$rssi" -ge -100 ]]; then
    (( rssi >= -50 )) && level=4
    (( rssi >= -60 && rssi < -50 )) && level=3
    (( rssi >= -70 && rssi < -60 )) && level=2
    (( rssi >= -80 && rssi < -70 )) && level=1
  fi
  case "$level" in
    4) print -r -n '󰤨' ;;
    3) print -r -n '󰤥' ;;
    2) print -r -n '󰤢' ;;
    1) print -r -n '󰤟' ;;
    *) print -r -n '󰤯' ;;
  esac
}

# Battery icon from capacity (0–100) and charging (0/1).
function _battery_icon() {
  local cap="${1:-0}" charging="${2:-0}"
  (( cap < 0 )) && cap=0
  (( cap > 100 )) && cap=100
  local icon
  if (( cap >= 100 )); then   icon='󰁹'
  elif (( cap >= 90 )); then  icon='󰂂'
  elif (( cap >= 80 )); then  icon='󰂁'
  elif (( cap >= 70 )); then  icon='󰂀'
  elif (( cap >= 60 )); then  icon='󰁿'
  elif (( cap >= 50 )); then  icon='󰁾'
  elif (( cap >= 40 )); then  icon='󰁽'
  elif (( cap >= 30 )); then  icon='󰁼'
  elif (( cap >= 20 )); then  icon='󰁻'
  elif (( cap >= 10 )); then  icon='󰁺'
  else                         icon='󰂎'
  fi
  (( charging == 1 )) && print -r -n '󱐋'
  print -r -n "$icon"
}

# Reads a single-value virtual file without surfacing transient kernel/sysfs errors.
function _read_file_quiet() {
  local file="$1" value
  IFS= read -r value 2>/dev/null < "$file" || [[ -n "$value" ]] || return 1
  [[ -n "$value" ]] || return 1
  print -r -n -- "$value"
}

# Formats positive minutes as "H:MM" for compact prompt display.
function _format_duration_minutes() {
  local minutes="${1:-0}"
  (( minutes > 0 )) || return 1
  printf '%d:%02d' $(( minutes / 60 )) $(( minutes % 60 ))
}

# Formats a cpufreq value in kHz as a compact one-decimal GHz value. Integer
# arithmetic keeps this safe to call on every prompt refresh without spawning
# awk or another formatter.
function _format_cpu_freq_khz() {
  local khz="${1:-}" tenths
  typeset -g __p10k_cpu_freq_str=
  [[ "$khz" == <-> ]] && (( khz > 0 )) || return 1
  tenths=$(( (khz + 50000) / 100000 ))
  __p10k_cpu_freq_str="$(( tenths / 10 )).$(( tenths % 10 ))G"
}

# --- Detection helpers ---
# Each helper reads system state, sets __p10k_*_status + relevant metric globals,
# and returns 1 when no data is available (segment hidden).

# Reads /proc/meminfo. Sets: __p10k_mem_pct, __p10k_mem_status.
# Status: normal <70%, warning 70–84%, critical ≥85%.
function _detect_memory() {
  local mem_total_kb mem_avail_kb mem_used_kb
  local proc_root="${NIRI_PLUS_PROC_ROOT:-/proc}"
  # Parse the two needed rows in-process.  This runs every refresh, unlike the
  # deliberately cached hardware/network probes below.
  local key value rest
  while read -r key value rest; do
    case "$key" in
      MemTotal:) mem_total_kb="$value" ;;
      MemAvailable:) mem_avail_kb="$value" ;;
    esac
    [[ -n "$mem_total_kb" && -n "$mem_avail_kb" ]] && break
  done < "$proc_root/meminfo" 2>/dev/null
  [[ -n "$mem_total_kb" && -n "$mem_avail_kb" && "$mem_total_kb" -gt 0 ]] || return 1
  mem_used_kb=$(( mem_total_kb - mem_avail_kb ))
  typeset -g __p10k_mem_pct=$(( 100 * mem_used_kb / mem_total_kb ))
  typeset -g __p10k_mem_status=normal
  (( __p10k_mem_pct >= 85 )) && __p10k_mem_status=critical
  (( __p10k_mem_pct >= 70 && __p10k_mem_pct < 85 )) && __p10k_mem_status=warning
  return 0
}

# Reads /proc/stat diff between calls for an interval-based CPU% and the current
# CPU 0 clock from cpufreq, falling back to /proc/cpuinfo when needed.
# Sets: __p10k_cpu_pct, __p10k_cpu_freq_str, __p10k_cpu_status.
# Status: normal <50%, warning 50–79%, critical ≥80%.
# The first call seeds the counter and hides the segment until a real delta
# exists.  A small integer EMA keeps the color and value from flickering.
function _detect_cpu() {
  local proc_root="${NIRI_PLUS_PROC_ROOT:-/proc}"
  local sys_root="${NIRI_PLUS_SYS_ROOT:-/sys}"
  local _cpu user nice system idle iowait irq softirq steal rest
  local total idle_all dt didle used raw_pct cpu_pct khz key value mhz whole fraction

  read -r _cpu user nice system idle iowait irq softirq steal rest < "$proc_root/stat" 2>/dev/null || return 1
  total=$(( user + nice + system + idle + iowait + irq + softirq + steal ))
  idle_all=$(( idle + iowait ))

  if [[ -z "${__P10K_SYS_PREV_TOTAL:-}" || -z "${__P10K_SYS_PREV_IDLE_ALL:-}" ]]; then
    typeset -g __P10K_SYS_PREV_TOTAL=$total __P10K_SYS_PREV_IDLE_ALL=$idle_all
    typeset -gi __P10K_CPU_SMOOTH_PCT=-1
    return 1
  fi
  dt=$(( total - __P10K_SYS_PREV_TOTAL ))
  didle=$(( idle_all - __P10K_SYS_PREV_IDLE_ALL ))
  typeset -g __P10K_SYS_PREV_TOTAL=$total
  typeset -g __P10K_SYS_PREV_IDLE_ALL=$idle_all

  (( dt > 0 )) || return 1
  used=$(( dt - didle ))
  (( used < 0 )) && used=0
  (( used > dt )) && used=$dt
  raw_pct=$(( 100 * used / dt ))

  if (( __P10K_CPU_SMOOTH_PCT < 0 )); then
    cpu_pct=$raw_pct
  else
    # 75% previous, 25% new.  Integer arithmetic keeps the prompt cheap.
    cpu_pct=$(( (__P10K_CPU_SMOOTH_PCT * 3 + raw_pct + 2) / 4 ))
  fi
  typeset -gi __P10K_CPU_SMOOTH_PCT=$cpu_pct
  typeset -g __p10k_cpu_pct=$cpu_pct
  typeset -g __p10k_cpu_status=normal
  (( cpu_pct >= 80 )) && __p10k_cpu_status=critical
  (( cpu_pct >= 50 && cpu_pct < 80 )) && __p10k_cpu_status=warning

  typeset -g __p10k_cpu_freq_str=
  if [[ -r "$sys_root/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq" ]]; then
    IFS= read -r khz < "$sys_root/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq" 2>/dev/null
  else
    while IFS=: read -r key value; do
      [[ "$key" == *'cpu MHz'* ]] || continue
      mhz="${value//[[:space:]]/}"
      whole="${mhz%%.*}"
      if [[ "$mhz" == *.* ]]; then
        fraction="${mhz#*.}"
      else
        fraction=
      fi
      fraction="${fraction}000"
      fraction="${fraction[1,3]}"
      if [[ "$whole" == <-> && "$fraction" == <-> ]]; then
        khz=$(( whole * 1000 + fraction ))
      fi
      break
    done < "$proc_root/cpuinfo" 2>/dev/null
  fi
  _format_cpu_freq_khz "$khz" || true
  return 0
}

# Checks BlueZ via busctl (preferred) or bluetoothctl (fallback). Returns 1 when
# no Bluetooth adapter exists (segment hidden). Results, including absence, are
# cached for five seconds. Sets: __p10k_bt_powered, __p10k_bt_count (connected
# devices), __p10k_bt_status.
# Status: connected = powered with devices, inactive = powered with none,
# error = probe failure. Powered-off adapters are hidden by the renderer.
function _detect_bluetooth() {
  local -i now=${EPOCHSECONDS:-$SECONDS}
  if (( now < __p10k_bt_cache_until )); then
    (( __p10k_bt_cache_available )) && return 0 || return 1
  fi

  typeset -g __p10k_bt_powered=0 __p10k_bt_count=0 __p10k_bt_status=error
  typeset -g __p10k_bt_cache_available=0

  if (( $+commands[busctl] )); then
    local tree adapter dev_path connected
    local -a adapters dev_paths

    tree="$(busctl tree org.bluez 2>/dev/null)"
    adapters=("${(@f)$(print -r -- "$tree" | awk '{print $NF}' | grep -E '^/org/bluez/hci[0-9]+$' | sort -u)}")
    if (( ${#adapters[@]} == 0 )); then
      typeset -g __p10k_bt_cache_until=$((now + 5))
      return 1
    fi

    for adapter in "${adapters[@]}"; do
      if [[ "$(busctl get-property org.bluez "$adapter" org.bluez.Adapter1 Powered 2>/dev/null | awk '{print $2}')" == "true" ]]; then
        __p10k_bt_powered=1
        break
      fi
    done

    if (( __p10k_bt_powered == 1 )); then
      dev_paths=("${(@f)$(print -r -- "$tree" | awk '{print $NF}' | grep -E '^/org/bluez/hci[0-9]+/dev_[A-Fa-f0-9_]+$' | sort -u)}")
      for dev_path in "${dev_paths[@]}"; do
        connected="$(busctl get-property org.bluez "$dev_path" org.bluez.Device1 Connected 2>/dev/null | awk '{print $2}')"
        [[ "$connected" == "true" ]] && (( __p10k_bt_count++ ))
      done
    fi
  elif (( $+commands[bluetoothctl] )); then
    local controllers info_default c cinfo
    controllers=("${(@f)$(bluetoothctl list 2>/dev/null | awk '{print $2}')}")
    if (( ${#controllers[@]} == 0 )); then
      typeset -g __p10k_bt_cache_until=$((now + 5))
      return 1
    fi

    info_default="$(bluetoothctl show 2>/dev/null)"
    if [[ -n "$info_default" && "$info_default" == *'Powered: yes'* ]]; then
      __p10k_bt_powered=1
    else
      for c in "${controllers[@]}"; do
        cinfo="$(bluetoothctl show "$c" 2>/dev/null)"
        if [[ "$cinfo" == *'Powered: yes'* ]]; then
          __p10k_bt_powered=1
          break
        fi
      done
    fi
    __p10k_bt_count=$(bluetoothctl devices Connected 2>/dev/null | wc -l | tr -d ' ')
    [[ -n "$__p10k_bt_count" ]] || __p10k_bt_count=0
  else
    typeset -g __p10k_bt_cache_until=$((now + 5))
    return 1
  fi

  if (( __p10k_bt_powered == 0 )); then
    __p10k_bt_status=inactive
  elif (( __p10k_bt_count > 0 )); then
    __p10k_bt_status=connected
  else
    __p10k_bt_status=inactive
  fi
  typeset -g __p10k_bt_cache_available=1 __p10k_bt_cache_until=$((now + 5))
  return 0
}

# Finds the active interface via nmcli (preferred) or ip route, then classifies
# it as wifi or ethernet. For wifi, reads signal strength via iw. Results,
# including disconnected state, are cached for five seconds.
# Sets: __p10k_net_iface, __p10k_net_type (wifi/ethernet/wifi_off/off),
#        __p10k_net_rssi (dBm, wifi only), __p10k_net_status.
# Status (wifi): connected ≥-60dBm, warning -60–-70dBm, critical <-70dBm,
# error = disconnected. Status (ethernet): connected. wifi_off/off: error.
function _detect_network() {
  local sys_root="${NIRI_PLUS_SYS_ROOT:-/sys}"
  local -i now=${EPOCHSECONDS:-$SECONDS}
  if (( now < __p10k_net_cache_until )); then
    (( __p10k_net_cache_available )) && return 0 || return 1
  fi

  typeset -g __p10k_net_type= __p10k_net_rssi= __p10k_net_status=error __p10k_net_iface=
  typeset -g __p10k_net_cache_available=0

  local nm_connected_dev nm_type route dev link
  if (( $+commands[nmcli] )); then
    nm_connected_dev="$(nmcli -t -f DEVICE,STATE device 2>/dev/null | awk -F: '$2 ~ /^connected/ {print $1; exit}')"
    if [[ -n "$nm_connected_dev" ]]; then
      __p10k_net_iface="$nm_connected_dev"
      nm_type="$(nmcli -t -f DEVICE,TYPE device 2>/dev/null | awk -F: -v dev="$__p10k_net_iface" '$1==dev {print $2; exit}')"
      [[ -n "$nm_type" ]] && __p10k_net_type="$nm_type"
    fi
  fi

  if [[ -z "$__p10k_net_iface" ]] && (( $+commands[ip] )); then
    route="$(ip route get 1.1.1.1 2>/dev/null)"
    dev="$(print -r -- "$route" | sed -nE 's/.* dev ([^ ]+).*/\1/p')"
    [[ -n "$dev" ]] && __p10k_net_iface="$dev"
  fi

  if [[ -z "$__p10k_net_type" && -n "$__p10k_net_iface" ]]; then
    if [[ -d "$sys_root/class/net/$__p10k_net_iface/wireless" ]]; then
      __p10k_net_type=wifi
    elif (( $+commands[iw] )); then
      iw dev 2>/dev/null | awk '/Interface/ {print $2}' | grep -qx "$__p10k_net_iface" && __p10k_net_type=wifi
    fi
    [[ -z "$__p10k_net_type" ]] && __p10k_net_type=ethernet
  fi

  if [[ "$__p10k_net_type" == wifi ]]; then
    if ! (( $+commands[iw] )); then
      __p10k_net_status=connected
      typeset -g __p10k_net_cache_available=1 __p10k_net_cache_until=$((now + 5))
      return 0
    fi
    link="$(iw dev "$__p10k_net_iface" link 2>/dev/null)"
    if [[ "$link" == *Connected* ]]; then
      __p10k_net_rssi="$(print -r -- "$link" | sed -nE 's/.*signal: (-?[0-9]+).*/\1/p' | head -n1)"
      __p10k_net_status=connected
      [[ -n "$__p10k_net_rssi" ]] && { (( __p10k_net_rssi < -70 )) && __p10k_net_status=critical; (( __p10k_net_rssi >= -70 && __p10k_net_rssi < -60 )) && __p10k_net_status=warning; }
    else
      __p10k_net_type=wifi_off
      __p10k_net_status=error
    fi
    typeset -g __p10k_net_cache_available=1 __p10k_net_cache_until=$((now + 5))
    return 0
  fi

  if [[ "$__p10k_net_type" == ethernet ]]; then
    __p10k_net_status=connected
    typeset -g __p10k_net_cache_available=1 __p10k_net_cache_until=$((now + 5))
    return 0
  fi

  # No active connection: distinguish "wifi available but off" vs "no wifi"
  if (( $+commands[iw] )); then
    iw dev 2>/dev/null | awk '/Interface/ {print $2}' | grep -q . && __p10k_net_type=wifi_off
  else
    local n
    for n in "$sys_root"/class/net/*(N); do
      [[ -d "$n/wireless" ]] && __p10k_net_type=wifi_off && break
    done
  fi
  [[ -z "$__p10k_net_type" ]] && __p10k_net_type=off
  typeset -g __p10k_net_cache_available=1 __p10k_net_cache_until=$((now + 5))
  return 0
}

# Converts one battery's sysfs power fields to integer micro-watts. `power_now`
# is preferred; when it is unavailable or invalid, use abs(`current_now`) ×
# `voltage_now` with the kernel's µA/µV units. The result is returned through a
# global so callers do not fork a shell on every prompt refresh.
function _battery_power_uw() {
  local power_uw="${1:-}" current_ua="${2:-}" voltage_uv="${3:-}"
  typeset -g __p10k_power_uw=

  if [[ "$power_uw" == <-> ]]; then
    __p10k_power_uw=$power_uw
    return 0
  fi

  if [[ "$current_ua" == -<-> ]]; then
    current_ua=$(( -current_ua ))
  elif [[ "$current_ua" != <-> ]]; then
    return 1
  fi
  [[ "$voltage_uv" == <-> ]] && (( voltage_uv > 0 )) || return 1
  __p10k_power_uw=$(( current_ua * voltage_uv / 1000000 ))
}

# Formats a non-negative integer micro-watt total using the shared one-decimal,
# half-up contract. Values below 0.1W are hidden. The global output keeps this
# helper deterministic and cheap to call from the prompt renderer.
function _format_power_uw() {
  local total_uw="${1:-}" tenths
  typeset -g __p10k_power_str=
  [[ "$total_uw" == <-> ]] && (( total_uw >= 100000 )) || return 1
  tenths=$(( (total_uw + 50000) / 100000 ))
  __p10k_power_str="$(( tenths / 10 )).$(( tenths % 10 ))W"
}

# Scans /sys/class/power_supply/* for system-scope Battery entries. Returns 1
# if none found (no hardware, segment hidden). Power draw is summed across all
# usable batteries in raw micro-watts, using power_now or current×voltage.
# Device-scope peripheral batteries are excluded. AC state is checked via any
# usable non-battery supply's `online` file. Detection (including no battery
# hardware) is cached for five seconds.
# Sets: __p10k_bat_cap (0–100), __p10k_bat_charging (0/1),
#        __p10k_bat_power_uw (raw total or empty), __p10k_bat_power_str (X.YW
#        or empty), __p10k_bat_eta (time to charge limit/full or empty),
#        __p10k_bat_full (1 when charging and at 100%/Full), __p10k_bat_status.
# Status while discharging: normal ≥30%, warning 15–29%, critical <15%.
# Charging is its own green state; AC-connected holding/full is neutral.
# Display: "{W }{%}icon{ ETA}" — wattage and % hidden when full.
function _detect_battery() {
  local sys_root="${NIRI_PLUS_SYS_ROOT:-/sys}"
  local -i now=${EPOCHSECONDS:-$SECONDS}
  if (( now < __p10k_bat_cache_until )); then
    (( __p10k_bat_cache_available )) && return 0 || return 1
  fi

  typeset -g __p10k_bat_cap= __p10k_bat_charging=0 __p10k_bat_power_uw= __p10k_bat_power_str= __p10k_bat_eta= __p10k_bat_status=normal __p10k_bat_full=0
  typeset -g __p10k_bat_cache_available=0

  local -a power_supplies=("$sys_root"/class/power_supply/*(N))
  if (( ${#power_supplies[@]} == 0 )); then
    typeset -g __p10k_bat_cache_until=$((now + 5))
    return 1
  fi

  local s dev_type scope cap stat power_uw cur_ua volt_uv
  local charge_now_val charge_full_val energy_now_val energy_full_val eta_min delta rate_val
  local p p_type p_scope online ac_online end_threshold target_pct target_now target_reached
  local -i power_total_uw=0 power_complete=1 primary_found=0

  ac_online=0
  for p in "${power_supplies[@]}"; do
    [[ -d "$p" && -f "$p/online" ]] || continue
    p_type="$(_read_file_quiet "$p/type")" || continue
    [[ "$p_type" == "Battery" ]] && continue
    p_scope="$(_read_file_quiet "$p/scope")" || p_scope=
    [[ "${p_scope:l}" == device ]] && continue
    online="$(_read_file_quiet "$p/online")" || continue
    [[ "$online" == "1" ]] && ac_online=1 && break
  done

  for s in "${power_supplies[@]}"; do
    [[ -d "$s" ]] || continue
    dev_type="$(_read_file_quiet "$s/type")" || continue
    [[ "$dev_type" == "Battery" ]] || continue
    scope="$(_read_file_quiet "$s/scope")" || scope=
    [[ "${scope:l}" == device ]] && continue

    cap= power_uw= cur_ua= volt_uv=
    charge_now_val= charge_full_val= energy_now_val= energy_full_val= eta_min=
    delta= rate_val= end_threshold= target_now=
    target_pct=100
    target_reached=0

    cur_ua="$(_read_file_quiet "$s/current_now")" || cur_ua=
    volt_uv="$(_read_file_quiet "$s/voltage_now")" || volt_uv=
    power_uw="$(_read_file_quiet "$s/power_now")" || power_uw=

    if charge_now_val="$(_read_file_quiet "$s/charge_now")" && charge_full_val="$(_read_file_quiet "$s/charge_full")"; then
      :
    elif energy_now_val="$(_read_file_quiet "$s/energy_now")" && energy_full_val="$(_read_file_quiet "$s/energy_full")"; then
      :
    fi

    if cap="$(_read_file_quiet "$s/capacity")"; then
      :
    elif [[ -n "$charge_now_val" && -n "$charge_full_val" && "$charge_full_val" -gt 0 ]]; then
      cap=$(( 100 * charge_now_val / charge_full_val ))
    elif [[ -n "$energy_now_val" && -n "$energy_full_val" && "$energy_full_val" -gt 0 ]]; then
      cap=$(( 100 * energy_now_val / energy_full_val ))
    fi
    [[ "$cap" == <-> ]] && (( cap >= 0 && cap <= 100 )) || continue

    if _battery_power_uw "$power_uw" "$cur_ua" "$volt_uv"; then
      # Keep the effective value for the primary battery's energy-based ETA as
      # well as the aggregate display total.
      power_uw=$__p10k_power_uw
      power_total_uw=$(( power_total_uw + power_uw ))
    else
      power_complete=0
    fi

    stat=
    stat="$(_read_file_quiet "$s/status")" || stat=

    end_threshold="$(_read_file_quiet "$s/charge_control_end_threshold")" || end_threshold=
    if [[ -n "$end_threshold" && "$end_threshold" -gt 0 && "$end_threshold" -le 100 ]]; then
      target_pct=$end_threshold
    fi
    if [[ "$stat" == "Full" ]]; then
      target_reached=1
    elif (( ac_online == 1 )); then
      if [[ -n "$charge_now_val" && -n "$charge_full_val" && "$charge_full_val" -gt 0 ]]; then
        target_now=$(( (charge_full_val * target_pct + 99) / 100 ))
        (( charge_now_val >= target_now )) && target_reached=1
      elif [[ -n "$energy_now_val" && -n "$energy_full_val" && "$energy_full_val" -gt 0 ]]; then
        target_now=$(( (energy_full_val * target_pct + 99) / 100 ))
        (( energy_now_val >= target_now )) && target_reached=1
      elif (( cap >= target_pct )); then
        target_reached=1
      fi
    fi

    if (( primary_found == 0 )); then
      primary_found=1
      __p10k_bat_cap=$cap
      case "$stat" in
        Charging)
          __p10k_bat_status=charging
          ;;
        Discharging)
          __p10k_bat_status=normal
          (( cap < 30 )) && __p10k_bat_status=warning
          (( cap < 15 )) && __p10k_bat_status=critical
          ;;
        *)
          # Full and "Not charging" are AC holding states, not errors.
          __p10k_bat_status=normal
          ;;
      esac

      __p10k_bat_eta=
      if [[ "$stat" == "Charging" && "$target_reached" -eq 0 ]]; then
        if [[ -n "$charge_now_val" && -n "$charge_full_val" && -n "$cur_ua" ]]; then
          target_now=$(( (charge_full_val * target_pct + 99) / 100 ))
          delta=$(( target_now - charge_now_val ))
          rate_val=$cur_ua
        elif [[ -n "$energy_now_val" && -n "$energy_full_val" && -n "$power_uw" ]]; then
          target_now=$(( (energy_full_val * target_pct + 99) / 100 ))
          delta=$(( target_now - energy_now_val ))
          rate_val=$power_uw
        fi
      elif [[ "$stat" == "Discharging" ]]; then
        if [[ -n "$charge_now_val" && -n "$cur_ua" ]]; then
          delta=$charge_now_val
          rate_val=$cur_ua
        elif [[ -n "$energy_now_val" && -n "$power_uw" ]]; then
          delta=$energy_now_val
          rate_val=$power_uw
        fi
      fi
      if [[ -n "$delta" && -n "$rate_val" ]]; then
        (( rate_val < 0 )) && rate_val=$(( -rate_val ))
        (( delta > 0 && rate_val > 0 )) && eta_min=$(( (60 * delta + rate_val - 1) / rate_val ))
        [[ -n "$eta_min" ]] && __p10k_bat_eta="$(_format_duration_minutes "$eta_min")"
      fi

      # The kernel's Battery/Status is authoritative for the charging icon and
      # green charging color. AC online alone may mean holding at a charge
      # limit, which should remain neutral.
      __p10k_bat_charging=0
      [[ "$stat" == Charging ]] && __p10k_bat_charging=1

      __p10k_bat_full=0
      (( ac_online == 1 )) && { [[ "$stat" == "Full" ]] || (( cap >= 100 )); } && __p10k_bat_full=1
    fi
  done

  (( primary_found == 1 )) || { typeset -g __p10k_bat_cache_until=$((now + 5)); return 1; }
  if (( power_complete == 1 )); then
    typeset -g __p10k_bat_power_uw=$power_total_uw
    _format_power_uw "$power_total_uw" || true
    typeset -g __p10k_bat_power_str=$__p10k_power_str
  fi
  typeset -g __p10k_bat_cache_available=1 __p10k_bat_cache_until=$((now + 5))
  return 0
}

# --- Prompt segments (detect -> render) ---
# `time` is intentionally left to Powerlevel10k's built-in segment.  Its
# POWERLEVEL9K_TIME_FORMAT uses native zsh `%D{...}` expansion and therefore
# avoids a `date` subprocess on every one-second refresh.

function prompt_cpu() {
  _detect_cpu || return
  local color text
  _p10k_color_for "$__p10k_cpu_status" >/dev/null
  color=$__p10k_color
  # Lead with current frequency, then utilization, under one fixed CPU icon.
  text="󰍛"
  [[ -n "$__p10k_cpu_freq_str" ]] && text+=" ${__p10k_cpu_freq_str}"
  text+=" ${__p10k_cpu_pct}%%"
  p10k segment -f "$color" -i '' -t "$text"
}

function prompt_memory() {
  _detect_memory || return
  local color text
  _p10k_color_for "$__p10k_mem_status" >/dev/null
  color=$__p10k_color
  text="󰘚${(l:3:: :)__p10k_mem_pct}%%"
  p10k segment -f "$color" -i '' -t "$text"
}

function prompt_bluetooth() {
  _detect_bluetooth || return
  # Powered-off adapters are not failures and add no useful information.
  (( __p10k_bt_powered == 0 )) && return
  local color icon text
  _p10k_color_for "$__p10k_bt_status" >/dev/null
  color=$__p10k_color
  icon='󰂯'  # nf-md-bluetooth
  text="$icon"
  (( __p10k_bt_count > 0 )) && text="${__p10k_bt_count}${icon}"
  p10k segment -f "$color" -i '' -t "$text"
}

function prompt_network() {
  _detect_network || return
  local color icon text
  _p10k_color_for "$__p10k_net_status" >/dev/null
  color=$__p10k_color
  case "$__p10k_net_type" in
    wifi)
      icon="$(_wifi_icon "$__p10k_net_rssi")"
      ;;
    ethernet)
      icon='󰈀'
      ;;
    wifi_off)
      icon='󰤮'
      ;;
    off)
      icon='󰲜'
      ;;
    *)
      icon='󰤯'
      ;;
  esac
  # A following cell lets Kitty render the wide Wi-Fi strength glyph at full size.
  [[ "$__p10k_net_type" == wifi ]] && icon+=" "
  p10k segment -f "$color" -i '' -t "$icon"
}

function prompt_battery() {
  _detect_battery || return
  local color icon cap_str power_str eta_str text
  _p10k_color_for "$__p10k_bat_status" >/dev/null
  color=$__p10k_color
  icon="$(_battery_icon "$__p10k_bat_cap" "$__p10k_bat_charging")"
  cap_str=
  (( __p10k_bat_full == 0 )) && cap_str="${__p10k_bat_cap}%% "
  power_str=
  if [[ -n "${__p10k_bat_power_str:-}" ]]; then
    (( __p10k_bat_charging == 0 )) && power_str="${__p10k_bat_power_str} "
    (( __p10k_bat_charging == 1 && __p10k_bat_cap < 100 )) && power_str="${__p10k_bat_power_str} "
  fi
  eta_str=
  [[ -n "${__p10k_bat_eta:-}" ]] && eta_str="${__p10k_bat_eta} "
  text="${power_str}${eta_str}${cap_str}${icon}"
  p10k segment -f "$color" -i '' -t "$text"
}
