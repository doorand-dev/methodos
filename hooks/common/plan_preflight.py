#!/usr/bin/env python3
"""Reject deterministic plan defects before an expensive semantic review."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path


PLACEHOLDER = re.compile(r"\b(TBD|TODO|implement later|fill in details|add appropriate|similar to slice)\b", re.I)
POSIX_COMMAND = re.compile(r"\b(test\s+-[efdr]|grep\s|bash\s|sh\s+-c)\b|\$[A-Za-z_][A-Za-z0-9_]*")


def frontmatter(text: str) -> str | None:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    return match.group(1) if match else None


def slice_blocks(data: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^  - id:\s*(.+?)\s*$", data))
    return [
        (match.group(1).strip(), data[match.start() : matches[index + 1].start() if index + 1 < len(matches) else len(data)])
        for index, match in enumerate(matches)
    ]


def paths(block: str) -> list[str]:
    result: list[str] = []
    for match in re.finditer(r"(?m)^\s+(?:create|modify|test):\s*\[([^]]*)\]", block):
        result.extend(path.strip().strip("'\"") for path in match.group(1).split(",") if path.strip())
    return result


def scalar(block: str, key: str) -> str | None:
    match = re.search(rf"(?m)^\s+{re.escape(key)}:\s*(.+?)\s*$", block)
    return match.group(1).strip().strip("'\"") if match else None


def inline_list(block: str, key: str) -> list[str] | None:
    match = re.search(rf"(?m)^\s+{re.escape(key)}:\s*\[([^]]*)\]\s*$", block)
    if not match:
        return None
    return [item.strip().strip("'\"") for item in match.group(1).split(",") if item.strip()]


def _check_repo_boundary(path: str, repo: Path) -> bool:
    """Return whether a declared path is a relative path inside ``repo``."""
    candidate = Path(path)
    if candidate.is_absolute():
        return False
    try:
        (repo / candidate).resolve().relative_to(repo.resolve())
    except ValueError:
        return False
    return True


def check(text: str, repo: Path | None = None) -> list[str]:
    errors: list[str] = []
    data = frontmatter(text)
    if data is None:
        return ["frontmatter must start and end with ---"]

    if not re.search(r"(?m)^slug:\s*[a-z0-9]+(?:-[a-z0-9]+)*\s*$", data):
        errors.append("slug must be kebab-case")
    if not re.search(r"(?m)^status:\s*approved\s*$", data):
        errors.append("status must be approved before reviewer dispatch")

    blocks = slice_blocks(data)
    if not blocks:
        errors.append("at least one slice is required")
    ids = [slice_id for slice_id, _ in blocks]
    for slice_id, count in Counter(ids).items():
        if count > 1:
            errors.append(f"duplicate slice id: {slice_id}")

    owner: dict[str, str] = {}
    for slice_id, block in blocks:
        scope_authority = scalar(block, "scope_authority")
        if scope_authority not in {"confirmed", "user_approved_unresolved"}:
            errors.append(f"slice {slice_id}: invalid or missing scope_authority")

        budget = re.search(r"(?m)^\s+line_budget:\s*(\d+)\s*$", block)
        if not budget:
            errors.append(f"slice {slice_id}: line_budget is required")
        elif not 1 <= int(budget.group(1)) <= 200:
            errors.append(f"slice {slice_id}: line_budget must be 1..200")

        for path in paths(block):
            if repo is not None and not _check_repo_boundary(path, repo):
                errors.append(f"slice {slice_id}: declared path escapes --repo: {path}")
            if path in owner:
                errors.append(f"path owned by multiple slices: {path} ({owner[path]}, {slice_id})")
            owner[path] = slice_id

        command = scalar(block, "command")
        expected_exit_code = scalar(block, "expected_exit_code")
        if not command:
            errors.append(f"slice {slice_id}: verification command is required")
        elif POSIX_COMMAND.search(command):
            errors.append(f"slice {slice_id}: POSIX shell syntax in PowerShell command")
        if expected_exit_code is None or not re.fullmatch(r"-?\d+", expected_exit_code):
            errors.append(f"slice {slice_id}: numeric expected_exit_code is required")

        verification_scope = scalar(block, "scope")
        proves = inline_list(block, "proves")
        risk_predicate = scalar(block, "risk_predicate")
        approved_by = scalar(block, "approved_by")
        if verification_scope not in {"focused", "integration", "full"}:
            errors.append(f"slice {slice_id}: invalid or missing verification scope")
        if not proves:
            errors.append(f"slice {slice_id}: verification proves must be non-empty")
        if verification_scope == "focused":
            if risk_predicate != "null" or approved_by != "null":
                errors.append(f"slice {slice_id}: focused verification requires null risk and approval")
        elif verification_scope in {"integration", "full"}:
            if risk_predicate in {None, "null"}:
                errors.append(f"slice {slice_id}: broader verification requires a named risk")
            if approved_by not in {"lifecycle_owner", "user"}:
                errors.append(f"slice {slice_id}: broader verification requires approval")

        review_checkpoint = scalar(block, "review_checkpoint")
        checkpoint_reason = scalar(block, "checkpoint_reason")
        if review_checkpoint not in {"skip", "candidate", "required"}:
            errors.append(f"slice {slice_id}: invalid or missing review_checkpoint")
        elif review_checkpoint == "skip" and checkpoint_reason != "null":
            errors.append(f"slice {slice_id}: skipped review requires checkpoint_reason: null")
        elif review_checkpoint in {"candidate", "required"} and checkpoint_reason in {None, "null"}:
            errors.append(f"slice {slice_id}: candidate or required review needs checkpoint_reason")

        if "public_contracts:" in block and "public_callers:" not in block:
            errors.append(f"slice {slice_id}: public_contracts requires public_callers inventory")

    for match in PLACEHOLDER.finditer(text):
        errors.append(f"placeholder: {match.group(1)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("--repo", type=Path, help="repository root for declared-path boundary checks")
    args = parser.parse_args()
    errors = check(args.plan.read_text(encoding="utf-8"), args.repo)
    if errors:
        print("FAIL")
        print(*errors, sep="\n")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
