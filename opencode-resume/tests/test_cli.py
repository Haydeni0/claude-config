"""Keeper tests: CLI entry - argument resolution, preview flag, interactive pick, errors."""

from __future__ import annotations

import io
from collections.abc import Callable
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from opencode_resume import cli


@pytest.fixture
def make_sessions(make_db: Callable[[list[dict]], Path]) -> Callable[[list[dict]], Path]:
    return make_db


def _session(sid: str, title: str, messages: list[dict], ts: int = 1) -> dict:
    return {"id": sid, "title": title, "directory": "/r", "time_updated": ts,
            "time_created": ts, "messages": messages}


def _user(text: str) -> dict:
    return {"id": "u1", "role": "user", "parts": [{"type": "text", "text": text}]}


def test_session_arg_prints_full_transcript(
    make_sessions: Callable[[list[dict]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    db = make_sessions([_session("ses_x", "My talk", [_user("hello")])])
    rc = cli.main(["--db", str(db), "My talk"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "**User:** hello" in out
    assert "Continuing this conversation in Claude Code." in out


def test_preview_flag_emits_truncated_preview(
    make_sessions: Callable[[list[dict]], Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    msgs = [
        {"id": f"m{i}", "role": "user" if i % 2 == 0 else "assistant",
         "parts": [{"type": "text", "text": f"turn {i}"}]}
        for i in range(40)
    ]
    db = make_sessions([_session("ses_x", "big", msgs)])
    rc = cli.main(["--db", str(db), "big", "--preview"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "preview truncated" in out
    assert "turn 20" not in out


def test_no_match_exits_nonzero(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    db = make_sessions([_session("ses_x", "real", [])])
    with pytest.raises(SystemExit) as exc:
        cli.main(["--db", str(db), "nope"])
    assert exc.value.code != 0


def test_no_arg_picks_by_number_via_stdin(
    make_sessions: Callable[[list[dict]], Path],
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = make_sessions([
        _session("ses_old", "older", [], ts=100),
        _session("ses_new", "newer", [_user("pick me")], ts=300),
    ])
    monkeypatch.setattr("sys.stdin", io.StringIO("1\n"))
    rc = cli.main(["--db", str(db)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "**User:** pick me" in out
    assert "**title:** newer" in out


def test_no_arg_no_sessions_exits_nonzero(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    db = make_sessions([])
    with pytest.raises(SystemExit) as exc:
        cli.main(["--db", str(db)])
    assert exc.value.code != 0
