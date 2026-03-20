---
name: typer
description: Use when building Python CLI tools, writing scripts that accept arguments, or any time argparse would otherwise be used. Enforces typer as the only CLI argument library.
---

# Typer for Python CLIs

Always use `typer` for Python CLI tools. Never use `argparse`, `optparse`, or raw `sys.argv` parsing.

## Why

- Type hints define the interface — no manual `add_argument` boilerplate
- Automatic `--help`, type validation, and error messages
- Cleaner, more readable code

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

## Common Patterns

| Need | Typer syntax |
|------|-------------|
| Required arg | `name: str` |
| Optional with default | `count: int = 1` |
| Flag | `verbose: bool = False` |
| Explicit option | `name: str = typer.Option(...)` |
| Explicit argument | `path: str = typer.Argument(...)` |
| Enum choices | `mode: MyEnum = MyEnum.fast` |
| File path | `path: Path = typer.Argument(...)` |
| Multiple subcommands | `app.command()` on multiple functions |

## Installation

```bash
uv add typer
# or for scripts:
uv pip install typer
```

## Argument Descriptions

Use `typer.Option` / `typer.Argument` with `help=` for any non-obvious parameter:

```python
@app.command()
def main(
    input_file: Path = typer.Argument(..., help="Path to input CSV"),
    output_dir: Path = typer.Option(Path("."), help="Directory to write results"),
    workers: int = typer.Option(4, help="Number of parallel workers"),
    dry_run: bool = typer.Option(False, help="Print actions without executing"),
):
    ...
```

- Always add `help=` to `Option` and non-obvious `Argument` params
- Use `...` as the default to mark a parameter as required
- Keep help strings brief - one clause, no full stops

## Rules

- NEVER use `argparse`
- NEVER use `sys.argv` for argument parsing
- NEVER use `click` directly (typer wraps it)
- Use type hints — they ARE the argument definitions
- Use `typer.echo()` instead of `print()` for CLI output
