#!/usr/bin/env python3
"""Run isolated checks for the portable terminal and desktop utility examples."""
from __future__ import annotations

import configparser
import json
import os
from pathlib import Path
import pty
import select
import shutil
import signal
import socket
import subprocess
import tempfile
import time
from unittest import mock
import types


ROOT = Path(__file__).resolve().parents[1]
TERMINAL = ROOT / "examples/terminal"
DESKTOP = ROOT / "examples/desktop"
TEST_COMPLETION_FPATH = ""
TEST_COMPLETION_FPATH_ROOT = Path()
TEST_COMPINIT_PATH = Path()
TEST_COMPAUDIT_PATH = Path()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(path.read_text(), str(path), "exec"), module.__dict__)
    return module


def put(path: Path, text: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    if executable:
        path.chmod(0o755)


def expose_zsh_audit_commands(path: Path) -> None:
    """Keep distro compinit's security audit usable in restricted PATH tests."""
    for name in ("getent", "grep"):
        command = shutil.which(name)
        require(command is not None, f"{name} is required by the system Zsh completion audit")
        link = path / name
        if not link.exists():
            link.symlink_to(command)


def prepare_zsh_completion_fpath(zsh: str, destination: Path) -> tuple[str, Path, Path, Path]:
    """Copy trusted completion and hook functions into a private, audited fpath."""
    probe_env = os.environ.copy()
    probe_env.pop("FPATH", None)
    probe_code = '''
autoload -Uz compinit compaudit compdump add-zle-hook-widget add-zsh-hook
autoload +X compinit compaudit compdump add-zle-hook-widget add-zsh-hook
for function_name in compinit compaudit compdump add-zle-hook-widget add-zsh-hook; do
  print -r -- "$function_name=$functions_source[$function_name]"
done
'''
    probe = subprocess.run(
        [zsh, "-dfc", probe_code],
        text=True,
        capture_output=True,
        env=probe_env,
        timeout=10,
    )
    require(probe.returncode == 0, f"could not locate trusted Zsh completion functions: {probe.stderr}")
    sources = {}
    for line in probe.stdout.splitlines():
        name, separator, path = line.partition("=")
        if separator:
            sources[name] = Path(path).resolve()
    required = ("compinit", "compaudit", "compdump", "add-zle-hook-widget", "add-zsh-hook")
    for name in required:
        require(name in sources and sources[name].is_file(), f"trusted Zsh function source was not identified: {name}")

    source_roots = []
    for name in required:
        source = sources[name]
        if source.parent not in source_roots:
            source_roots.append(source.parent)
    for source_root in source_roots:
        require(source_root.stat().st_uid == 0, f"Zsh completion source is not system-owned: {source_root}")
        for path in (source_root, *source_root.rglob("*")):
            metadata = path.stat()
            require(metadata.st_uid == 0, f"Zsh function source is not system-owned: {path}")
            require(not (metadata.st_mode & 0o022), f"Zsh function source is writable by group/others: {path}")
        source_dir = source_root
        while source_dir != source_dir.parent:
            metadata = source_dir.stat()
            require(metadata.st_uid == 0, f"Zsh completion source parent is not system-owned: {source_dir}")
            require(not (metadata.st_mode & 0o022), f"Zsh completion source parent is writable by group/others: {source_dir}")
            source_dir = source_dir.parent

    destination.mkdir(mode=0o700, parents=True)
    destination.chmod(0o700)
    copied_roots = {}
    for index, source_root in enumerate(source_roots):
        target_root = destination / f"{index:02d}-{source_root.name}"
        shutil.copytree(source_root, target_root)
        copied_roots[source_root] = target_root
    fpath_dirs = []
    for source_root in source_roots:
        target_root = copied_roots[source_root]
        tree_paths = [target_root, *target_root.rglob("*")]
        for path in tree_paths:
            if path.is_dir():
                path.chmod(0o700)
                fpath_dirs.append(path)
            elif path.is_file():
                path.chmod(path.stat().st_mode & ~0o022)

    return (
        os.pathsep.join(str(path) for path in fpath_dirs),
        destination,
        copied_roots[sources["compinit"].parent] / "compinit",
        copied_roots[sources["compaudit"].parent] / "compaudit",
    )


def isolated_zsh_env(env: dict[str, str], *, ambient_fpath: str | None = None) -> dict[str, str]:
    if not TEST_COMPLETION_FPATH:
        return env
    return env | {
        "FPATH": ambient_fpath or TEST_COMPLETION_FPATH,
        "NIRI_PLUS_TEST_COMPLETION_FPATH": TEST_COMPLETION_FPATH,
        "NIRI_PLUS_TEST_COMPLETION_FPATH_ROOT": str(TEST_COMPLETION_FPATH_ROOT),
        "NIRI_PLUS_TEST_COMPINIT_PATH": str(TEST_COMPINIT_PATH),
        "NIRI_PLUS_TEST_COMPAUDIT_PATH": str(TEST_COMPAUDIT_PATH),
    }


def zsh_run(
    zsh: str,
    code: str,
    env: dict[str, str],
    *,
    ambient_fpath: str | None = None,
) -> subprocess.CompletedProcess[str]:
    isolated_env = isolated_zsh_env(env, ambient_fpath=ambient_fpath)
    if TEST_COMPLETION_FPATH:
        code = 'fpath=("${(@s.:.)NIRI_PLUS_TEST_COMPLETION_FPATH}")\n' + code
    result = subprocess.run([zsh, "-c", code], text=True, capture_output=True, env=isolated_env, timeout=20)
    if result.returncode:
        raise AssertionError(f"zsh failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
    return result


def check_isolated_completion_fpath(zsh: str, bundle: Path, home: Path, xdg: Path) -> int:
    unsafe_fpath = bundle / "insecure-ambient-fpath"
    unsafe_fpath.mkdir(mode=0o777)
    unsafe_fpath.chmod(0o777)
    require(unsafe_fpath.stat().st_mode & 0o022 != 0, "ambient fpath regression fixture is not writable by group/others")
    env = os.environ.copy() | {
        "HOME": str(home),
        "XDG_STATE_HOME": str(xdg / "audit-state"),
        "XDG_CACHE_HOME": str(xdg / "audit-cache"),
        "NIRI_PLUS_TEST_UNSAFE_FPATH": str(unsafe_fpath),
        "ZSH_FORCE_FULL_PROMPT": "1",
    }
    code = f'''source "{TERMINAL / 'init.zsh'}"
niri_plus_shell_init
(( $+functions[compdef] == 1 )) || exit 71
(( $+functions[compaudit] == 1 )) || exit 72
[[ "$functions_source[compinit]" == "$NIRI_PLUS_TEST_COMPINIT_PATH" ]] || exit 73
[[ "$functions_source[compaudit]" == "$NIRI_PLUS_TEST_COMPAUDIT_PATH" ]] || exit 74
(( ${{fpath[(Ie)$NIRI_PLUS_TEST_UNSAFE_FPATH]}} == 0 )) || exit 75
for directory in $fpath; do
  [[ "$directory" == "$NIRI_PLUS_TEST_COMPLETION_FPATH_ROOT"/* ]] || exit 76
done
compaudit >/dev/null 2>&1 || exit 77
print -r -- ISOLATED_COMPAUDIT_OK
'''
    result = zsh_run(zsh, code, env, ambient_fpath=str(unsafe_fpath))
    require("ISOLATED_COMPAUDIT_OK" in result.stdout, "isolated completion fpath did not retain the normal compaudit")
    return 7


def wait_for_shell(pid: int, fd: int, timeout: float) -> bytes:
    output = bytearray()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            finished, status = os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            return bytes(output)
        if finished:
            return bytes(output)
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            try:
                chunk = os.read(fd, 8192)
            except OSError:
                chunk = b""
            if chunk:
                output.extend(chunk)
    raise TimeoutError("interactive Zsh did not exit")


def check_interactive_watcher(zsh: str, bundle: Path, home: Path, xdg: Path) -> int:
    install = bundle / "interactive"
    install.mkdir(parents=True)
    for name in ("zshrc", "init.zsh", "p10k.zsh", "p10k-custom-segments.zsh"):
        shutil.copyfile(TERMINAL / name, install / name)
    for directory, file, label in (
        ("zsh-autosuggestions", "zsh-autosuggestions.zsh", "autosuggestions"),
        ("zsh-history-substring-search", "zsh-history-substring-search.zsh", "substring"),
        ("zsh-syntax-highlighting", "zsh-syntax-highlighting.zsh", "syntax"),
        ("powerlevel10k", "powerlevel10k.zsh-theme", "powerlevel10k"),
    ):
        path = install / "plugins" / directory / file
        content = f'print -r -- {label} >> "$NIRI_PLUS_TEST_PLUGIN_ORDER"\n'
        if label == "powerlevel10k":
            content += "function p10k { : }\n"
        put(path, content)
    (install / ".zshrc").write_text(
        f'''fpath=("${{(@s.:.)NIRI_PLUS_TEST_COMPLETION_FPATH}}")
function niri_plus_shell_pre_init() {{ print -r -- pre >> "$NIRI_PLUS_TEST_PLUGIN_ORDER"; }}
source "{install / 'zshrc'}"
niri_plus_shell_init
niri_plus_shell_finish
'''
    )

    test_bin = bundle / "interactive-bin"
    test_bin.mkdir()
    expose_zsh_audit_commands(test_bin)
    mkdir = shutil.which("mkdir")
    mv = shutil.which("mv")
    sleep = shutil.which("sleep")
    require(mkdir is not None and mv is not None and sleep is not None, "mkdir, mv, and sleep are required for watcher test")
    (test_bin / "mkdir").symlink_to(mkdir)
    (test_bin / "mv").symlink_to(mv)
    put(
        test_bin / "sleep",
        "#!/bin/sh\nprintf '%s\\n' \"$$\" >> \"$NIRI_PLUS_TEST_SLEEP_PID_FILE\"\nexec "
        + sleep
        + ' "$@"\n',
        executable=True,
    )
    put(
        test_bin / "zoxide",
        "#!/bin/sh\nprintf '%s\\n' zoxide >> \"$NIRI_PLUS_TEST_PLUGIN_ORDER\"\nprintf '%s\\n' 'typeset -g NIRI_PLUS_TEST_ZOXIDE=1'\n",
        executable=True,
    )
    put(
        test_bin / "fzf",
        "#!/bin/sh\n[ \"$1\" = --zsh ] && { printf '%s\\n' fzf >> \"$NIRI_PLUS_TEST_PLUGIN_ORDER\"; printf '%s\\n' 'typeset -g NIRI_PLUS_TEST_FZF=1'; }\n",
        executable=True,
    )
    sleep_log = bundle / "sleep-pids"
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "ZDOTDIR": str(install),
            "XDG_CONFIG_HOME": str(xdg / "config"),
            "XDG_STATE_HOME": str(xdg / "state-interactive"),
            "XDG_CACHE_HOME": str(xdg / "cache-interactive"),
            "PATH": str(test_bin),
            "ZSH_RIGHT_PROMPT_REFRESH_INTERVAL": "0.08",
            "ZSH_FORCE_FULL_PROMPT": "1",
            "NIRI_PLUS_TEST_PLUGIN_ORDER": str(bundle / "interactive-plugin-order"),
            "NIRI_PLUS_TEST_SLEEP_PID_FILE": str(sleep_log),
        }
    )
    pid, fd = pty.fork()
    if pid == 0:
        os.execvpe(zsh, [zsh, "-d", "-i"], isolated_zsh_env(env))
    output = bytearray()
    try:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and not sleep_log.exists():
            ready, _, _ = select.select([fd], [], [], 0.1)
            if ready:
                try:
                    output.extend(os.read(fd, 8192))
                except OSError:
                    break
        require(sleep_log.exists(), f"interactive prompt did not start refresh worker: {output.decode(errors='replace')}")
        os.write(fd, b"print -r -- NIRI_PLUS_TEST_READY\n")
        marker_deadline = time.monotonic() + 5
        while time.monotonic() < marker_deadline and b"NIRI_PLUS_TEST_READY" not in output:
            ready, _, _ = select.select([fd], [], [], 0.1)
            if ready:
                try:
                    output.extend(os.read(fd, 8192))
                except OSError:
                    break
        require(b"NIRI_PLUS_TEST_READY" in output, "interactive shell did not accept a test command")
        os.write(fd, b"exit\n")
        output.extend(wait_for_shell(pid, fd, 8))
        pid = -1
    finally:
        if pid > 0:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass
        try:
            os.close(fd)
        except OSError:
            pass

    order = (bundle / "interactive-plugin-order").read_text().splitlines()
    require(
        order == ["pre", "autosuggestions", "substring", "powerlevel10k", "zoxide", "fzf", "syntax"],
        f"interactive starter or repeated init/finish changed order or ran twice: {order}",
    )
    pids = {int(value) for value in sleep_log.read_text().splitlines() if value.isdigit()}
    require(bool(pids), "refresh watcher never launched its timer")
    deadline = time.monotonic() + 3
    alive = set(pids)
    while alive and time.monotonic() < deadline:
        alive = set()
        for child_pid in pids:
            try:
                os.kill(child_pid, 0)
            except ProcessLookupError:
                continue
            # A process that has exited but has not yet been reaped can appear
            # as a zombie; only a running timer is a leaked watcher.
            status = Path(f"/proc/{child_pid}/stat")
            if status.exists() and status.read_text().split()[2] == "Z":
                continue
            alive.add(child_pid)
        if alive:
            time.sleep(0.05)
    require(not alive, f"refresh timer process remained after shell exit: {sorted(alive)}")
    return len(pids)


def pty_read_until(fd: int, marker: bytes, timeout: float, context: str) -> bytes:
    output = bytearray()
    deadline = time.monotonic() + timeout
    while marker not in output and time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.1)
        if not ready:
            continue
        try:
            chunk = os.read(fd, 8192)
        except OSError:
            break
        if not chunk:
            break
        output.extend(chunk)
    require(marker in output, f"{context}: {output.decode(errors='replace')}")
    return bytes(output)


def sleep_log_count(path: Path) -> int:
    return len(path.read_text().splitlines()) if path.exists() else 0


def wait_for_sleep_log_growth(path: Path, previous_count: int, context: str) -> int:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        count = sleep_log_count(path)
        if count > previous_count:
            return count
        time.sleep(0.05)
    raise AssertionError(f"{context}: refresh watcher did not start")


def require_sleep_log_stable(path: Path, context: str) -> int:
    time.sleep(0.25)
    first = sleep_log_count(path)
    time.sleep(0.25)
    second = sleep_log_count(path)
    require(first == second, f"{context}: watcher restarted in agent mode ({first} -> {second})")
    return second


def check_watcher_mode_transitions(zsh: str, bundle: Path, home: Path, xdg: Path) -> int:
    install = bundle / "watcher-transitions"
    install.mkdir()
    shutil.copyfile(TERMINAL / "init.zsh", install / "init.zsh")
    (install / "p10k.zsh").write_text("# isolated watcher transition fixture\n")
    plugin_root = install / "plugins"
    finish_log = bundle / "transition-finish-log"
    put(
        plugin_root / "zsh-syntax-highlighting" / "zsh-syntax-highlighting.zsh",
        'print -r -- finish >> "$NIRI_PLUS_TEST_FINISH_LOG"\n',
    )

    test_bin = bundle / "transition-bin"
    test_bin.mkdir()
    expose_zsh_audit_commands(test_bin)
    mkdir = shutil.which("mkdir")
    mv = shutil.which("mv")
    sleep = shutil.which("sleep")
    require(mkdir is not None and mv is not None and sleep is not None, "mkdir, mv, and sleep are required for watcher transition checks")
    (test_bin / "mkdir").symlink_to(mkdir)
    (test_bin / "mv").symlink_to(mv)
    put(
        test_bin / "sleep",
        "#!/bin/sh\nprintf '%s\\n' \"$$\" >> \"$NIRI_PLUS_TEST_SLEEP_PID_FILE\"\nexec "
        + sleep
        + ' "$@"\n',
        executable=True,
    )

    (install / ".zshrc").write_text(
        f'''fpath=("${{(@s.:.)NIRI_PLUS_TEST_COMPLETION_FPATH}}")
function niri_plus_test_hook_count() {{
  local hook_type="$1" function_name="$2" hook
  local -a hooks=()
  local -i count=0
  zstyle -a "zle-$hook_type" widgets hooks 2>/dev/null || hooks=()
  for hook in "${{hooks[@]}}"; do
    [[ "${{hook#*:}}" == "$function_name" ]] && (( ++count ))
  done
  print -r -- "$count"
}}
function precmd() {{ print -r -- NIRI_PLUS_TRANSITION_PROMPT_READY; }}
source "{install / 'init.zsh'}"
ZSH_FORCE_FULL_PROMPT=1
niri_plus_shell_init
niri_plus_shell_finish
niri_plus_shell_finish
[[ "$(niri_plus_test_hook_count line-init _rp_line_init)" == 1 ]] || exit 81
[[ "$(niri_plus_test_hook_count line-finish _rp_line_finish)" == 1 ]] || exit 82
'''
    )

    sleep_log = bundle / "transition-sleep-pids"
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "ZDOTDIR": str(install),
            "XDG_CONFIG_HOME": str(xdg / "transition-config"),
            "XDG_STATE_HOME": str(xdg / "transition-state"),
            "XDG_CACHE_HOME": str(xdg / "transition-cache"),
            "NIRI_PLUS_ZSH_PLUGIN_DIR": str(plugin_root),
            "NIRI_PLUS_ZSH_THEME_DIR": str(plugin_root),
            "NIRI_PLUS_ZSH_AGENT_HISTORY": "skip",
            "ZSH_FORCE_FULL_PROMPT": "1",
            "ZSH_RIGHT_PROMPT_REFRESH_INTERVAL": "0.08",
            "NIRI_PLUS_TEST_FINISH_LOG": str(finish_log),
            "NIRI_PLUS_TEST_SLEEP_PID_FILE": str(sleep_log),
            "PATH": str(test_bin),
        }
    )

    pid, fd = pty.fork()
    if pid == 0:
        os.execvpe(zsh, [zsh, "-d", "-i"], isolated_zsh_env(env))
    checks = 0
    try:
        pty_read_until(fd, b"NIRI_PLUS_TRANSITION_PROMPT_READY", 8, "human watcher did not reach its first prompt")
        initial_count = wait_for_sleep_log_growth(sleep_log, 0, "initial human mode")
        require(finish_log.read_text().splitlines() == ["finish"], "initial finish was not idempotent")
        checks += 2

        def run_to_prompt(command: str, context: str) -> None:
            os.write(fd, command.encode() + b"\n")
            pty_read_until(fd, b"NIRI_PLUS_TRANSITION_PROMPT_READY", 5, context)

        run_to_prompt(
            '''export NIRI_PLUS_AGENT_TOOL=1
ZSH_FORCE_FULL_PROMPT=
NIRI_PLUS_ZSH_AGENT_HISTORY=skip
niri_plus_shell_init
niri_plus_shell_finish
[[ "$NIRI_PLUS_SHELL_MODE" == agent && "$__NIRI_PLUS_SHELL_INITIALIZED_MODE" == agent ]] || exit 83
[[ -z "${__NIRI_PLUS_SHELL_FINISHED:-}" ]] || exit 84
[[ "$(niri_plus_test_hook_count line-init _rp_line_init)" == 0 ]] || exit 85
[[ "$(niri_plus_test_hook_count line-finish _rp_line_finish)" == 0 ]] || exit 86''',
            "skip agent transition did not return to an agent prompt",
        )
        stable_count = require_sleep_log_stable(sleep_log, "skip agent transition")
        require(finish_log.read_text().splitlines() == ["finish"], "agent finish ran human integrations")
        checks += 3

        run_to_prompt(
            '''unset NIRI_PLUS_AGENT_TOOL
ZSH_FORCE_FULL_PROMPT=1
NIRI_PLUS_ZSH_AGENT_HISTORY=skip
niri_plus_shell_init
[[ "$NIRI_PLUS_SHELL_MODE" == human && "$__NIRI_PLUS_SHELL_INITIALIZED_MODE" == human ]] || exit 87
[[ -z "${__NIRI_PLUS_SHELL_FINISHED:-}" ]] || exit 88
[[ "$(niri_plus_test_hook_count line-init _rp_line_init)" == 1 ]] || exit 89
[[ "$(niri_plus_test_hook_count line-finish _rp_line_finish)" == 1 ]] || exit 90
niri_plus_shell_init
[[ "$(niri_plus_test_hook_count line-init _rp_line_init)" == 1 ]] || exit 91
niri_plus_shell_finish
niri_plus_shell_finish''',
            "human re-entry after skip did not restore one watcher",
        )
        stable_count = wait_for_sleep_log_growth(sleep_log, stable_count, "human re-entry after skip")
        require(finish_log.read_text().splitlines() == ["finish", "finish"], "human re-entry inherited stale finish state")
        checks += 3

        legacy_history = home / "legacy-history" / "history"
        run_to_prompt(
            f'''export NIRI_PLUS_AGENT_TOOL=1
ZSH_FORCE_FULL_PROMPT=
NIRI_PLUS_ZSH_AGENT_HISTORY=legacy
NIRI_PLUS_ZSH_HISTORY_FILE="{legacy_history}"
niri_plus_shell_init
niri_plus_shell_finish
[[ "$NIRI_PLUS_SHELL_MODE" == agent && "$__NIRI_PLUS_SHELL_INITIALIZED_MODE" == agent ]] || exit 92
[[ "$HISTFILE" == "{legacy_history}" ]] || exit 93
[[ -z "${{__NIRI_PLUS_SHELL_FINISHED:-}}" ]] || exit 94
[[ "$(niri_plus_test_hook_count line-init _rp_line_init)" == 0 ]] || exit 95
[[ "$(niri_plus_test_hook_count line-finish _rp_line_finish)" == 0 ]] || exit 96''',
            "legacy agent transition did not return to an agent prompt",
        )
        stable_count = require_sleep_log_stable(sleep_log, "legacy agent transition")
        require(legacy_history.parent.is_dir(), "legacy agent transition did not initialize its history parent")
        require(finish_log.read_text().splitlines() == ["finish", "finish"], "legacy agent finish ran human integrations")
        checks += 3

        run_to_prompt(
            '''unset NIRI_PLUS_AGENT_TOOL NIRI_PLUS_ZSH_HISTORY_FILE
ZSH_FORCE_FULL_PROMPT=1
NIRI_PLUS_ZSH_AGENT_HISTORY=skip
niri_plus_shell_init
[[ "$NIRI_PLUS_SHELL_MODE" == human && "$__NIRI_PLUS_SHELL_INITIALIZED_MODE" == human ]] || exit 97
[[ -z "${__NIRI_PLUS_SHELL_FINISHED:-}" ]] || exit 98
[[ "$(niri_plus_test_hook_count line-init _rp_line_init)" == 1 ]] || exit 99
[[ "$(niri_plus_test_hook_count line-finish _rp_line_finish)" == 1 ]] || exit 100
niri_plus_shell_init
[[ "$(niri_plus_test_hook_count line-init _rp_line_init)" == 1 ]] || exit 101
niri_plus_shell_finish
niri_plus_shell_finish''',
            "human re-entry after legacy did not restore one watcher",
        )
        stable_count = wait_for_sleep_log_growth(sleep_log, stable_count, "human re-entry after legacy")
        require(finish_log.read_text().splitlines() == ["finish", "finish", "finish"], "legacy re-entry inherited stale finish state")
        checks += 3

        os.write(fd, b"exit\n")
        wait_for_shell(pid, fd, 8)
        pid = -1
    finally:
        if pid > 0:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass
        try:
            os.close(fd)
        except OSError:
            pass

    pids = {int(value) for value in sleep_log.read_text().splitlines() if value.isdigit()}
    deadline = time.monotonic() + 3
    alive = set(pids)
    while alive and time.monotonic() < deadline:
        alive = set()
        for child_pid in pids:
            try:
                os.kill(child_pid, 0)
            except ProcessLookupError:
                continue
            status = Path(f"/proc/{child_pid}/stat")
            if status.exists() and status.read_text().split()[2] == "Z":
                continue
            alive.add(child_pid)
        if alive:
            time.sleep(0.05)
    require(not alive, f"transition watcher processes remained after shell exit: {sorted(alive)}")
    return checks + 1


def check_shell_api(zsh: str, bundle: Path, home: Path, xdg: Path) -> int:
    checks = 0
    source_state = xdg / "api-source-state"
    source_cache = xdg / "api-source-cache"
    source_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "TERM_PROGRAM": "",
        "XDG_STATE_HOME": str(source_state),
        "XDG_CACHE_HOME": str(source_cache),
        "NIRI_PLUS_ZSH_AGENT_HISTORY": "skip",
    }
    source_code = f'''PROMPT=before-source
RPROMPT=before-right
source "{TERMINAL / 'init.zsh'}"
niri_plus_shell_finish
[[ $+functions[niri_plus_shell_init] == 1 && $+functions[niri_plus_shell_finish] == 1 ]] || exit 61
[[ "$PROMPT" == before-source && "$RPROMPT" == before-right ]] || exit 62
[[ -z "${{NIRI_PLUS_SHELL_MODE:-}}" && -z "${{NIRI_PLUS_ZSH_HOME:-}}" ]] || exit 63
[[ ! -e "$XDG_STATE_HOME" && ! -e "$XDG_CACHE_HOME" ]] || exit 64
print -r -- SOURCE_ONLY_API_OK
'''
    result = zsh_run(zsh, source_code, source_env)
    require("SOURCE_ONLY_API_OK" in result.stdout, "sourcing init.zsh performed initialization instead of defining the API")
    checks += 1

    caller = bundle / "outer-caller.zsh"
    caller.write_text(
        f'''source "{TERMINAL / 'init.zsh'}"
niri_plus_shell_init
niri_plus_shell_finish
[[ "$NIRI_PLUS_SHELL_MODE" == agent ]] || print -r -- OUTER_MODE_FAILURE
[[ "$NIRI_PLUS_SHELL_MODE" == agent ]] && return
print -r -- HUMAN_ONLY_SECTION_RAN
'''
    )
    caller_env = source_env | {
        "NIRI_PLUS_AGENT_TOOL": "1",
        "NIRI_PLUS_ZSH_AGENT_HISTORY": "skip",
        "ZSH_FORCE_FULL_PROMPT": "",
        "ZSH_FORCE_SIMPLE_PROMPT": "",
    }
    result = zsh_run(zsh, f'source "{caller}"; print -r -- OUTER_CALLER_CONTINUED', caller_env)
    require("OUTER_CALLER_CONTINUED" in result.stdout, "outer .zshrc did not continue after its own return")
    require("HUMAN_ONLY_SECTION_RAN" not in result.stdout and "OUTER_MODE_FAILURE" not in result.stdout, "agent shell ran caller-owned human hooks")
    require(not (source_state / "zsh").exists() and not (source_cache / "niri-plus-zsh").exists(), "agent skip mode initialized history or completion")
    checks += 3

    override_home = bundle / "override-home"
    override_home.mkdir()
    override_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(override_home),
        "TERM_PROGRAM": "",
        "XDG_STATE_HOME": str(xdg / "override-state"),
        "XDG_CACHE_HOME": str(xdg / "override-cache"),
        "NIRI_PLUS_AGENT_TOOL": "1",
        "NIRI_PLUS_SHELL_MODE": "stale-exported-value",
        "NIRI_PLUS_ZSH_AGENT_HISTORY": "skip",
        "NIRI_PLUS_ZSH_PLUGIN_DIR": "",
        "NIRI_PLUS_ZSH_THEME_DIR": "",
        "NIRI_PLUS_ZSH_HISTORY_FILE": "",
        "NIRI_PLUS_ZSH_COMPDUMP": "",
        "ZSH_FORCE_FULL_PROMPT": "1",
        "ZSH_FORCE_SIMPLE_PROMPT": "1",
    }
    override_code = f'''source "{TERMINAL / 'init.zsh'}"
niri_plus_shell_init
[[ "$NIRI_PLUS_SHELL_MODE" == human ]] || exit 65
[[ "${{(t)NIRI_PLUS_SHELL_MODE}}" != *export* ]] || exit 66
[[ "$NIRI_PLUS_ZSH_HOME" == "{TERMINAL}" ]] || exit 67
[[ "$NIRI_PLUS_ZSH_PLUGIN_DIR" == "$NIRI_PLUS_ZSH_HOME/plugins" ]] || exit 68
[[ "$NIRI_PLUS_ZSH_THEME_DIR" == "$NIRI_PLUS_ZSH_PLUGIN_DIR" ]] || exit 69
[[ "$NIRI_PLUS_ZSH_HISTORY_FILE" == "$XDG_STATE_HOME/zsh/history" ]] || exit 70
[[ "$NIRI_PLUS_ZSH_COMPDUMP" == "$XDG_CACHE_HOME/niri-plus-zsh/zcompdump-$ZSH_VERSION" ]] || exit 71
ZSH_FORCE_FULL_PROMPT=
ZSH_FORCE_SIMPLE_PROMPT=1
unset NIRI_PLUS_AGENT_TOOL
niri_plus_shell_init
[[ "$NIRI_PLUS_SHELL_MODE" == agent && "$PROMPT" == '%m%# ' ]] || exit 72
print -r -- MODE_OVERRIDES_OK:${{NIRI_PLUS_SHELL_MODE}}:${{(t)NIRI_PLUS_SHELL_MODE}}
'''
    result = zsh_run(zsh, override_code, override_env)
    require("MODE_OVERRIDES_OK:agent:scalar" in result.stdout, "mode overrides or non-exported computed mode changed")
    checks += 1

    explicit_compdump = bundle / "native-cache" / "zsh" / "zcompdump"
    explicit_cache_env = source_env | {
        "HOME": str(bundle / "compdump-home"),
        "XDG_CACHE_HOME": str(bundle / "unused-cache"),
        "XDG_STATE_HOME": str(bundle / "compdump-state"),
        "NIRI_PLUS_ZSH_COMPDUMP": str(explicit_compdump),
        "ZSH_FORCE_FULL_PROMPT": "1",
    }
    result = zsh_run(
        zsh,
        f'''source "{TERMINAL / 'init.zsh'}"
niri_plus_shell_init
[[ "$NIRI_PLUS_ZSH_COMPDUMP" == "{explicit_compdump}" ]] || exit 73
[[ "$ZSH_CACHE_DIR" == "{explicit_compdump.parent}" ]] || exit 74
print -r -- EXPLICIT_COMPDUMP_OK
''',
        explicit_cache_env,
    )
    require("EXPLICIT_COMPDUMP_OK" in result.stdout, "explicit compdump path was not retained")
    require(explicit_compdump.parent.is_dir(), "explicit compdump parent was not created")
    require(not (bundle / "unused-cache").exists(), "explicit compdump also created the unused portable cache")
    checks += 3

    legacy_history = override_home / ".local/state/zsh/history"
    legacy_env = source_env | {
        "NIRI_PLUS_AGENT_TOOL": "1",
        "NIRI_PLUS_ZSH_AGENT_HISTORY": "legacy",
        "NIRI_PLUS_ZSH_HISTORY_FILE": str(legacy_history),
        "ZSH_FORCE_FULL_PROMPT": "",
        "ZSH_FORCE_SIMPLE_PROMPT": "",
        "XDG_STATE_HOME": str(xdg / "legacy-state"),
        "XDG_CACHE_HOME": str(xdg / "legacy-cache"),
    }
    result = zsh_run(
        zsh,
        f'source "{TERMINAL / "zshrc"}"; print -r -- "LEGACY:$NIRI_PLUS_SHELL_MODE:$HISTFILE"',
        legacy_env,
    )
    require(f"LEGACY:agent:{legacy_history}" in result.stdout, "legacy agent history path was not preserved")
    require(legacy_history.parent.is_dir(), "legacy agent history initialization did not create its existing parent")
    require(not (xdg / "legacy-cache").exists(), "legacy agent mode initialized the completion cache")
    checks += 3
    return checks


def main() -> int:
    zsh = shutil.which("zsh")
    require(zsh is not None, "Zsh is required for the isolated terminal checks")
    checks = 0

    for path in (TERMINAL / "zshrc", TERMINAL / "init.zsh", TERMINAL / "p10k.zsh", TERMINAL / "p10k-custom-segments.zsh"):
        result = subprocess.run([zsh, "-n", str(path)], text=True, capture_output=True)
        require(result.returncode == 0, f"Zsh syntax failed for {path}: {result.stderr}")
        checks += 1
    for path in (TERMINAL / "fetch.py", DESKTOP / "desktop-session-menu", DESKTOP / "desktop-session-ready"):
        compile(path.read_text(), str(path), "exec")
        checks += 1

    pins = json.loads((TERMINAL / "pins.json").read_text())
    require(pins["schema_version"] == 1 and len(pins["plugins"]) == 4, "expected four pinned upstream projects")
    for project in pins["plugins"]:
        require(len(project["commit"]) == 40 and len(project["sha256"]) == 64, f"invalid immutable pin: {project['name']}")
        require(project["archive_url"].endswith(project["commit"]), f"archive is not commit-pinned: {project['name']}")
    checks += 4

    fetcher = load_module("niri_plus_terminal_fetch", TERMINAL / "fetch.py")
    session = load_module("niri_plus_desktop_session", DESKTOP / "desktop-session-menu")
    ready = load_module("niri_plus_desktop_ready", DESKTOP / "desktop-session-ready")

    with tempfile.TemporaryDirectory(prefix="niri-plus-terminal-check-") as temporary:
        global TEST_COMPLETION_FPATH, TEST_COMPLETION_FPATH_ROOT, TEST_COMPINIT_PATH, TEST_COMPAUDIT_PATH
        base = Path(temporary)
        home = base / "home"
        home.mkdir()
        xdg = base / "xdg"
        xdg.mkdir()
        bundle = base / "bundle"
        bundle.mkdir()
        (
            TEST_COMPLETION_FPATH,
            TEST_COMPLETION_FPATH_ROOT,
            TEST_COMPINIT_PATH,
            TEST_COMPAUDIT_PATH,
        ) = prepare_zsh_completion_fpath(zsh, bundle / "owned-completion-fpath")
        checks += check_isolated_completion_fpath(zsh, bundle, home, xdg)
        checks += check_shell_api(zsh, bundle, home, xdg)
        with mock.patch.dict(os.environ, {"HOME": str(home)}):
            existing = home / "existing"
            existing.mkdir()
            marker = existing / "keep.txt"
            marker.write_text("preserve")
            try:
                fetcher.install(existing)
            except ValueError as error:
                require("already exists" in str(error), "fetcher did not reject a pre-existing install path")
            else:
                raise AssertionError("fetcher accepted a pre-existing install path")
            require(marker.read_text() == "preserve", "fetcher changed an existing destination")
            try:
                fetcher.safe_destination(str(base / "outside"), home)
            except ValueError as error:
                require("below your home" in str(error), "fetcher rejected an outside path for the wrong reason")
            else:
                raise AssertionError("fetcher accepted a path outside HOME")
            checks += 3

        for path in ("examples/desktop/niri-plus-network.desktop", "examples/desktop/niri-plus-bluetooth.desktop", "examples/desktop/niri-plus-audio.desktop", "examples/desktop/niri-plus-session.desktop"):
            parser = configparser.ConfigParser(interpolation=None)
            parser.read(ROOT / path)
            entry = parser["Desktop Entry"]
            require(entry.get("Type") == "Application" and entry.get("Exec") and entry.get("TryExec"), f"invalid desktop entry: {path}")
            checks += 1

        calls = []

        def fake_run(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        cancel = lambda options, prompt: None
        require(not session.dispatch("Restart", run=fake_run, picker=cancel) and not calls, "restart cancellation dispatched an action")
        require(not session.dispatch("Shut down", run=fake_run, picker=lambda options, prompt: "Cancel") and not calls, "shutdown cancellation dispatched an action")
        require(session.dispatch("Restart", run=fake_run, picker=lambda options, prompt: "Restart"), "confirmed restart was not dispatched")
        require(calls[-1][0] == ["systemctl", "reboot"] and calls[-1][1].get("check"), "restart dispatch changed")
        require(session.dispatch("Shut down", run=fake_run, picker=lambda options, prompt: "Shut down"), "confirmed shutdown was not dispatched")
        require(calls[-1][0] == ["systemctl", "poweroff"], "shutdown dispatch changed")
        require(session.dispatch("Lock", run=fake_run) and calls[-1][0] == ["systemctl", "--user", "start", "desktop-lock.service"], "manual lock no longer uses its independent service")
        require(session.dispatch("Log out", run=fake_run) and calls[-1][0] == ["niri", "msg", "action", "quit"], "logout no longer preserves Niri confirmation")
        calls.clear()
        require(session.dispatch("Suspend", run=fake_run, lock_before_suspend=True), "configured suspend was not dispatched")
        require([call[0] for call in calls] == [["systemctl", "--user", "start", "desktop-lock.service"], ["systemctl", "suspend"]], "lock-before-suspend order changed")
        calls.clear()
        def failed_lock(command, **kwargs):
            calls.append((command, kwargs))
            raise subprocess.CalledProcessError(1, command)
        try:
            session.dispatch("Suspend", run=failed_lock, lock_before_suspend=True)
        except subprocess.CalledProcessError:
            require(len(calls) == 1 and calls[0][0][-1] == "desktop-lock.service", "failed lock admitted suspend")
        else:
            raise AssertionError("failed lock was ignored")
        checks += 8

        policy_root = base / "policy"
        policy_path = policy_root / "desktop-session/power.toml"
        policy_path.parent.mkdir(parents=True)
        try:
            session.read_lock_before_suspend(policy_root)
        except SystemExit as error:
            require("Suspend canceled" in str(error), "missing power policy failed with an unclear message")
        else:
            raise AssertionError("missing power policy was guessed")
        policy_path.write_text("lock_before_suspend = true\n")
        require(session.read_lock_before_suspend(policy_root) is True, "true power policy did not parse")
        policy_path.write_text("lock_before_suspend = 0\n")
        try:
            session.read_lock_before_suspend(policy_root)
        except SystemExit as error:
            require("invalid lock_before_suspend" in str(error), "invalid power policy failed unclearly")
        else:
            raise AssertionError("non-Boolean power policy was accepted")
        checks += 3

        runtime = base / "wayland-runtime"
        runtime.mkdir()
        socket_path = runtime / "wayland-test"
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(socket_path))
        server.listen(1)
        require(ready.session_ready({"WAYLAND_DISPLAY": "wayland-test", "XDG_RUNTIME_DIR": str(runtime)}), "ready helper rejected a responding isolated Wayland socket")
        accepted, _ = server.accept()
        accepted.close()
        server.close()
        require(not ready.session_ready({}), "ready helper accepted missing Wayland environment")
        checks += 2

        # Agent startup returns before paths, plugins, completion, or watchers.
        agent_env = os.environ.copy()
        agent_env.update(
            {
                "HOME": str(home),
                "XDG_STATE_HOME": str(xdg / "agent-state"),
                "XDG_CACHE_HOME": str(xdg / "agent-cache"),
                "NIRI_PLUS_AGENT_TOOL": "1",
                "NIRI_PLUS_TERMINAL_RC": str(TERMINAL / "zshrc"),
                "ZSH_FORCE_FULL_PROMPT": "",
            }
        )
        result = zsh_run(zsh, 'source "$NIRI_PLUS_TERMINAL_RC"; print -r -- "AGENT:$PROMPT:$+functions[compdef]:$+functions[_rp_start_timer]"', agent_env)
        require("AGENT:%m%# :0:0" in result.stdout, "agent shell did not take the simple early return")
        require(not (xdg / "agent-state/zsh").exists() and not (xdg / "agent-cache/niri-plus-zsh").exists(), "agent shell created full-shell state")
        checks += 2

        # Build a tiny plugin fixture; this verifies startup order without
        # depending on globally installed plugins or reaching hardware services.
        install = bundle / "human"
        install.mkdir()
        for name in ("zshrc", "init.zsh", "p10k.zsh", "p10k-custom-segments.zsh"):
            shutil.copyfile(TERMINAL / name, install / name)
        plugin_order = bundle / "plugin-order"
        for directory, file, label in (
            ("zsh-autosuggestions", "zsh-autosuggestions.zsh", "autosuggestions"),
            ("zsh-history-substring-search", "zsh-history-substring-search.zsh", "substring"),
            ("zsh-syntax-highlighting", "zsh-syntax-highlighting.zsh", "syntax"),
            ("powerlevel10k", "powerlevel10k.zsh-theme", "powerlevel10k"),
        ):
            content = f'print -r -- {label} >> "$NIRI_PLUS_TEST_PLUGIN_ORDER"\n'
            if label == "powerlevel10k":
                content += "function p10k { : }\n"
            put(install / "plugins" / directory / file, content)
        test_bin = bundle / "human-bin"
        test_bin.mkdir()
        expose_zsh_audit_commands(test_bin)
        mkdir = shutil.which("mkdir")
        mv = shutil.which("mv")
        require(mkdir is not None and mv is not None, "mkdir and mv are required for isolated startup")
        (test_bin / "mkdir").symlink_to(mkdir)
        (test_bin / "mv").symlink_to(mv)
        put(test_bin / "zoxide", "#!/bin/sh\nprintf '%s\\n' zoxide >> \"$NIRI_PLUS_TEST_PLUGIN_ORDER\"\nprintf '%s\\n' 'typeset -g NIRI_PLUS_TEST_ZOXIDE=1'\n", executable=True)
        put(test_bin / "fzf", "#!/bin/sh\n[ \"$1\" = --zsh ] && { printf '%s\\n' fzf >> \"$NIRI_PLUS_TEST_PLUGIN_ORDER\"; printf '%s\\n' 'typeset -g NIRI_PLUS_TEST_FZF=1'; }\n", executable=True)
        (install / ".zshrc").write_text(
            f'''function niri_plus_shell_pre_init() {{ print -r -- pre >> "$NIRI_PLUS_TEST_PLUGIN_ORDER"; }}
source "{install / 'zshrc'}"
niri_plus_shell_init
niri_plus_shell_finish
'''
        )
        proc = bundle / "proc"
        sysroot = bundle / "sys"
        put(proc / "meminfo", "MemTotal: 1000 kB\nMemAvailable: 300 kB\n")
        put(proc / "stat", "cpu 100 0 100 800 0 0 0 0\n")
        put(proc / "cpuinfo", "processor : 0\n")
        put(sysroot / "devices/system/cpu/cpu0/cpufreq/scaling_cur_freq", "3300000\n")
        battery = sysroot / "class/power_supply/BAT0"
        for field, value in (("type", "Battery"), ("scope", "System"), ("capacity", "75"), ("status", "Discharging"), ("power_now", "10000000"), ("energy_now", "30000000"), ("energy_full", "40000000")):
            put(battery / field, value + "\n")
        shell_env = os.environ.copy()
        shell_env.update(
            {
                "HOME": str(home),
                "ZDOTDIR": str(install),
                "XDG_CONFIG_HOME": str(xdg / "human-config"),
                "XDG_STATE_HOME": str(xdg / "human-state"),
                "XDG_CACHE_HOME": str(xdg / "human-cache"),
                "NIRI_PLUS_PROC_ROOT": str(proc),
                "NIRI_PLUS_SYS_ROOT": str(sysroot),
                "NIRI_PLUS_TEST_PLUGIN_ORDER": str(plugin_order),
                "PATH": str(test_bin),
                "ZSH_FORCE_FULL_PROMPT": "1",
            }
        )
        code = f'''function niri_plus_shell_pre_init() {{ print -r -- pre >> "$NIRI_PLUS_TEST_PLUGIN_ORDER"; }}
source "{install / 'init.zsh'}"
niri_plus_shell_init
print -r -- private-cli-integration >> "$NIRI_PLUS_TEST_PLUGIN_ORDER"
niri_plus_shell_finish
niri_plus_shell_finish
[[ "$NIRI_PLUS_SHELL_MODE" == human && "${{(t)NIRI_PLUS_SHELL_MODE}}" != *export* ]] || exit 61
[[ "$NIRI_PLUS_ZSH_HOME" == "{install}" ]] || exit 62
[[ "$NIRI_PLUS_ZSH_PLUGIN_DIR" == "$NIRI_PLUS_ZSH_HOME/plugins" ]] || exit 63
[[ "$NIRI_PLUS_ZSH_THEME_DIR" == "$NIRI_PLUS_ZSH_PLUGIN_DIR" ]] || exit 64
[[ "$NIRI_PLUS_ZSH_COMPDUMP" == "$XDG_CACHE_HOME/niri-plus-zsh/zcompdump-$ZSH_VERSION" ]] || exit 65
_detect_memory || exit 31
(( __p10k_mem_pct == 70 )) || exit 32
_detect_cpu && exit 33
print -r -- 'cpu 200 0 200 800 0 0 0 0' > "$NIRI_PLUS_PROC_ROOT/stat"
_detect_cpu || exit 34
(( __p10k_cpu_pct == 100 )) || exit 35
[[ "$__p10k_cpu_freq_str" == 3.3G ]] || exit 36
_detect_network || exit 37
[[ "$__p10k_net_type" == off ]] || exit 38
_detect_bluetooth && exit 39
_detect_battery || exit 40
[[ "$__p10k_bat_cap" == 75 && "$__p10k_bat_eta" == 3:00 ]] || exit 41
[[ "$HISTFILE" == "$XDG_STATE_HOME/zsh/history" ]] || exit 42
[[ "${{options[sharehistory]}}" == on && "${{options[histverify]}}" == on ]] || exit 58
(( HISTSIZE == 100000 && SAVEHIST == 100000 )) || exit 59
[[ "$(bindkey '^[[A')" == *history-substring-search-up* ]] || exit 60
(( $+functions[compdef] == 1 )) || exit 43
[[ "$NIRI_PLUS_TEST_FZF" == 1 && "$NIRI_PLUS_TEST_ZOXIDE" == 1 ]] || exit 44
(( $+functions[_rp_start_timer] == 0 )) || exit 45
_p10k_color_for info >/dev/null; (( __p10k_color == 7 )) || exit 46
_p10k_color_for normal >/dev/null; (( __p10k_color == 15 )) || exit 47
_p10k_color_for connected >/dev/null; (( __p10k_color == 6 )) || exit 48
_p10k_color_for inactive >/dev/null; (( __p10k_color == 8 )) || exit 49
_p10k_color_for charging >/dev/null; (( __p10k_color == 2 )) || exit 50
_p10k_color_for warning >/dev/null; (( __p10k_color == 3 )) || exit 51
_p10k_color_for error >/dev/null; (( __p10k_color == 1 )) || exit 52
_p10k_color_for critical >/dev/null; (( __p10k_color == 9 )) || exit 53
typeset -F 6 started=$EPOCHREALTIME
for i in {{1..100}}; do
  _detect_memory >/dev/null || :
  _detect_cpu >/dev/null || :
  _detect_network >/dev/null || :
  _detect_bluetooth >/dev/null || :
  _detect_battery >/dev/null || :
done
typeset -F 6 elapsed=$(( EPOCHREALTIME - started ))
typeset -F 3 refresh_ms=$(( 1000 * elapsed / 100 ))
print -r -- "PROBE_MS:$refresh_ms"
print -r -- "HUMAN:$POWERLEVEL9K_DIR_FOREGROUND:$POWERLEVEL9K_VCS_CLEAN_FOREGROUND:$POWERLEVEL9K_VCS_MODIFIED_FOREGROUND:$POWERLEVEL9K_VCS_UNTRACKED_FOREGROUND:$POWERLEVEL9K_VCS_CONFLICTED_FOREGROUND:$POWERLEVEL9K_PROMPT_CHAR_OK_VIINS_FOREGROUND:$POWERLEVEL9K_PROMPT_CHAR_ERROR_VIINS_FOREGROUND"
'''
        started = time.perf_counter()
        result = zsh_run(zsh, code, shell_env)
        probe_ms = (time.perf_counter() - started) * 1000
        require("HUMAN:4:2:3:6:1:2:9" in result.stdout, "portable prompt did not use selected Neutral Slate ANSI role indexes")
        refresh_ms = float(next(line.split(":", 1)[1] for line in result.stdout.splitlines() if line.startswith("PROBE_MS:")))
        require(
            plugin_order.read_text().splitlines() == ["pre", "autosuggestions", "substring", "powerlevel10k", "private-cli-integration", "zoxide", "fzf", "syntax"],
            "pre-init, CLI integration, or syntax-highlighting order changed",
        )
        checks += 10

        # Missing optional commands and devices remain a supported startup.
        missing_install = bundle / "missing"
        missing_install.mkdir()
        shutil.copyfile(TERMINAL / "zshrc", missing_install / "zshrc")
        shutil.copyfile(TERMINAL / "init.zsh", missing_install / "init.zsh")
        shutil.copyfile(TERMINAL / "p10k.zsh", missing_install / "p10k.zsh")
        shutil.copyfile(TERMINAL / "p10k-custom-segments.zsh", missing_install / "p10k-custom-segments.zsh")
        missing_env = shell_env | {"PATH": str(test_bin / "empty-path"), "NIRI_PLUS_TEST_PLUGIN_ORDER": str(bundle / "missing-order")}
        (test_bin / "empty-path").mkdir()
        expose_zsh_audit_commands(test_bin / "empty-path")
        (test_bin / "empty-path" / "mkdir").symlink_to(mkdir)
        empty_sys = bundle / "empty-sys"
        empty_sys.mkdir()
        missing_env["NIRI_PLUS_SYS_ROOT"] = str(empty_sys)
        missing_code = f'''source "{missing_install / 'zshrc'}"
[[ -r "$HISTFILE" || -d "$ZSH_STATE_DIR" ]] || exit 51
_detect_memory || exit 52
_detect_network || exit 53
[[ "$__p10k_net_type" == off ]] || exit 54
_detect_bluetooth && exit 55
_detect_battery && exit 56
(( $+commands[fzf] == 0 && $+commands[zoxide] == 0 )) || exit 57
print -r -- MISSING_TOOLS_OK
'''
        result = zsh_run(zsh, missing_code, missing_env)
        require("MISSING_TOOLS_OK" in result.stdout, "missing commands/devices prevented shell startup")
        checks += 2

        timer_count = check_interactive_watcher(zsh, bundle, home, xdg)
        checks += 3
        checks += check_watcher_mode_transitions(zsh, bundle, home, xdg)

    print(json.dumps({"checks": checks, "plugins": 4, "watcher_processes_started_and_reaped": timer_count, "fixture_startup_ms": round(probe_ms, 2), "fixture_status_refresh_ms_per_call": round(refresh_ms, 3), "live_desktop_operations": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
