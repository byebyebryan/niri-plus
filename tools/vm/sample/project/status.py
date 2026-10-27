#!/usr/bin/env python3
"""Show actual local fixture checks with the terminal's semantic ANSI colors."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parent
GUARD = ROOT / "tools" / "guest-guard.sh"


def main() -> int:
    # The project is deliberately guest-only even though its checks are small.
    subprocess.run([str(GUARD)], check=True, stdout=subprocess.DEVNULL)
    checks = (
        ("Local page is present", (ROOT / "site" / "index.html").is_file()),
        ("Python project is ready", (PROJECT / "status.py").is_file() and sys.version_info >= (3, 10)),
        ("Setup receipt is present", (ROOT / "setup-receipt.json").is_file()),
    )
    print("Niri Plus · guest sample")
    for label, passed in checks:
        color = "\033[32m" if passed else "\033[31m"
        status = "✓" if passed else "✗"
        print(f"{color}{status} {label}\033[0m")
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
