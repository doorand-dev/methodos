from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


HOOK = Path(__file__).with_name("worktree-advisory.py")
STATE = Path(__file__).with_name("worktree_git_state.py")


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)


def test_dirty_primary_checkout_emits_codex_native_advisory(tmp_path) -> None:
    git(tmp_path, "init", "-b", "master")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "foreign.txt").write_text("dirty\n", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"cwd": str(tmp_path)}),
        text=True,
        capture_output=True,
        check=True,
    )

    output = json.loads(completed.stdout)
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "foreign dirty/staged/untracked" in context
    assert "~/.codex/rules/worktree.md" in context
    assert "EnterWorktree" not in context
    assert "worktree-cap" not in context


def test_sources_do_not_claim_dormant_enforcement() -> None:
    source = HOOK.read_text(encoding="utf-8") + STATE.read_text(encoding="utf-8")
    assert "worktree-cap" not in source
    assert "EnterWorktree" not in source
