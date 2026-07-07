#!/usr/bin/env python3
"""Codex PreToolUse hook candidate: require model intent on spawn_agent calls."""

from __future__ import annotations

import io
import json
import re
import sys
from typing import Any

if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SPAWN_TOOLS = {"spawn_agent", "multi_agent_v1.spawn_agent"}
MODEL_RE = re.compile(
    r"\b(model|모델)\s*[:=]\s*([\w.-]+|inherited/current|current|inherit|상속)\b",
    re.IGNORECASE,
)


def _as_text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _prompt_text(tool_input: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("message", "prompt", "description"):
        value = tool_input.get(key)
        if isinstance(value, str):
            parts.append(value)
    for item in tool_input.get("items") or []:
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            parts.append(item["text"])
    return "\n".join(parts)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, EOFError):
        return 0

    tool_name = _as_text(payload.get("tool_name") or payload.get("name"))
    if tool_name not in SPAWN_TOOLS:
        return 0

    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return 0

    if _as_text(tool_input.get("model")).strip():
        return 0
    if MODEL_RE.search(_prompt_text(tool_input)):
        return 0

    print(
        "[codex-spawn-model-gate] spawn_agent 호출에 model 의도를 명시하세요.\n"
        "  예: model='gpt-5.5' 또는 prompt에 `model: inherited/current`.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
