#!/usr/bin/env python3
"""Require declared model resources before Codex creates an agent or task."""

from __future__ import annotations

import io
import json
import sys
import tomllib
from pathlib import Path
from typing import Any


if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SPAWN_AGENT = "multi_agent_v1__spawn_agent"
CREATE_THREAD = "codex_app__create_thread"
AGENT_PROFILE_DIR = Path.home() / ".codex" / "agents"


def _fixed_agent_profile_has_resources(agent_type: Any) -> bool:
    if not isinstance(agent_type, str) or not agent_type.strip():
        return False
    profile_name = agent_type.strip()
    if Path(profile_name).name != profile_name:
        return False
    try:
        profile = tomllib.loads(
            (AGENT_PROFILE_DIR / f"{profile_name}.toml").read_text(encoding="utf-8")
        )
    except (OSError, tomllib.TOMLDecodeError):
        return False
    return bool(
        str(profile.get("model") or "").strip()
        and str(profile.get("model_reasoning_effort") or "").strip()
    )


def _missing_spawn_fields(tool_input: dict[str, Any]) -> list[str]:
    if _fixed_agent_profile_has_resources(tool_input.get("agent_type")):
        return []
    missing: list[str] = []
    if not str(tool_input.get("model") or "").strip():
        missing.append("tool_input.model")
    if not str(tool_input.get("reasoning_effort") or "").strip():
        missing.append("tool_input.reasoning_effort")
    return missing


def _missing_thread_fields(tool_input: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not str(tool_input.get("model") or "").strip():
        missing.append("tool_input.model")
    if not str(tool_input.get("thinking") or "").strip():
        missing.append("tool_input.thinking")
    return missing


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, EOFError):
        return 0

    tool_name = payload.get("tool_name")
    if tool_name not in {SPAWN_AGENT, CREATE_THREAD}:
        return 0
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}

    if tool_name == SPAWN_AGENT:
        missing = _missing_spawn_fields(tool_input)
        guidance = (
            "Pass explicit model and reasoning_effort, or use an agent_type profile "
            "that declares model and model_reasoning_effort."
        )
    else:
        missing = _missing_thread_fields(tool_input)
        guidance = "Pass explicit model and thinking."

    if not missing:
        return 0
    print(
        f"[spawn-resource-gate] {tool_name} blocked: "
        + " + ".join(missing)
        + f" missing. {guidance}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
