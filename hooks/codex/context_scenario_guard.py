#!/usr/bin/env python3
"""Advisory context-placement check for Codex apply_patch calls."""

from __future__ import annotations

import json
import re
import sys


TOOL_NAME = "apply_patch"
PATCH_HEADER = re.compile(r"\*\*\* (?:(?:Add|Update|Delete) File|Move to): (.+)$")
HOT_BASENAMES = {"AGENTS.md", "SKILL.md", "MEMORY.md", "hooks.json"}
HOT_SEGMENTS = {"rules", "agents", "hooks", "skills", "handoffs"}
HOT_SUFFIXES = {".md", ".toml", ".json", ".py"}


def _hot_targets(patch: str) -> list[str]:
    targets: list[str] = []
    for line in patch.splitlines():
        match = PATCH_HEADER.fullmatch(line)
        if match is None:
            continue
        path = match.group(1).strip().replace("\\", "/")
        parts = tuple(part for part in path.split("/") if part)
        basename = parts[-1] if parts else ""
        if basename in HOT_BASENAMES or (
            any(part in HOT_SEGMENTS for part in parts)
            and any(path.endswith(suffix) for suffix in HOT_SUFFIXES)
        ):
            targets.append(path)
    return targets


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, EOFError):
        return 0

    if not isinstance(payload, dict) or payload.get("tool_name") != TOOL_NAME:
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    patch = tool_input.get("command")
    if not isinstance(patch, str):
        return 0

    targets = _hot_targets(patch)
    if not targets:
        return 0

    advisory = (
        "Context-placement self-check for exact hot targets: "
        + ", ".join(targets)
        + ". This patch is proceeding. After it completes, verify reader+trigger; "
        "choose the minimum "
        "global/project/subtree scope; check existing SSOT/duplicate; name the "
        "actual consumer/load path. Only if semantic placement remains ambiguous, "
        "run context-novelist before the next edit."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": advisory,
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
