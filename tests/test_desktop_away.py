"""Include the isolated away-mode checks in normal CI discovery."""
from pathlib import Path
import runpy
import unittest

_checks = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/check-desktop-away.py"))
for _name, _value in _checks.items():
    if isinstance(_value, type) and issubclass(_value, unittest.TestCase):
        globals()[_name] = _value
del _checks, _name, _value
