---
name: uv
description: Use when running Python, managing Python packages, setting up environments, or running pytest.
---

# Using uv

All Python package management uses `uv`. Never use `pip`, `pip3`, `python -m pip`, `conda`, or `poetry`.

## Venv

Never use `source` to activate the venv. Invoke venv binaries directly:

```bash
.venv/bin/python script.py
.venv/bin/pytest [args...]
.venv/bin/<tool>
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

## Rules

- NEVER use `pip` or `pip3` directly
- NEVER use `python -m pip`
- NEVER use `python -m pytest`, `uv run pytest`, or `uv run python -m pytest`
- NEVER use `source` to activate the venv - invoke venv binaries directly (`.venv/bin/python`, `.venv/bin/pytest`, etc.)
- Use `.venv/bin/python`, not `.venv/bin/python3`
- Package source code lives at `./.venv/lib/<python_version>/site-packages/`
