import os
import pathlib
from typer.testing import CliRunner

from settings_sync.agy import sync_agy_agents_md, sync_agy_skills
from settings_sync.cli import Paths, app, run_agy
from settings_sync.sync import Status


def test_sync_agy_agents_md(tmp_path: pathlib.Path):
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# Rules\nSee @skills/uv for info.\n")
    target = tmp_path / "AGENTS.md"

    outcome = sync_agy_agents_md(target, claude_md)

    assert outcome.status == Status.CREATED
    assert target.is_file()
    assert "the `uv` skill" in target.read_text()


def test_sync_agy_skills_symlinks(tmp_path: pathlib.Path):
    source_dir = tmp_path / "claude" / "skills"
    (source_dir / "uv").mkdir(parents=True)
    (source_dir / "uv" / "SKILL.md").write_text("---\nname: uv\ndescription: d\n---\nBody\n")
    (source_dir / "pytest").mkdir(parents=True)
    (source_dir / "pytest" / "SKILL.md").write_text("---\nname: pytest\ndescription: d\n---\nBody\n")

    target_dir = tmp_path / "gemini" / "skills"

    outcomes = sync_agy_skills(target_dir, source_dir)

    assert len(outcomes) == 2
    assert all(o.status == Status.CREATED for o in outcomes)
    assert (target_dir / "uv").is_symlink()
    assert (target_dir / "pytest").is_symlink()
    assert os.readlink(target_dir / "uv") == "../../claude/skills/uv"


def test_sync_agy_skills_orphan_handling(tmp_path: pathlib.Path):
    source_dir = tmp_path / "claude" / "skills"
    (source_dir / "uv").mkdir(parents=True)
    (source_dir / "uv" / "SKILL.md").write_text("---\nname: uv\ndescription: d\n---\nBody\n")

    target_dir = tmp_path / "gemini" / "skills"
    target_dir.mkdir(parents=True)
    # create orphan
    (target_dir / "old-skill").mkdir(parents=True)

    # Without force, warn
    outcomes = sync_agy_skills(target_dir, source_dir, force=False)
    orphan_outcomes = [o for o in outcomes if "old-skill" in str(o.path)]
    assert len(orphan_outcomes) == 1
    assert orphan_outcomes[0].status == Status.WARNED
    assert (target_dir / "old-skill").exists()

    # With force, removed
    outcomes = sync_agy_skills(target_dir, source_dir, force=True)
    orphan_outcomes = [o for o in outcomes if "old-skill" in str(o.path)]
    assert len(orphan_outcomes) == 1
    assert orphan_outcomes[0].status == Status.REPLACED
    assert not (target_dir / "old-skill").exists()


def test_sync_agy_skills_dry_run_does_not_create_dir(tmp_path: pathlib.Path):
    source_dir = tmp_path / "claude" / "skills"
    (source_dir / "uv").mkdir(parents=True)
    (source_dir / "uv" / "SKILL.md").write_text("---\nname: uv\ndescription: d\n---\nBody\n")

    target_dir = tmp_path / "gemini" / "skills"

    outcomes = sync_agy_skills(target_dir, source_dir, dry_run=True)
    assert not target_dir.exists()
    assert len(outcomes) == 1
    assert outcomes[0].status == Status.WOULD_CREATE


runner = CliRunner()


def test_cli_agy_all(tmp_path: pathlib.Path):
    claude = tmp_path / "claude"
    claude.mkdir(parents=True)
    (claude / "CLAUDE.md").write_text("# Rules\nSee @skills/uv.\n")
    (claude / "skills" / "uv").mkdir(parents=True)
    (claude / "skills" / "uv" / "SKILL.md").write_text("---\nname: uv\ndescription: d\n---\nBody\n")

    agy_dir = tmp_path / "gemini" / "config"

    result = runner.invoke(app, ["--claude-dir", str(claude), "--agy-dir", str(agy_dir), "agy"])

    assert result.exit_code == 0
    assert (agy_dir / "AGENTS.md").is_file()
    assert (agy_dir / "skills" / "uv").is_symlink()
