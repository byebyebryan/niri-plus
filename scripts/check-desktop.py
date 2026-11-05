#!/usr/bin/env python3
"""Check portable desktop examples using isolated files and command stubs."""
import argparse
import configparser
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", action="store_true", help="Also validate Niri fragments and desktop entries with installed tools")
    args = parser.parse_args()
    power = load("niri_plus_example_power", ROOT / "examples/session/desktop-power")
    greeter = load("niri_plus_example_greeter", ROOT / "examples/login/derive-theme.py")
    identity = json.loads((ROOT / "design/identity.json").read_text()) if (ROOT / "design/identity.json").exists() else json.loads((ROOT / "data/identity.json").read_text())
    policy = __import__("tomllib").loads((ROOT / "examples/session/power.toml.example").read_text())
    checks = 0
    with tempfile.TemporaryDirectory(prefix="niri-plus-desktop-check-") as temporary:
        base = Path(temporary)
        config = base / "config"
        file = config / "desktop-session/power.toml"
        file.parent.mkdir(parents=True)
        with mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(config)}):
            for content in ("", "ac_monitor_timeout = true\n"):
                file.write_text(content)
                try:
                    power.load_policy()
                except (KeyError, ValueError):
                    pass
                else:
                    raise AssertionError("incomplete/invalid idle policy was admitted")
                checks += 1
            file.write_text((ROOT / "examples/session/power.toml.example").read_text())
            assert power.load_policy() == policy
            checks += 1
        ac = power.idle_command(policy, False, executable=base / "helper with spaces")
        battery = power.idle_command(policy, True, executable=base / "helper with spaces")
        assert "1800" not in ac and "1800" in battery
        assert ac[:4] == ["swayidle", "-w", "-C", "/dev/null"]
        assert ac[ac.index("before-sleep") + 1] == power.DISPLAY_OFF
        assert battery[-2:] == ["lock", power.LOCK]
        assert power.LOCK in power.idle_command(dict(policy, lock_before_suspend=True), True)[-5]
        calls = []
        fake = lambda command, **kwargs: calls.append(command)
        power.maybe_suspend(policy, True, power=lambda: False, run=fake)
        power.maybe_suspend(policy, False, power=lambda: False, run=fake)
        assert not calls
        power.maybe_suspend(policy, True, power=lambda: True, run=fake)
        assert calls == [["systemctl", "suspend"]]
        checks += 7

        supplies = base / "supplies"
        peripheral = supplies / "peripheral"
        peripheral.mkdir(parents=True)
        for key, value in {"type": "Battery", "scope": "Device", "status": "Discharging"}.items():
            (peripheral / key).write_text(value)
        assert not power.on_battery(supplies)
        system = supplies / "BAT0"
        system.mkdir()
        for key, value in {"type": "Battery", "scope": "System", "status": "Discharging", "present": "1"}.items():
            (system / key).write_text(value)
        assert power.on_battery(supplies)
        adapter = supplies / "AC"
        adapter.mkdir()
        (adapter / "type").write_text("Mains")
        (adapter / "online").write_text("1")
        assert not power.on_battery(supplies)
        alert = power.BatteryAlert(10)
        alerts = []
        for percent in [10, 9, 13, 10]:
            alert.update({"present": "yes", "state": "discharging", "percentage": f"{percent}%"}, alerts.append)
        assert alerts == [10, 10]
        checks += 4

        upstream = base / "upstream"
        upstream.mkdir()
        (upstream / "Main.qml").write_text('color: "#1e1e2e"\nerror: "#f38ba8"\n')
        output = base / "derived"
        derived = greeter.derive(upstream, output, identity)
        colors = (identity.get("direction") or next(x for x in identity["candidates"] if x["id"] == "neutral-slate"))["colors"]
        assert colors["secure_surface"] in (derived / "Main.qml").read_text()
        assert colors["error"] in (derived / "Main.qml").read_text()
        assert "Font=Noto Sans" in (derived / "theme.conf.user").read_text()
        before = (derived / "Main.qml").read_bytes()
        try:
            greeter.derive(upstream, output, identity)
        except ValueError:
            pass
        else:
            raise AssertionError("existing greeter output was overwritten")
        assert (derived / "Main.qml").read_bytes() == before
        (upstream / "linked.qml").symlink_to(upstream / "Main.qml")
        try:
            greeter.derive(upstream, base / "symlink-output", identity)
        except ValueError:
            pass
        else:
            raise AssertionError("symlink greeter source was accepted")
        assert not (base / "symlink-output").exists()
        checks += 6

        bindir = base / "bin"
        bindir.mkdir()
        log = base / "commands.jsonl"
        shim = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
command = Path(sys.argv[0]).name
with Path(os.environ["NIRI_DESKTOP_CHECK_LOG"]).open("a") as stream:
    stream.write(json.dumps([command, *sys.argv[1:]]) + "\\n")
if command == "wpctl" and sys.argv[1:2] == ["get-volume"]:
    print(os.environ.get("NIRI_DESKTOP_CHECK_VOLUME", "Volume: 0.42"))
if command == "brightnessctl" and sys.argv[-1:] == ["info"]:
    print("fixture,backlight,42,42%,100")
'''
        for command in ("wpctl", "notify-send", "brightnessctl"):
            path = bindir / command
            path.write_text(shim)
            path.chmod(0o755)
        env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ["PATH"], NIRI_DESKTOP_CHECK_LOG=str(log))
        volume = ROOT / "examples/feedback/notify-volume"
        for action in ("show", "mic-show", "up"):
            subprocess.run(["bash", str(volume), action], env=env, check=True, capture_output=True)
        commands = [json.loads(line) for line in log.read_text().splitlines()]
        popups = [command for command in commands if command[0] == "notify-send"]
        assert len(popups) == 3
        assert all("--hint=boolean:transient:true" in command and "--hint=boolean:suppress-sound:true" in command for command in popups)
        assert any("string:x-canonical-private-synchronous:microphone" in argument for command in popups for argument in command)
        assert ["wpctl", "set-volume", "--limit", "1.0", "@DEFAULT_AUDIO_SINK@", "5%+"] in commands
        for action, reading, icon, value, summary in (
            ("show", "Volume: 0.00", "audio-volume-low-symbolic", 0, "Volume: 0%"),
            ("down", "Volume: 0.20", "audio-volume-low-symbolic", 20, "Volume: 20%"),
            ("show", "Volume: 0.42", "audio-volume-medium-symbolic", 42, "Volume: 42%"),
            ("up", "Volume: 1.50", "audio-volume-high-symbolic", 100, "Volume: 150%"),
            ("mute", "Volume: 0.42 [MUTED]", "audio-volume-muted-symbolic", 0, "Volume: Muted (42%)"),
            ("mic-show", "Volume: 0.70", "microphone-sensitivity-high-symbolic", 70, "Microphone: On (70%)"),
            ("mic-mute", "Volume: 0.42 [MUTED]", "microphone-sensitivity-muted-symbolic", 0, "Microphone: Muted (42%)"),
        ):
            log.write_text("")
            subprocess.run(["bash", str(volume), action],
                           env=dict(env, NIRI_DESKTOP_CHECK_VOLUME=reading), check=True, capture_output=True)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            popup, = [call for call in calls if call[0] == "notify-send"]
            assert f"--icon={icon}" in popup and f"--hint=int:value:{value}" in popup
            assert popup[-1] == summary and "--expire-time=1500" in popup
            assert "--hint=boolean:transient:true" in popup and "--hint=boolean:suppress-sound:true" in popup
            tag = "microphone" if action.startswith("mic-") else "volume"
            assert f"--hint=string:x-canonical-private-synchronous:{tag}" in popup
            if action in ("show", "mic-show"):
                assert [call for call in calls if call[0] == "wpctl"] == [
                    ["wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@" if tag == "microphone" else "@DEFAULT_AUDIO_SINK@"]]
            checks += 1

        # Override only backlight discovery; every device command remains a stub.
        bash_env = base / "backlight-discovery.bash"
        bash_env.write_text('compgen() { return "$NIRI_DESKTOP_CHECK_BACKLIGHT_STATUS"; }\n')
        brightness = ROOT / "examples/feedback/notify-brightness"
        for status in ("0", "1"):
            for action in ("show", "up", "down"):
                log.write_text("")
                subprocess.run(["bash", str(brightness), action], env=dict(
                    env, BASH_ENV=str(bash_env), NIRI_DESKTOP_CHECK_BACKLIGHT_STATUS=status),
                    check=True, capture_output=True)
                calls = [json.loads(line) for line in log.read_text().splitlines()]
                if status == "1":
                    assert not calls
                else:
                    popup, = [call for call in calls if call[0] == "notify-send"]
                    assert "--icon=display-brightness-symbolic" in popup and popup[-1] == "Brightness: 42%"
                    assert "--hint=int:value:42" in popup and "--expire-time=1500" in popup
                    assert "--hint=string:x-canonical-private-synchronous:brightness" in popup
                    assert "--hint=boolean:transient:true" in popup and "--hint=boolean:suppress-sound:true" in popup
                    if action == "down":
                        assert ["brightnessctl", "--class=backlight", "--min-value=1", "set", "5%-"] in calls
                    if action == "show":
                        assert len(calls) == 2
                checks += 1
        for helper in (volume, ROOT / "examples/feedback/notify-brightness"):
            subprocess.run(["bash", "-n", str(helper)], check=True)
        checks += 6

    entries = sorted((ROOT / "examples/desktop").glob("*.desktop")) + [ROOT / "examples/files/nvim-terminal.desktop"]
    for path in entries:
        entry = configparser.ConfigParser(interpolation=None)
        entry.read(path)
        assert entry["Desktop Entry"]["Type"] == "Application" and entry["Desktop Entry"]["Exec"]
        checks += 1
    if args.native:
        for command in ("niri", "desktop-file-validate"):
            assert shutil.which(command), f"missing native validator: {command}"
        for path in entries:
            subprocess.run(["desktop-file-validate", str(path)], check=True)
            checks += 1
        for name in ("examples/niri/config.kdl", "examples/feedback/binds.kdl"):
            subprocess.run(["niri", "validate", "--config", str(ROOT / name)], check=True, capture_output=True)
            checks += 1
    print(json.dumps({"checks": checks, "native": args.native, "live_desktop_operations": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
