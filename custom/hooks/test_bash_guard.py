"""Tests for the PreToolUse hook `check-bash-guard.sh`.

Hard-denies S3 delete operations, all deletes under /mnt/data, and deletes on
filesystem root. The hook is invoked as a real subprocess (with jq parsing
exercised end to end):
- a deny decision JSON on stdout when the command would delete S3 data,
  delete anything under /mnt/data, or delete filesystem root;
- silence (empty stdout) when the command is allowed through.

Command cases are loaded from bash-guard-cases.json (shared with the
opencode bash-guard.js plugin test). Harness-specific tests (jq payload
parsing) stay here - they have no opencode equivalent.

Scope mirrors the user's choices:
  S3:       deletes only blocked. Uploads (cp ./x s3://..., s3api put-*) and
            read ops (ls, cp download, sync download, list-*/get-*) allowed.
  /mnt/data: ALL deletes blocked (rm, rmdir, shred, unlink, trash,
            find -delete, find -exec rm). Reads/writes allowed.
  root:     deletes on / or /* blocked (any flag arrangement).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent / "check-bash-guard.sh"
CASES = json.loads((Path(__file__).resolve().parent / "bash-guard-cases.json").read_text())
GROUPS = {g["name"]: g for g in CASES["groups"]}


def _bash() -> str:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is required")
    assert bash is not None
    return bash


def _require_jq() -> None:
    if shutil.which("jq") is None:
        pytest.skip("jq is required")


def _run(command: str) -> subprocess.CompletedProcess[str]:
    _require_jq()
    payload = json.dumps({"tool_input": {"command": command}})
    # No check=True: a non-zero exit (e.g. bug under set -euo pipefail) should
    # surface as an assertion failure, not a swallowed CalledProcessError.
    result = subprocess.run(
        [_bash(), str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"hook exited {result.returncode}; stderr={result.stderr!r}, "
        f"stdout={result.stdout!r}"
    )
    return result


def _assert_allowed(result: subprocess.CompletedProcess[str]) -> None:
    assert result.stdout == "", f"expected no decision, got: {result.stdout!r}"


def _assert_denied(result: subprocess.CompletedProcess[str], needle: str) -> None:
    assert result.stdout, "expected a deny decision on stdout"
    decision = json.loads(result.stdout)
    hook_output = decision["hookSpecificOutput"]
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "deny"
    assert needle in hook_output["permissionDecisionReason"], (
        f"expected {needle!r} in reason, got {hook_output['permissionDecisionReason']!r}"
    )


# -- shared corpus (parametrized from bash-guard-cases.json) -------------
# Add a command to the JSON and it flows into both this test and the opencode
# plugin test. The functions below are thin parametrize-and-assert wrappers;
# the corpus is the source of truth for what's blocked/allowed.

def _group(name: str) -> dict:
    return GROUPS[name]


def _cases(name: str) -> list[str]:
    return _group(name)["commands"]


def _needle(name: str) -> str:
    return _group(name)["needle"]


for _g in CASES["groups"]:
    _expect = _g["expect"]
    _name = _g["name"]
    _needle_val = _g.get("needle", "")
    if _expect == "deny":
        def _make_denier(group_name, group_needle):
            def _test(command):
                _assert_denied(_run(command), group_needle)
            _test.__name__ = f"test_{group_name}"
            return pytest.mark.parametrize("command", GROUPS[group_name]["commands"])(_test)
        globals()[f"test_{_name}"] = _make_denier(_name, _needle_val)
    else:
        def _make_allower(group_name):
            def _test(command):
                _assert_allowed(_run(command))
            _test.__name__ = f"test_{group_name}"
            return pytest.mark.parametrize("command", GROUPS[group_name]["commands"])(_test)
        globals()[f"test_{_name}"] = _make_allower(_name)


# -- payload edge cases (harness-specific: tests jq/JSON parsing) ----------
# No opencode equivalent - the opencode plugin receives output.args.command
# directly from the framework, no stdin JSON to parse.


@pytest.mark.parametrize(
    "payload",
    [
        {"tool_input": {}},
        {"tool_input": {"command": ""}},
        {"tool_input": {"command": "ls -la"}},
        {"tool_input": {"command": "echo hello"}},
        {"tool_input": {"command": "aws s3 ls s3://bucket/"}},
    ],
)
def test_edge_payloads(payload: dict) -> None:
    _require_jq()
    result = subprocess.run(
        [_bash(), str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == "", f"expected silence for {payload!r}, got {result.stdout!r}"
