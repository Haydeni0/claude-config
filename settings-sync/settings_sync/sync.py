"""Shared outcome types and symlink sync helper."""

import os
import shutil
from enum import StrEnum
from pathlib import Path
from typing import Self


class Status(StrEnum):
    CREATED = "created"
    REPLACED = "replaced"
    UNCHANGED = "unchanged"
    SKIPPED = "skipped"
    NO_SOURCE = "no_source"
    FAILED = "failed"
    WARNED = "warned"
    WOULD_CREATE = "would_create"
    WOULD_REPLACE = "would_replace"
    WOULD_SKIP = "would_skip"


class Outcome:
    """Result of one sync action: what happened at a path."""

    def __init__(
        self,
        path: Path,
        status: Status,
        detail: str = "",
        old_content: str | None = None,
        new_content: str | None = None,
    ) -> None:
        self.path = path
        self.status = status
        self.detail = detail
        self.old_content = old_content
        self.new_content = new_content

    @property
    def changed(self) -> bool:
        return self.status in (Status.CREATED, Status.REPLACED)

    def __repr__(self) -> str:
        return f"Outcome(path={self.path!r}, status={self.status!r}, detail={self.detail!r})"

    def __eq__(self, other: "Outcome") -> bool:  # type: ignore[override]
        return (
            isinstance(other, Outcome)
            and self.path == other.path
            and self.status == other.status
            and self.detail == other.detail
        )


def _resolve_link_target(link: Path) -> Path:
    rel = os.readlink(link)
    return (link.parent / rel).resolve()


def sync_symlink(target: Path, source: Path, force: bool = False, dry_run: bool = False) -> Outcome:
    """Create or repair a relative symlink at `target` pointing to `source`."""
    desired_rel = os.path.relpath(source, target.parent)

    if dry_run:
        if not target.exists() and not target.is_symlink():
            return Outcome(target, Status.WOULD_CREATE, f"symlink -> {desired_rel}")
        if target.is_symlink() and _resolve_link_target(target) == source.resolve():
            return Outcome(target, Status.UNCHANGED, "already correct")
        return Outcome(target, Status.WOULD_REPLACE, f"-> {desired_rel}")

    if not target.exists() and not target.is_symlink():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(desired_rel)
        return Outcome(target, Status.CREATED, f"symlink -> {desired_rel}")

    if target.is_symlink():
        if _resolve_link_target(target) == source.resolve():
            return Outcome(target, Status.UNCHANGED, "already correct")
        if not force:
            return Outcome(
                target,
                Status.WARNED,
                f"symlink points elsewhere; use --force to retarget -> {desired_rel}",
            )
        target.unlink()
        target.symlink_to(desired_rel)
        return Outcome(target, Status.REPLACED, f"retargeted -> {desired_rel}")

    if not force:
        return Outcome(
            target,
            Status.SKIPPED,
            f"real file/dir exists at {target}; use --force to replace with symlink",
        )

    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()
    target.symlink_to(desired_rel)
    return Outcome(target, Status.REPLACED, f"replaced real entry -> {desired_rel}")


def sync_text(target: Path, content: str, force: bool = False, dry_run: bool = False) -> Outcome:
    """Write `content` to `target`, refusing to clobber a diverging file without force."""
    if dry_run:
        if not target.exists():
            return Outcome(target, Status.WOULD_CREATE, "new file", new_content=content)
        existing = target.read_text()
        if existing == content:
            return Outcome(target, Status.UNCHANGED, "identical")
        return Outcome(target, Status.WOULD_REPLACE, "differs from source", old_content=existing, new_content=content)

    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return Outcome(target, Status.CREATED, "new file", new_content=content)

    existing = target.read_text()
    if existing == content:
        return Outcome(target, Status.UNCHANGED, "identical")

    if not force:
        return Outcome(
            target,
            Status.SKIPPED,
            "differs from source; use --force to overwrite",
            old_content=existing,
            new_content=content,
        )

    target.write_text(content)
    return Outcome(target, Status.REPLACED, "overwrote diverging file", old_content=existing, new_content=content)
