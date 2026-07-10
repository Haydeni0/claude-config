"""Resolve the highest-cached superpowers version and symlink its opencode plugin."""

import re
from pathlib import Path

from sync_opencode.sync import Outcome, Status, sync_symlink

_SUPERPOWERS_ROOT = Path("claude-plugins-official") / "superpowers"
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _parse_semver(name: str) -> tuple[int, ...]:
    return tuple(int(p) for p in name.split("."))


def resolve_superpowers_js(cache_root: Path) -> Path | None:
    superpowers_dir = cache_root / _SUPERPOWERS_ROOT
    if not superpowers_dir.is_dir():
        return None
    versions = [d.name for d in superpowers_dir.iterdir() if d.is_dir() and _VERSION_RE.match(d.name)]
    if not versions:
        return None
    highest = max(versions, key=_parse_semver)
    js = superpowers_dir / highest / ".opencode" / "plugins" / "superpowers.js"
    return js if js.is_file() else None


def sync_superpowers(target: Path, cache_root: Path, force: bool = False, dry_run: bool = False) -> Outcome:
    source = resolve_superpowers_js(cache_root)
    if source is None:
        return Outcome(target, Status.NO_SOURCE, "superpowers not found in cache")
    return sync_symlink(target, source, force=force, dry_run=dry_run)
