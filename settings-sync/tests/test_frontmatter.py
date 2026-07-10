import pathlib

import pytest

from settings_sync.frontmatter import dump, parse


def test_parse_extracts_frontmatter_and_body():
    markdown = "---\nname: review\ntools: Read, Grep\nskills:\n  - a\n---\nBody text.\n"
    frontmatter, body = parse(markdown)
    assert frontmatter["name"] == "review"
    assert frontmatter["skills"] == ["a"]
    assert body == "Body text.\n"


def test_parse_returns_empty_dict_when_no_frontmatter():
    markdown = "Just body, no frontmatter.\n"
    frontmatter, body = parse(markdown)
    assert frontmatter == {}
    assert body == markdown


def test_parse_treats_unclosed_delimiter_as_no_frontmatter():
    markdown = "---\nname: review\nbut no closing delimiter\n"
    frontmatter, body = parse(markdown)
    assert frontmatter == {}
    assert body == markdown


def test_dump_round_trips_through_parse():
    frontmatter = {"name": "review", "tools": "Read, Grep", "skills": ["a", "b"]}
    body = "You are a reviewer.\n"
    markdown = dump(frontmatter, body)
    parsed_fm, parsed_body = parse(markdown)
    assert parsed_fm == frontmatter
    assert parsed_body == body
