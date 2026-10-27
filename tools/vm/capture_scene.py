#!/usr/bin/env python3
"""Record one guest-only Niri Plus browser/terminal scene and its receipt."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
APP_ROOT = SCRIPT_PATH.parents[1]
TOOLS_ROOT = SCRIPT_PATH.parent
PROFILE_RELATIVE = Path(".cache/niri-plus-vm/chrome-profile")
PAGE_TITLE = "Niri Plus Guest Pilot"
KITTY_TITLE = "Niri Plus Sample Project"
WARMUP_TITLE = "Niri Plus Zsh Warmup"
TARGET_FPS = 30
CAPTURE_OUTPUT_NAME = "Virtual-1"
CAPTURE_OUTPUT_MODE = "1920x1080@60.000"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_guest() -> None:
    guard = TOOLS_ROOT / "guest-guard.sh"
    result = subprocess.run([str(guard)], text=True, capture_output=True)
    if result.returncode:
        sys.stderr.write(result.stderr or result.stdout)
        raise SystemExit(result.returncode)


def read_setup_receipt() -> dict[str, Any]:
    path = APP_ROOT / "setup-receipt.json"
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"guest setup receipt is missing or symlinked: {path}")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if receipt.get("schema_version") != 1:
        raise ValueError("unsupported guest setup receipt")
    if receipt.get("guest", {}).get("hostname") != "niri-plus-arch":
        raise ValueError("setup receipt does not identify the pilot guest")
    return receipt


def ensure_safe_home_path(path: Path, home: Path) -> None:
    resolved_home = home.resolve()
    if path.is_symlink() or not path.resolve(strict=False).is_relative_to(resolved_home):
        raise ValueError(f"refusing unsafe guest output path: {path}")
    current = resolved_home
    for part in path.relative_to(resolved_home).parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"refusing to write through a symlink: {current}")


def discover_niri_environment() -> tuple[dict[str, str], Path]:
    uid = os.getuid()
    runtime_directory = Path(f"/run/user/{uid}")
    if runtime_directory.is_symlink() or not runtime_directory.is_dir():
        raise ValueError(f"user runtime directory is unavailable: {runtime_directory}")
    runtime_stat = runtime_directory.stat()
    if runtime_stat.st_uid != uid or stat.S_IMODE(runtime_stat.st_mode) & 0o077:
        raise ValueError("user runtime directory has unexpected ownership or permissions")

    sockets = []
    socket_pattern = re.compile(r"^niri\.(.+)\.([0-9]+)\.sock$")
    for candidate in sorted(runtime_directory.glob("niri.*.sock")):
        match = socket_pattern.fullmatch(candidate.name)
        if match is None or not stat.S_ISSOCK(candidate.stat().st_mode) or candidate.stat().st_uid != uid:
            continue
        pid = int(match.group(2))
        process_directory = Path(f"/proc/{pid}")
        if not process_directory.is_dir() or process_directory.stat().st_uid != uid:
            continue
        try:
            arguments = [item.decode(errors="replace") for item in (process_directory / "cmdline").read_bytes().split(b"\0") if item]
        except OSError:
            continue
        if not any(Path(argument).name == "niri" for argument in arguments[:3]):
            continue
        sockets.append((candidate, match.group(1)))
    if len(sockets) != 1:
        raise ValueError(f"expected one running Niri IPC socket for demo, found {len(sockets)}")

    socket_path, wayland_display = sockets[0]
    environment = os.environ.copy()
    environment.update({
        "XDG_RUNTIME_DIR": str(runtime_directory),
        "WAYLAND_DISPLAY": wayland_display,
        "NIRI_SOCKET": str(socket_path),
        "XDG_SESSION_TYPE": "wayland",
        "XDG_CURRENT_DESKTOP": "niri",
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path={runtime_directory}/bus",
    })
    manager = subprocess.run(
        ["systemctl", "--user", "show-environment"],
        text=True,
        capture_output=True,
        env=environment,
    )
    if manager.returncode == 0:
        for line in manager.stdout.splitlines():
            key, separator, value = line.partition("=")
            if separator and key in {"DISPLAY", "WAYLAND_DISPLAY", "NIRI_SOCKET", "XDG_CURRENT_DESKTOP", "XDG_SESSION_TYPE"}:
                if key in {"WAYLAND_DISPLAY", "NIRI_SOCKET"} and value and environment[key] != value:
                    raise ValueError(f"user manager environment points to another compositor: {key}")
                if value:
                    environment[key] = value
    return environment, socket_path


def run_niri(environment: dict[str, str], *arguments: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["niri", "msg", *arguments],
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        env=environment,
    )


def niri_json(environment: dict[str, str], name: str) -> Any:
    result = run_niri(environment, "--json", name, capture=True)
    return json.loads(result.stdout)


def set_capture_output_mode(environment: dict[str, str]) -> dict[str, Any]:
    outputs = niri_json(environment, "outputs")
    if not isinstance(outputs, dict) or len(outputs) != 1 or CAPTURE_OUTPUT_NAME not in outputs:
        raise ValueError(f"pilot capture expects one {CAPTURE_OUTPUT_NAME} output")
    output = outputs[CAPTURE_OUTPUT_NAME]
    modes = output.get("modes", [])
    if not any(
        mode.get("width") == 1920
        and mode.get("height") == 1080
        and mode.get("refresh_rate") == 60000
        for mode in modes
    ):
        raise ValueError(f"guest output does not advertise the requested {CAPTURE_OUTPUT_MODE} mode")

    run_niri(environment, "output", CAPTURE_OUTPUT_NAME, "mode", CAPTURE_OUTPUT_MODE)
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        outputs = niri_json(environment, "outputs")
        output = outputs.get(CAPTURE_OUTPUT_NAME, {}) if isinstance(outputs, dict) else {}
        modes = output.get("modes", [])
        current_index = output.get("current_mode")
        if isinstance(current_index, int) and 0 <= current_index < len(modes):
            current = modes[current_index]
            if current.get("width") == 1920 and current.get("height") == 1080 and current.get("refresh_rate") == 60000:
                return outputs
        time.sleep(0.1)
    raise TimeoutError(f"Niri did not select {CAPTURE_OUTPUT_MODE} on {CAPTURE_OUTPUT_NAME}")


def wait_for_windows(environment: dict[str, str], timeout: float = 45.0) -> list[dict[str, Any]]:
    deadline = time.monotonic() + timeout
    latest: list[dict[str, Any]] = []
    while time.monotonic() < deadline:
        latest = niri_json(environment, "windows")
        if not isinstance(latest, list):
            raise ValueError("Niri returned an unexpected windows payload")
        has_chrome = any(PAGE_TITLE in str(window.get("title", "")) for window in latest)
        has_kitty = any(
            str(window.get("app_id", "")).lower() == "kitty"
            or KITTY_TITLE in str(window.get("title", ""))
            for window in latest
        )
        if has_chrome and has_kitty:
            return latest
        time.sleep(0.25)
    raise TimeoutError("timed out waiting for the local Chrome page and Kitty project window")


def identify_scene_windows(windows: list[dict[str, Any]]) -> tuple[int, int]:
    chrome = [window for window in windows if PAGE_TITLE in str(window.get("title", ""))]
    kitty = [
        window for window in windows
        if str(window.get("app_id", "")).lower() == "kitty"
        or KITTY_TITLE in str(window.get("title", ""))
    ]
    if len(windows) != 2 or len(chrome) != 1 or len(kitty) != 1 or chrome[0].get("id") == kitty[0].get("id"):
        titles = [str(window.get("title", "")) for window in windows]
        raise ValueError(f"expected exactly one local Chrome page and one Kitty window; got {titles}")
    if chrome[0].get("is_floating") or kitty[0].get("is_floating"):
        raise ValueError("the pilot windows must both use Niri's tiling layout")
    workspace_id = chrome[0].get("workspace_id")
    if workspace_id is None or kitty[0].get("workspace_id") != workspace_id:
        raise ValueError("Chrome and Kitty must be on the same Niri workspace")
    return int(chrome[0]["id"]), int(kitty[0]["id"])


def focused_window_id(environment: dict[str, str]) -> int | None:
    windows = niri_json(environment, "windows")
    focused = [window for window in windows if window.get("is_focused")]
    return int(focused[0]["id"]) if len(focused) == 1 else None


def focus_window(environment: dict[str, str], window_id: int) -> None:
    if focused_window_id(environment) != window_id:
        run_niri(environment, "action", "focus-window", "--id", str(window_id))
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        if focused_window_id(environment) == window_id:
            return
        time.sleep(0.05)
    raise ValueError(f"Niri did not focus the intended window id {window_id}")


def arrange_scene_windows(environment: dict[str, str], windows: list[dict[str, Any]]) -> tuple[int, int]:
    chrome_id, kitty_id = identify_scene_windows(windows)
    focus_window(environment, chrome_id)
    run_niri(environment, "action", "move-column-to-first")
    focus_window(environment, kitty_id)
    run_niri(environment, "action", "move-column-to-last")
    latest = niri_json(environment, "windows")
    current_chrome_id, current_kitty_id = identify_scene_windows(latest)
    if (current_chrome_id, current_kitty_id) != (chrome_id, kitty_id):
        raise ValueError("Niri window identities changed while arranging the scene")
    by_id = {int(window["id"]): window for window in latest}
    chrome_position = by_id[chrome_id].get("layout", {}).get("pos_in_scrolling_layout")
    kitty_position = by_id[kitty_id].get("layout", {}).get("pos_in_scrolling_layout")
    if (
        not isinstance(chrome_position, list)
        or not isinstance(kitty_position, list)
        or len(chrome_position) != 2
        or len(kitty_position) != 2
        or int(chrome_position[0]) + 1 != int(kitty_position[0])
    ):
        raise ValueError("Niri did not place Chrome immediately left of Kitty")
    focus_window(environment, kitty_id)
    return chrome_id, kitty_id


def invoke_keys(environment: dict[str, str], *arguments: str) -> None:
    subprocess.run(["wtype", *arguments], check=True, env=environment)


def invoke_keys_for_window(environment: dict[str, str], window_id: int, *arguments: str) -> None:
    if focused_window_id(environment) != window_id:
        raise ValueError(f"refusing input: Niri focus is not intended window id {window_id}")
    invoke_keys(environment, *arguments)


def warm_zsh(environment: dict[str, str], output_directory: Path) -> None:
    """Complete first-run prompt initialization in an owned, unrecorded Kitty."""
    marker = output_directory / "zsh-warmup.ready"
    run_niri(
        environment, "action", "spawn", "--", "kitty", "--title", WARMUP_TITLE,
        "/usr/bin/zsh", "--login", "-i", "-c", 'printf ready > "$1"',
        "zsh", str(marker),
    )
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        windows = niri_json(environment, "windows")
        if marker.is_file() and marker.read_text() == "ready" and not windows:
            return
        time.sleep(0.2)
    raise TimeoutError("the owned Zsh warmup did not finish before recording")


def screen_size_from_png(path: Path) -> tuple[int, int]:
    with path.open("rb") as image:
        header = image.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("grim did not produce a valid PNG image")
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def command_version(command: list[str]) -> str:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:
        return "unavailable"
    return (result.stdout or result.stderr).strip()


def record_renderer_evidence(output: Path, environment: dict[str, str]) -> dict[str, Any]:
    graphics = subprocess.run(["glxinfo", "-B"], text=True, capture_output=True, env=environment)
    graphics_text = graphics.stdout + graphics.stderr
    (output / "graphics-renderer.txt").write_text(graphics_text, encoding="utf-8")
    renderer_lines = {}
    for line in graphics_text.splitlines():
        for label in ("OpenGL vendor string:", "OpenGL renderer string:", "OpenGL version string:"):
            if line.strip().startswith(label):
                renderer_lines[label.removesuffix(":")] = line.split(":", 1)[1].strip()

    journal = subprocess.run(
        ["journalctl", "--user", "-b", "-u", "niri.service", "--no-pager", "-o", "short-iso"],
        text=True,
        capture_output=True,
        env=environment,
    )
    journal_text = journal.stdout + journal.stderr
    (output / "niri-session-log.txt").write_text(journal_text, encoding="utf-8")
    likely_renderer_lines = [
        line for line in journal_text.splitlines()
        if re.search(r"renderer|render node|EGL|OpenGL|Vulkan|GPU", line, re.IGNORECASE)
    ]
    return {
        "glxinfo_exit_code": graphics.returncode,
        "glxinfo_summary": renderer_lines,
        "renderer_evidence_file": "graphics-renderer.txt",
        "niri_log_evidence_file": "niri-session-log.txt",
        "niri_renderer_log_lines": likely_renderer_lines,
    }


def probe_video(path: Path, output_directory: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,width,height,avg_frame_rate,r_frame_rate,pix_fmt,nb_frames,color_range,color_space",
            "-show_entries", "format=duration", "-of", "json", str(path),
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    probe_path = output_directory / "video-probe.json"
    probe_path.write_text(result.stdout, encoding="utf-8")
    payload = json.loads(result.stdout)
    streams = payload.get("streams", [])
    if len(streams) != 1:
        raise ValueError("ffprobe did not find exactly one video stream")
    stream = streams[0]
    duration = float(payload.get("format", {}).get("duration", 0))
    if not 15 <= duration <= 30:
        raise ValueError(f"recording duration is outside the 15-30 second pilot window: {duration:.3f}s")
    if stream.get("codec_name") != "h264":
        raise ValueError(f"expected an H.264 recording, got {stream.get('codec_name')!r}")
    if int(stream.get("width", 0)) <= 0 or int(stream.get("height", 0)) <= 0:
        raise ValueError("ffprobe returned invalid video dimensions")
    return {
        "duration_seconds": round(duration, 3),
        "codec": stream.get("codec_name"),
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "average_frame_rate": stream.get("avg_frame_rate"),
        "reported_frame_rate": stream.get("r_frame_rate"),
        "pixel_format": stream.get("pix_fmt"),
        "color_range": stream.get("color_range", "unspecified"),
        "color_space": stream.get("color_space", "unspecified"),
        "frame_count": stream.get("nb_frames"),
        "sha256": sha256_file(path),
        "probe_file": "video-probe.json",
    }


def verify_terminal_black(still: Path, video: Path, width: int, height: int, duration: float) -> dict[str, Any]:
    """Catch a full/limited-range mismatch in an empty terminal region."""
    x, y = width * 3 // 4, height * 3 // 4
    values = []
    for path, seek in [(still, None), (video, max(0, duration - 1))]:
        command = ["ffmpeg", "-v", "error"]
        if seek is not None:
            command.extend(["-ss", str(seek)])
        command.extend([
            "-i", str(path), "-vf", f"format=rgb24,crop=1:1:{x}:{y}",
            "-frames:v", "1", "-f", "rawvideo", "-",
        ])
        raw = subprocess.check_output(command)
        if len(raw) != 3:
            raise ValueError("cannot decode the terminal black verification pixel")
        values.append(list(raw))
    if values != [[0, 0, 0], [0, 0, 0]]:
        raise ValueError(f"terminal black changed between the still and decoded video: {values}")
    return {"sample_xy": [x, y], "still_rgb": values[0], "decoded_video_rgb": values[1]}


def capture(output_directory: Path) -> dict[str, Any]:
    verify_guest()
    home = Path.home().resolve()
    if os.geteuid() == 0 or os.environ.get("USER") != "demo":
        raise ValueError("run capture as the ordinary demo user, not root")
    setup_receipt = read_setup_receipt()
    environment, socket_path = discover_niri_environment()
    if not isinstance(niri_json(environment, "windows"), list) or niri_json(environment, "windows"):
        raise ValueError("close all guest application windows before capture; the scene uses a clean desktop")
    outputs = set_capture_output_mode(environment)

    for command in ("google-chrome-stable", "kitty", "wtype", "wf-recorder", "grim", "ffprobe"):
        if not shutil_which(command):
            raise ValueError(f"required guest command is unavailable: {command}")

    project_directory = APP_ROOT / "project"
    site_page = APP_ROOT / "site/index.html"
    if site_page.is_symlink() or not site_page.is_file() or not (project_directory / "status.py").is_file():
        raise ValueError("the installed local sample page/project is incomplete")

    profile_directory = home / PROFILE_RELATIVE
    ensure_safe_home_path(profile_directory, home)
    if profile_directory.exists():
        raise ValueError(
            f"isolated Chrome profile already exists: {profile_directory}; remove this guest-only sample profile after closing Chrome before a fresh capture"
        )
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if output_directory.exists():
        raise ValueError(f"capture output already exists: {output_directory}")
    ensure_safe_home_path(output_directory, home)
    output_directory.mkdir(parents=True, exist_ok=False)
    profile_directory.parent.mkdir(parents=True, exist_ok=True)
    profile_directory.mkdir(mode=0o700)
    recording_path = output_directory / "guest-demo.mp4"
    still_path = output_directory / "still.png"
    recorder_log_path = output_directory / "wf-recorder.log"
    page_uri = site_page.resolve().as_uri()
    warm_zsh(environment, output_directory)

    run_niri(
        environment,
        "action", "spawn", "--", "google-chrome-stable",
        f"--user-data-dir={profile_directory}",
        "--ozone-platform=wayland",
        "--force-dark-mode",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-sync",
        "--disable-background-mode",
        "--disable-extensions",
        page_uri,
    )
    run_niri(
        environment,
        "action", "spawn", "--", "kitty",
        "--directory", str(project_directory),
        "--title", KITTY_TITLE,
    )
    windows = wait_for_windows(environment)
    chrome_window_id, kitty_window_id = arrange_scene_windows(environment, windows)
    time.sleep(0.75)
    invoke_keys_for_window(environment, kitty_window_id, "-M", "ctrl", "-k", "l", "-m", "ctrl")
    time.sleep(0.5)

    recorder_command = [
        "wf-recorder", "--file", str(recording_path),
        "--codec", "libx264", "--framerate", str(TARGET_FPS),
        "--pixel-format", "yuv420p", "--codec-param", "color_range=tv",
    ]
    with recorder_log_path.open("w", encoding="utf-8") as recorder_log:
        recorder = subprocess.Popen(recorder_command, stdout=recorder_log, stderr=subprocess.STDOUT, env=environment)
        try:
            time.sleep(1.0)
            if recorder.poll() is not None:
                raise RuntimeError(f"wf-recorder exited during startup; inspect {recorder_log_path}")

            # The visible sequence targets the Niri instance found above. It uses
            # Niri IPC for column focus and wtype for actual browser/terminal keys.
            time.sleep(4.0)
            focus_window(environment, chrome_window_id)
            time.sleep(3.0)
            focus_window(environment, kitty_window_id)
            invoke_keys_for_window(environment, kitty_window_id, "-d", "35", "--", "python3 ./status.py")
            invoke_keys_for_window(environment, kitty_window_id, "-k", "Return")
            time.sleep(4.0)
            focus_window(environment, chrome_window_id)
            time.sleep(0.75)
            invoke_keys_for_window(environment, chrome_window_id, "-k", "Page_Down")
            time.sleep(2.5)
            invoke_keys_for_window(environment, chrome_window_id, "-k", "Page_Down")
            time.sleep(2.5)
            invoke_keys_for_window(environment, chrome_window_id, "-k", "Page_Up")
            time.sleep(1.5)
            invoke_keys_for_window(environment, chrome_window_id, "-M", "ctrl", "-k", "Home", "-m", "ctrl")
            time.sleep(0.5)
            focus_window(environment, kitty_window_id)
            time.sleep(4.0)
        finally:
            if recorder.poll() is None:
                recorder.send_signal(signal.SIGINT)
                try:
                    recorder.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    recorder.terminate()
                    recorder.wait(timeout=5)
        if recorder.returncode not in {0, -signal.SIGINT}:
            raise RuntimeError(f"wf-recorder exited with status {recorder.returncode}; inspect {recorder_log_path}")

    if not recording_path.is_file() or recording_path.stat().st_size == 0:
        raise ValueError("wf-recorder produced no video file")
    subprocess.run(["grim", "-t", "png", str(still_path)], check=True, env=environment)
    image_width, image_height = screen_size_from_png(still_path)
    video = probe_video(recording_path, output_directory)
    if (image_width, image_height) != (video["width"], video["height"]) or (image_width, image_height) != (1920, 1080):
        raise ValueError("still/video dimensions do not match the selected 1920x1080 capture mode")
    black_verification = verify_terminal_black(still_path, recording_path, image_width, image_height, video["duration_seconds"])
    renderer = record_renderer_evidence(output_directory, environment)

    receipt = {
        "schema_version": 1,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "guest": {
            "hostname": "niri-plus-arch",
            "uid": os.getuid(),
            "niri_ipc_socket": str(socket_path),
            "outputs": outputs,
        },
        "public_inputs": setup_receipt.get("public_inputs", {}),
        "software": {
            "niri": command_version(["niri", "--version"]),
            "chrome": command_version(["google-chrome-stable", "--version"]),
            "kitty": command_version(["kitty", "--version"]),
            "zsh": command_version(["zsh", "--version"]),
            "font_matches": setup_receipt.get("fonts", {}),
        },
        "scene": [
            "Hold the local sample page and Kitty project side by side.",
            "Move focus between Niri columns using the scoped compositor IPC.",
            "Type and run the guest-guarded local sample check in Zsh.",
            "Scroll the local Chrome page with Page Down and Page Up key events.",
            "Return focus to the terminal and hold the final frame.",
        ],
        "presentation": {
            "output_mode": CAPTURE_OUTPUT_MODE,
            "chrome_dark_mode": True,
            "zsh_warmup_completed": True,
            "final_page_position": "top",
            "input_route": "guest Niri IPC and focused guest virtual keyboard; no host input injection",
            "terminal_black_verification": black_verification,
        },
        "recording": {
            "path": recording_path.name,
            "settings": {
                "recorder": "wf-recorder",
                "command": ["wf-recorder", "--codec", "libx264", "--framerate", TARGET_FPS, "--pixel-format", "yuv420p", "--codec-param", "color_range=tv"],
                "audio": False,
                "requested_fps": TARGET_FPS,
            },
            **video,
        },
        "still": {
            "path": still_path.name,
            "format": "PNG",
            "width": image_width,
            "height": image_height,
            "sha256": sha256_file(still_path),
        },
        "renderer": renderer,
        "evidence_files": [
            "wf-recorder.log", "graphics-renderer.txt", "niri-session-log.txt", "video-probe.json",
        ],
    }
    (output_directory / "capture-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def shutil_which(command: str) -> str | None:
    from shutil import which
    return which(command)


def main() -> int:
    verify_guest()
    home = Path.home().resolve()
    base = home / "Videos/niri-plus-vm"
    ensure_safe_home_path(base, home)
    base.mkdir(parents=True, exist_ok=True)
    output_directory = base / datetime.now(timezone.utc).strftime("pilot-%Y%m%dT%H%M%SZ")
    receipt = capture(output_directory)
    print(f"Capture saved in {output_directory}")
    print(f"Video: {receipt['recording']['width']}x{receipt['recording']['height']} at {receipt['recording']['average_frame_rate']} for {receipt['recording']['duration_seconds']} seconds")
    print(f"Still: {output_directory / receipt['still']['path']}")
    print(f"Receipt: {output_directory / 'capture-receipt.json'}")
    return 0


if __name__ == "__main__":
    verify_guest()
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(f"capture_scene.py: {error}", file=sys.stderr)
        raise SystemExit(1)
