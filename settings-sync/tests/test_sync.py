import json
import pathlib

from settings_sync.sync import Status, sync_dir_files, sync_dir_symlinks, sync_json


def test_sync_json_creates_new_file(tmp_path: pathlib.Path):
    target = tmp_path / "settings.json"
    outcome = sync_json(target, '{"a": 1, "b": 2}\n')
    assert outcome.status == Status.CREATED
    assert target.is_file()
    assert json.loads(target.read_text()) == {"a": 1, "b": 2}


def test_sync_json_identical_semantic_content(tmp_path: pathlib.Path):
    target = tmp_path / "settings.json"
    target.write_text('{\n  "b": 2,\n  "a": 1\n}\n')
    # Same dict, different key order/formatting
    outcome = sync_json(target, '{"a": 1, "b": 2}\n')
    assert outcome.status == Status.UNCHANGED
    assert outcome.detail == "identical"


def test_sync_json_detects_semantic_diff(tmp_path: pathlib.Path):
    target = tmp_path / "settings.json"
    target.write_text('{"a": 1, "b": 3}\n')
    outcome = sync_json(target, '{"a": 1, "b": 2}\n', force=False)
    assert outcome.status == Status.SKIPPED
    assert "differs" in outcome.detail


def test_sync_json_rejects_invalid_source_json(tmp_path: pathlib.Path):
    target = tmp_path / "settings.json"
    outcome = sync_json(target, '{"a": 1, broken json')
    assert outcome.status == Status.FAILED
    assert "invalid JSON" in outcome.detail
    assert not target.exists()


def test_sync_dir_symlinks_missing_source_dir(tmp_path: pathlib.Path):
    source_dir = tmp_path / "nonexistent"
    target_dir = tmp_path / "dst"
    target_dir.mkdir(parents=True)
    (target_dir / "existing-file").write_text("keep me")

    outcomes = sync_dir_symlinks(target_dir, source_dir, force=True)
    assert len(outcomes) == 1
    assert outcomes[0].status == Status.NO_SOURCE
    assert (target_dir / "existing-file").exists()


def test_sync_dir_symlinks_creates_and_cleans_orphans(tmp_path: pathlib.Path):
    source_dir = tmp_path / "src"
    (source_dir / "skill-a").mkdir(parents=True)
    (source_dir / "skill-b").mkdir(parents=True)

    target_dir = tmp_path / "dst"
    target_dir.mkdir(parents=True)
    (target_dir / "orphan-skill").mkdir(parents=True)

    # Without force -> warn on orphan
    outcomes = sync_dir_symlinks(target_dir, source_dir, force=False)
    assert any(o.status == Status.WARNED and "orphan-skill" in str(o.path) for o in outcomes)
    assert (target_dir / "skill-a").is_symlink()
    assert (target_dir / "orphan-skill").exists()

    # With force -> orphan removed
    outcomes = sync_dir_symlinks(target_dir, source_dir, force=True)
    assert any(o.status == Status.REPLACED and "orphan-skill" in str(o.path) for o in outcomes)
    assert not (target_dir / "orphan-skill").exists()


def test_sync_dir_files_with_orphans(tmp_path: pathlib.Path):
    source_dir = tmp_path / "src"
    source_dir.mkdir(parents=True)
    (source_dir / "provider-a.json").write_text('{"name": "a"}')

    target_dir = tmp_path / "dst"
    target_dir.mkdir(parents=True)
    (target_dir / "orphan.json").write_text('{"name": "orphan"}')

    # Without force -> warn on orphan
    outcomes = sync_dir_files(target_dir, source_dir, pattern="*.json", force=False, sync_fn=sync_json)
    assert any(o.status == Status.WARNED and "orphan.json" in str(o.path) for o in outcomes)
    assert (target_dir / "provider-a.json").is_file()

    # With force -> orphan deleted
    outcomes = sync_dir_files(target_dir, source_dir, pattern="*.json", force=True, sync_fn=sync_json)
    assert any(o.status == Status.REPLACED and "orphan.json" in str(o.path) for o in outcomes)
    assert not (target_dir / "orphan.json").exists()
