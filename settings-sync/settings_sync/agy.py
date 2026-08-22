"""Sync AGY (Antigravity) config from ~/.claude."""

import shutil
from pathlib import Path

from settings_sync.agents_md import sync_agents_md
from settings_sync.sync import Outcome, Status, sync_symlink


def sync_agy_agents_md(
    target: Path,
    claude_md: Path,
    force: bool = False,
    dry_run: bool = False,
) -> Outcome:
    """Sync CLAUDE.md -> AGENTS.md (rewriting @skills/<n> refs)."""
    return sync_agents_md(target, claude_md, force=force, dry_run=dry_run)


def sync_agy_skills(
    target_dir: Path,
    source_dir: Path,
    force: bool = False,
    dry_run: bool = False,
) -> list[Outcome]:
    """Symlink each skill in source_dir into target_dir and remove orphans."""
    outcomes: list[Outcome] = []
    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    source_names: set[str] = set()
    if source_dir.is_dir():
        for source_skill in sorted(source_dir.iterdir(), key=lambda p: p.name):
            if not source_skill.is_dir():
                continue
            source_names.add(source_skill.name)
            target_skill = target_dir / source_skill.name
            outcomes.append(sync_symlink(target_skill, source_skill, force=force, dry_run=dry_run))

    if target_dir.is_dir():
        for target_skill in sorted(target_dir.iterdir(), key=lambda p: p.name):
            if target_skill.name not in source_names:
                if dry_run:
                    outcomes.append(Outcome(target_skill, Status.WOULD_REPLACE, "orphan (would delete)"))
                    continue
                if not force:
                    outcomes.append(Outcome(target_skill, Status.WARNED, "orphan; use --force to remove"))
                    continue
                if target_skill.is_dir() and not target_skill.is_symlink():
                    shutil.rmtree(target_skill)
                else:
                    target_skill.unlink()
                outcomes.append(Outcome(target_skill, Status.REPLACED, "deleted orphan"))

    return outcomes
