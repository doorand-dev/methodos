from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


HOOK = Path(__file__).with_name("wait_agent_timeout.py")


def _run_hook(tool_name: str, tool_input: dict[str, object]) -> dict[str, object] | None:
    completed = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_name": tool_name, "tool_input": tool_input}),
        text=True,
        capture_output=True,
        check=True,
    )
    if not completed.stdout.strip():
        return None
    return json.loads(completed.stdout)


def _updated_input(output: dict[str, object]) -> dict[str, object]:
    hook_output = output["hookSpecificOutput"]
    assert isinstance(hook_output, dict)
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "allow"
    updated_input = hook_output["updatedInput"]
    assert isinstance(updated_input, dict)
    return updated_input


def test_rewrites_short_timeout_and_preserves_single_call_input() -> None:
    output = _run_hook(
        "multi_agent_v1__wait_agent",
        {"targets": ["agent-1"], "timeout_ms": 50_000},
    )

    assert output is not None
    assert set(output) == {"hookSpecificOutput"}
    assert _updated_input(output) == {
        "targets": ["agent-1"],
        "timeout_ms": 3_600_000,
    }


def test_rewrites_missing_timeout() -> None:
    output = _run_hook("multi_agent_v1__wait_agent", {"targets": ["agent-1"]})

    assert output is not None
    assert _updated_input(output)["timeout_ms"] == 3_600_000


def test_leaves_maximum_and_schema_invalid_larger_timeout_to_runtime() -> None:
    assert (
        _run_hook(
            "multi_agent_v1__wait_agent",
            {"targets": ["agent-1"], "timeout_ms": 3_600_000},
        )
        is None
    )
    assert (
        _run_hook(
            "multi_agent_v1__wait_agent",
            {"targets": ["agent-1"], "timeout_ms": 3_600_001},
        )
        is None
    )
    assert (
        _run_hook(
            "multi_agent_v1__wait_agent",
            {"targets": ["agent-1"], "timeout_ms": "50000"},
        )
        is None
    )


def test_does_not_touch_wait_threads_snapshot() -> None:
    assert (
        _run_hook(
            "codex_app__wait_threads",
            {"targets": [{"threadId": "thread-1"}], "timeoutMs": 0},
        )
        is None
    )
