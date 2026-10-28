#!/usr/bin/env python3
"""Small guest-only native input/capture helper for the Arch desktop scenes.

Read one JSON operation on stdin. This is lab tooling, not a desktop service.
The installed pilot's guard and socket discovery run before every operation.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

import capture_scene as pilot


def main() -> None:
    pilot.verify_guest()
    if os.geteuid() == 0 or Path.home() != Path('/home/demo'):
        raise ValueError('run as the ordinary demo user')
    environment, _ = pilot.discover_niri_environment()
    request = json.load(sys.stdin)
    action = request['action']
    result: object = None
    if action == 'windows':
        result = pilot.niri_json(environment, 'windows')
    elif action == 'wait-window':
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            matches = [window for window in pilot.niri_json(environment, 'windows')
                       if window.get('app_id') == request['app_id']]
            if len(matches) == 1:
                result = matches[0]
                break
            time.sleep(.1)
        else:
            raise TimeoutError('expected one native window for ' + request['app_id'])
    elif action == 'spawn':
        pilot.run_niri(environment, 'action', 'spawn', '--', *request['arguments'])
    elif action == 'keys':
        if 'id' in request:
            pilot.focus_window(environment, int(request['id']))
        subprocess.run(['wtype', *request['arguments']], env=environment, check=True)
    elif action in {'focus', 'close'}:
        window_id = int(request['id'])
        if window_id not in {int(w['id']) for w in pilot.niri_json(environment, 'windows')}:
            raise ValueError('window disappeared')
        pilot.focus_window(environment, window_id)
        if action == 'close':
            pilot.run_niri(environment, 'action', 'close-window')
    elif action in {'start-recording', 'stop-recording', 'screenshot'}:
        name = request['name']
        if not re.fullmatch(r'[a-z][a-z0-9-]{0,47}', name):
            raise ValueError('invalid scene name')
        state = Path.home() / '.local/state/niri-plus-desktop/recordings'
        pilot.ensure_safe_home_path(state, Path.home())
        state.mkdir(parents=True, exist_ok=True)
        receipt = state / (name + '.json')
        pilot.ensure_safe_home_path(receipt, Path.home())
        if action == 'start-recording':
            if receipt.exists():
                raise ValueError('scene receipt already exists; use a new scene name')
            pilot.set_capture_output_mode(environment)
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            directory = Path.home() / 'Videos/niri-plus-vm' / ('desktop-' + name + '-' + stamp)
            pilot.ensure_safe_home_path(directory, Path.home())
            directory.mkdir(parents=True, exist_ok=False)
            video = directory / 'native.mp4'
            with (directory / 'recorder.log').open('x') as log:
                process = subprocess.Popen([
                    'wf-recorder', '--file', str(video), '--codec', 'libx264',
                    '--framerate', '30', '--no-damage', '--pixel-format', 'yuv420p',
                    '--codec-param', 'color_range=tv',
                ], env=environment, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True)
            time.sleep(.5)
            if process.poll() is not None:
                raise RuntimeError('recorder failed; inspect its log')
            started = (Path('/proc') / str(process.pid) / 'stat').read_text().split(') ', 1)[1].split()[19]
            result = {'pid': process.pid, 'pid_start_ticks': started, 'directory': str(directory), 'video': str(video)}
            with receipt.open('x') as stream:
                json.dump(result, stream)
        else:
            result = json.loads(receipt.read_text())
            directory = Path(result['directory'])
            pilot.ensure_safe_home_path(directory, Path.home())
            if not directory.is_relative_to(Path.home() / 'Videos/niri-plus-vm'):
                raise ValueError('recording directory escaped the lab')
            if Path(result['video']) != directory / 'native.mp4':
                raise ValueError('recording video path changed')
            pilot.ensure_safe_home_path(Path(result['video']), Path.home())
            if action == 'screenshot':
                target = directory / 'still.png'
                pilot.ensure_safe_home_path(target, Path.home())
                if target.exists():
                    raise ValueError('still already exists')
                subprocess.run(['grim', str(target)], env=environment, check=True)
            else:
                process = Path('/proc') / str(int(result['pid']))
                arguments = (process / 'cmdline').read_bytes().split(b'\0')
                started = (process / 'stat').read_text().split(') ', 1)[1].split()[19]
                if process.stat().st_uid != os.getuid() or started != result['pid_start_ticks'] or str(result['video']).encode() not in arguments or b'wf-recorder' not in arguments[0]:
                    raise ValueError('recording process identity changed')
                os.kill(int(result['pid']), signal.SIGINT)
                for _ in range(100):
                    try:
                        status = (process / 'stat').read_text().split(') ', 1)[1]
                    except FileNotFoundError:
                        break
                    if status.startswith('Z '):
                        break
                    time.sleep(.1)
                else:
                    raise TimeoutError('recorder did not finish')
                subprocess.run(['ffmpeg', '-v', 'error', '-i', result['video'], '-f', 'null', '-'], check=True)
                result['completed'] = True
                receipt.write_text(json.dumps(result) + '\n')
    else:
        raise ValueError('unknown native desktop operation')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
