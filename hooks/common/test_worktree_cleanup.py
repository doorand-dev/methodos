from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).with_name("worktree-cleanup.py")


def load_module():
    spec = importlib.util.spec_from_file_location("worktree_cleanup", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@pytest.fixture
def cleanup(tmp_path, monkeypatch):
    module = load_module()
    codex_home = tmp_path / "codex-home"
    queue = codex_home / "worktrees" / "cleanup.md"
    queue.parent.mkdir(parents=True)
    queue.write_text("# Worktree cleanup candidates\n", encoding="utf-8")
    monkeypatch.setattr(module, "HOME", codex_home)
    monkeypatch.setattr(module, "QUEUE", queue)
    monkeypatch.setattr(module, "LOCK", queue.with_suffix(".lock"))
    return module


@pytest.fixture
def integrated_worktree(tmp_path):
    primary = tmp_path / "primary"
    worktree = tmp_path / "worktree"
    primary.mkdir()
    git(primary, "init", "-b", "master")
    git(primary, "config", "user.email", "test@example.com")
    git(primary, "config", "user.name", "Test")
    (primary / "base.txt").write_text("base\n", encoding="utf-8")
    git(primary, "add", "base.txt")
    git(primary, "commit", "-m", "base")
    git(primary, "worktree", "add", "-b", "topic", str(worktree))
    (worktree / "topic.txt").write_text("topic\n", encoding="utf-8")
    git(worktree, "add", "topic.txt")
    git(worktree, "commit", "-m", "topic")
    git(primary, "merge", "--no-ff", "topic", "-m", "merge topic")
    return primary, worktree


def test_reap_removes_only_unchanged_integrated_worktree(
    cleanup, integrated_worktree, capsys
):
    primary, worktree = integrated_worktree
    assert cleanup.enqueue(str(worktree), "merged", None) == 0

    assert cleanup.reap(primary) == 0

    assert not worktree.exists()
    assert "removed:" in capsys.readouterr().out
    assert str(worktree).replace("\\", "/") not in cleanup.QUEUE.read_text("utf-8")


def test_reap_holds_when_head_changes_after_enqueue(
    cleanup, integrated_worktree, capsys
):
    primary, worktree = integrated_worktree
    assert cleanup.enqueue(str(worktree), "merged", None) == 0
    (worktree / "later.txt").write_text("later\n", encoding="utf-8")
    git(worktree, "add", "later.txt")
    git(worktree, "commit", "-m", "later")

    assert cleanup.reap(primary) == 0

    assert worktree.exists()
    assert "source HEAD changed" in capsys.readouterr().out
    assert str(worktree).replace("\\", "/") in cleanup.QUEUE.read_text("utf-8")


def test_reap_holds_when_status_changes_after_enqueue(
    cleanup, integrated_worktree, capsys
):
    primary, worktree = integrated_worktree
    assert cleanup.enqueue(str(worktree), "merged", None) == 0
    (worktree / "topic.txt").write_text("changed\n", encoding="utf-8")

    assert cleanup.reap(primary) == 0

    assert worktree.exists()
    assert "worktree snapshot changed" in capsys.readouterr().out


def test_discarded_lease_hashes_file_content(cleanup, integrated_worktree, capsys):
    primary, worktree = integrated_worktree
    (worktree / "topic.txt").write_text("discard version one\n", encoding="utf-8")
    assert cleanup.enqueue(str(worktree), "discarded", None) == 0
    (worktree / "topic.txt").write_text("discard version two\n", encoding="utf-8")

    assert cleanup.reap(primary) == 0

    assert worktree.exists()
    assert "worktree snapshot changed" in capsys.readouterr().out


def test_reap_holds_when_path_is_reused_by_another_worktree(
    cleanup, integrated_worktree, capsys
):
    primary, worktree = integrated_worktree
    assert cleanup.enqueue(str(worktree), "merged", None) == 0
    git(primary, "worktree", "remove", str(worktree))
    git(primary, "branch", "-D", "topic")
    git(primary, "worktree", "add", "-b", "replacement", str(worktree), "master")

    assert cleanup.reap(primary) == 0

    assert worktree.exists()
    assert "cleanup lease marker missing" in capsys.readouterr().out


def test_reap_holds_when_integration_is_lost(cleanup, integrated_worktree, capsys):
    primary, worktree = integrated_worktree
    base_before_merge = git(primary, "rev-parse", "HEAD^1")
    assert cleanup.enqueue(str(worktree), "merged", None) == 0
    git(primary, "reset", "--hard", base_before_merge)

    assert cleanup.reap(primary) == 0

    assert worktree.exists()
    assert "worktree is no longer integrated" in capsys.readouterr().out


def test_session_start_inside_queued_worktree_cancels_retirement(
    cleanup, integrated_worktree, capsys
):
    _primary, worktree = integrated_worktree
    assert cleanup.enqueue(str(worktree), "merged", None) == 0
    nested = worktree / "nested"
    nested.mkdir()

    assert cleanup.reap(nested) == 0

    assert worktree.exists()
    assert "retirement cancelled: worktree reactivated" in capsys.readouterr().out
    assert str(worktree).replace("\\", "/") not in cleanup.QUEUE.read_text("utf-8")


def test_explicit_dequeue_precedes_reuse(cleanup, integrated_worktree, capsys):
    _primary, worktree = integrated_worktree
    assert cleanup.enqueue(str(worktree), "merged", None) == 0

    assert cleanup.dequeue(str(worktree)) == 0

    assert worktree.exists()
    assert "dequeued:" in capsys.readouterr().out
    assert str(worktree).replace("\\", "/") not in cleanup.QUEUE.read_text("utf-8")


def test_reap_holds_legacy_existing_entry(cleanup, integrated_worktree, capsys):
    primary, worktree = integrated_worktree
    cleanup.QUEUE.write_text(
        "# Worktree cleanup candidates\n\n"
        f"- path: `{worktree.as_posix()}` | disposition: merged | "
        f"primary: `{primary.as_posix()}` | queued_at: 2026-07-30\n",
        encoding="utf-8",
    )

    assert cleanup.reap(primary) == 0

    assert worktree.exists()
    assert "legacy queue entry requires re-enqueue" in capsys.readouterr().out


def test_two_process_reapers_remove_one_worktree(cleanup, integrated_worktree):
    primary, worktree = integrated_worktree
    assert cleanup.enqueue(str(worktree), "merged", None) == 0
    env = {**os.environ, "CODEX_HOME": str(cleanup.HOME)}
    payload = json.dumps({"cwd": str(primary)})
    processes = [
        subprocess.Popen(
            [sys.executable, str(SCRIPT)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        for _ in range(2)
    ]
    results = [process.communicate(payload, timeout=30) for process in processes]

    assert [process.returncode for process in processes] == [0, 0]
    assert sum(output.count("removed:") for output, _error in results) == 1
    assert not worktree.exists()
    assert str(worktree).replace("\\", "/") not in cleanup.QUEUE.read_text("utf-8")
