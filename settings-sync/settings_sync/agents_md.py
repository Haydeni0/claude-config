"""Build AGENTS.md from CLAUDE.md (rewriting @skills/<n> refs)."""

import re
from pathlib import Path

from settings_sync.sync import Outcome, Status, sync_text

SKILLS_REF = re.compile(r"@skills/([a-zA-Z0-9_-]+)")


def _rewrite_skills_refs(markdown: str) -> str:
    return SKILLS_REF.sub(r"the `\1` skill", markdown)


def build_agents_md(claude_md: Path, rules_path: Path | None = None) -> str:
    markdown = claude_md.read_text()
    markdown = _rewrite_skills_refs(markdown)
    if rules_path is not None and rules_path.is_file():
        markdown = markdown.rstrip() + "\n\n" + rules_path.read_text()
    return markdown


def sync_agents_md(
    target: Path,
    claude_md: Path,
    force: bool = False,
    dry_run: bool = False,
    rules_path: Path | None = None,
) -> Outcome:
    if not claude_md.is_file():
        return Outcome(target, Status.NO_SOURCE, f"CLAUDE.md not found: {claude_md}")
    content = build_agents_md(claude_md, rules_path=rules_path)
    return sync_text(target, content, force=force, dry_run=dry_run)
