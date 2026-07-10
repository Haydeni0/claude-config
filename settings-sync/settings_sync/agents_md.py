"""Expand CLAUDE.md @ imports into a self-contained AGENTS.md."""

import re
from pathlib import Path

from settings_sync.sync import Outcome, sync_text

SKILLS_REF = re.compile(r"@skills/([a-zA-Z0-9_-]+)")
IMPORT_LINE = re.compile(r"^@(\S+\.md)\s*$", re.MULTILINE)


def _rewrite_skills_refs(markdown: str) -> str:
    return SKILLS_REF.sub(r"the `\1` skill", markdown)


def _expand_imports(markdown: str, base_dir: Path, seen: set[Path]) -> str:
    def replace(match: re.Match) -> str:
        rel = match.group(1)
        path = (base_dir / rel).resolve()
        if not path.is_file():
            return match.group(0)
        if path in seen:
            return f"<!-- already imported: {rel} -->"
        seen.add(path)
        content = path.read_text()
        return _expand_imports(content, base_dir, seen)

    return IMPORT_LINE.sub(replace, markdown)


def build_agents_md(claude_md: Path, rules_path: Path | None = None) -> str:
    base_dir = claude_md.parent
    markdown = claude_md.read_text()
    markdown = _rewrite_skills_refs(markdown)
    markdown = _expand_imports(markdown, base_dir, set())
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
    content = build_agents_md(claude_md, rules_path=rules_path)
    return sync_text(target, content, force=force, dry_run=dry_run)
