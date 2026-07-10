"""Sync ~/.claude config into ~/.pi/agent (the pi harness)."""

from pathlib import Path

from settings_sync.agents_md import build_agents_md
from settings_sync.sync import Outcome, Status, sync_text


def sync_pi_config(target: Path, template: Path, dry_run: bool = False) -> Outcome:
    """Wholesale-copy the pointer template into <agent>/settings.json.

    pi's settings.json is fully owned by the template (single source of truth
    in ~/.claude). pi's own state keys (e.g. lastChangelogVersion) are disposable:
    overwriting them makes pi re-show the changelog once, then pi rewrites the
    key. Diverging targets are always overwritten (no --force needed), unlike
    sync_config which protects hand-edits.
    """
    if not template.is_file():
        return Outcome(target, Status.NO_SOURCE, f"template not found: {template}")
    content = template.read_text()
    return sync_text(target, content, force=True, dry_run=dry_run)


def sync_pi_context(target: Path, claude_md: Path, force: bool = False, dry_run: bool = False) -> Outcome:
    """Inline CLAUDE.md (@imports expanded, @skills/x rewritten) into <agent>/CLAUDE.md.

    pi can't expand @ imports, so we inline them here (same transform opencode's
    AGENTS.md uses, via build_agents_md with rules_path=None). Refuses to clobber
    a diverging file without --force, matching AGENTS.md handling.
    """
    if not claude_md.is_file():
        return Outcome(target, Status.NO_SOURCE, f"CLAUDE.md not found: {claude_md}")
    content = build_agents_md(claude_md, rules_path=None)
    return sync_text(target, content, force=force, dry_run=dry_run)
