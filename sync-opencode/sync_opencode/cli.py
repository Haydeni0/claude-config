"""CLI entrypoint: sync ~/.claude config into ~/.config/opencode."""

import difflib
from dataclasses import dataclass
from pathlib import Path

import typer

from sync_opencode.agents import sync_agents_dir
from sync_opencode.agents_md import sync_agents_md
from sync_opencode.commands import sync_commands
from sync_opencode.config import sync_config, sync_tui
from sync_opencode.plugins import sync_superpowers
from sync_opencode.skills import validate_skills
from sync_opencode.sync import Outcome, Status

app = typer.Typer(add_completion=False, no_args_is_help=False)

SYNC_STEPS = ("config", "tui", "agents-md", "agents", "commands", "plugins")


@dataclass(slots=True, frozen=True)
class Paths:
    claude_dir: Path
    opencode_dir: Path


def run_step(name: str, paths: Paths, force: bool, dry_run: bool) -> list[Outcome]:
    if name == "config":
        return [sync_config(paths.opencode_dir / "opencode.json", paths.claude_dir / "opencode" / "opencode.json", force, dry_run)]
    if name == "tui":
        return [sync_tui(paths.opencode_dir / "tui.json", paths.claude_dir / "opencode" / "tui.json", force, dry_run)]
    if name == "agents-md":
        return [sync_agents_md(paths.opencode_dir / "AGENTS.md", paths.claude_dir / "CLAUDE.md", force, dry_run)]
    if name == "agents":
        return sync_agents_dir(paths.opencode_dir / "agents", paths.claude_dir / "agents", force, dry_run)
    if name == "commands":
        return sync_commands(
            paths.opencode_dir / "commands",
            paths.claude_dir / "commands",
            paths.claude_dir / "skills",
            force,
            dry_run,
        )
    if name == "plugins":
        cache = paths.claude_dir / "plugins" / "cache"
        return [sync_superpowers(paths.opencode_dir / "plugins" / "superpowers.js", cache, force, dry_run)]
    raise ValueError(f"unknown step: {name}")


def run_all(paths: Paths, force: bool, dry_run: bool, steps: tuple[str, ...] = SYNC_STEPS) -> tuple[list[Outcome], list[Outcome]]:
    sync_outcomes: list[Outcome] = []
    for step in steps:
        sync_outcomes.extend(run_step(step, paths, force, dry_run))
    skills_outcomes = validate_skills(paths.claude_dir / "skills")
    return sync_outcomes, skills_outcomes


_FAILURE_STATES = {Status.SKIPPED, Status.FAILED, Status.WARNED, Status.WOULD_CREATE, Status.WOULD_REPLACE, Status.WOULD_SKIP}


def exit_code(sync_outcomes: list[Outcome]) -> int:
    return 1 if any(o.status in _FAILURE_STATES for o in sync_outcomes) else 0


def _format_diff(outcome: Outcome) -> str:
    if outcome.old_content is None or outcome.new_content is None:
        return ""
    diff = difflib.unified_diff(
        outcome.old_content.splitlines(keepends=True),
        outcome.new_content.splitlines(keepends=True),
        fromfile=str(outcome.path) + " (current)",
        tofile=str(outcome.path) + " (generated)",
    )
    return "".join(diff)


def report(sync_outcomes: list[Outcome], skills_outcomes: list[Outcome], verbose: bool) -> None:
    for o in sync_outcomes:
        typer.echo(f"  {o.status.value:14s} {o.path}")
        if o.detail:
            typer.echo(f"                 {o.detail}")
        if verbose and o.status in (Status.SKIPPED, Status.REPLACED, Status.WOULD_REPLACE):
            diff = _format_diff(o)
            if diff:
                typer.echo(diff)
    for o in skills_outcomes:
        typer.echo(f"  {o.status.value:14s} {o.detail}")


def _paths(claude_dir: Path, opencode_dir: Path) -> Paths:
    return Paths(claude_dir=claude_dir, opencode_dir=opencode_dir)


def _run(steps: tuple[str, ...], paths: Paths, force: bool, dry_run: bool, check: bool, verbose: bool) -> int:
    effective_dry = dry_run or check
    sync_outcomes, skills_outcomes = run_all(paths, force, effective_dry, steps)
    report(sync_outcomes, skills_outcomes, verbose)
    return exit_code(sync_outcomes)


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    force: bool = typer.Option(False, "--force", help="Clobber conflicting managed paths."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would change without writing."),
    check: bool = typer.Option(False, "--check", help="Exit nonzero if drift detected (writes nothing)."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show diffs for changed text artifacts."),
    claude_dir: Path = typer.Option(Path.home() / ".claude", "--claude-dir", help="Source ~/.claude directory."),
    opencode_dir: Path = typer.Option(Path.home() / ".config" / "opencode", "--opencode-dir", help="Target ~/.config/opencode directory."),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    typer.echo("Syncing all steps...")
    code = _run(SYNC_STEPS, _paths(claude_dir, opencode_dir), force, dry_run, check, verbose)
    raise typer.Exit(code)


@app.command()
def config(
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    check: bool = typer.Option(False, "--check"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    claude_dir: Path = typer.Option(Path.home() / ".claude", "--claude-dir"),
    opencode_dir: Path = typer.Option(Path.home() / ".config" / "opencode", "--opencode-dir"),
) -> None:
    code = _run(("config",), _paths(claude_dir, opencode_dir), force, dry_run, check, verbose)
    raise typer.Exit(code)


@app.command()
def tui(
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    check: bool = typer.Option(False, "--check"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    claude_dir: Path = typer.Option(Path.home() / ".claude", "--claude-dir"),
    opencode_dir: Path = typer.Option(Path.home() / ".config" / "opencode", "--opencode-dir"),
) -> None:
    code = _run(("tui",), _paths(claude_dir, opencode_dir), force, dry_run, check, verbose)
    raise typer.Exit(code)


@app.command("agents-md")
def agents_md_cmd(
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    check: bool = typer.Option(False, "--check"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    claude_dir: Path = typer.Option(Path.home() / ".claude", "--claude-dir"),
    opencode_dir: Path = typer.Option(Path.home() / ".config" / "opencode", "--opencode-dir"),
) -> None:
    code = _run(("agents-md",), _paths(claude_dir, opencode_dir), force, dry_run, check, verbose)
    raise typer.Exit(code)


@app.command()
def agents(
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    check: bool = typer.Option(False, "--check"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    claude_dir: Path = typer.Option(Path.home() / ".claude", "--claude-dir"),
    opencode_dir: Path = typer.Option(Path.home() / ".config" / "opencode", "--opencode-dir"),
) -> None:
    code = _run(("agents",), _paths(claude_dir, opencode_dir), force, dry_run, check, verbose)
    raise typer.Exit(code)


@app.command()
def commands(
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    check: bool = typer.Option(False, "--check"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    claude_dir: Path = typer.Option(Path.home() / ".claude", "--claude-dir"),
    opencode_dir: Path = typer.Option(Path.home() / ".config" / "opencode", "--opencode-dir"),
) -> None:
    code = _run(("commands",), _paths(claude_dir, opencode_dir), force, dry_run, check, verbose)
    raise typer.Exit(code)


@app.command()
def plugins(
    force: bool = typer.Option(False, "--force"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    check: bool = typer.Option(False, "--check"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    claude_dir: Path = typer.Option(Path.home() / ".claude", "--claude-dir"),
    opencode_dir: Path = typer.Option(Path.home() / ".config" / "opencode", "--opencode-dir"),
) -> None:
    code = _run(("plugins",), _paths(claude_dir, opencode_dir), force, dry_run, check, verbose)
    raise typer.Exit(code)


@app.command()
def skills(
    claude_dir: Path = typer.Option(Path.home() / ".claude", "--claude-dir"),
) -> None:
    outcomes = validate_skills(claude_dir / "skills")
    report([], outcomes, verbose=True)
    raise typer.Exit(1 if any(o.status == Status.WARNED for o in outcomes) else 0)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
