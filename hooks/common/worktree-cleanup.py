#!/usr/bin/env python3
"""Queue and reap explicitly retired Codex worktrees with identity-bound leases."""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


HOME = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
QUEUE = HOME / "worktrees" / "cleanup.md"
LOCK = QUEUE.with_suffix(".lock")
LEASE_MARKER = "codex-cleanup-lease"
LINE = re.compile(
    r"^\s*- path: `(?P<path>[^`]+)` \| disposition: "
    r"(?P<disposition>merged|discarded|verification) \| primary: "
    r"`(?P<primary>[^`]+)` \| queued_at: (?P<queued_at>\d{4}-\d{2}-\d{2})"
    r"(?: \| source_head: `(?P<source_head>[0-9a-f]{40})`"
    r" \| gitdir: `(?P<gitdir>[^`]+)`"
    r" \| status_sha256: `(?P<status_sha256>[0-9a-f]{64})`"
    r" \| base_ref: `(?P<base_ref>[^`]+)`"
    r" \| lease: `(?P<lease>[0-9a-f]{32})`)?\s*$"
)
CODEX_WORKTREE_CONTAINER = re.compile(r"^[0-9a-f]{4}$")


@dataclass(frozen=True)
class Candidate:
    path: Path
    disposition: str
    primary: Path
    queued_at: str
    source_head: str | None = None
    gitdir: Path | None = None
    status_sha256: str | None = None
    base_ref: str | None = None
    lease: str | None = None

    @property
    def bound(self) -> bool:
        return all(
            (
                self.source_head,
                self.gitdir,
                self.status_sha256,
                self.base_ref,
                self.lease,
            )
        )


def canonical(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(args, 124, "", str(exc))


def run_bytes(*args: str) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            args,
            capture_output=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(args, 124, b"", str(exc).encode())


def worktrees(primary: Path) -> set[Path]:
    result = run("git", "-C", str(primary), "worktree", "list", "--porcelain")
    if result.returncode:
        return set()
    return {
        canonical(line.removeprefix("worktree "))
        for line in result.stdout.splitlines()
        if line.startswith("worktree ")
    }


def gitdir_for(path: Path) -> Path | None:
    result = run("git", "-C", str(path), "rev-parse", "--absolute-git-dir")
    return canonical(result.stdout.strip()) if result.returncode == 0 else None


def head_for(path: Path) -> str | None:
    result = run("git", "-C", str(path), "rev-parse", "HEAD")
    return result.stdout.strip() if result.returncode == 0 else None


def status_sha256(path: Path) -> str | None:
    diff = run_bytes(
        "git", "-C", str(path), "diff", "--binary", "--no-ext-diff", "HEAD", "--"
    )
    untracked = run(
        "git", "-C", str(path), "ls-files", "--others", "--exclude-standard", "-z"
    )
    if diff.returncode or untracked.returncode:
        return None
    digest = hashlib.sha256()
    digest.update(b"tracked\0")
    digest.update(diff.stdout)
    for relative in sorted(item for item in untracked.stdout.split("\0") if item):
        blob = run("git", "-C", str(path), "hash-object", "--no-filters", "--", relative)
        if blob.returncode or not blob.stdout.strip():
            return None
        digest.update(b"\0untracked\0")
        digest.update(relative.encode("utf-8", errors="surrogatepass"))
        digest.update(b"\0")
        digest.update(blob.stdout.strip().encode("ascii"))
    return digest.hexdigest()


def clean(path: Path) -> bool:
    result = run(
        "git", "-C", str(path), "status", "--porcelain=v1", "--untracked-files=all"
    )
    return result.returncode == 0 and not result.stdout.strip()


def primary_for(path: Path) -> Path | None:
    result = run("git", "-C", str(path), "worktree", "list", "--porcelain")
    if result.returncode:
        return None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            return canonical(line.removeprefix("worktree "))
    return None


def resolve_base_ref(primary: Path, requested: str | None) -> str | None:
    if requested:
        base_ref = requested
    else:
        branch = run("git", "-C", str(primary), "symbolic-ref", "--short", "HEAD")
        if branch.returncode or not branch.stdout.strip():
            return None
        base_ref = f"refs/heads/{branch.stdout.strip()}"
    resolved = run("git", "-C", str(primary), "rev-parse", "--verify", base_ref)
    return base_ref if resolved.returncode == 0 else None


def integrated(source_head: str, primary: Path, base_ref: str) -> bool:
    ancestor = run(
        "git", "-C", str(primary), "merge-base", "--is-ancestor", source_head, base_ref
    )
    if ancestor.returncode == 0:
        return True
    cherry = run("git", "-C", str(primary), "cherry", base_ref, source_head)
    return cherry.returncode == 0 and not any(
        line.startswith("+") for line in cherry.stdout.splitlines()
    )


def parse_line(line: str) -> Candidate | None:
    match = LINE.match(line)
    if match is None:
        return None
    return Candidate(
        path=canonical(match.group("path")),
        disposition=match.group("disposition"),
        primary=canonical(match.group("primary")),
        queued_at=match.group("queued_at"),
        source_head=match.group("source_head"),
        gitdir=canonical(match.group("gitdir")) if match.group("gitdir") else None,
        status_sha256=match.group("status_sha256"),
        base_ref=match.group("base_ref"),
        lease=match.group("lease"),
    )


def parse_queue() -> tuple[list[str], list[Candidate]]:
    if not QUEUE.exists():
        return [], []
    lines = QUEUE.read_text(encoding="utf-8").splitlines()
    return lines, [item for line in lines if (item := parse_line(line)) is not None]


def candidate_line(candidate: Candidate) -> str:
    line = (
        f"- path: `{candidate.path.as_posix()}` | disposition: "
        f"{candidate.disposition} | primary: `{candidate.primary.as_posix()}` | "
        f"queued_at: {candidate.queued_at}"
    )
    if candidate.bound:
        line += (
            f" | source_head: `{candidate.source_head}`"
            f" | gitdir: `{candidate.gitdir.as_posix()}`"
            f" | status_sha256: `{candidate.status_sha256}`"
            f" | base_ref: `{candidate.base_ref}`"
            f" | lease: `{candidate.lease}`"
        )
    return line


def _atomic_write(lines: list[str]) -> None:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="cleanup-", suffix=".tmp", dir=QUEUE.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(lines).rstrip() + "\n")
        os.replace(name, QUEUE)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(name)


def rewrite_queue(lines: list[str], replacements: dict[Path, Candidate | None]) -> None:
    output: list[str] = []
    seen: set[Path] = set()
    for line in lines:
        item = parse_line(line)
        if item is None or item.path not in replacements:
            output.append(line)
            continue
        if item.path in seen:
            continue
        replacement = replacements[item.path]
        if replacement is not None:
            output.append(candidate_line(replacement))
        seen.add(item.path)
    for path, replacement in replacements.items():
        if path not in seen and replacement is not None:
            if output and output[-1] != "":
                output.append("")
            output.append(candidate_line(replacement))
    _atomic_write(output)


@contextlib.contextmanager
def queue_lock(timeout: float = 5.0):
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    handle = LOCK.open("a+b")
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write(b"\0")
        handle.flush()
    deadline = time.monotonic() + timeout
    locked = False
    try:
        while not locked:
            handle.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("cleanup queue lock timed out")
                time.sleep(0.05)
        yield
    finally:
        if locked:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def marker_path(candidate: Candidate) -> Path | None:
    return candidate.gitdir / LEASE_MARKER if candidate.gitdir else None


def write_marker(candidate: Candidate) -> None:
    marker = marker_path(candidate)
    if marker is None or candidate.lease is None:
        raise OSError("cleanup lease is incomplete")
    marker.write_text(candidate.lease + "\n", encoding="ascii")


def clear_marker(candidate: Candidate) -> None:
    marker = marker_path(candidate)
    if marker and marker.exists():
        with contextlib.suppress(OSError):
            if candidate.lease is None or marker.read_text("ascii").strip() == candidate.lease:
                marker.unlink()


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validate(candidate: Candidate) -> tuple[bool, str]:
    if not candidate.bound:
        return False, "legacy queue entry requires re-enqueue"
    if not candidate.primary.is_dir():
        return False, "primary checkout missing"
    if candidate.path not in worktrees(candidate.primary):
        return False, "worktree is no longer registered"
    if gitdir_for(candidate.path) != candidate.gitdir:
        return False, "worktree identity changed"
    marker = marker_path(candidate)
    if marker is None or not marker.is_file():
        return False, "cleanup lease marker missing"
    try:
        marker_lease = marker.read_text(encoding="ascii").strip()
    except OSError:
        return False, "cleanup lease marker unreadable"
    if marker_lease != candidate.lease:
        return False, "cleanup lease changed"
    if head_for(candidate.path) != candidate.source_head:
        return False, "source HEAD changed"
    current_status = status_sha256(candidate.path)
    if current_status is None or current_status != candidate.status_sha256:
        return False, "worktree snapshot changed"
    if candidate.disposition != "discarded" and not clean(candidate.path):
        return False, "worktree is not clean"
    if candidate.disposition == "merged" and not integrated(
        candidate.source_head, candidate.primary, candidate.base_ref
    ):
        return False, "worktree is no longer integrated"
    return True, "validated"


def remove(candidate: Candidate) -> tuple[bool, str]:
    args = ["git", "-C", str(candidate.primary), "worktree", "remove"]
    if candidate.disposition == "discarded":
        args.append("--force")
    args.append(str(candidate.path))
    result = run(*args)
    if not candidate.path.exists():
        return True, "git worktree remove"
    detail = result.stderr.strip().splitlines()
    return False, detail[-1] if detail else "git worktree remove failed"


def prune_empty_orphans() -> list[Path]:
    root = HOME / "worktrees"
    removed: list[Path] = []
    if not root.is_dir():
        return removed
    leaves: list[Path] = []
    for parent in root.iterdir():
        if not parent.is_dir():
            continue
        leaves.append(parent)
        if CODEX_WORKTREE_CONTAINER.fullmatch(parent.name):
            leaves.extend(child for child in parent.iterdir() if child.is_dir())
    for directory in sorted(leaves, key=lambda item: len(item.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            continue
        removed.append(directory)
    return removed


def enqueue(path_arg: str, disposition: str, requested_base_ref: str | None) -> int:
    path = canonical(path_arg)
    primary = primary_for(path)
    if primary is None or path not in worktrees(primary):
        print(f"worktree is not registered: {path}", file=sys.stderr)
        return 2
    source_head = head_for(path)
    gitdir = gitdir_for(path)
    status = status_sha256(path)
    base_ref = resolve_base_ref(primary, requested_base_ref)
    if not all((source_head, gitdir, status, base_ref)):
        print(f"worktree identity cannot be resolved: {path}", file=sys.stderr)
        return 2
    if disposition != "discarded" and not clean(path):
        print(f"worktree is not clean: {path}", file=sys.stderr)
        return 2
    if disposition == "merged" and not integrated(source_head, primary, base_ref):
        print(f"worktree is not integrated: {path}", file=sys.stderr)
        return 2
    candidate = Candidate(
        path=path,
        disposition=disposition,
        primary=primary,
        queued_at=dt.date.today().isoformat(),
        source_head=source_head,
        gitdir=gitdir,
        status_sha256=status,
        base_ref=base_ref,
        lease=uuid.uuid4().hex,
    )
    try:
        with queue_lock():
            lines, existing = parse_queue()
            old = next((item for item in existing if item.path == path), None)
            write_marker(candidate)
            try:
                rewrite_queue(lines, {path: candidate})
            except Exception:
                clear_marker(candidate)
                raise
            if old:
                clear_marker(old)
    except (OSError, TimeoutError) as exc:
        print(f"cleanup queue update failed: {exc}", file=sys.stderr)
        return 2
    print(f"queued: {path}")
    return 0


def dequeue(path_arg: str) -> int:
    path = canonical(path_arg)
    try:
        with queue_lock():
            lines, candidates = parse_queue()
            candidate = next((item for item in candidates if item.path == path), None)
            if candidate is None:
                print(f"not queued: {path}")
                return 0
            clear_marker(candidate)
            rewrite_queue(lines, {path: None})
    except (OSError, TimeoutError) as exc:
        print(f"cleanup queue update failed: {exc}", file=sys.stderr)
        return 2
    print(f"dequeued: {path}")
    return 0


def reap(cwd_override: str | Path | None = None) -> int:
    if cwd_override is None:
        try:
            payload = json.load(sys.stdin)
        except Exception:
            payload = {}
        cwd = canonical(payload.get("cwd") or os.getcwd())
    else:
        cwd = canonical(cwd_override)
    messages: list[str] = []
    try:
        with queue_lock():
            lines, candidates = parse_queue()
            replacements: dict[Path, Candidate | None] = {}
            for candidate in candidates:
                if is_within(cwd, candidate.path):
                    clear_marker(candidate)
                    replacements[candidate.path] = None
                    messages.append(
                        f"retirement cancelled: worktree reactivated: {candidate.path}"
                    )
                    continue
                if not candidate.path.exists():
                    run("git", "-C", str(candidate.primary), "worktree", "prune")
                    replacements[candidate.path] = None
                    messages.append(f"removed queue record: {candidate.path} (already absent)")
                    continue
                valid, reason = validate(candidate)
                if not valid:
                    messages.append(f"pending: {candidate.path} ({reason})")
                    continue
                done, reason = remove(candidate)
                if done:
                    clear_marker(candidate)
                    replacements[candidate.path] = None
                    messages.append(f"removed: {candidate.path} ({reason})")
                else:
                    messages.append(f"pending: {candidate.path} ({reason})")
            if replacements:
                rewrite_queue(lines, replacements)
            messages.extend(
                f"removed empty orphan: {path}" for path in prune_empty_orphans()
            )
    except (OSError, TimeoutError) as exc:
        messages.append(f"pending: cleanup queue unavailable ({exc})")
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
    parser.add_argument("--dequeue", metavar="PATH")
    parser.add_argument(
        "--disposition", choices=("merged", "discarded", "verification")
    )
    parser.add_argument("--base-ref")
    args = parser.parse_args()
    if args.enqueue and args.dequeue:
        parser.error("--enqueue and --dequeue are mutually exclusive")
    if args.enqueue:
        if not args.disposition:
            parser.error("--enqueue requires --disposition")
        return enqueue(args.enqueue, args.disposition, args.base_ref)
    if args.dequeue:
        if args.disposition or args.base_ref:
            parser.error("--disposition/--base-ref cannot be used with --dequeue")
        return dequeue(args.dequeue)
    if args.disposition or args.base_ref:
        parser.error("--disposition/--base-ref require --enqueue")
    return reap()


if __name__ == "__main__":
    raise SystemExit(main())
