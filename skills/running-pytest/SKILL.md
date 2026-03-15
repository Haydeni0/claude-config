---
name: running-pytest
description: How to run pytest in this workspace. Activates the local .venv and invokes pytest with the correct environment.
---

# Running Pytest

## Instructions

1. Activate the uv virtual environment first:

    ```bash
    source .venv/bin/activate
    ```

2. Run pytest (forwarding any user-supplied arguments):

    ```bash
    pytest [args...]
    ```

Do NOT use `python -m pytest`, `uv run pytest`, or `uv run python -m pytest`. Do NOT attempt to `pip install pytest` - the venv already has it.
