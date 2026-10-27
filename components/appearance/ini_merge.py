"""Preserve unmanaged INI data while updating explicitly managed keys."""

import re
import sys


def merge_ini(text, managed, merge_value=None):
    """Merge section/key values while retaining unrelated text and line endings."""
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)
    pending = {section: dict(values) for section, values in managed.items()}
    merge = merge_value if merge_value is not None else lambda section, key, current, desired: desired
    output = []
    section = None
    seen_sections = set()
    seen_keys = set()

    def finish_section():
        if section not in pending:
            return
        remaining = pending[section]
        if remaining and output and not output[-1].endswith(("\n", "\r")):
            output[-1] += newline
        for key, value in remaining.items():
            output.append(f"{key}={value}{newline}")
        pending[section] = {}

    for line in lines:
        header = re.match(r"^\s*\[([^\]]+)\]\s*(?:[;#].*)?(?:\r?\n)?$", line)
        if header:
            finish_section()
            section = header.group(1)
            seen_sections.add(section)
            output.append(line)
            continue
        assignment = re.match(r"^\s*([^=;#]+?)\s*=(.*?)(?:\r?\n)?$", line)
        if section in managed and assignment:
            key = assignment.group(1).strip()
            if key in managed[section]:
                identity = (section, key)
                if identity in seen_keys:
                    continue
                seen_keys.add(identity)
                value = merge(section, key, assignment.group(2), str(managed[section][key]))
                pending[section].pop(key, None)
                if assignment.group(2) == value:
                    output.append(line)
                else:
                    output.append(f"{key}={value}{newline}")
                continue
        output.append(line)
    finish_section()
    for name, values in pending.items():
        if name in seen_sections or not values:
            continue
        if output:
            if not output[-1].endswith(("\n", "\r")):
                output[-1] += newline
            if output[-1].strip():
                output.append(newline)
        output.append(f"[{name}]{newline}")
        for key, value in values.items():
            output.append(f"{key}={value}{newline}")
    return "".join(output)


# When included into the existing managed KDE script, `managed` and an optional
# `merge_value` are already present in the shared globals namespace.
if "managed" in globals():
    sys.stdout.write(merge_ini(sys.stdin.read(), managed, globals().get("merge_value")))
