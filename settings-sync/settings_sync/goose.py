"""Sync ~/.claude config into ~/.config/goose (the goose harness)."""

from pathlib import Path

from settings_sync.agents_md import build_agents_md
from settings_sync.sync import Outcome, Status, sync_text


def sync_goose_hints(target: Path, claude_md: Path, force: bool = False, dry_run: bool = False) -> Outcome:
    """Inline CLAUDE.md (@imports expanded, @skills/x rewritten) into .goosehints.

    goose supports @ imports natively, but we inline them for consistency with
    opencode (AGENTS.md) and pi (CLAUDE.md) - single self-contained file, no
    dependency on goose's @ resolution behaviour. Same transform via
    build_agents_md with rules_path=None. Refuses to clobber a diverging file
    without --force.
    """
    if not claude_md.is_file():
        return Outcome(target, Status.NO_SOURCE, f"CLAUDE.md not found: {claude_md}")
    content = build_agents_md(claude_md, rules_path=None)
    return sync_text(target, content, force=force, dry_run=dry_run)


def sync_goose_config(target: Path, source: Path, force: bool = False, dry_run: bool = False) -> Outcome:
    """Copy ~/.claude/goose/config.yaml into ~/.config/goose/config.yaml.

    The template is the source of truth for base settings (e.g. telemetry).
    Refuses to clobber a diverging file without --force - machine-specific
    settings (provider, model) set via `goose configure` or env vars are
    preserved. Use --force to reset to the template.
    """
    if not source.is_file():
        return Outcome(target, Status.NO_SOURCE, f"config source not found: {source}")
    content = source.read_text()
    return sync_text(target, content, force=force, dry_run=dry_run)


def sync_goose_providers(target_dir: Path, source_dir: Path, force: bool = False, dry_run: bool = False) -> list[Outcome]:
    """Sync ~/.claude/goose/custom_providers/*.json into ~/.config/goose/custom_providers/.

    Each provider JSON is copied as-is (no transform). Orphaned target files
    not in source are warned (or removed with --force), matching the agents dir
    pattern.
    """
    outcomes: list[Outcome] = []

    if not source_dir.is_dir():
        outcomes.append(Outcome(target_dir, Status.NO_SOURCE, f"providers source dir not found: {source_dir}"))
        return outcomes

    if dry_run:
        source_names = {p.name for p in source_dir.glob("*.json") if p.is_file()}
        for source_file in sorted(source_dir.glob("*.json"), key=lambda p: p.name):
            if not source_file.is_file():
                continue
            outcomes.append(sync_text(target_dir / source_file.name, source_file.read_text(), force, dry_run))
        for target_file in sorted(target_dir.glob("*.json"), key=lambda p: p.name) if target_dir.is_dir() else []:
            if target_file.name not in source_names:
                outcomes.append(Outcome(target_file, Status.WOULD_REPLACE, "orphan (would delete)"))
        return outcomes

    target_dir.mkdir(parents=True, exist_ok=True)

    source_names = {p.name for p in source_dir.glob("*.json") if p.is_file()}

    for source_file in sorted(source_dir.glob("*.json"), key=lambda p: p.name):
        if not source_file.is_file():
            continue
        outcomes.append(sync_text(target_dir / source_file.name, source_file.read_text(), force, dry_run))

    for target_file in sorted(target_dir.glob("*.json"), key=lambda p: p.name):
        if target_file.name not in source_names:
            if not force:
                outcomes.append(Outcome(target_file, Status.WARNED, "orphan not in source; use --force to remove"))
                continue
            target_file.unlink()
            outcomes.append(Outcome(target_file, Status.REPLACED, "deleted orphan"))

    return outcomes
