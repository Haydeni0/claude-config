"""Keeper tests: session listing and resolution (top-level only, exact id / title match)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from opencode_resume.convert import list_sessions, match_session


@pytest.fixture
def make_sessions(make_db: Callable[[list[dict]], Path]) -> Callable[[list[dict]], Path]:
    return make_db


def test_list_sessions_excludes_subagents_and_orders_by_recency(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    db = make_sessions([
        {"id": "ses_old", "title": "old", "time_updated": 100, "time_created": 100},
        {"id": "ses_new", "title": "new", "time_updated": 300, "time_created": 300},
        {"id": "ses_sub", "title": "sub", "parent_id": "ses_new", "time_updated": 500},
    ])
    assert [r["id"] for r in list_sessions(db)] == ["ses_new", "ses_old"]


def test_match_session_accepts_exact_id(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    db = make_sessions([
        {"id": "ses_a", "title": "Slurm partitions overview", "time_updated": 100},
        {"id": "ses_b", "title": "Neural field profiling", "time_updated": 300},
    ])
    assert match_session(db, "ses_a")["id"] == "ses_a"


def test_match_session_substring_picks_most_recent_match(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    db = make_sessions([
        {"id": "ses_a", "title": "Slurm partitions overview", "time_updated": 100},
        {"id": "ses_b", "title": "Neural field profiling", "time_updated": 300},
    ])
    assert match_session(db, "field")["id"] == "ses_b"


def test_match_session_returns_none_when_nothing_matches(
    make_sessions: Callable[[list[dict]], Path],
) -> None:
    db = make_sessions([{"id": "ses_a", "title": "real", "time_updated": 1}])
    assert match_session(db, "nonexistent") is None
