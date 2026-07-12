"""Tests for the PreToolUse hook `check-delete-safety.sh`.

Hard-denies S3 delete operations and all deletes under /mnt/data. The hook
is invoked as a real subprocess (with jq parsing exercised end to end):
- a deny decision JSON on stdout when the command would delete S3 data or
  delete anything under /mnt/data;
- silence (empty stdout) when the command is allowed through.

Scope mirrors the user's choices:
  S3:       deletes only blocked. Uploads (cp ./x s3://..., s3api put-*) and
            read ops (ls, cp download, sync download, list-*/get-*) allowed.
  /mnt/data: ALL deletes blocked (rm, rmdir, shred, unlink, trash,
            find -delete, find -exec rm). Reads/writes allowed.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parent / "check-delete-safety.sh"


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
        f"expected {needle!r} in reason, got: {hook_output['permissionDecisionReason']!r}"
    )


# -- S3 deletes blocked ------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "aws s3 rm s3://bucket/foo",
        "aws s3 rm s3://bucket/foo --recursive",
        "aws s3 rb s3://bucket",
        "aws s3 sync --delete ./local s3://bucket/dir",
        "aws s3 sync ./local s3://bucket/dir --delete",
        # s3api delete-* family (19 ops).
        "aws s3api delete-object --bucket b --key foo",
        "aws s3api delete-objects --bucket b --delete file://d.json",
        "aws s3api delete-bucket --bucket b",
        "aws s3api delete-bucket-policy --bucket b",
        "aws s3api delete-bucket-lifecycle --bucket b",
        "aws s3api delete-bucket-tagging --bucket b",
        "aws s3api delete-object-tagging --bucket b --key foo",
        "aws s3api delete-public-access-block --bucket b",
        # Env-var prefix + flags.
        "AWS_PROFILE=coreweave aws s3 rm s3://bucket/foo --recursive",
        # Flag-before-source / whitespace variants.
        "aws s3 rm --recursive s3://bucket/foo",
        "  aws s3  rm  s3://bucket/foo  ",
        "aws\ts3\trm\ts3://bucket/foo",
        # Wrapped / compound forms (the `if`-matcher-fails-open bypass).
        'bash -c "aws s3 rm s3://bucket/foo"',
        "sh -c 'aws s3 rm s3://bucket/foo'",
        "echo $(aws s3 rm s3://bucket/foo)",
        "true && aws s3 rm s3://bucket/foo",
        "false || aws s3 rm s3://bucket/foo",
        "aws s3 ls s3://bucket/ && aws s3 rm s3://bucket/foo",
        'bash -c "aws s3api delete-object --bucket b --key foo"',
    ],
)
def test_s3_deletes_blocked(command: str) -> None:
    _assert_denied(_run(command), "S3")


# -- S3 read ops + uploads allowed ------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "aws s3 ls s3://bucket/",
        "aws s3 cp s3://bucket/specs/v1.yaml -",
        "aws s3 cp s3://bucket/specs/v1.yaml ./local.yaml",
        "aws s3 sync s3://bucket/dir ./local-dir",
        "aws s3 cp --recursive s3://bucket/dir ./local-dir",
        "aws s3api list-objects-v2 --bucket b",
        "aws s3api get-object --bucket b --key foo /tmp/foo",
        "aws s3api head-object --bucket b --key foo",
        "aws s3api list-buckets",
        # Uploads stay allowed (deletes-only scope).
        "aws s3 cp ./local s3://bucket/foo",
        "aws s3 sync ./local-dir s3://bucket/dir",
        "aws s3api put-object --bucket b --key foo --body ./foo",
    ],
)
def test_s3_non_deletes_allowed(command: str) -> None:
    _assert_allowed(_run(command))


# -- /mnt/data deletes blocked ---------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf /mnt/data",
        "rm -rf /mnt/data/",
        "rm /mnt/data/apps/foo",
        "rm -f /mnt/data/apps/foo",
        "rmdir /mnt/data/empty",
        "shred /mnt/data/secret",
        "unlink /mnt/data/file",
        "find /mnt/data -delete",
        "find /mnt/data -name '*.tmp' -delete",
        "find /mnt/data -name x -exec rm {} +",
        "find /mnt/data -name x -exec rm -f {} \\;",
        "find /mnt/data -execdir rm {} ;",
        # Deep path under /mnt/data.
        "rm -rf /mnt/data/dora_preprocessing/old",
        # Env-prefix + compound forms.
        "AWS_PROFILE=p rm -rf /mnt/data/scratch",
        'bash -c "rm -rf /mnt/data"',
        "echo $(rm -rf /mnt/data)",
        "true && rm -rf /mnt/data",
        "ls /mnt/data && rm -rf /mnt/data/apps",
    ],
)
def test_mnt_data_deletes_blocked(command: str) -> None:
    _assert_denied(_run(command), "/mnt/data")


# -- /mnt/data non-deletes allowed -----------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "ls /mnt/data",
        "ls -la /mnt/data/apps",
        "cat /mnt/data/apps/foo",
        "find /mnt/data -name '*.csv'",
        "find /mnt/data -name x -exec cat {} +",
        "cp ./x /mnt/data/apps/x",
        "mkdir -p /mnt/data/new",
        "touch /mnt/data/new/file",
        # Deletes OUTSIDE /mnt/data are not this hook's concern.
        "rm -rf /tmp/junk",
        "rm /home/hayden.dorahy/scratch",
        "find /tmp -delete",
        "shred /tmp/secret",
    ],
)
def test_mnt_data_non_deletes_allowed(command: str) -> None:
    _assert_allowed(_run(command))


# -- false-positive guards (verb + path must be structurally linked) --------
# Regression: an early flatten-everything + co-occurrence check denied these
# because the delete verb and /mnt/data appeared as unrelated words. The hook
# now splits on command separators first and requires /mnt/data to be an
# argument to the verb within the same segment.
#
# KNOWN LIMITATION (accepted tradeoff): the hook cannot distinguish a delete
# verb nested inside a quoted flag VALUE (`git commit -m "rm /mnt/data/x"`,
# `echo "rm -rf /mnt/data"`) from a delete verb inside a quoted wrapper that
# EXECUTES (`bash -c "rm -rf /mnt/data"`). Both flatten to the same token
# stream. We deliberately DENY both: the cost of a false positive is a denied
# commit message the user rewords; the cost of a false negative is lost data
# under /mnt/data. So the two quoted-message cases below are NOT asserted as
# allowed - they are expected to be denied, and the user rewords if hit.
@pytest.mark.parametrize(
    "command",
    [
        # Delete verb + /mnt/data on opposite sides of a separator: allowed
        # (separate subcommands; the rm has no /mnt/data arg).
        "rm /tmp/junk && echo cleaned /mnt/data done",
        # find on a non-/mnt/data path; /mnt/data only in an -exec message:
        # allowed (find's search path is /tmp, not /mnt/data).
        'find /tmp -name x -exec echo {} /mnt/data ;',
    ],
)
def test_mnt_data_false_positives_allowed(command: str) -> None:
    _assert_allowed(_run(command))


# Quoted-message cases the hook deliberately denies (see note above): the verb
# and /mnt/data co-occur inside the same quoted flag value, which is
# indistinguishable from a `bash -c "rm -rf /mnt/data"` wrapper. Denying is the
# safe choice; the user rewords the message if hit.
@pytest.mark.parametrize(
    "command",
    [
        'git commit -m "rm the /mnt/data scratch dir"',
        'echo "rm -rf /mnt/data is blocked" >> notes.md',
    ],
)
def test_mnt_data_quoted_false_positives_denied(command: str) -> None:
    _assert_denied(_run(command), "/mnt/data")


# -- payload edge cases -----------------------------------------------------


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
