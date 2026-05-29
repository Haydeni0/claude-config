---
name: pytest-guidelines
description: Use when writing or reviewing Python pytest tests, when tests import unittest.mock, or when keeper tests target private methods or implementation details.
---

# Pytest Guidelines

## Overview

Keeper tests document **public behavior** only. During TDD, temporary tests live in `tests/tdd_scaffolding/` and are deleted when done.

## Quick Reference

| Do | Don't |
|---|---|
| `uv run pytest` | bare `pytest`, `python -m pytest`, `.venv/bin/pytest` |
| `mocker.patch(...)` (`pytest-mock`) | `unittest.mock` |
| Patch where the name is **used**, not where it's defined | patch at definition site |
| Test public inputs/outputs and side effects | test `_private` methods in keeper tests |
| `@pytest.mark.parametrize` for input variants | loops inside test bodies |
| `with pytest.raises(...)` for errors | manual try/except in tests |

Discovery: files `test_*.py`, functions `test_*()`, classes `Test*`. Shared fixtures in `tests/conftest.py`.

## Running

**REQUIRED:** See `uv` skill. Always `uv run pytest [args...]`.

## Mocking

Never import or use `unittest.mock`. Use the `pytest-mock` `mocker` fixture only - mocks auto-stop after each test.

```python
mock_get = mocker.patch("my_package.api_client.requests.get", ...)
mock_get.assert_called_once_with(...)
```

If a project lacks `pytest-mock`, add it (`uv add pytest-mock`) - do not fall back to `unittest.mock`.

## Keeper Tests

Applies to tests in `tests/` outside `tdd_scaffolding/`.

Test **observable behavior** through public APIs. Never write keeper tests for names starting with `_`.

If refactoring internals forces keeper test changes, the test was too coupled - rewrite at a higher level.

### Rationalizations

| Excuse | Reality |
|---|---|
| "The bug is in the private helper" | Exercise it through the public API that calls it |
| "Easier to unit-test in isolation" | Use `tests/tdd_scaffolding/` during TDD, then delete |
| "I'll mock with unittest.mock quickly" | Use `mocker`; install `pytest-mock` if missing |
| "This helper is stable enough to test directly" | Stability doesn't make it public API |
| "Scaffolding is useful documentation - keep it" | Convert edge cases to keeper tests; delete `tdd_scaffolding/` |

### Red Flags - STOP

- Keeper test imports or calls `_something`
- `from unittest.mock import patch` or `import unittest.mock`
- Granular TDD test left in `tests/` after implementation complete
- Bare `pytest` in commands

## TDD Scaffolding

**REQUIRED BACKGROUND:** Use `tdd` skill. Scaffolding tests may target internals; they are temporary and deleted before done. Convert behavior to keeper tests per this skill.

## Common Mistakes

- Patching `my_package.utils.requests` when code imports `requests` inside `api_client` - patch `my_package.api_client.requests`
- Leaving `tdd_scaffolding/` after TDD completes
- Testing return value structure field-by-field when one behavioral assertion suffices
- `@pytest.fixture` duplicated across files instead of shared `conftest.py`

## Example

Public API test with fixture and mock at the use site:

```python
import pytest


@pytest.fixture
def calculator():
    return OrderCalculator()


def test_order_total_includes_ny_tax(mocker, calculator):
    mocker.patch("my_package.tax.lookup_rate", return_value=0.08875)
    total = calculator.get_order_total(subtotal=100, state="NY")
    assert total == pytest.approx(108.875)
```
