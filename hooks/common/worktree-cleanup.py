#!/usr/bin/env python3
"""Queue and reap explicitly retired Codex worktrees.

`~/.codex/worktrees/cleanup.md` is the single approval queue.  A worktree is
never inferred to be disposable: it is queued only after a completed merge,
clean verification, or an explicit user discard.  SessionStart retries queued
removals from a different cwd, so Windows directory locks defer deletion rather
than turning into data loss.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


HOME = Path.home() / ".codex"
QUEUE = HOME / "worktrees" / "cleanup.md"
LINE = re.compile(
    r"^\s*- path: `(?P<path>[^`]+)` \| disposition: "
    r"(?P<disposition>merged|discarded|verification) \| primary: "
    r"`(?P<primary>[^`]+)` \| queued_at: (?P<queued_at>\d{4}-\d{2}-\d{2})\s*$"
)
CODEX_WORKTREE_CONTAINER = re.compile(r"^[0-9a-f]{4}$")


@dataclass(frozen=True)
class Candidate:
    path: Path
    disposition: str
    primary: Path
    queued_at: str


def canonical(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def worktrees(primary: Path) -> set[Path]:
    result = run("git", "-C", str(primary), "worktree", "list", "--porcelain")
    if result.returncode:
        return set()
    return {
        canonical(line.removeprefix("worktree "))
        for line in result.stdout.splitlines()
        if line.startswith("worktree ")
    }


def clean(path: Path) -> bool:
    result = run("git", "-C", str(path), "status", "--porcelain")
    return result.returncode == 0 and not result.stdout.strip()


def unintegrated_commits(path: Path, primary: Path) -> list[str]:
    """Commits in the worktree branch that are not yet in the primary HEAD."""
    head = run("git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD")
    if head.returncode or not head.stdout.strip():
        return ["<unresolved HEAD>"]
    branch = head.stdout.strip()
    if branch == "HEAD":
        return ["<detached HEAD>"]
    base = run("git", "-C", str(primary), "rev-parse", "--abbrev-ref", "HEAD")
    if base.returncode or not base.stdout.strip():
        return ["<unresolved primary HEAD>"]
    result = run("git", "-C", str(primary), "cherry", base.stdout.strip(), branch)
    if result.returncode:
        return ["<cherry failed>"]
    return [line for line in result.stdout.splitlines() if line.startswith("+")]


def primary_for(path: Path) -> Path | None:
    result = run("git", "-C", str(path), "worktree", "list", "--porcelain")
    if result.returncode:
        return None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            return canonical(line.removeprefix("worktree "))
    return None


def parse_queue() -> tuple[list[str], list[Candidate]]:
    if not QUEUE.exists():
        return [], []
    lines = QUEUE.read_text(encoding="utf-8").splitlines()
    candidates: list[Candidate] = []
    for line in lines:
        match = LINE.match(line)
        if match:
            candidates.append(
                Candidate(
                    path=canonical(match.group("path")),
                    disposition=match.group("disposition"),
                    primary=canonical(match.group("primary")),
                    queued_at=match.group("queued_at"),
                )
            )
    return lines, candidates


def candidate_line(candidate: Candidate) -> str:
    return (
        f"- path: `{candidate.path.as_posix()}` | disposition: "
        f"{candidate.disposition} | primary: `{candidate.primary.as_posix()}` | "
        f"queued_at: {candidate.queued_at}"
    )


def write_queue(lines: list[str], removed: set[Candidate]) -> None:
    if not removed:
        return
    kept = [line for line in lines if line not in {candidate_line(item) for item in removed}]
    QUEUE.write_text("\n".join(kept).rstrip() + "\n", encoding="utf-8")


def owned_unregistered_worktree(candidate: Candidate) -> bool:
    git_file = candidate.path / ".git"
    if not git_file.is_file() or not candidate.primary.is_dir():
        return False
    try:
        pointer = git_file.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return False
    if not pointer.startswith("gitdir: "):
        return False
    gitdir = canonical(pointer.removeprefix("gitdir: ").strip())
    expected = canonical(candidate.primary / ".git" / "worktrees")
    try:
        gitdir.relative_to(expected)
        return True
    except ValueError:
        return False


def remove(candidate: Candidate) -> tuple[bool, str]:
    if not candidate.path.exists():
        run("git", "-C", str(candidate.primary), "worktree", "prune")
        return True, "already absent"
    if not candidate.primary.is_dir():
        return False, "primary checkout missing"

    registered = candidate.path in worktrees(candidate.primary)
    if registered:
        result = run(
            "git", "-C", str(candidate.primary), "worktree", "remove", "--force", str(candidate.path)
        )
        if not candidate.path.exists():
            return True, "git worktree remove"
        if candidate.path in worktrees(candidate.primary):
            detail = result.stderr.strip().splitlines()
            return False, detail[-1] if detail else "git worktree remove failed"

    if not owned_unregistered_worktree(candidate):
        return False, "unregistered path ownership cannot be verified"
    try:
        shutil.rmtree(candidate.path)
    except OSError as exc:
        return False, str(exc)
    run("git", "-C", str(candidate.primary), "worktree", "prune")
    return True, "removed leftover directory"


def prune_empty_orphans() -> list[Path]:
    root = HOME / "worktrees"
    removed: list[Path] = []
    if not root.is_dir():
        return removed
    # Codex creates either <root>/<worktree> or <root>/<id>/<worktree>.
    # Never descend into a worktree: an empty cache subdirectory is not an
    # orphaned worktree and must remain untouched.
    leaves: list[Path] = []
    for parent in root.iterdir():
        if not parent.is_dir():
            continue
        leaves.append(parent)
        if CODEX_WORKTREE_CONTAINER.fullmatch(parent.name):
            leaves.extend(child for child in parent.iterdir() if child.is_dir())
    for directory in sorted(leaves, key=lambda p: len(p.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            continue
        removed.append(directory)
    return removed


def enqueue(path_arg: str, disposition: str) -> int:
    path = canonical(path_arg)
    primary = primary_for(path)
    if primary is None or path not in worktrees(primary):
        print(f"worktree is not registered: {path}", file=sys.stderr)
        return 2
    if disposition != "discarded" and not clean(path):
        print(f"worktree is not clean: {path}", file=sys.stderr)
        return 2
    if disposition == "merged":
        pending = unintegrated_commits(path, primary)
        if pending:
            print(
                f"worktree is not integrated: {path} ({len(pending)} unintegrated commit(s))",
                file=sys.stderr,
            )
            return 2

    lines, candidates = parse_queue()
    if any(item.path == path for item in candidates):
        print(f"already queued: {path}")
        return 0
    candidate = Candidate(path, disposition, primary, dt.date.today().isoformat())
    with QUEUE.open("a", encoding="utf-8") as handle:
        if lines and lines[-1] != "":
            handle.write("\n")
        handle.write(candidate_line(candidate) + "\n")
    print(f"queued: {path}")
    return 0


def reap() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    cwd = canonical(payload.get("cwd") or os.getcwd())
    lines, candidates = parse_queue()
    removed: set[Candidate] = set()
    messages: list[str] = []
    for candidate in candidates:
        if candidate.path == cwd:
            messages.append(f"skip current cwd: {candidate.path}")
            continue
        done, reason = remove(candidate)
        if done:
            removed.add(candidate)
            messages.append(f"removed: {candidate.path} ({reason})")
        else:
            messages.append(f"pending: {candidate.path} ({reason})")
    write_queue(lines, removed)
    empty = prune_empty_orphans()
    messages.extend(f"removed empty orphan: {path}" for path in empty)
    if messages:
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": "[worktree-cleanup]\n" + "\n".join(messages),
                }
            },
            sys.stdout,
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--enqueue", metavar="PATH")
    parser.add_argument(
        "--disposition", choices=("merged", "discarded", "verification")
    )
    args = parser.parse_args()
    if args.enqueue:
        if not args.disposition:
            parser.error("--enqueue requires --disposition")
        return enqueue(args.enqueue, args.disposition)
    if args.disposition:
        parser.error("--disposition requires --enqueue")
    return reap()


if __name__ == "__main__":
    raise SystemExit(main())
