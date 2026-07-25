---
name: typer
description: Use when writing or editing any Python script that accepts command-line arguments - including standalone scripts, demos, benchmarks, experiments, profiling harnesses, and throwaway one-offs. Triggers on argparse, optparse, sys.argv, or any argv parsing in a Python file.
---

# Typer for Python CLIs

Use `typer` for any Python script that parses argv. Never `argparse`, `optparse`, or raw `sys.argv`.

This applies to **all** scripts with argv parsing - not just production CLI tools. "Standalone", "demo", "throwaway", "experiment", "benchmark", and "minimal-deps" scripts are not exceptions. If a script reads flags or args, use typer. The "stdlib only / no deps" rationale does not override this - typer is already a project dependency.

## Red Flags - STOP and use typer

You are about to violate this rule if you reach for any of these:
- Writing `import argparse` in a script that takes flags
- Reaching for `argparse` because the script is "throwaway", "standalone", "a quick demo", "an experiment", or "minimal"
- Using `sys.argv` parsing because "it's too small to need a CLI library"
- Adding `add_argument` calls

**All of these mean: stop, use typer.**

## Rationalizations

| Excuse | Reality |
|--------|---------|
| "It's a throwaway/demo/experiment script" | Demos need arg parsing too. typer is the same effort as argparse. |
| "It's standalone, argparse is stdlib" | typer is already a project dependency. stdlib-only is not a constraint. |
| "It's too small to need a CLI library" | typer scales down - a 5-flag script is 5 typed params, less code than argparse. |
| "production tools use typer, this doesn't" | The throwaway/production split is the trap. If it parses argv, use typer. |

## Basic Pattern

```python
import typer

app = typer.Typer()

@app.command()
def main(
    name: str,
    count: int = 1,
    verbose: bool = False,
):
    for _ in range(count):
        typer.echo(f"Hello {name}")

if __name__ == "__main__":
    app()
```

## Quick Reference

| Need | Typer syntax |
|------|-------------|
| Required arg | `name: str` |
| Optional with default | `count: int = 1` |
| Flag | `verbose: bool = False` |
| Explicit option | `name: str = typer.Option(...)` |
| Explicit argument | `path: str = typer.Argument(...)` |
| Fixed string choices (no class) | `quad: Literal["a", "b", "c"] = "a"` |
| Enum choices | `mode: MyEnum = MyEnum.fast` |
| Path | `out: Path = typer.Option(Path("."))` |
| Multiple subcommands | `app.command()` on multiple functions |

Type options at the boundary - see `programming-principles.md` ("Don't pass around strings for things that have a richer type").

## Argument Help

Add `help=` to every `typer.Option` / `typer.Argument`, and use `...` to mark a required param:

```python
@app.command()
def main(
    input_file: Path = typer.Argument(..., help="Path to input CSV"),
    workers: int = typer.Option(4, help="Number of parallel workers"),
):
    ...
```

Keep help strings brief - one clause, no full stops.

## Rules

- NEVER use `argparse`
- NEVER use `sys.argv` for argument parsing
- NEVER use `click` directly (typer wraps it)
- Use type hints - they ARE the argument definitions
- Use `typer.echo()` instead of `print()` for CLI output
