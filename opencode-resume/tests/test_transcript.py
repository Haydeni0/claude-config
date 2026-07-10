"""Keeper tests: transcript rendering - header, user/assistant turns, tools, truncation, preview."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from opencode_resume.convert import (
    OUTPUT_KEEP,
    OUTPUT_THRESHOLD,
    build_preview,
    build_transcript,
)


@pytest.fixture
def make_sessions(make_db: Callable[[list[dict]], Path]) -> Callable[[list[dict]], Path]:
    return make_db


def _user(text: str) -> dict:
    return {"role": "user", "parts": [{"type": "text", "text": text}]}


def _assistant(parts: list[dict]) -> dict:
    return {"role": "assistant", "parts": parts}


def _text(text: str, ts: int | None = None) -> dict:
    p = {"type": "text", "text": text}
    if ts is not None:
        p["time_created"] = ts
    return p


def _tool(tool: str, inp: dict | None = None, output: str | None = None,
          status: str = "completed", ts: int | None = None) -> dict:
    state: dict = {"status": status, "input": inp or {}}
    if output is not None:
        state["output"] = output
    p = {"type": "tool", "tool": tool, "callID": "c", "state": state}
    if ts is not None:
        p["time_created"] = ts
    return p


def _reasoning(text: str) -> dict:
    return {"type": "reasoning", "text": text, "time": {"start": 1, "end": 2}}


def _session(messages: list[dict], **kw) -> dict:
    s = {"id": "ses_x", "title": "t", "directory": "/r",
         "time_updated": 1, "time_created": 1, "messages": messages}
    s.update(kw)
    return s


def test_header_includes_metadata(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    out = build_transcript(make_sessions([_session(
        [_user("hi"), _assistant([_text("hey")])],
        title="My session", directory="/repo",
        model='{"providerID":"glm","modelID":"glm-5.2"}', agent="build",
    )]), "ses_x")
    assert "# opencode session -> Claude Code resume" in out
    assert "**title:** My session" in out
    assert "**dir:** /repo" in out
    assert "**model:** glm-5.2" in out
    assert "**agent:** build" in out
    assert "**msgs:** 2" in out
    assert "**opencode session id:** ses_x" in out


def test_renders_user_then_assistant_text_in_order(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    out = build_transcript(make_sessions([_session(
        [_user("what is 2+2"), _assistant([_text("4")])],
    )]), "ses_x")
    assert "**User:** what is 2+2" in out
    assert "**Assistant:** 4" in out
    assert out.index("**User:** what is 2+2") < out.index("**Assistant:** 4")


def test_ends_with_continuation_prompt(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    out = build_transcript(make_sessions([_session([_user("hi")])]), "ses_x")
    assert "Continuing this conversation in Claude Code." in out
    assert out.rstrip().endswith("Respond to the user's next message.")


def test_tool_renders_as_blockquote_with_name_and_input(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    out = build_transcript(make_sessions([_session(
        [_assistant([_tool("webfetch", {"url": "https://x"})])],
    )]), "ses_x")
    assert "> **webfetch**" in out
    assert "https://x" in out


def test_tool_output_included_when_completed(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    out = build_transcript(make_sessions([_session(
        [_assistant([_tool("webfetch", {"url": "u"}, output="hello world")])],
    )]), "ses_x")
    assert "hello world" in out


def test_reasoning_parts_are_dropped(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    out = build_transcript(make_sessions([_session(
        [_assistant([_reasoning("secret"), _text("visible reply")])],
    )]), "ses_x")
    assert "visible reply" in out
    assert "secret" not in out


def test_text_and_tool_preserve_time_order(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    out = build_transcript(make_sessions([_session(
        [_assistant([_text("let me check", 10), _tool("webfetch", output="R", ts=20), _text("done", 30)])],
    )]), "ses_x")
    assert out.index("**Assistant:** let me check") < out.index("> **webfetch**")
    assert out.index("> **webfetch**") < out.index("**Assistant:** done")


def test_small_tool_output_kept_in_full(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    out = build_transcript(make_sessions([_session(
        [_assistant([_tool("webfetch", output="small output")])],
    )]), "ses_x")
    assert "small output" in out
    assert "truncated" not in out


def test_large_tool_output_truncated_with_marker(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    big = "x" * (OUTPUT_THRESHOLD + 100)
    out = build_transcript(make_sessions([_session(
        [_assistant([_tool("webfetch", output=big)])],
    )]), "ses_x")
    assert "[truncated," in out
    assert f"{len(big)} chars total]" in out
    assert out.count("x" * OUTPUT_KEEP) == 1


def test_short_transcript_previewed_in_full(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    full = build_transcript(make_sessions([_session(
        [_user("a"), _assistant([_text("b")]), _user("c")],
    )]), "ses_x")
    assert build_preview(full) == full


def test_long_transcript_preview_has_header_tail_and_marker(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    msgs = [
        {"id": f"m{i}", "role": "user" if i % 2 == 0 else "assistant",
         "parts": [{"type": "text", "text": f"turn {i}"}]}
        for i in range(40)
    ]
    full = build_transcript(make_sessions([_session(
        msgs, title="big session",
    )]), "ses_x")
    preview = build_preview(full)
    assert "**title:** big session" in preview
    assert "preview truncated" in preview
    assert "turn 39" in preview
    assert "turn 20" not in preview
