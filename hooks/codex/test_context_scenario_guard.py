from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path


HOOK = Path(__file__).with_name("context_scenario_guard.py")


def _run_hook(
    tool_name: str | None = "apply_patch",
    tool_input: dict[str, object] | None = None,
    raw_input: str | None = None,
) -> dict[str, object] | None:
    if raw_input is None:
        raw_input = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
    completed = subprocess.run(
        [sys.executable, str(HOOK)],
        input=raw_input,
        text=True,
        capture_output=True,
        check=True,
    )
    if not completed.stdout.strip():
        return None
    return json.loads(completed.stdout)


def test_multiple_hot_headers_emit_advisory_with_exact_normalized_paths() -> None:
    output = _run_hook(
        tool_input={
            "command": "\n".join(
                [
                    "*** Begin Patch",
                    "*** Add File: docs/AGENTS.md",
                    "*** Update File: config\\rules\\policy.toml",
                    "*** Delete File: src/agents/legacy.md",
                    "*** Update File: nested/SKILL.md",
                    "*** Add File: settings/hooks.json",
                    "*** Update File: src/runtime.py",
                    "*** Move to: hooks/runtime.py",
                    "*** End Patch",
                ]
            )
        }
    )

    assert output is not None
    assert set(output) == {"hookSpecificOutput"}
    hook_output = output["hookSpecificOutput"]
    assert isinstance(hook_output, dict)
    assert hook_output["hookEventName"] == "PreToolUse"
    assert set(hook_output) == {"hookEventName", "additionalContext"}
    context = hook_output["additionalContext"]
    assert isinstance(context, str)
    for path in (
        "docs/AGENTS.md",
        "config/rules/policy.toml",
        "src/agents/legacy.md",
        "nested/SKILL.md",
        "settings/hooks.json",
        "hooks/runtime.py",
    ):
        assert path in context
    for instruction in (
        "verify reader+trigger",
        "minimum global/project/subtree scope",
        "existing SSOT/duplicate",
        "actual consumer/load path",
        "context-novelist before the next edit",
    ):
        assert instruction in context
    assert "permissionDecision" not in hook_output
    assert "updatedInput" not in hook_output


def test_ordinary_source_patch_is_silent() -> None:
    assert (
        _run_hook(tool_input={"command": "*** Update File: src/example.py"})
        is None
    )


def test_hook_implementation_and_memory_are_hot_targets() -> None:
    output = _run_hook(
        tool_input={
            "command": "\n".join(
                (
                    "*** Update File: .codex/hooks/policy.py",
                    "*** Update File: docs/MEMORY.md",
                )
            )
        }
    )
    context = output["hookSpecificOutput"]["additionalContext"]
    assert ".codex/hooks/policy.py" in context
    assert "docs/MEMORY.md" in context


def test_malformed_missing_and_non_apply_patch_inputs_are_silent() -> None:
    assert _run_hook(raw_input="{") is None
    assert _run_hook(tool_input={}) is None
    assert _run_hook(tool_input={"command": 123}) is None
    assert _run_hook(tool_name="Edit", tool_input={"command": "*** Add File: AGENTS.md"}) is None


def test_guard_source_has_no_external_or_process_invocation_path() -> None:
    source = HOOK.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_imports = {"subprocess", "socket", "urllib", "requests", "httpx"}
    forbidden_calls = {
        "Popen",
        "call",
        "check_call",
        "check_output",
        "create_subprocess_exec",
        "create_subprocess_shell",
        "eval",
        "exec",
        "spawn",
        "system",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name.split(".", 1)[0] not in forbidden_imports for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            called = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else None
            assert called not in forbidden_calls
