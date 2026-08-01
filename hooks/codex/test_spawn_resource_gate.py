from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Mapping


HOOK = Path(__file__).with_name("spawn-resource-gate.py")


def _run_hook(
    tool_name: str,
    tool_input: dict[str, object],
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_name": tool_name, "tool_input": tool_input}),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def test_missing_canonical_spawn_resources_are_blocked() -> None:
    completed = _run_hook(
        "multi_agent_v1__spawn_agent",
        {"agent_type": "default", "message": "probe"},
    )

    assert completed.returncode == 2
    assert "tool_input.model" in completed.stderr
    assert "tool_input.reasoning_effort" in completed.stderr


def test_explicit_canonical_spawn_resources_are_allowed() -> None:
    completed = _run_hook(
        "multi_agent_v1__spawn_agent",
        {
            "agent_type": "default",
            "message": "probe",
            "model": "gpt-5.6-luna",
            "reasoning_effort": "high",
        },
    )

    assert completed.returncode == 0
    assert completed.stderr == ""


def test_fixed_profile_resources_are_allowed(tmp_path: Path) -> None:
    profile_dir = tmp_path / ".codex" / "agents"
    profile_dir.mkdir(parents=True)
    (profile_dir / "luna-high-worker.toml").write_text(
        'model = "gpt-5.6-luna"\nmodel_reasoning_effort = "high"\n',
        encoding="utf-8",
    )
    completed = _run_hook(
        "multi_agent_v1__spawn_agent",
        {"agent_type": "luna-high-worker", "message": "probe"},
        env=dict(os.environ, USERPROFILE=str(tmp_path), HOME=str(tmp_path)),
    )

    assert completed.returncode == 0
    assert completed.stderr == ""


def test_create_thread_requires_explicit_model_and_thinking() -> None:
    blocked = _run_hook("codex_app__create_thread", {"prompt": "probe"})
    allowed = _run_hook(
        "codex_app__create_thread",
        {"prompt": "probe", "model": "gpt-5.6-sol", "thinking": "medium"},
    )

    assert blocked.returncode == 2
    assert "tool_input.model" in blocked.stderr
    assert "tool_input.thinking" in blocked.stderr
    assert allowed.returncode == 0


def test_non_spawn_tools_are_ignored() -> None:
    completed = _run_hook("multi_agent_v1__wait_agent", {"timeout_ms": 50_000})

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""
