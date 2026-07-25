import json
import pathlib

from typer.testing import CliRunner

from settings_sync.cli import Paths, app, run_opencode


def _make_claude_home(tmp_path: pathlib.Path) -> pathlib.Path:
    home = tmp_path / "claude"
    (home / "claude_md_imports").mkdir(parents=True)
    (home / "claude_md_imports" / "extra.md").write_text("Extra rules.\n")
    (home / "CLAUDE.md").write_text("# Rules\n@claude_md_imports/extra.md\nSee @skills/uv.\n")
    (home / "opencode").mkdir(parents=True)
    (home / "opencode" / "opencode.json").write_text(json.dumps({"model": "test/model"}))
    (home / "opencode" / "tui.json").write_text(json.dumps({"theme": "tokyonight"}))
    (home / "agents").mkdir(parents=True)
    (home / "agents" / "reviewer.md").write_text("---\nname: reviewer\ndescription: r\ntools: Read\n---\nBody.\n")
    (home / "commands").mkdir(parents=True)
    (home / "commands" / "foo.md").write_text("---\ndescription: foo\n---\nRun foo.\n")
    (home / "skills").mkdir(parents=True)
    (home / "skills" / "uv").mkdir(parents=True)
    (home / "skills" / "uv" / "SKILL.md").write_text("---\nname: uv\ndescription: d\n---\nBody.\n")
    (home / "pi").mkdir(parents=True)
    (home / "pi" / "settings.json").write_text(json.dumps({"skills": ["~/.claude/skills"], "prompts": ["~/.claude/commands"]}))
    (home / "goose").mkdir(parents=True)
    (home / "goose" / "config.yaml").write_text("GOOSE_TELEMETRY_ENABLED: false\n")
    (home / "goose" / "custom_providers").mkdir(parents=True)
    (home / "goose" / "custom_providers" / "test.json").write_text(json.dumps({"name": "test"}))
    return home


runner = CliRunner()


def test_all_creates_everything(tmp_path: pathlib.Path):
    claude = _make_claude_home(tmp_path)
    opencode = tmp_path / "config" / "opencode"
    pi_dir = tmp_path / "pi-agent"
    goose_dir = tmp_path / "goose-config"

    result = runner.invoke(app, ["--claude-dir", str(claude), "--opencode-dir", str(opencode), "--pi-dir", str(pi_dir), "--goose-dir", str(goose_dir)])

    assert result.exit_code == 0
    assert (opencode / "opencode.json").is_file()
    assert (opencode / "tui.json").is_file()
    assert json.loads((opencode / "tui.json").read_text())["theme"] == "tokyonight"
    assert (opencode / "AGENTS.md").is_file()
    assert (opencode / "AGENTS.md").read_text().count("Extra rules.") == 1
    assert (opencode / "agents" / "reviewer.md").is_file()
    assert (opencode / "commands" / "foo.md").is_file()
    assert (opencode / "commands" / "uv.md").is_file()
    assert json.loads((pi_dir / "settings.json").read_text())["skills"] == ["~/.claude/skills"]
    assert "the `uv` skill" in (pi_dir / "CLAUDE.md").read_text()
    assert (goose_dir / ".goosehints").is_file()
    assert (goose_dir / "config.yaml").is_file()
    assert (goose_dir / "custom_providers" / "test.json").is_file()


def test_all_exits_nonzero_on_conflict(tmp_path: pathlib.Path):
    claude = _make_claude_home(tmp_path)
    opencode = tmp_path / "config" / "opencode"
    pi_dir = tmp_path / "pi-agent"
    goose_dir = tmp_path / "goose-config"
    opencode.mkdir(parents=True)
    (opencode / "opencode.json").write_text(json.dumps({"hand": "edited"}))

    result = runner.invoke(app, ["--claude-dir", str(claude), "--opencode-dir", str(opencode), "--pi-dir", str(pi_dir), "--goose-dir", str(goose_dir)])

    assert result.exit_code == 1


def test_force_resolves_conflicts(tmp_path: pathlib.Path):
    claude = _make_claude_home(tmp_path)
    opencode = tmp_path / "config" / "opencode"
    pi_dir = tmp_path / "pi-agent"
    goose_dir = tmp_path / "goose-config"
    opencode.mkdir(parents=True)
    (opencode / "opencode.json").write_text(json.dumps({"hand": "edited"}))

    result = runner.invoke(app, ["--force", "--claude-dir", str(claude), "--opencode-dir", str(opencode), "--pi-dir", str(pi_dir), "--goose-dir", str(goose_dir)])

    assert result.exit_code == 0
    assert json.loads((opencode / "opencode.json").read_text())["model"] == "test/model"


def test_check_exits_nonzero_on_drift_without_writing(tmp_path: pathlib.Path):
    claude = _make_claude_home(tmp_path)
    opencode = tmp_path / "config" / "opencode"
    pi_dir = tmp_path / "pi-agent"
    goose_dir = tmp_path / "goose-config"

    result = runner.invoke(app, ["--check", "--claude-dir", str(claude), "--opencode-dir", str(opencode), "--pi-dir", str(pi_dir), "--goose-dir", str(goose_dir)])

    assert result.exit_code == 1
    assert not (opencode / "opencode.json").exists()


def test_dry_run_creates_nothing(tmp_path: pathlib.Path):
    claude = _make_claude_home(tmp_path)
    opencode = tmp_path / "config" / "opencode"
    pi_dir = tmp_path / "pi-agent"
    goose_dir = tmp_path / "goose-config"

    result = runner.invoke(app, ["--dry-run", "--claude-dir", str(claude), "--opencode-dir", str(opencode), "--pi-dir", str(pi_dir), "--goose-dir", str(goose_dir)])

    assert result.exit_code == 1
    assert not (opencode / "opencode.json").exists()
    assert not (opencode / "AGENTS.md").exists()
    assert not (pi_dir / "settings.json").exists()
    assert not (goose_dir / ".goosehints").exists()


def test_opencode_agents_only(tmp_path: pathlib.Path):
    claude = _make_claude_home(tmp_path)
    opencode = tmp_path / "config" / "opencode"
    pi_dir = tmp_path / "pi-agent"

    result = runner.invoke(app, ["--claude-dir", str(claude), "--opencode-dir", str(opencode), "--pi-dir", str(pi_dir), "opencode", "agents"])

    assert result.exit_code == 0
    assert (opencode / "agents" / "reviewer.md").is_file()
    assert not (opencode / "opencode.json").exists()
    assert not (pi_dir / "settings.json").exists()


def test_opencode_config_only(tmp_path: pathlib.Path):
    claude = _make_claude_home(tmp_path)
    opencode = tmp_path / "config" / "opencode"
    pi_dir = tmp_path / "pi-agent"

    result = runner.invoke(app, ["--claude-dir", str(claude), "--opencode-dir", str(opencode), "--pi-dir", str(pi_dir), "opencode", "config"])

    assert result.exit_code == 0
    assert (opencode / "opencode.json").is_file()
    assert not (opencode / "AGENTS.md").exists()


def test_run_opencode_pure_returns_outcomes(tmp_path: pathlib.Path):
    claude = _make_claude_home(tmp_path)
    opencode = tmp_path / "config" / "opencode"
    paths = Paths(claude_dir=claude, opencode_dir=opencode)

    sync_outcomes, skills_outcomes = run_opencode(paths, force=False, dry_run=False)

    statuses = {o.status for o in sync_outcomes}
    from settings_sync.sync import Status

    assert Status.CREATED in statuses
