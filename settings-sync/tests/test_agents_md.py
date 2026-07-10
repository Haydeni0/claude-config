import pathlib

import pytest

from settings_sync.agents_md import build_agents_md


def test_skills_ref_rewritten_to_plain_text(tmp_path: pathlib.Path):
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("See @skills/uv for rules.\n")
    result = build_agents_md(claude_md)
    assert "the `uv` skill" in result
    assert "@skills/uv" not in result


def test_file_import_inlined(tmp_path: pathlib.Path):
    (tmp_path / "imports").mkdir()
    (tmp_path / "imports" / "foo.md").write_text("Imported content.\n")
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("Header\n@imports/foo.md\nFooter\n")
    result = build_agents_md(claude_md)
    assert "Imported content." in result
    assert "@imports/foo.md" not in result


def test_imports_expand_recursively(tmp_path: pathlib.Path):
    (tmp_path / "imports").mkdir()
    (tmp_path / "imports" / "outer.md").write_text("Outer start\n@imports/inner.md\nOuter end\n")
    (tmp_path / "imports" / "inner.md").write_text("Inner content\n")
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("@imports/outer.md\n")
    result = build_agents_md(claude_md)
    assert "Outer start" in result
    assert "Inner content" in result
    assert "Outer end" in result


def test_cycle_does_not_infinite_loop(tmp_path: pathlib.Path):
    (tmp_path / "imports").mkdir()
    (tmp_path / "imports" / "a.md").write_text("A\n@imports/b.md\n")
    (tmp_path / "imports" / "b.md").write_text("B\n@imports/a.md\n")
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("@imports/a.md\n")
    result = build_agents_md(claude_md)
    assert "A" in result
    assert "B" in result


def test_missing_import_left_intact(tmp_path: pathlib.Path):
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("@does/not/exist.md\n")
    result = build_agents_md(claude_md)
    assert "@does/not/exist.md" in result


def test_sync_agents_md_writes_expanded_content(tmp_path: pathlib.Path):
    claude = tmp_path / "claude" / "CLAUDE.md"
    claude.parent.mkdir(parents=True)
    claude.write_text("See @skills/uv.\n@imports/foo.md\n")
    (tmp_path / "claude" / "imports").mkdir()
    (tmp_path / "claude" / "imports" / "foo.md").write_text("Foo body.\n")
    target = tmp_path / "config" / "opencode" / "AGENTS.md"

    from settings_sync.agents_md import sync_agents_md
    outcome = sync_agents_md(target, claude)

    from settings_sync.sync import Status
    assert outcome.status == Status.CREATED
    assert "Foo body." in target.read_text()
    assert "the `uv` skill" in target.read_text()


def test_sync_agents_md_skips_diverging_without_force(tmp_path: pathlib.Path):
    claude = tmp_path / "claude" / "CLAUDE.md"
    claude.parent.mkdir(parents=True)
    claude.write_text("New content\n")
    target = tmp_path / "config" / "opencode" / "AGENTS.md"
    target.parent.mkdir(parents=True)
    target.write_text("hand-edited\n")

    from settings_sync.agents_md import sync_agents_md
    from settings_sync.sync import Status
    outcome = sync_agents_md(target, claude)

    assert outcome.status == Status.SKIPPED
    assert target.read_text() == "hand-edited\n"
