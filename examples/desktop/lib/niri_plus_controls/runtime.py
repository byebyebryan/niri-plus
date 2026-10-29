"""Per-invocation Rofi owner, private callback socket, and credential handoff."""

from __future__ import annotations

from dataclasses import dataclass, field
import fcntl
import json
import os
from pathlib import Path
import shutil
import select
import shlex
import signal
import socket
import socketserver
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from typing import Mapping

from .appearance import default_appearance_path, default_theme_path, load_appearance
from .app import MAX_PENDING_POLLS, ControlsApp, Page
from .model import ControlsBackend, Utility
from .rofi import MAX_FRAME_BYTES, RofiProtocolError, ScriptRequest


MAX_CALLBACK_BYTES = 64 * 1024
MAX_SECRET_BYTES = 4096
RUNTIME_DIR_NAME = "niri-plus-controls"
PENDING_POLL_SECONDS = 1


@dataclass(slots=True)
class SecretPromptRequest:
    prompt: str
    ready: threading.Event = field(default_factory=threading.Event)
    callback_done: threading.Event = field(default_factory=threading.Event)
    value: bytearray | None = None


class SecretBroker:
    """Pause one callback while the owner releases Rofi's input grab."""

    def __init__(self):
        self._lock = threading.Lock()
        self._request: SecretPromptRequest | None = None
        self._changed = threading.Event()
        self._local = threading.local()

    def prompt(self, prompt: str) -> bytearray | None:
        request = SecretPromptRequest(prompt=prompt)
        with self._lock:
            if self._request is not None:
                raise RuntimeError("a credential prompt is already active")
            self._request = request
            self._local.request = request
            self._changed.set()
        if not request.ready.wait(timeout=300):
            return None
        return request.value

    def finish_callback(self) -> None:
        request = getattr(self._local, "request", None)
        if request is not None:
            request.callback_done.set()
            self._local.request = None

    def is_secret_callback(self) -> bool:
        return getattr(self._local, "request", None) is not None

    def wait_for_request(self, timeout: float) -> SecretPromptRequest | None:
        if not self._changed.wait(timeout):
            return None
        with self._lock:
            request = self._request
            self._request = None
            self._changed.clear()
            return request

    @staticmethod
    def resolve(request: SecretPromptRequest, value: bytearray | None) -> None:
        request.value = value
        request.ready.set()


class _ControllerServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = False
    block_on_close = True
    allow_reuse_address = False

    def handle_error(self, request, client_address):
        # socketserver's default prints native exception text. Never let an
        # unexpected credential/backend error become a traceback diagnostic.
        self.close_menu.set()

    def __init__(self, address, handler, *, app: ControlsApp, broker: SecretBroker, trace: Path | None):
        self.app = app
        self.broker = broker
        self.trace = trace
        self.close_menu = threading.Event()
        self.restart_menu = threading.Event()
        self.pending_timeout_active = False
        self.app_lock = threading.Lock()
        super().__init__(address, handler)


class _CallbackHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        server: _ControllerServer = self.server  # type: ignore[assignment]
        self.request.settimeout(10)
        raw = self.rfile.readline(MAX_CALLBACK_BYTES + 1)
        try:
            if len(raw) > MAX_CALLBACK_BYTES or not raw.endswith(b"\n"):
                raise RofiProtocolError("callback request exceeds its size limit")
            value = json.loads(raw)
            if not isinstance(value, dict) or set(value) != {"retv", "data", "info"}:
                raise RofiProtocolError("callback request has unexpected fields")
            if type(value["retv"]) is not int or not isinstance(value["data"], dict):
                raise RofiProtocolError("callback request fields are invalid")
            if value["info"] is not None and not isinstance(value["info"], dict):
                raise RofiProtocolError("callback selection is invalid")
            request = ScriptRequest(value["retv"], value["data"], value["info"])
            with server.app_lock:
                output = server.app.handle(request)
                if output is None:
                    server.close_menu.set()
                    output = ""
                state = server.app._resume_state
                if request.retv != 0 and state is not None:
                    pending_timeout_needed = state.page == Page.PENDING and state.pending_polls < MAX_PENDING_POLLS
                    if pending_timeout_needed != server.pending_timeout_active:
                        server.restart_menu.set()
                encoded = output.encode("utf-8")
                if len(encoded) > MAX_FRAME_BYTES:
                    raise RofiProtocolError("Rofi callback frame exceeds its size limit")
                self.wfile.write(encoded)
                self.wfile.flush()
                self._write_trace(request, output, server)
        except Exception as error:
            # Never dump callback data, Rofi environment, or backend details to
            # stderr: ROFI_DATA/INFO are bounded metadata and must not become a log.
            try:
                self.wfile.write(b"")
                self.wfile.flush()
            except OSError:
                pass
            owned_handoff = isinstance(error, (BrokenPipeError, ConnectionResetError)) and (
                server.broker.is_secret_callback() or server.restart_menu.is_set())
            if server.trace is not None:
                _append_json(server.trace, {"event": "owned-handoff-pipe-closed" if owned_handoff else "callback-error", "error": type(error).__name__})
            if not owned_handoff:
                server.close_menu.set()
        finally:
            server.broker.finish_callback()

    @staticmethod
    def _write_trace(request: ScriptRequest, output: str, server: _ControllerServer) -> None:
        if server.trace is None:
            return
        state = server.app._resume_state
        fixture = server.app.backend
        events = getattr(fixture, "events", ())
        _append_json(
            server.trace,
            {
                "event": "callback",
                "retv": request.retv,
                "selected": request.info,
                "state": state.payload() if state is not None else None,
                "frame": output,
                "backend_events": list(events),
            },
        )


def _append_json(path: Path, value: object) -> None:
    raw = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("utf-8") + b"\n"
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise RuntimeError("proof trace must be a private file owned by this user")
        os.write(fd, raw)
    finally:
        os.close(fd)


def _secure_directory(path: Path) -> Path:
    if path.is_symlink():
        raise RuntimeError(f"private runtime path must not be a symlink: {path}")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise RuntimeError(f"private runtime directory has unsafe ownership or permissions: {path}")
    return path


class RuntimeLease:
    """Cross-invocation owner lock plus a private, removable callback directory."""

    def __init__(self):
        runtime_home = os.environ.get("XDG_RUNTIME_DIR")
        if runtime_home:
            base = Path(runtime_home)
            if not base.is_absolute() or base.is_symlink():
                raise RuntimeError("XDG_RUNTIME_DIR must be an absolute private directory")
            base_info = base.stat()
            if not stat.S_ISDIR(base_info.st_mode) or base_info.st_uid != os.getuid() or base_info.st_mode & 0o077:
                raise RuntimeError("XDG_RUNTIME_DIR must be owned by this user with mode 0700")
        else:
            base = Path(tempfile.gettempdir())
        self.root = _secure_directory(base / RUNTIME_DIR_NAME)
        lock_path = self.root / "owner.lock"
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0), 0o600)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            os.close(fd)
            raise RuntimeError("controls owner lock has unsafe ownership or permissions")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            raise AlreadyRunning("A controls menu is already open") from None
        self.lock_fd = fd
        self.invocation_dir = Path(tempfile.mkdtemp(prefix="invocation-", dir=self.root))
        os.chmod(self.invocation_dir, 0o700)
        self.socket_path = self.invocation_dir / "c.sock"

    def close(self) -> None:
        shutil.rmtree(self.invocation_dir, ignore_errors=True)
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(self.lock_fd)


class AlreadyRunning(RuntimeError):
    pass


def _make_backend(utility: Utility, *, fixture: bool) -> ControlsBackend:
    if fixture:
        from .fixture import FixtureBackend

        return FixtureBackend(utility)
    if utility == Utility.AUDIO:
        from .audio import AudioBackend

        return AudioBackend()
    if utility == Utility.NETWORK:
        try:
            from .network import NetworkBackend  # type: ignore[import-not-found]
        except ImportError as error:
            raise RuntimeError("Network controls backend is not staged") from error
        return NetworkBackend()
    try:
        from .bluetooth import BluetoothBackend  # type: ignore[import-not-found]
    except ImportError as error:
        raise RuntimeError("Bluetooth controls backend is not staged") from error
    return BluetoothBackend()


def _notify_already_running(rofi: str, *, no_config: bool) -> None:
    command = [rofi]
    if no_config:
        command.append("-no-config")
    command += ["-e", "A controls menu is already open."]
    try:
        process = subprocess.Popen(command, start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        _stop_process_group(process)


def _stop_process_group(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=1.5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=1.5)


def _password_prompt(
    rofi: str,
    prompt: str,
    theme: Path,
    *,
    no_config: bool,
    env: Mapping[str, str],
) -> bytearray | None:
    command = [rofi]
    if no_config:
        command.append("-no-config")
    command += [
        "-dmenu", "-password", "-disable-history", "-p", prompt,
        "-theme", str(theme), "-kb-cancel", "Escape,Control+g",
        "-theme-str", 'entry { placeholder: "Enter credential"; }',
    ]
    process: subprocess.Popen | None = None
    secret = bytearray()
    scratch = bytearray(1024)
    deadline = time.monotonic() + 300
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=dict(env),
            start_new_session=True,
        )
        if process.stdout is None:
            return None
        fd = process.stdout.fileno()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(command, 300)
            readable, _, _ = select.select([fd], [], [], remaining)
            if not readable:
                raise subprocess.TimeoutExpired(command, 300)
            count = os.readv(fd, [scratch])
            if count == 0:
                break
            if len(secret) + count > MAX_SECRET_BYTES:
                secret[:] = b"\0" * len(secret)
                scratch[:count] = b"\0" * count
                _stop_process_group(process)
                return None
            view = memoryview(scratch)[:count]
            try:
                secret.extend(view)
            finally:
                view.release()
                scratch[:count] = b"\0" * count
        process.wait(timeout=max(0.01, deadline - time.monotonic()))
    except (OSError, subprocess.TimeoutExpired):
        if process is not None and process.poll() is None:
            _stop_process_group(process)
        secret[:] = b"\0" * len(secret)
        return None
    finally:
        scratch[:] = b"\0" * len(scratch)
        if process is not None and process.stdout is not None:
            process.stdout.close()
        if process is not None and process.poll() is None:
            _stop_process_group(process)
    if process.returncode != 0:
        secret[:] = b"\0" * len(secret)
        return None
    if secret.endswith(b"\r\n"):
        del secret[-2:]
    elif secret.endswith(b"\n"):
        del secret[-1:]
    if b"\0" in secret:
        secret[:] = b"\0" * len(secret)
        return None
    return secret


def callback_main(env: Mapping[str, str] | None = None) -> int:
    env = env or os.environ
    socket_path = env.get("NIRI_PLUS_CONTROLS_SOCKET")
    if not socket_path:
        return 1
    try:
        request = ScriptRequest.from_environment(env)
        payload = json.dumps(
            {"retv": request.retv, "data": request.data, "info": request.info},
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        if len(payload) > MAX_CALLBACK_BYTES:
            return 1
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(60)
        client.connect(socket_path)
        client.sendall(payload)
        chunks: list[bytes] = []
        remaining = MAX_FRAME_BYTES + 1
        while remaining:
            data = client.recv(min(65_536, remaining))
            if not data:
                break
            chunks.append(data)
            remaining -= len(data)
        client.close()
        response = b"".join(chunks)
        if len(response) > MAX_FRAME_BYTES:
            return 1
        sys.stdout.buffer.write(response)
        sys.stdout.buffer.flush()
        return 0
    except (OSError, ValueError, TypeError, RofiProtocolError):
        return 1


def _dispatcher_path() -> Path:
    return Path(__file__).resolve().parents[2] / "bin" / "desktop-controls"


def _run_controller(
    utility: Utility,
    *,
    fixture: bool,
    no_config: bool,
    appearance_path: Path,
    theme: Path,
    proof_trace: Path | None,
    rofi: str,
) -> int:
    appearance = load_appearance(appearance_path)
    if not theme.is_file():
        raise RuntimeError(f"controls theme does not exist: {theme}")
    lease = RuntimeLease()
    backend = _make_backend(utility, fixture=fixture)
    broker = SecretBroker()
    advanced_command = {
        Utility.NETWORK: ["nm-connection-editor"],
        Utility.AUDIO: ["pavucontrol"],
        Utility.BLUETOOTH: ["kitty", "--", "bluetoothctl"],
    }[utility]
    advanced_available = not fixture and all(shutil.which(item) for item in (
        ("kitty", "bluetoothctl") if utility == Utility.BLUETOOTH else (advanced_command[0],)))
    app = ControlsApp(
        utility,
        str(uuid.uuid4()),
        backend,
        appearance,
        prompt_secret=broker.prompt,
        advanced_available=advanced_available,
    )
    server = _ControllerServer(str(lease.socket_path), _CallbackHandler, app=app, broker=broker, trace=proof_trace)
    os.chmod(lease.socket_path, 0o600)
    server_thread = threading.Thread(target=server.serve_forever, name="controls-callback-server", daemon=True)
    server_thread.start()
    base_env = os.environ.copy()
    env = dict(base_env)
    env["NIRI_PLUS_CONTROLS_SOCKET"] = str(lease.socket_path)
    dispatcher = str(_dispatcher_path())
    command = [
        rofi,
        "-show", "controls",
        "-modi", f"controls:{shlex.quote(dispatcher)}",
        "-no-sort",
        "-eh", "2",
        "-kb-custom-1", "Alt+r",
        "-kb-custom-7", "Tab",
        "-kb-custom-8", "ISO_Left_Tab",
        "-kb-element-next", "",
        "-kb-element-prev", "",
        "-kb-accept-custom", "",
        "-kb-delete-entry", "",
        "-kb-cancel", "Escape,Control+g",
        "-kb-move-char-forward", "Control+f",
        "-kb-move-char-back", "Control+b",
        "-theme", str(theme),
    ]
    if no_config:
        command.insert(1, "-no-config")

    def launch(*, pending_timeout: bool) -> subprocess.Popen:
        timeout_delay = str(PENDING_POLL_SECONDS if pending_timeout else 0)
        timeout_action = "kb-custom-19" if pending_timeout else "kb-cancel"
        launch_command = command + [
            "-timeout-delay", timeout_delay,
            "-timeout-action", timeout_action,
        ]
        if proof_trace is not None:
            _append_json(
                proof_trace,
                {
                    "event": "rofi-launch",
                    "pending_timeout": pending_timeout,
                    "timeout_delay": int(timeout_delay),
                    "timeout_action": timeout_action,
                },
            )
        return subprocess.Popen(
            launch_command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=None,
            env=env,
            start_new_session=True,
        )

    process: subprocess.Popen | None = None
    try:
        process = launch(pending_timeout=False)
        while process is not None:
            secret_request = broker.wait_for_request(0.05)
            if secret_request is not None:
                if process.poll() is not None:
                    broker.resolve(secret_request, None)
                    secret_request.callback_done.wait(timeout=30)
                    process = None
                    break
                # Rofi holds the keyboard grab while waiting for its script child.
                # Retire only this invocation before starting the password dmenu.
                server.pending_timeout_active = False
                _stop_process_group(process)
                secret = _password_prompt(
                    rofi, secret_request.prompt, theme,
                    no_config=no_config, env=base_env,
                )
                broker.resolve(secret_request, secret)
                secret_request.callback_done.wait(timeout=30)
                if secret:
                    server.restart_menu.clear()
                    state = app._resume_state
                    pending_timeout = bool(state and state.page == Page.PENDING and state.pending_polls < MAX_PENDING_POLLS)
                    server.pending_timeout_active = pending_timeout
                    process = launch(pending_timeout=pending_timeout)
                    continue
                process = None
                break
            if server.close_menu.is_set():
                _stop_process_group(process)
                process = None
                break
            if server.restart_menu.is_set():
                if process.poll() is not None:
                    process = None
                    break
                server.restart_menu.clear()
                state = app._resume_state
                pending_timeout = bool(state and state.page == Page.PENDING and state.pending_polls < MAX_PENDING_POLLS)
                server.pending_timeout_active = pending_timeout
                _stop_process_group(process)
                process = launch(pending_timeout=pending_timeout)
                continue
            try:
                process.wait(timeout=0.05)
                process = None
            except subprocess.TimeoutExpired:
                continue
        return 0
    finally:
        if process is not None:
            _stop_process_group(process)
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)
        backend.close()
        if proof_trace is not None:
            _append_json(proof_trace, {"event": "finalize", "backend_events": list(getattr(backend, "events", ()))})
        lease.close()
        if app.launch_advanced and advanced_available:
            # Only the explicitly accepted native handoff outlives this menu.
            # It receives no callback socket/state or credential environment.
            subprocess.Popen(advanced_command, env=base_env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def _parser_for(utility: Utility):
    import argparse

    parser = argparse.ArgumentParser(prog=f"desktop-{utility.value}-menu")
    parser.add_argument("--fixture", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-config", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--appearance", type=Path, default=default_appearance_path())
    parser.add_argument("--theme", type=Path, default=default_theme_path())
    parser.add_argument("--proof-trace", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--rofi", default=shutil.which("rofi") or "rofi", help=argparse.SUPPRESS)
    return parser


def main_for(utility: Utility | str, argv: list[str] | None = None) -> int:
    utility = Utility(utility)
    args = _parser_for(utility).parse_args(argv)
    if args.proof_trace is not None and not (args.fixture and args.no_config):
        raise SystemExit("proof trace requires the inert fixture and private no-config mode")
    try:
        return _run_controller(
            utility,
            fixture=args.fixture,
            no_config=args.no_config,
            appearance_path=args.appearance,
            theme=args.theme,
            proof_trace=args.proof_trace,
            rofi=args.rofi,
        )
    except AlreadyRunning:
        _notify_already_running(args.rofi, no_config=args.no_config)
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print(f"desktop-{utility.value}-menu: {error}", file=sys.stderr)
        return 1


def common_main(argv: list[str] | None = None) -> int:
    if "ROFI_RETV" in os.environ:
        return callback_main()
    import argparse

    parser = argparse.ArgumentParser(prog="desktop-controls")
    parser.add_argument("--utility", required=True, choices=[item.value for item in Utility])
    args, rest = parser.parse_known_args(argv)
    return main_for(Utility(args.utility), rest)

