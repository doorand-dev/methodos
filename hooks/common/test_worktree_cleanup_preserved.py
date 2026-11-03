from __future__ import annotations

import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


CLEANUP_PATH = Path(__file__).with_name("worktree-cleanup.py")
SPEC = importlib.util.spec_from_file_location("worktree_cleanup", CLEANUP_PATH)
assert SPEC is not None and SPEC.loader is not None
cleanup = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cleanup
SPEC.loader.exec_module(cleanup)


def git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode:
        raise AssertionError(
            f"git {' '.join(args)} failed: {result.stderr.strip()}"
        )
    return result


class WorktreeCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.primary: Path | None = None
        self.source: Path | None = None
        self.old_home = cleanup.HOME
        self.old_queue = cleanup.QUEUE
        self.old_lock = cleanup.LOCK
        cleanup.HOME = self.root / "codex-home"
        cleanup.QUEUE = cleanup.HOME / "worktrees" / "cleanup.md"
        cleanup.LOCK = cleanup.QUEUE.with_suffix(".lock")

    def tearDown(self) -> None:
        if self.primary is not None and self.source is not None and self.source.exists():
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(self.primary),
                    "worktree",
                    "remove",
                    "--force",
                    str(self.source),
                ],
                capture_output=True,
                check=False,
            )
        cleanup.HOME = self.old_home
        cleanup.QUEUE = self.old_queue
        cleanup.LOCK = self.old_lock
        self.temp.cleanup()

    def make_repo(self, *, unmerged: bool = False) -> tuple[Path, Path]:
        primary = self.root / "primary"
        source = self.root / "source"
        git("init", "-b", "main", str(primary), cwd=self.root)
        git("config", "user.email", "test@example.com", cwd=primary)
        git("config", "user.name", "Worktree Test", cwd=primary)
        (primary / ".gitignore").write_text("*.ignored\n", encoding="utf-8")
        (primary / "tracked.txt").write_text("base\n", encoding="utf-8")
        git("add", ".gitignore", "tracked.txt", cwd=primary)
        git("commit", "-m", "initial", cwd=primary)
        if unmerged:
            git("worktree", "add", "-b", "feature", str(source), "HEAD", cwd=primary)
            (source / "tracked.txt").write_text("feature\n", encoding="utf-8")
            git("add", "tracked.txt", cwd=source)
            git("commit", "-m", "feature", cwd=source)
        else:
            git("worktree", "add", "--detach", str(source), "HEAD", cwd=primary)
        self.primary = primary
        self.source = source
        return primary, source

    def enqueue_silently(self, path: Path, disposition: str) -> int:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            return cleanup.enqueue(str(path), disposition, None)

    def candidate(self) -> cleanup.Candidate:
        _, candidates = cleanup.parse_queue()
        self.assertEqual(len(candidates), 1)
        return candidates[0]

    def test_preserved_dirty_roundtrip_validate_and_remove(self) -> None:
        primary, source = self.make_repo()
        (source / "tracked.txt").write_text("dirty\n", encoding="utf-8")
        (source / "untracked.txt").write_text("untracked\n", encoding="utf-8")
        (source / "ignored.ignored").write_text("ignored\n", encoding="utf-8")
        git("add", "tracked.txt", cwd=source)

        self.assertEqual(self.enqueue_silently(source, "preserved"), 0)
        candidate = self.candidate()
        self.assertEqual(candidate.disposition, "preserved")
        self.assertEqual(cleanup.validate(candidate), (True, "validated"))

        removed, _ = cleanup.remove(candidate)
        self.assertTrue(removed)
        self.assertFalse(source.exists())
        self.assertTrue(primary.exists())

    def test_merged_dirty_is_rejected(self) -> None:
        _, source = self.make_repo()
        (source / "tracked.txt").write_text("dirty\n", encoding="utf-8")

        self.assertEqual(self.enqueue_silently(source, "merged"), 2)
        self.assertFalse(cleanup.QUEUE.exists())

    def test_preserved_unmerged_is_rejected(self) -> None:
        _, source = self.make_repo(unmerged=True)
        (source / "after-commit.txt").write_text("dirty\n", encoding="utf-8")

        self.assertEqual(self.enqueue_silently(source, "preserved"), 2)
        self.assertFalse(cleanup.QUEUE.exists())

    def assert_preserved_change_rejected(self, change) -> None:
        _, source = self.make_repo()
        self.assertEqual(self.enqueue_silently(source, "preserved"), 0)
        change(source)
        self.assertFalse(cleanup.validate(self.candidate())[0])

    def test_enqueue_then_tracked_change_is_rejected(self) -> None:
        self.assert_preserved_change_rejected(
            lambda source: (source / "tracked.txt").write_text(
                "changed\n", encoding="utf-8"
            )
        )

    def test_enqueue_then_untracked_change_is_rejected(self) -> None:
        self.assert_preserved_change_rejected(
            lambda source: (source / "untracked.txt").write_text(
                "changed\n", encoding="utf-8"
            )
        )

    def test_enqueue_then_index_only_change_is_rejected(self) -> None:
        def change(source: Path) -> None:
            index_only = source / "index-only.txt"
            index_only.write_text("indexed\n", encoding="utf-8")
            git("add", "index-only.txt", cwd=source)
            index_only.unlink()

        self.assert_preserved_change_rejected(change)

    def test_enqueue_then_ignored_change_is_rejected(self) -> None:
        self.assert_preserved_change_rejected(
            lambda source: (source / "ignored.ignored").write_text(
                "ignored\n", encoding="utf-8"
            )
        )

    def test_current_cwd_is_protected(self) -> None:
        _, source = self.make_repo()
        self.assertEqual(self.enqueue_silently(source, "preserved"), 0)

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(cleanup.reap(source), 0)

        self.assertIn("retirement cancelled", output.getvalue())
        self.assertTrue(source.exists())
        self.assertFalse(cleanup.parse_queue()[1])


    def test_cli_requires_explicit_action(self) -> None:
        with mock.patch.object(sys, "argv", [str(CLEANUP_PATH)]), \
                mock.patch.object(cleanup, "reap") as reap, \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as stopped:
                cleanup.main()
        self.assertEqual(stopped.exception.code, 2)
        reap.assert_not_called()
        self.assertFalse(cleanup.QUEUE.exists())

    def test_cli_reap_does_not_read_hook_stdin(self) -> None:
        _, source = self.make_repo()
        self.assertEqual(self.enqueue_silently(source, "preserved"), 0)
        hook_input = io.StringIO('{"cwd": "unrelated"}')
        with mock.patch.object(sys, "argv", [str(CLEANUP_PATH), "--reap"]), \
                mock.patch.object(sys, "stdin", hook_input), \
                mock.patch.object(cleanup.os, "getcwd", return_value=str(source)), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cleanup.main(), 0)
        self.assertEqual(hook_input.tell(), 0)
        self.assertTrue(source.exists())
        self.assertFalse(cleanup.parse_queue()[1])

    def test_cli_reap_preserves_changed_retirement(self) -> None:
        primary, source = self.make_repo()
        self.assertEqual(self.enqueue_silently(source, "preserved"), 0)
        (source / "later.txt").write_text("new work\n", encoding="utf-8")
        with mock.patch.object(sys, "argv", [str(CLEANUP_PATH), "--reap"]), \
                mock.patch.object(cleanup.os, "getcwd", return_value=str(primary)), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(cleanup.main(), 0)
        self.assertIn("pending:", output.getvalue())
        self.assertTrue(source.exists())
        self.assertEqual(len(cleanup.parse_queue()[1]), 1)


if __name__ == "__main__":
    unittest.main()
