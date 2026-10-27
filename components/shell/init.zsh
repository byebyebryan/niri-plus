# Shared Niri Plus Zsh core. Sourcing this file only defines the public API.

function _niri_plus_shell_is_agent() {
  [[ -n "${ZSH_FORCE_FULL_PROMPT:-}" ]] && return 1
  [[ -n "${ZSH_FORCE_SIMPLE_PROMPT:-}" ]] && return 0

  local terminal_program="${TERM_PROGRAM:l}"
  local -a markers=(
    NIRI_PLUS_AGENT_TOOL
    CODEX_CI CODEX_THREAD_ID
    CLAUDE_PROJECT_DIR CLAUDE_ENV_FILE CLAUDE_CODE_REMOTE
    GEMINI_CLI GEMINI_CLI_IDE_SERVER_PORT GEMINI_CLI_IDE_WORKSPACE_PATH
    OPENCODE_CLIENT CURSOR_AGENT ANTIGRAVITY_AGENT
  )
  local marker
  for marker in "${markers[@]}"; do
    [[ -n "${(P)marker:-}" ]] && return 0
  done

  [[ "${CURSOR_AGENT:-}" == true ]] && return 0

  if [[ "$terminal_program" == vscode || "$terminal_program" == cursor || "$terminal_program" == antigravity ]]; then
    local -a ide_agent_markers=(
      VSCODE_COPILOT_CHAT_TOKEN VSCODE_COPILOT_INTEGRATION_ID
      GITHUB_COPILOT_CLI_MODE
      COPILOT_AGENT_JOB_ID COPILOT_AGENT_SESSION_ID COPILOT_AGENT_PROMPT
      CODEX_SHELL CODEX_INTERNAL_ORIGINATOR_OVERRIDE
    )
    for marker in "${ide_agent_markers[@]}"; do
      [[ -n "${(P)marker:-}" ]] && return 0
    done
    [[ "${CODEX_INTERNAL_ORIGINATOR_OVERRIDE:-}" == codex_vscode* ]] && return 0
  fi

  local -a compatibility_markers=(
    AGENT_TOOL_CALLING AI_AGENT_TOOL_CALLING
    VSCODE_AGENT_TOOL_CALLING CURSOR_AGENT_TOOL_CALLING ANTIGRAVITY_AGENT_TOOL_CALLING
  )
  for marker in "${compatibility_markers[@]}"; do
    [[ -n "${(P)marker:-}" ]] && return 0
  done

  if [[ "$terminal_program" == vscode || "$terminal_program" == cursor || "$terminal_program" == antigravity ]]; then
    [[ ! -t 0 || ! -t 1 || ! -t 2 ]] && return 0
  fi
  return 1
}

function _niri_plus_shell_init_history() {
  local history_file="${NIRI_PLUS_ZSH_HISTORY_FILE:-${XDG_STATE_HOME:-$HOME/.local/state}/zsh/history}"
  typeset -g ZSH_STATE_DIR="${history_file:h}"
  typeset -g NIRI_PLUS_ZSH_HISTORY_FILE="$history_file"
  typeset -g HISTFILE="$NIRI_PLUS_ZSH_HISTORY_FILE"
  HISTSIZE=100000
  SAVEHIST=100000
  mkdir -p -- "$ZSH_STATE_DIR"
  setopt HIST_IGNORE_DUPS HIST_IGNORE_ALL_DUPS HIST_EXPIRE_DUPS_FIRST
  setopt HIST_REDUCE_BLANKS HIST_VERIFY SHARE_HISTORY EXTENDED_HISTORY
}

function _niri_plus_shell_init_completion() {
  local cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/niri-plus-zsh"
  typeset -g NIRI_PLUS_ZSH_COMPDUMP="${NIRI_PLUS_ZSH_COMPDUMP:-$cache_dir/zcompdump-$ZSH_VERSION}"
  typeset -g ZSH_CACHE_DIR="${NIRI_PLUS_ZSH_COMPDUMP:h}"
  mkdir -p -- "$ZSH_CACHE_DIR"
  autoload -Uz compinit
  compinit -d "$NIRI_PLUS_ZSH_COMPDUMP"
  zstyle ':completion:*' menu select
  zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'
}

function _niri_plus_shell_source_if_readable() {
  [[ -r "$1" ]] && source "$1"
}

function _niri_plus_shell_init_watcher() {
  [[ -o interactive ]] || return 0

  autoload -Uz add-zle-hook-widget add-zsh-hook
  typeset -gi __RP_REFRESH_FD=-1

  function _rp_stop_timer() {
    if (( __RP_REFRESH_FD >= 0 )); then
      zle -F "$__RP_REFRESH_FD" 2>/dev/null
      { exec {__RP_REFRESH_FD}<&-; } 2>/dev/null
      __RP_REFRESH_FD=-1
    fi
  }

  function _rp_on_tick() {
    local tick
    if ! IFS= read -r tick <&"$1"; then
      _rp_stop_timer
      return
    fi
    if (( $+functions[_p9k_set_prompt] )); then
      local _p9k__refresh_reason=precmd
      _p9k_set_prompt
    fi
    zle .reset-prompt 2>/dev/null || zle reset-prompt
  }

  function _rp_start_timer() {
    local interval="${ZSH_RIGHT_PROMPT_REFRESH_INTERVAL:-1}"
    [[ "${NIRI_PLUS_SHELL_MODE:-}" == human ]] || return 0
    (( __RP_REFRESH_FD >= 0 )) && return
    exec {__RP_REFRESH_FD}< <(
      while true; do
        sleep "$interval" || break
        print -r -- . || break
      done
    )
    zle -F "$__RP_REFRESH_FD" _rp_on_tick
  }

  function _rp_line_init() { _rp_start_timer }
  function _rp_line_finish() { _rp_stop_timer }

  add-zle-hook-widget -d line-init _rp_line_init 2>/dev/null
  add-zle-hook-widget -d line-finish _rp_line_finish 2>/dev/null
  add-zle-hook-widget line-init _rp_line_init
  add-zle-hook-widget line-finish _rp_line_finish
  add-zsh-hook -d zshexit _rp_stop_timer 2>/dev/null
  add-zsh-hook zshexit _rp_stop_timer
}

function _niri_plus_shell_stop_watcher() {
  if (( $+functions[_rp_stop_timer] )); then
    _rp_stop_timer
  fi

  if (( $+functions[add-zle-hook-widget] )); then
    add-zle-hook-widget -d line-init _rp_line_init 2>/dev/null
    add-zle-hook-widget -d line-finish _rp_line_finish 2>/dev/null
  fi
  if (( $+functions[add-zsh-hook] )); then
    add-zsh-hook -d zshexit _rp_stop_timer 2>/dev/null
  fi
}

function niri_plus_shell_init() {
  local init_file="${functions_source[niri_plus_shell_init]:-}"
  local agent_history="${NIRI_PLUS_ZSH_AGENT_HISTORY:-skip}"
  local mode

  if [[ -z "$init_file" ]]; then
    print -u2 -r -- "niri_plus_shell_init: cannot locate the sourced init.zsh"
    return 2
  fi
  case "$agent_history" in
    skip|legacy) ;;
    *)
      print -u2 -r -- "niri_plus_shell_init: NIRI_PLUS_ZSH_AGENT_HISTORY must be skip or legacy"
      return 2
      ;;
  esac

  typeset -g NIRI_PLUS_ZSH_HOME="${init_file:A:h}"
  if _niri_plus_shell_is_agent; then
    mode=agent
  else
    mode=human
  fi
  typeset -g +x NIRI_PLUS_SHELL_MODE
  typeset -g NIRI_PLUS_SHELL_MODE="$mode"

  if [[ "$mode" == agent ]]; then
    _niri_plus_shell_stop_watcher
    unset __NIRI_PLUS_SHELL_FINISHED
    PROMPT='%m%# '
    RPROMPT=
    if [[ "$agent_history" == legacy ]]; then
      _niri_plus_shell_init_history
    fi
    typeset -g __NIRI_PLUS_SHELL_INITIALIZED_MODE=agent
    return 0
  fi

  if [[ "${__NIRI_PLUS_SHELL_INITIALIZED_MODE:-}" == human ]]; then
    return 0
  fi
  unset __NIRI_PLUS_SHELL_FINISHED
  _niri_plus_shell_init_history

  if (( $+functions[niri_plus_shell_pre_init] )); then
    niri_plus_shell_pre_init
  fi

  local plugin_root="${NIRI_PLUS_ZSH_PLUGIN_DIR:-$NIRI_PLUS_ZSH_HOME/plugins}"
  local theme_root="${NIRI_PLUS_ZSH_THEME_DIR:-$plugin_root}"
  typeset -g NIRI_PLUS_ZSH_PLUGIN_DIR="$plugin_root"
  typeset -g NIRI_PLUS_ZSH_THEME_DIR="$theme_root"
  typeset -g ZSH_PLUGIN_DIR="$NIRI_PLUS_ZSH_PLUGIN_DIR"
  typeset -g ZSH_THEME_DIR="$NIRI_PLUS_ZSH_THEME_DIR"

  _niri_plus_shell_init_completion

  _niri_plus_shell_source_if_readable "$NIRI_PLUS_ZSH_PLUGIN_DIR/zsh-autosuggestions/zsh-autosuggestions.zsh"
  _niri_plus_shell_source_if_readable "$NIRI_PLUS_ZSH_PLUGIN_DIR/zsh-history-substring-search/zsh-history-substring-search.zsh"
  _niri_plus_shell_source_if_readable "$NIRI_PLUS_ZSH_THEME_DIR/powerlevel10k/powerlevel10k.zsh-theme"

  bindkey -e
  bindkey '^[[A' history-substring-search-up
  bindkey '^[[B' history-substring-search-down

  _niri_plus_shell_source_if_readable "$NIRI_PLUS_ZSH_HOME/p10k.zsh"
  _niri_plus_shell_init_watcher
  typeset -g __NIRI_PLUS_SHELL_INITIALIZED_MODE=human
}

function niri_plus_shell_finish() {
  [[ "${NIRI_PLUS_SHELL_MODE:-}" == human ]] || return 0
  [[ "${__NIRI_PLUS_SHELL_INITIALIZED_MODE:-}" == human ]] || return 0
  [[ "${__NIRI_PLUS_SHELL_FINISHED:-}" == 1 ]] && return 0

  if (( $+commands[zoxide] )); then
    eval "$(zoxide init zsh)"
  fi

  if (( $+commands[fzf] )); then
    local fzf_init
    fzf_init="$(fzf --zsh 2>/dev/null)" || fzf_init=
    [[ -n "$fzf_init" ]] && eval "$fzf_init"
  fi

  _niri_plus_shell_source_if_readable "$NIRI_PLUS_ZSH_PLUGIN_DIR/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
  typeset -g __NIRI_PLUS_SHELL_FINISHED=1
}
