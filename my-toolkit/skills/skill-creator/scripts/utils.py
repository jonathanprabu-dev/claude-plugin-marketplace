"""Shared utilities for skill-creator scripts."""

import json
from pathlib import Path



def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content)."""
    content = (skill_path / "SKILL.md").read_text()
    lines = content.split("\n")

    if lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter (no opening ---)")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("SKILL.md missing frontmatter (no closing ---)")

    name = ""
    description = ""
    frontmatter_lines = lines[1:end_idx]
    i = 0
    while i < len(frontmatter_lines):
        line = frontmatter_lines[i]
        if line.startswith("name:"):
            name = line[len("name:"):].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:"):].strip()
            # Handle YAML multiline indicators (>, |, >-, |-)
            if value in (">", "|", ">-", "|-"):
                continuation_lines: list[str] = []
                i += 1
                while i < len(frontmatter_lines) and (frontmatter_lines[i].startswith("  ") or frontmatter_lines[i].startswith("\t")):
                    continuation_lines.append(frontmatter_lines[i].strip())
                    i += 1
                description = " ".join(continuation_lines)
                continue
            else:
                description = value.strip('"').strip("'")
        i += 1

    return name, description, content


def normalize_eval_set(raw: object) -> list[dict]:
    """Normalize supported eval JSON shapes for trigger evaluation.

    Skill authoring evals are usually stored as:
      {"skill_name": "...", "evals": [{"prompt": "..."}]}

    The trigger harness historically expected:
      [{"query": "...", "should_trigger": true}]

    This accepts both, maps prompt->query, and treats schema-style eval cases as
    positive trigger examples unless they explicitly set should_trigger.
    """
    if isinstance(raw, dict):
        if "evals" not in raw:
            raise ValueError("Eval JSON object must contain an 'evals' array")
        raw_items = raw["evals"]
    else:
        raw_items = raw

    if not isinstance(raw_items, list):
        raise ValueError("Eval set must be a list, or an object with an 'evals' list")

    normalized: list[dict] = []
    for idx, item in enumerate(raw_items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Eval item {idx} must be an object")

        query = item.get("query") or item.get("prompt")
        if not isinstance(query, str) or not query.strip():
            raise ValueError(f"Eval item {idx} must contain a non-empty 'query' or 'prompt'")

        normalized_item = dict(item)
        normalized_item["query"] = query
        normalized_item["should_trigger"] = bool(item.get("should_trigger", True))
        normalized.append(normalized_item)

    return normalized


def load_eval_set(path: Path) -> list[dict]:
    """Load and normalize an eval JSON file."""
    return normalize_eval_set(json.loads(path.read_text()))
