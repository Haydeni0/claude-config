"""Parse and emit YAML frontmatter in markdown files."""

import yaml


def parse(markdown: str) -> tuple[dict, str]:
    delimiter = "---\n"
    if not markdown.startswith(delimiter):
        return {}, markdown
    end = markdown.find("\n---\n", len(delimiter))
    if end == -1:
        return {}, markdown
    frontmatter_text = markdown[len(delimiter):end]
    body = markdown[end + len("\n---\n"):]
    data = yaml.safe_load(frontmatter_text) or {}
    return data, body


def dump(frontmatter: dict, body: str) -> str:
    yaml_block = yaml.safe_dump(frontmatter, sort_keys=False, default_flow_style=False)
    return f"---\n{yaml_block}---\n{body}"

