import pytest

from settings_sync.agents import transform_agent
from settings_sync.frontmatter import parse

CODE_REVIEWER = """---
name: code-reviewer
description: Code review assistant.
tools: Read, Grep, Glob, Bash, Agent
disallowedTools: Write, Edit
skills:
  - code-review-guidelines
---

You are a code review assistant.
"""

META_REVIEWER = """---
name: meta-reviewer
description: Meta-review assistant.
tools: Read, Grep, Glob, Bash
disallowedTools: Write, Edit, Agent
skills:
  - meta-review-guidelines
  - code-review-guidelines
---

Body.
"""


def test_allowed_tools_map_to_allow():
    transformed, _ = transform_agent(CODE_REVIEWER)
    fm, _ = parse(transformed)
    permission = fm["permission"]
    assert permission["read"] == "allow"
    assert permission["grep"] == "allow"
    assert permission["glob"] == "allow"
    assert permission["bash"] == "allow"
    assert permission["task"] == "allow"


def test_unlisted_mapped_tools_denied():
    transformed, _ = transform_agent(CODE_REVIEWER)
    fm, _ = parse(transformed)
    permission = fm["permission"]
    assert permission["edit"] == "deny"
    assert permission["list"] == "deny"
    assert permission["todowrite"] == "deny"
    assert permission["webfetch"] == "deny"


def test_disallowed_tool_omitted_from_tools_is_denied():
    transformed, _ = transform_agent(META_REVIEWER)
    fm, _ = parse(transformed)
    assert fm["permission"]["task"] == "deny"


def test_skills_restricted_to_allowlist():
    transformed, _ = transform_agent(META_REVIEWER)
    fm, _ = parse(transformed)
    skill_perm = fm["permission"]["skill"]
    assert skill_perm["*"] == "deny"
    assert skill_perm["meta-review-guidelines"] == "allow"
    assert skill_perm["code-review-guidelines"] == "allow"


def test_opencode_only_keys_not_set():
    transformed, _ = transform_agent(CODE_REVIEWER)
    fm, _ = parse(transformed)
    permission = fm["permission"]
    for key in ("question", "lsp", "external_directory", "doom_loop", "websearch"):
        assert key not in permission


def test_body_preserved():
    transformed, _ = transform_agent(CODE_REVIEWER)
    _, body = parse(transformed)
    assert body.strip() == "You are a code review assistant."


def test_mode_defaults_to_subagent():
    transformed, _ = transform_agent(CODE_REVIEWER)
    fm, _ = parse(transformed)
    assert fm["mode"] == "subagent"


def test_unknown_tool_warns():
    unknown = """---
name: weird
description: Has unknown tool
tools: Read, NotARealTool
---

Body.
"""
    _, warnings = transform_agent(unknown)
    assert any("NotARealTool" in w for w in warnings)


def test_claude_code_only_keys_dropped():
    transformed, _ = transform_agent(CODE_REVIEWER)
    fm, _ = parse(transformed)
    assert "tools" not in fm
    assert "disallowedTools" not in fm
    assert "skills" not in fm


def test_transform_is_deterministic_across_runs():
    t1, _ = transform_agent(CODE_REVIEWER)
    t2, _ = transform_agent(CODE_REVIEWER)
    assert t1 == t2
