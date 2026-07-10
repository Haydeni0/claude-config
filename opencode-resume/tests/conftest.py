"""Shared fixtures: a hermetic synthetic opencode SQLite DB.

Builds the minimal slice of the opencode schema the converter reads
(session/message/part + a stub project for the FK), so tests never touch
the user's real ~/.local/share/opencode/opencode.db.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from pathlib import Path

import pytest

PROJECT_ID = "proj_test"
WORKSPACE_ID = "ws_test"


SCHEMA = """
CREATE TABLE `project` (
  `id` text PRIMARY KEY,
  `worktree` text NOT NULL,
  `vcs` text,
  `name` text,
  `icon_url` text,
  `icon_url_override` text,
  `icon_color` text,
  `time_created` integer NOT NULL,
  `time_updated` integer NOT NULL,
  `time_initialized` integer,
  `sandboxes` text NOT NULL,
  `commands` text
);
CREATE TABLE `session` (
  `id` text PRIMARY KEY,
  `project_id` text NOT NULL,
  `workspace_id` text,
  `parent_id` text,
  `slug` text NOT NULL,
  `directory` text NOT NULL,
  `path` text,
  `title` text NOT NULL,
  `version` text NOT NULL,
  `share_url` text,
  `summary_additions` integer,
  `summary_deletions` integer,
  `summary_files` integer,
  `summary_diffs` text,
  `metadata` text,
  `cost` real DEFAULT 0 NOT NULL,
  `tokens_input` integer DEFAULT 0 NOT NULL,
  `tokens_output` integer DEFAULT 0 NOT NULL,
  `tokens_reasoning` integer DEFAULT 0 NOT NULL,
  `tokens_cache_read` integer DEFAULT 0 NOT NULL,
  `tokens_cache_write` integer DEFAULT 0 NOT NULL,
  `revert` text,
  `permission` text,
  `agent` text,
  `model` text,
  `time_created` integer NOT NULL,
  `time_updated` integer NOT NULL,
  `time_compacting` integer,
  `time_archived` integer,
  FOREIGN KEY (`project_id`) REFERENCES `project`(`id`) ON DELETE CASCADE
);
CREATE TABLE `message` (
  `id` text PRIMARY KEY,
  `session_id` text NOT NULL,
  `time_created` integer NOT NULL,
  `time_updated` integer NOT NULL,
  `data` text NOT NULL,
  FOREIGN KEY (`session_id`) REFERENCES `session`(`id`) ON DELETE CASCADE
);
CREATE TABLE `part` (
  `id` text PRIMARY KEY,
  `message_id` text NOT NULL,
  `session_id` text NOT NULL,
  `time_created` integer NOT NULL,
  `time_updated` integer NOT NULL,
  `data` text NOT NULL,
  FOREIGN KEY (`message_id`) REFERENCES `message`(`id`) ON DELETE CASCADE
);
"""


# A session spec: dict of row fields (minus the fiddly defaults) the builder fills in.
SessionSpec = dict


def _model_json(model_id: str, provider: str = "glm") -> str:
    return json.dumps({"providerID": provider, "modelID": model_id})


def build_db(
    db_path: Path,
    sessions: list[SessionSpec],
) -> None:
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        "INSERT INTO project (id, worktree, sandboxes, time_created, time_updated) "
        "VALUES (?, ?, '[]', 0, 0)",
        (PROJECT_ID, "/worktree"),
    )
    t = 1
    for spec in sessions:
        sid = spec["id"]
        title = spec.get("title", "untitled")
        directory = spec.get("directory", "/repo")
        parent_id = spec.get("parent_id")
        model = spec.get("model", _model_json("glm-5.2"))
        agent = spec.get("agent", "build")
        time_created = spec.get("time_created", t)
        time_updated = spec.get("time_updated", t)
        conn.execute(
            """INSERT INTO session
               (id, project_id, workspace_id, parent_id, slug, directory, title,
                version, model, agent, time_created, time_updated, cost,
                tokens_input, tokens_output, tokens_reasoning,
                tokens_cache_read, tokens_cache_write)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0, 0)""",
            (
                sid, PROJECT_ID, WORKSPACE_ID, parent_id, "slug", directory, title,
                "v1", model, agent, time_created, time_updated,
            ),
        )
        msgs = spec.get("messages", [])
        for mi, msg in enumerate(msgs):
            mid = msg.get("id", f"{sid}_msg{mi}")
            mdata = {"role": msg["role"], "time": {"created": t}}
            if "model" in msg:
                mdata["model"] = msg["model"]
            if "agent" in msg:
                mdata["agent"] = msg["agent"]
            mt = msg.get("time_created", t)
            conn.execute(
                "INSERT INTO message (id, session_id, time_created, time_updated, data) "
                "VALUES (?, ?, ?, ?, ?)",
                (mid, sid, mt, mt, json.dumps(mdata)),
            )
            parts = msg.get("parts", [])
            for pi, part in enumerate(parts):
                pid = part.get("id", f"{mid}_part{pi}")
                pt = part.get("time_created", t + pi)
                conn.execute(
                    "INSERT INTO part (id, message_id, session_id, time_created, time_updated, data) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (pid, mid, sid, pt, pt, json.dumps(part)),
                )
            t += len(parts) + 1
        t += 1
    conn.commit()
    conn.close()


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "opencode.db"


@pytest.fixture
def make_db(db_path: Path) -> Callable[[list[SessionSpec]], Path]:
    def _make(sessions: list[SessionSpec]) -> Path:
        build_db(db_path, sessions)
        return db_path

    return _make
