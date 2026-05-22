---
name: pytest-guidelines
description: Use for any tasks involving Python tests with pytest, or when any file uses or imports `unittest.mock`.
---

# Pytest Best Practices

## Running Pytest

Always invoke via `uv run` — never use bare `pytest`, `python -m pytest`, or `.venv/bin/pytest`. See the `uv` skill for full rules.

```bash
uv run pytest [args...]
```

## Instructions

### 1. Project Structure & Discovery

Pytest discovers tests based on naming conventions. Adhere to this standard structure to ensure tests are found and executed correctly.

* **Directory Layout:**

    ```text
    my_project/
    ├── src/
    │   └── my_package/
    │       └── module.py
    ├── tests/
    │   ├── conftest.py       # Shared fixtures
    │   ├── __init__.py       # Makes 'tests' a package (optional but recommended)
    │   └── test_module.py    # Test files must start with test_ or end with _test
    └── pyproject.toml        # Configuration
    ```

* **Naming Conventions:**
  * Files: `test_*.py` or `*_test.py`
  * Functions: `test_*()`
  * Classes: `Test*` (Do not use `__init__` in test classes)

### 2. The AAA Pattern

Structure every test function using the **Arrange-Act-Assert** pattern to maximize readability.

* **Arrange:** Set up the initial state (variables, database, mocks).
* **Act:** Trigger the specific behavior or function you are testing.
* **Assert:** Verify the result matches expectations.

### 3. Fixtures (Setup & Teardown)

Use fixtures instead of `setup_method` or `teardown_method`. Fixtures are dependency injection for tests.

* **Define in `conftest.py`:** Place fixtures used by multiple test files in `tests/conftest.py`. You do not need to import them manually.
* **Scopes:** Use the tightest scope possible (`function` is default).
  * `function`: Run once per test.
  * `class`: Run once per test class.
  * `module`: Run once per file.
  * `session`: Run once per entire test suite (e.g., spinning up a Docker container).
* **Teardown with `yield`:** Code after the `yield` statement runs after the test finishes.

### 4. Parametrization

Avoid writing loops inside tests or duplicating test logic. Use `@pytest.mark.parametrize` to run the same test function with different inputs.

### 5. Mocking

Prefer the `pytest-mock` plugin (which provides the `mocker` fixture) over `unittest.mock` directly. It ensures mocks are automatically stopped after the test. If `pytest-mock` is not installed, fall back to `unittest.mock.patch` as a context manager or decorator - never use it as a standalone call without cleanup.

* **Pattern:** `mocker.patch("path.to.dependency", return_value=...)`
* **Verification:** `mock_obj.assert_called_once_with(...)`

### 6. Assertions

Use standard Python `assert` statements. Pytest rewrites these at runtime to provide detailed introspection (diffs) on failure.

* **Exceptions:** Use `with pytest.raises(ExpectedException):` to test error handling.

### 7. Testing Philosophy: Behavior over Implementation

Strictly adhere to testing **Public APIs only**.

* **Do not test private methods:** Never write tests for functions or methods starting with an underscore (`_function_name`). These are implementation details.
* **Test Observable Behavior:** Tests should verify *what* the code does (inputs/outputs, side effects), not *how* it does it.
* **Refactoring Safety:** If refactoring the internal logic of a function requires changing the test, the test was likely too coupled to implementation. Rewrite the test to be more high-level.

## Examples

### Basic Test with Fixture (AAA Pattern)

```python
import pytest
from my_package.wallet import Wallet

@pytest.fixture
def empty_wallet():
    """Returns a Wallet instance with 0 balance."""
    return Wallet(balance=0)

def test_wallet_add_cash(empty_wallet):
    # Arrange
    wallet = empty_wallet
    amount = 10

    # Act
    wallet.add_cash(amount)

    # Assert
    assert wallet.balance == 10
```

### Parametrization (Data-Driven Tests)

```python
import pytest
from my_package.math import add

@pytest.mark.parametrize("a, b, expected", [
    (1, 1, 2),
    (10, 20, 30),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_add(a, b, expected):
    assert add(a, b) == expected
```

### Mocking External Dependencies

```python
def test_fetch_user_data(mocker):
    # Arrange: Mock the 'requests.get' call in the module being tested
    mock_get = mocker.patch("my_package.api_client.requests.get")
    
    # Configure the mock to return a specific JSON response
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"id": 1, "name": "Test User"}
    mock_get.return_value = mock_response

    from my_package.api_client import get_user

    # Act
    user = get_user(1)

    # Assert
    assert user["name"] == "Test User"
    mock_get.assert_called_once_with("[https://api.example.com/users/1](https://api.example.com/users/1)")
```

### Testing Exceptions

```python
import pytest

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        1 / 0
```

### ❌ Bad (Testing Implementation)

```python
# Testing a private helper function directly
def test_internal_tax_calculation():
    calculator = OrderCalculator()
    # This method might be deleted or renamed later!
    tax = calculator._calculate_state_tax(100, "NY") 
    assert tax == 8.875
```

### ✅ Good (Testing Public API)

```python
# Testing the result the user actually cares about
def test_order_total_includes_ny_tax():
    calculator = OrderCalculator()
    # The public method calls the private helper internally
    total = calculator.get_order_total(subtotal=100, state="NY")
    assert total == 108.875
```
