---
name: uv
description: Use when managing Python packages, running scripts, setting up environments, or running pytest.
---

# Using uv

All Python package management uses `uv`. Never use `pip`, `pip3`, `python -m pip`, `conda`, or `poetry`.

## Venv

```bash
source ./.venv/bin/activate   # activate (venv is at workspace root)
```

## Common Commands

| Task | Command |
|------|---------|
| Check if package is installed | `uv pip show <pkg>` |
| Install package | `uv pip install <pkg>` |
| Install from requirements | `uv pip install -r requirements.txt` |
| Install project deps | `uv pip install -e .` |
| Add to pyproject | `uv add <pkg>` |
| Run script | `uv run python script.py` |
| Run tool (no install) | `uvx <tool>` |

## pytest

```bash
source .venv/bin/activate && pytest [args...]
```

## Rules

- NEVER use `pip` or `pip3` directly
- NEVER use `python -m pip`
- NEVER use `python -m pytest`, `uv run pytest`, or `uv run python -m pytest`
- Always activate `./.venv` before running python commands in a shell session
- Package source code lives at `./.venv/lib/<python_version>/site-packages/`
