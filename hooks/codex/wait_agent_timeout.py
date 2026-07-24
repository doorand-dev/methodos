#!/usr/bin/env python3
"""Raise short Codex wait_agent calls to the runtime's maximum wait window."""

from __future__ import annotations

import json
import sys
from typing import Any


TOOL_NAME = "multi_agent_v1__wait_agent"
MAX_TIMEOUT_MS = 3_600_000


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, EOFError):
        return 0

    if payload.get("tool_name") != TOOL_NAME:
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    timeout_ms = tool_input.get("timeout_ms")
    if timeout_ms is not None:
        if not isinstance(timeout_ms, (int, float)) or isinstance(timeout_ms, bool):
            return 0
        if timeout_ms >= MAX_TIMEOUT_MS:
            return 0

    updated_input: dict[str, Any] = dict(tool_input)
    updated_input["timeout_ms"] = MAX_TIMEOUT_MS
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "updatedInput": updated_input,
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
