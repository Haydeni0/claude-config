"""Transform Claude Code agent markdown into opencode agent markdown."""

from pathlib import Path

from sync_opencode.frontmatter import dump, parse
from sync_opencode.sync import Outcome, Status, sync_text

CLAUDE_TO_OPENCODE_TOOLS: dict[str, str] = {
    "Read": "read",
    "Write": "edit",
    "Edit": "edit",
    "apply_patch": "edit",
    "Glob": "glob",
    "Grep": "grep",
    "Bash": "bash",
    "Agent": "task",
    "Task": "task",
    "List": "list",
    "TodoWrite": "todowrite",
    "Skill": "skill",
    "WebFetch": "webfetch",
}

OPENCODE_KEYS_WITH_CLAUDE_EQUIV = set(CLAUDE_TO_OPENCODE_TOOLS.values())


def _parse_tools_list(raw: str | list) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(t).strip() for t in raw]
    return [t.strip() for t in str(raw).split(",") if t.strip()]


def build_permission(frontmatter: dict, warnings: list[str]) -> dict:
    allowed_tools = _parse_tools_list(frontmatter.get("tools"))
    allowed_opencode_keys: set[str] = set()
    for tool in allowed_tools:
        mapped = CLAUDE_TO_OPENCODE_TOOLS.get(tool)
        if mapped is None:
            warnings.append(f"Unknown Claude Code tool '{tool}' in agent '{frontmatter.get('name')}': skipped")
            continue
        allowed_opencode_keys.add(mapped)

    permission: dict = {}
    for key in sorted(OPENCODE_KEYS_WITH_CLAUDE_EQUIV):
        if key == "skill":
            continue
        permission[key] = "allow" if key in allowed_opencode_keys else "deny"

    skills = frontmatter.get("skills") or []
    if skills:
        skill_perm: dict = {"*": "deny"}
        for skill in skills:
            skill_perm[str(skill)] = "allow"
        permission["skill"] = skill_perm

    return permission


def transform_agent(markdown: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    frontmatter, body = parse(markdown)
    permission = build_permission(frontmatter, warnings)

    opencode_fm = {k: v for k, v in frontmatter.items() if k not in ("tools", "disallowedTools", "skills")}
    opencode_fm["permission"] = permission
    opencode_fm.setdefault("mode", "subagent")

    return dump(opencode_fm, body), warnings


def sync_agents_dir(target_dir: Path, source_dir: Path, force: bool = False, dry_run: bool = False) -> list[Outcome]:
    outcomes: list[Outcome] = []
    target_dir.mkdir(parents=True, exist_ok=True)

    source_names = {p.name for p in source_dir.glob("*.md") if p.is_file()}
    for source_file in sorted(source_dir.glob("*.md"), key=lambda p: p.name):
        if not source_file.is_file():
            continue
        transformed, warnings = transform_agent(source_file.read_text())
        for w in warnings:
            outcomes.append(Outcome(source_file, Status.WARNED, w))
        target_file = target_dir / source_file.name
        outcomes.append(sync_text(target_file, transformed, force=force, dry_run=dry_run))

    for target_file in sorted(target_dir.glob("*.md"), key=lambda p: p.name):
        if target_file.name not in source_names:
            if dry_run:
                outcomes.append(Outcome(target_file, Status.WOULD_REPLACE, "orphan (would delete)"))
                continue
            if not force:
                outcomes.append(Outcome(target_file, Status.WARNED, "orphan not in source; use --force to remove"))
                continue
            target_file.unlink()
            outcomes.append(Outcome(target_file, Status.REPLACED, "deleted orphan"))

    return outcomes
