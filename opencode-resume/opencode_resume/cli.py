"""CLI entry: resolve a session and print its transcript (full or preview)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from opencode_resume.convert import (
    DEFAULT_DB,
    build_preview,
    build_transcript,
    list_sessions,
    match_session,
    msg_count,
    parse_model,
)


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="opencode-resume",
        description="Convert an opencode session into a Claude Code transcript.",
    )
    ap.add_argument(
        "session",
        nargs="?",
        help="exact session id or title substring; omit to pick interactively",
    )
    ap.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"opencode SQLite DB (default: {DEFAULT_DB})",
    )
    ap.add_argument(
        "--preview",
        action="store_true",
        help="emit a truncated preview to stdout instead of the full transcript",
    )
    return ap


def _resolve(db_path: Path, query: str | None) -> str:
    if query is not None:
        row = match_session(db_path, query)
        if row is None:
            sys.exit(f"no top-level session matched: {query!r}")
        return row["id"]
    rows = list_sessions(db_path)
    if not rows:
        sys.exit("no top-level opencode sessions found")
    print("Recent opencode sessions (top-level only):\n", file=sys.stderr)
    for i, r in enumerate(rows, 1):
        count = msg_count(db_path, r["id"])
        print(
            f"  {i}. {r['title'][:50]:<50} | {r['directory']} | "
            f"{parse_model(r['model'])} | {count} msgs",
            file=sys.stderr,
        )
    print("\nEnter a number, an exact session id, or a title substring: ",
          file=sys.stderr, end="")
    sys.stderr.flush()
    choice = input().strip()
    if choice.isdigit() and 1 <= int(choice) <= len(rows):
        return rows[int(choice) - 1]["id"]
    row = match_session(db_path, choice)
    if row is None:
        sys.exit(f"no match for: {choice!r}")
    return row["id"]


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    session_id = _resolve(args.db, args.session)
    transcript = build_transcript(args.db, session_id)
    print(build_preview(transcript) if args.preview else transcript)
    return 0


if __name__ == "__main__":
    sys.exit(main())
