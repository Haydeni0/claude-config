"""Convert an opencode session (SQLite) into a Claude Code transcript.

Reads session/message/part tables from an opencode SQLite DB and emits a
markdown transcript the current Claude Code session ingests as context.
Pure stdlib (sqlite3, json, argparse, sys). Designed to run with python3, no venv.
"""

from __future__ import annotations

import datetime
import json
import sqlite3
from pathlib import Path

DEFAULT_DB = Path.home() / ".local" / "share" / "opencode" / "opencode.db"

OUTPUT_THRESHOLD = 2048
OUTPUT_KEEP = 500

CONTINUATION_PROMPT = (
    "Continuing this conversation in Claude Code. "
    "Respond to the user's next message."
)


def _truncate_output(text: str) -> str:
    if len(text) < OUTPUT_THRESHOLD:
        return text
    return f"{text[:OUTPUT_KEEP]}\n... [truncated, {len(text)} chars total]"


def _open(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


_SESSION_COLS = (
    "id, title, directory, time_updated, time_created, model, agent, parent_id"
)


def list_sessions(db_path: Path) -> list[sqlite3.Row]:
    conn = _open(db_path)
    rows = conn.execute(
        f"SELECT {_SESSION_COLS} FROM session "
        "WHERE parent_id IS NULL ORDER BY time_updated DESC",
    ).fetchall()
    conn.close()
    return rows


def match_session(db_path: Path, query: str) -> sqlite3.Row | None:
    conn = _open(db_path)
    row = conn.execute(
        f"SELECT {_SESSION_COLS} FROM session WHERE id = ?", (query,)
    ).fetchone()
    if row is None:
        row = conn.execute(
            f"SELECT {_SESSION_COLS} FROM session "
            "WHERE parent_id IS NULL AND title LIKE ? "
            "ORDER BY time_updated DESC LIMIT 1",
            (f"%{query}%",),
        ).fetchone()
    conn.close()
    return row


def msg_count(db_path: Path, session_id: str) -> int:
    conn = _open(db_path)
    count = conn.execute(
        "SELECT count(*) FROM message WHERE session_id = ?", (session_id,)
    ).fetchone()[0]
    conn.close()
    return count


def parse_model(model_json: str | None) -> str:
    if not model_json:
        return "unknown"
    try:
        d = json.loads(model_json)
        return d.get("modelID") or d.get("id") or model_json
    except (json.JSONDecodeError, TypeError):
        return model_json


def _fmt_time(ts_ms: int | None) -> str:
    if not ts_ms:
        return "unknown"
    return datetime.datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d %H:%M")


def _session_span(conn: sqlite3.Connection, session_id: str) -> tuple[str, str]:
    row = conn.execute(
        "SELECT min(time_created), max(time_created) FROM message WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    return _fmt_time(row[0]), _fmt_time(row[1])


def _iter_parts(conn: sqlite3.Connection, message_id: str):
    for row in conn.execute(
        "SELECT data FROM part WHERE message_id = ? ORDER BY time_created",
        (message_id,),
    ):
        yield json.loads(row["data"])


def _render_user_turn(conn: sqlite3.Connection, message_id: str, out: list[str]) -> None:
    texts = [
        p["text"]
        for p in _iter_parts(conn, message_id)
        if p.get("type") == "text" and p.get("text", "").strip()
    ]
    content = "\n".join(texts) if texts else "*(no user text)*"
    out.append(f"\n**User:** {content}")


PREVIEW_HEAD = 12
PREVIEW_TAIL = 8


def build_preview(transcript: str) -> str:
    lines = transcript.split("\n")
    if len(lines) <= PREVIEW_HEAD + PREVIEW_TAIL:
        return transcript
    head = lines[:PREVIEW_HEAD]
    tail = lines[-PREVIEW_TAIL:]
    return (
        "\n".join(head)
        + "\n\n... (preview truncated, full transcript loaded as context) ...\n\n"
        + "\n".join(tail)
    )


def _render_tool_part(part: dict, out: list[str]) -> None:
    tool = part.get("tool", "unknown")
    state = part.get("state", {})
    status = state.get("status", "unknown")
    inp = state.get("input") or {}
    inp_str = json.dumps(inp, ensure_ascii=False)
    out.append(f"\n> **{tool}** `{inp_str}`")
    output = state.get("output")
    if output is not None and status == "completed":
        text = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
        out.append(f"> \n> {_truncate_output(text)}")


def _render_assistant_turn(conn: sqlite3.Connection, message_id: str, out: list[str]) -> None:
    has_content = False
    for part in _iter_parts(conn, message_id):
        ptype = part.get("type")
        if ptype == "text" and part.get("text", "").strip():
            out.append(f"\n**Assistant:** {part['text']}")
            has_content = True
        elif ptype == "tool":
            _render_tool_part(part, out)
            has_content = True
    if not has_content:
        out.append("\n**Assistant:** *(tool call)*")


def _build_header(conn: sqlite3.Connection, session_row: sqlite3.Row) -> list[str]:
    model = parse_model(session_row["model"])
    span_start, span_end = _session_span(conn, session_row["id"])
    msg_count = conn.execute(
        "SELECT count(*) FROM message WHERE session_id = ?", (session_row["id"],)
    ).fetchone()[0]
    return [
        "# opencode session -> Claude Code resume",
        f"**title:** {session_row['title']}",
        f"**dir:** {session_row['directory']}",
        f"**model:** {model}  |  **agent:** {session_row['agent'] or 'build'}",
        f"**msgs:** {msg_count}  |  **span:** {span_start} -> {span_end}",
        f"**opencode session id:** {session_row['id']}",
        "",
        "---",
        "",
    ]


def build_transcript(db_path: Path, session_id: str) -> str:
    conn = _open(db_path)
    session_row = conn.execute(
        f"SELECT {_SESSION_COLS} FROM session WHERE id = ?", (session_id,)
    ).fetchone()
    if session_row is None:
        conn.close()
        raise KeyError(session_id)
    out: list[str] = _build_header(conn, session_row)
    for msg_row in conn.execute(
        "SELECT id, data FROM message WHERE session_id = ? ORDER BY time_created",
        (session_id,),
    ):
        role = json.loads(msg_row["data"]).get("role")
        if role == "user":
            _render_user_turn(conn, msg_row["id"], out)
        elif role == "assistant":
            _render_assistant_turn(conn, msg_row["id"], out)
    out.append("")
    out.append("---")
    out.append("")
    out.append(CONTINUATION_PROMPT)
    out.append("")
    conn.close()
    return "\n".join(out)
