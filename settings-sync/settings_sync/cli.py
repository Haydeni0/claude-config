"""CLI entrypoint: sync ~/.claude config into opencode, pi, and goose.

~/.claude is the single source of truth. `sync opencode` derives config
into ~/.config/opencode; `sync pi` writes pointers + inlined context
into ~/.pi/agent; `sync goose` writes hints + config + providers into
~/.config/goose. Bare `sync` (or `sync all`) runs all three.
"""

import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer

from settings_sync.agents import sync_agents_dir
from settings_sync.agents_md import sync_agents_md
from settings_sync.commands import sync_commands
from settings_sync.config import sync_config, sync_tui
from settings_sync.goose import sync_goose_config, sync_goose_hints, sync_goose_providers
from settings_sync.pi import sync_pi_config, sync_pi_context, sync_pi_keybindings
from settings_sync.plugins import sync_superpowers
from settings_sync.skills import validate_skills
from settings_sync.sync import Outcome, Status

app = typer.Typer(add_completion=False, no_args_is_help=False)
opencode_app = typer.Typer(add_completion=False, no_args_is_help=False, help="Sync opencode config.")
pi_app = typer.Typer(add_completion=False, no_args_is_help=False, help="Sync pi config.")
goose_app = typer.Typer(add_completion=False, no_args_is_help=False, help="Sync goose config.")

OPENCODE_STEPS = ("config", "tui", "agents-md", "agents", "commands", "plugins")
PI_STEPS = ("config", "context", "keybindings")
GOOSE_STEPS = ("hints", "config", "providers")


@dataclass(slots=True, frozen=True)
class Paths:
    claude_dir: Path
    opencode_dir: Path
    pi_dir: Path | None = None
    goose_dir: Path | None = None


def run_opencode_step(name: str, paths: Paths, force: bool, dry_run: bool) -> list[Outcome]:
    if name == "config":
        return [sync_config(paths.opencode_dir / "opencode.json", paths.claude_dir / "opencode" / "opencode.json", force, dry_run)]
    if name == "tui":
        return [sync_tui(paths.opencode_dir / "tui.json", paths.claude_dir / "opencode" / "tui.json", force, dry_run)]
    if name == "agents-md":
        return [sync_agents_md(paths.opencode_dir / "AGENTS.md", paths.claude_dir / "CLAUDE.md", force, dry_run, rules_path=paths.claude_dir / "opencode" / "rules.md")]
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
    raise ValueError(f"unknown opencode step: {name}")


def run_pi_step(name: str, paths: Paths, force: bool, dry_run: bool) -> list[Outcome]:
    if paths.pi_dir is None:
        raise ValueError("pi_dir is required for pi steps")
    if name == "config":
        return [sync_pi_config(paths.pi_dir / "settings.json", paths.claude_dir / "pi" / "settings.json", dry_run)]
    if name == "context":
        return [sync_pi_context(paths.pi_dir / "CLAUDE.md", paths.claude_dir / "CLAUDE.md", force, dry_run)]
    if name == "keybindings":
        return [sync_pi_keybindings(paths.pi_dir / "keybindings.json", paths.claude_dir / "pi" / "keybindings.json", dry_run)]
    raise ValueError(f"unknown pi step: {name}")


def run_goose_step(name: str, paths: Paths, force: bool, dry_run: bool) -> list[Outcome]:
    if paths.goose_dir is None:
        raise ValueError("goose_dir is required for goose steps")
    if name == "hints":
        return [sync_goose_hints(paths.goose_dir / ".goosehints", paths.claude_dir / "CLAUDE.md", force, dry_run)]
    if name == "config":
        return [sync_goose_config(paths.goose_dir / "config.yaml", paths.claude_dir / "goose" / "config.yaml", force, dry_run)]
    if name == "providers":
        return sync_goose_providers(paths.goose_dir / "custom_providers", paths.claude_dir / "goose" / "custom_providers", force, dry_run)
    raise ValueError(f"unknown goose step: {name}")


def run_opencode(paths: Paths, force: bool, dry_run: bool, steps: tuple[str, ...] = OPENCODE_STEPS) -> tuple[list[Outcome], list[Outcome]]:
    sync_outcomes: list[Outcome] = []
    for step in steps:
        sync_outcomes.extend(run_opencode_step(step, paths, force, dry_run))
    skills_outcomes = validate_skills(paths.claude_dir / "skills")
    return sync_outcomes, skills_outcomes


def run_pi(paths: Paths, force: bool, dry_run: bool, steps: tuple[str, ...] = PI_STEPS) -> tuple[list[Outcome], list[Outcome]]:
    sync_outcomes: list[Outcome] = []
    for step in steps:
        sync_outcomes.extend(run_pi_step(step, paths, force, dry_run))
    skills_outcomes = validate_skills(paths.claude_dir / "skills")
    return sync_outcomes, skills_outcomes


def run_goose(paths: Paths, force: bool, dry_run: bool, steps: tuple[str, ...] = GOOSE_STEPS) -> tuple[list[Outcome], list[Outcome]]:
    sync_outcomes: list[Outcome] = []
    for step in steps:
        sync_outcomes.extend(run_goose_step(step, paths, force, dry_run))
    skills_outcomes = validate_skills(paths.claude_dir / "skills")
    return sync_outcomes, skills_outcomes


def run_all_tools(paths: Paths, force: bool, dry_run: bool) -> tuple[list[Outcome], list[Outcome]]:
    sync_outcomes: list[Outcome] = []
    for step in OPENCODE_STEPS:
        sync_outcomes.extend(run_opencode_step(step, paths, force, dry_run))
    for step in PI_STEPS:
        sync_outcomes.extend(run_pi_step(step, paths, force, dry_run))
    if paths.goose_dir is not None:
        for step in GOOSE_STEPS:
            sync_outcomes.extend(run_goose_step(step, paths, force, dry_run))
    skills_outcomes = validate_skills(paths.claude_dir / "skills")
    return sync_outcomes, skills_outcomes


_FAILURE_STATES = {Status.SKIPPED, Status.FAILED, Status.WARNED, Status.WOULD_CREATE, Status.WOULD_REPLACE, Status.WOULD_SKIP}


def exit_code(sync_outcomes: list[Outcome]) -> int:
    return 1 if any(o.status in _FAILURE_STATES for o in sync_outcomes) else 0


def _run_skills(ctx: typer.Context) -> int:
    """Run validate_skills and report. One exit-code policy for all skills invocations."""
    paths = _ctx_paths(ctx)
    _, _, _, verbose = _ctx_flags(ctx)
    outcomes = validate_skills(paths.claude_dir / "skills")
    report([], outcomes, verbose=True)
    return 1 if any(o.status == Status.WARNED for o in outcomes) else 0


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


def _ctx_paths(ctx: typer.Context) -> Paths:
    obj: Any = ctx.obj
    return obj["paths"]


def _ctx_flags(ctx: typer.Context) -> tuple[bool, bool, bool, bool]:
    obj: Any = ctx.obj
    return obj["force"], obj["dry_run"], obj["check"], obj["verbose"]


def _run_steps(ctx: typer.Context, tool: str, steps: tuple[str, ...]) -> int:
    paths = _ctx_paths(ctx)
    force, dry_run, check, verbose = _ctx_flags(ctx)
    effective_dry = dry_run or check
    runner = {"opencode": run_opencode, "pi": run_pi, "goose": run_goose}[tool]
    sync_outcomes, skills_outcomes = runner(paths, force, effective_dry, steps)
    report(sync_outcomes, skills_outcomes, verbose)
    return exit_code(sync_outcomes) or (1 if any(o.status == Status.WARNED for o in skills_outcomes) else 0)


def _run_all(ctx: typer.Context) -> int:
    paths = _ctx_paths(ctx)
    force, dry_run, check, verbose = _ctx_flags(ctx)
    effective_dry = dry_run or check
    sync_outcomes, skills_outcomes = run_all_tools(paths, force, effective_dry)
    report(sync_outcomes, skills_outcomes, verbose)
    return exit_code(sync_outcomes) or (1 if any(o.status == Status.WARNED for o in skills_outcomes) else 0)


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    force: bool = typer.Option(False, "--force", help="Clobber conflicting managed paths."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would change without writing."),
    check: bool = typer.Option(False, "--check", help="Exit nonzero if drift detected (writes nothing)."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show diffs for changed text artifacts."),
    claude_dir: Path = typer.Option(Path.home() / ".claude", "--claude-dir", help="Source ~/.claude directory."),
    opencode_dir: Path = typer.Option(Path.home() / ".config" / "opencode", "--opencode-dir", help="Target ~/.config/opencode directory."),
    pi_dir: Path = typer.Option(Path.home() / ".pi" / "agent", "--pi-dir", help="Target ~/.pi/agent directory."),
    goose_dir: Path = typer.Option(Path.home() / ".config" / "goose", "--goose-dir", help="Target ~/.config/goose directory."),
) -> None:
    """Sync ~/.claude config into opencode, pi, and goose. ~/.claude is the source of truth."""
    ctx.obj = {"paths": Paths(claude_dir=claude_dir, opencode_dir=opencode_dir, pi_dir=pi_dir, goose_dir=goose_dir), "force": force, "dry_run": dry_run, "check": check, "verbose": verbose}
    if ctx.invoked_subcommand is None:
        typer.echo("Syncing all tools (opencode + pi + goose)...")
        raise typer.Exit(_run_all(ctx))


@app.command()
def all(ctx: typer.Context) -> None:
    """Sync opencode, pi, and goose."""
    typer.echo("Syncing all tools (opencode + pi + goose)...")
    raise typer.Exit(_run_all(ctx))


# ---- opencode group ----

@opencode_app.callback(invoke_without_command=True)
def opencode_callback(ctx: typer.Context) -> None:
    """Sync opencode config (all steps)."""
    if ctx.invoked_subcommand is None:
        typer.echo("Syncing opencode...")
        raise typer.Exit(_run_steps(ctx, "opencode", OPENCODE_STEPS))


@opencode_app.command()
def config(ctx: typer.Context) -> None:
    raise typer.Exit(_run_steps(ctx, "opencode", ("config",)))


@opencode_app.command()
def tui(ctx: typer.Context) -> None:
    raise typer.Exit(_run_steps(ctx, "opencode", ("tui",)))


@opencode_app.command("agents-md")
def agents_md(ctx: typer.Context) -> None:
    raise typer.Exit(_run_steps(ctx, "opencode", ("agents-md",)))


@opencode_app.command()
def agents(ctx: typer.Context) -> None:
    raise typer.Exit(_run_steps(ctx, "opencode", ("agents",)))


@opencode_app.command()
def commands(ctx: typer.Context) -> None:
    raise typer.Exit(_run_steps(ctx, "opencode", ("commands",)))


@opencode_app.command()
def plugins(ctx: typer.Context) -> None:
    raise typer.Exit(_run_steps(ctx, "opencode", ("plugins",)))


@opencode_app.command()
def skills(ctx: typer.Context) -> None:
    raise typer.Exit(_run_skills(ctx))


# ---- pi group ----

@pi_app.callback(invoke_without_command=True)
def pi_callback(ctx: typer.Context) -> None:
    """Sync pi config (pointers + inlined context)."""
    if ctx.invoked_subcommand is None:
        typer.echo("Syncing pi...")
        raise typer.Exit(_run_steps(ctx, "pi", PI_STEPS))


@pi_app.command()
def config(ctx: typer.Context) -> None:
    raise typer.Exit(_run_steps(ctx, "pi", ("config",)))


@pi_app.command()
def context(ctx: typer.Context) -> None:
    raise typer.Exit(_run_steps(ctx, "pi", ("context",)))


@pi_app.command()
def keybindings(ctx: typer.Context) -> None:
    raise typer.Exit(_run_steps(ctx, "pi", ("keybindings",)))


@pi_app.command()
def skills(ctx: typer.Context) -> None:
    raise typer.Exit(_run_skills(ctx))


# ---- goose group ----

@goose_app.callback(invoke_without_command=True)
def goose_callback(ctx: typer.Context) -> None:
    """Sync goose config (all steps)."""
    if ctx.invoked_subcommand is None:
        typer.echo("Syncing goose...")
        raise typer.Exit(_run_steps(ctx, "goose", GOOSE_STEPS))


@goose_app.command()
def hints(ctx: typer.Context) -> None:
    raise typer.Exit(_run_steps(ctx, "goose", ("hints",)))


@goose_app.command()
def config(ctx: typer.Context) -> None:
    raise typer.Exit(_run_steps(ctx, "goose", ("config",)))


@goose_app.command()
def providers(ctx: typer.Context) -> None:
    raise typer.Exit(_run_steps(ctx, "goose", ("providers",)))


@goose_app.command()
def skills(ctx: typer.Context) -> None:
    raise typer.Exit(_run_skills(ctx))


app.add_typer(opencode_app, name="opencode")
app.add_typer(pi_app, name="pi")
app.add_typer(goose_app, name="goose")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
