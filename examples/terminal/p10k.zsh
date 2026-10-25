# Niri Plus portable adaptation of the selected Powerlevel10k configuration.

'builtin' 'local' '-a' 'p10k_config_opts'
[[ ! -o 'aliases'         ]] || p10k_config_opts+=('aliases')
[[ ! -o 'sh_glob'         ]] || p10k_config_opts+=('sh_glob')
[[ ! -o 'no_brace_expand' ]] || p10k_config_opts+=('no_brace_expand')
'builtin' 'setopt' 'no_aliases' 'no_sh_glob' 'brace_expand'

() {
  emulate -L zsh -o extended_glob

  # Allow reloading this file without stale values.
  unset -m '(POWERLEVEL9K_*|DEFAULT_USER)~POWERLEVEL9K_GITSTATUS_DIR'

  [[ $ZSH_VERSION == (5.<1->*|<6->.*) ]] || return

  # Left prompt: keep only what you care about.
  typeset -g POWERLEVEL9K_LEFT_PROMPT_ELEMENTS=(
    context
    dir_joined
    vcs
    newline
    prompt_char
  )

  # Right prompt: custom runtime status segments.
  typeset -g POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS=(
    time
    cpu
    memory
    bluetooth
    network
    battery
  )

  typeset -g POWERLEVEL9K_MODE=nerdfont-v3
  typeset -g POWERLEVEL9K_ICON_PADDING=none

  # Lean style.
  typeset -g POWERLEVEL9K_BACKGROUND=
  typeset -g POWERLEVEL9K_{LEFT,RIGHT}_{LEFT,RIGHT}_WHITESPACE=
  typeset -g POWERLEVEL9K_{LEFT,RIGHT}_SUBSEGMENT_SEPARATOR=' '
  typeset -g POWERLEVEL9K_{LEFT,RIGHT}_SEGMENT_SEPARATOR=
  typeset -g POWERLEVEL9K_ICON_BEFORE_CONTENT=true
  # Native zsh prompt expansion; avoids spawning `date` on every refresh.
  typeset -g POWERLEVEL9K_TIME_FORMAT='%D{%H:%M:%S}'
  typeset -g POWERLEVEL9K_TIME_FOREGROUND=7

  # Multiline prompt without separators.
  typeset -g POWERLEVEL9K_PROMPT_ADD_NEWLINE=true
  typeset -g POWERLEVEL9K_MULTILINE_FIRST_PROMPT_PREFIX=
  typeset -g POWERLEVEL9K_MULTILINE_NEWLINE_PROMPT_PREFIX=
  typeset -g POWERLEVEL9K_MULTILINE_LAST_PROMPT_PREFIX=
  typeset -g POWERLEVEL9K_MULTILINE_FIRST_PROMPT_SUFFIX=
  typeset -g POWERLEVEL9K_MULTILINE_NEWLINE_PROMPT_SUFFIX=
  typeset -g POWERLEVEL9K_MULTILINE_LAST_PROMPT_SUFFIX=
  typeset -g POWERLEVEL9K_LEFT_PROMPT_FIRST_SEGMENT_START_SYMBOL=
  typeset -g POWERLEVEL9K_RIGHT_PROMPT_LAST_SEGMENT_END_SYMBOL=
  typeset -g POWERLEVEL9K_MULTILINE_FIRST_PROMPT_GAP_CHAR=' '

  # Prompt character style. p10k names 0-7 are reliable; 8-15 uses numeric indices.
  typeset -g POWERLEVEL9K_PROMPT_CHAR_OK_{VIINS,VICMD,VIVIS,VIOWR}_FOREGROUND=2     # selected green
  typeset -g POWERLEVEL9K_PROMPT_CHAR_ERROR_{VIINS,VICMD,VIVIS,VIOWR}_FOREGROUND=9  # bright red
  typeset -g POWERLEVEL9K_PROMPT_CHAR_{OK,ERROR}_VIINS_CONTENT_EXPANSION='❯'
  typeset -g POWERLEVEL9K_PROMPT_CHAR_{OK,ERROR}_VICMD_CONTENT_EXPANSION='❮'
  typeset -g POWERLEVEL9K_PROMPT_CHAR_{OK,ERROR}_VIVIS_CONTENT_EXPANSION='Ⅴ'
  typeset -g POWERLEVEL9K_PROMPT_CHAR_{OK,ERROR}_VIOWR_CONTENT_EXPANSION='▶'
  typeset -g POWERLEVEL9K_PROMPT_CHAR_OVERWRITE_STATE=true
  typeset -g POWERLEVEL9K_PROMPT_CHAR_LEFT_PROMPT_LAST_SEGMENT_END_SYMBOL=

  # Context + directory + VCS tuning. Numeric colors are xterm indexes.
  # `dir_joined` is Powerlevel10k's zero-gap variant: context's trailing colon
  # is immediately followed by the directory (for example `starship:~`).
  typeset -g POWERLEVEL9K_ALWAYS_SHOW_CONTEXT=true
  typeset -g POWERLEVEL9K_CONTEXT_FOREGROUND=7
  typeset -g POWERLEVEL9K_CONTEXT_DEFAULT_FOREGROUND=7
  typeset -g POWERLEVEL9K_CONTEXT_REMOTE_FOREGROUND=3
  typeset -g POWERLEVEL9K_CONTEXT_SUDO_FOREGROUND=9
  typeset -g POWERLEVEL9K_CONTEXT_ROOT_FOREGROUND=9
  typeset -g POWERLEVEL9K_CONTEXT_REMOTE_SUDO_FOREGROUND=9
  typeset -g POWERLEVEL9K_CONTEXT_TEMPLATE='%m:'
  typeset -g POWERLEVEL9K_CONTEXT_DEFAULT_TEMPLATE='%m:'
  typeset -g POWERLEVEL9K_CONTEXT_REMOTE_TEMPLATE='%n@%m:'
  typeset -g POWERLEVEL9K_CONTEXT_SUDO_TEMPLATE='%n@%m:'
  typeset -g POWERLEVEL9K_CONTEXT_ROOT_TEMPLATE='%n@%m:'
  typeset -g POWERLEVEL9K_CONTEXT_REMOTE_SUDO_TEMPLATE='%n@%m:'
  typeset -g POWERLEVEL9K_CONTEXT_VISUAL_IDENTIFIER_EXPANSION=
  typeset -g POWERLEVEL9K_CONTEXT_{DEFAULT,SUDO,ROOT,REMOTE,REMOTE_SUDO}_VISUAL_IDENTIFIER_EXPANSION=
  typeset -g POWERLEVEL9K_DIR_FOREGROUND=4               # selected blue
  typeset -g POWERLEVEL9K_DIR_VISUAL_IDENTIFIER_EXPANSION=
  typeset -g POWERLEVEL9K_DIR_SHORTEN_STRATEGY=truncate_to_unique
  typeset -g POWERLEVEL9K_DIR_SHORTENED_FOREGROUND=4     # selected blue
  typeset -g POWERLEVEL9K_DIR_ANCHOR_FOREGROUND=4        # selected blue
  typeset -g POWERLEVEL9K_DIR_ANCHOR_BOLD=true
  typeset -g POWERLEVEL9K_VCS_FOREGROUND=7               # secondary neutral fallback
  typeset -g POWERLEVEL9K_VCS_CLEAN_FOREGROUND=2         # clean
  typeset -g POWERLEVEL9K_VCS_MODIFIED_FOREGROUND=3      # staged/unstaged changes
  typeset -g POWERLEVEL9K_VCS_UNTRACKED_FOREGROUND=6     # untracked files
  typeset -g POWERLEVEL9K_VCS_CONFLICTED_FOREGROUND=1    # conflicts
  typeset -g POWERLEVEL9K_VCS_CONFLICTED_STATE=true
  # gitstatusd styles each compact field with STATE+FORMAT foregrounds.  Keep
  # every field in a state semantically colored (not a green wall).
  typeset -g POWERLEVEL9K_VCS_CLEAN_{COMMIT,BRANCH,TAG,ACTION,REMOTE_BRANCH,DIRTY,STAGED,UNSTAGED,UNTRACKED,INCOMING_CHANGES,OUTGOING_CHANGES,STASH}FORMAT_FOREGROUND=2
  typeset -g POWERLEVEL9K_VCS_MODIFIED_{COMMIT,BRANCH,TAG,ACTION,REMOTE_BRANCH,DIRTY,STAGED,UNSTAGED,UNTRACKED,INCOMING_CHANGES,OUTGOING_CHANGES,STASH}FORMAT_FOREGROUND=3
  typeset -g POWERLEVEL9K_VCS_UNTRACKED_{COMMIT,BRANCH,TAG,ACTION,REMOTE_BRANCH,DIRTY,STAGED,UNSTAGED,UNTRACKED,INCOMING_CHANGES,OUTGOING_CHANGES,STASH}FORMAT_FOREGROUND=6
  typeset -g POWERLEVEL9K_VCS_CONFLICTED_{COMMIT,BRANCH,TAG,ACTION,REMOTE_BRANCH,DIRTY,STAGED,UNSTAGED,UNTRACKED,INCOMING_CHANGES,OUTGOING_CHANGES,STASH}FORMAT_FOREGROUND=1
  typeset -g POWERLEVEL9K_VCS_VISUAL_IDENTIFIER_EXPANSION=
  typeset -g POWERLEVEL9K_VCS_BRANCH_ICON=
  typeset -g POWERLEVEL9K_VCS_GIT_ICON=
  typeset -g POWERLEVEL9K_VCS_LOADING_TEXT=''
  # Manual VCS icons with spacing (padding=none causes touching)
  typeset -g POWERLEVEL9K_VCS_OUTGOING_CHANGES_ICON='↑'
  typeset -g POWERLEVEL9K_VCS_INCOMING_CHANGES_ICON='↓'
  typeset -g POWERLEVEL9K_VCS_STAGED_ICON='+'
  typeset -g POWERLEVEL9K_VCS_UNSTAGED_ICON='!'
  typeset -g POWERLEVEL9K_VCS_UNTRACKED_ICON='?'
  typeset -g POWERLEVEL9K_VCS_STASH_ICON='*'
  typeset -g POWERLEVEL9K_VCS_CONFLICT_ICON='~'

  # Custom segment implementations live outside this file.
  local custom_segments="$NIRI_PLUS_ZSH_HOME/p10k-custom-segments.zsh"
  [[ -r "$custom_segments" ]] && source "$custom_segments"

  typeset -g POWERLEVEL9K_TRANSIENT_PROMPT=always
  typeset -g POWERLEVEL9K_INSTANT_PROMPT=off
  typeset -g POWERLEVEL9K_DISABLE_HOT_RELOAD=true

  (( ! $+functions[p10k] )) || p10k reload
}

# Tell `p10k configure` which file it should overwrite.
typeset -g POWERLEVEL9K_CONFIG_FILE=${${(%):-%x}:a}

(( ${#p10k_config_opts} )) && setopt ${p10k_config_opts[@]}
'builtin' 'unset' 'p10k_config_opts'
