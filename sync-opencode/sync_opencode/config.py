"""Read the base opencode config from ~/.claude and write the generated opencode.json."""

import json
import re
from pathlib import Path

from sync_opencode.sync import Outcome, Status, sync_text

OPENCODE_SCHEMA = "https://opencode.ai/config.json"
TUI_SCHEMA = "https://opencode.ai/tui.json"

_LINE_COMMENT = re.compile(r"//[^\n]*")
_TRAILING_COMMA = re.compile(r",(\s*[}\]])")


def _strip_jsonc(text: str) -> str:
    out: list[str] = []
    i = 0
    n = len(text)
    in_string = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        out.append(ch)
        i += 1
    stripped = "".join(out)
    return _TRAILING_COMMA.sub(r"\1", stripped)


def _merge_legacy_jsonc(target: Path, config: dict) -> bool:
    jsonc = target.with_suffix(".jsonc")
    if not jsonc.is_file():
        return True
    try:
        legacy = json.loads(_strip_jsonc(jsonc.read_text()))
    except json.JSONDecodeError:
        return False
    for key, value in legacy.items():
        if key == "$schema":
            continue
        config[key] = value
    jsonc.unlink()
    return True


def build_config(base_path: Path) -> dict:
    if base_path.is_file():
        config = json.loads(base_path.read_text())
    else:
        config = {}
    config.setdefault("$schema", OPENCODE_SCHEMA)
    return config


def sync_config(target: Path, base_path: Path, force: bool = False, dry_run: bool = False) -> Outcome:
    config = build_config(base_path)
    if not dry_run:
        if not _merge_legacy_jsonc(target, config):
            return Outcome(
                target,
                Status.WARNED,
                f"could not parse existing {target.with_suffix('.jsonc')}; fix or remove it manually",
            )
    content = json.dumps(config, indent=2) + "\n"
    return sync_text(target, content, force=force, dry_run=dry_run)


def build_tui(base_path: Path) -> dict:
    if base_path.is_file():
        config = json.loads(base_path.read_text())
    else:
        config = {}
    config.setdefault("$schema", TUI_SCHEMA)
    return config


def sync_tui(target: Path, base_path: Path, force: bool = False, dry_run: bool = False) -> Outcome:
    config = build_tui(base_path)
    content = json.dumps(config, indent=2) + "\n"
    return sync_text(target, content, force=force, dry_run=dry_run)
