#!/usr/bin/env python3
"""Context surface PostToolUse hook candidate.

Advises on edits to hot context files such as AGENTS.md, CLAUDE.md, and
SKILL.md. It performs only mechanical checks: missing relative references,
oversized always-on files, nested context surfaces, and weak reader/trigger
signals. It does not call an LLM and does not replace context-novelist.

Set METHODOS_CONTEXT_GUARD_STRICT=1 to block when mechanical issues are found.
Default is advisory-only (exit 0).
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def _ensure_utf8_stderr() -> None:
    if sys.stderr and hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


_ensure_utf8_stderr()

CONTEXT_FILENAMES = {"AGENTS.md", "CLAUDE.md", "SKILL.md"}
MAX_ALWAYS_ON_LINES = 250
MAX_SKILL_LINES = 500
READER_TRIGGER_RE = re.compile(
    r"\b(reader|consumer|trigger|scope|when|route|routing)\b"
    r"|읽|트리거|언제|진입|세션|범위|관객|소비|라우팅",
    re.IGNORECASE,
)
MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
URL_RE = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)
INLINE_PATH_RE = re.compile(
    r"(^\.{1,2}[\\/])|([\\/].*\.(md|py|ps1|json|toml|ya?ml|txt|html)$)",
    re.IGNORECASE,
)


def _as_text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("tool_input") or payload.get("input") or {}
    return value if isinstance(value, dict) else {}


def _tool_name(payload: dict[str, Any]) -> str:
    return _as_text(payload.get("tool_name") or payload.get("name"))


def _file_path(tool_input: dict[str, Any]) -> str:
    return _as_text(tool_input.get("file_path") or tool_input.get("path"))


def _fallback_text(tool_name: str, tool_input: dict[str, Any]) -> str:
    if tool_name == "Write":
        return _as_text(tool_input.get("content"))
    if tool_name == "Edit":
        return _as_text(tool_input.get("new_string"))
    if tool_name == "MultiEdit":
        parts: list[str] = []
        for edit in tool_input.get("edits") or []:
            if isinstance(edit, dict):
                parts.append(_as_text(edit.get("new_string")))
        return "\n".join(p for p in parts if p)
    return ""


def _read_current_text(path: Path, tool_name: str, tool_input: dict[str, Any]) -> str:
    try:
        if path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass
    return _fallback_text(tool_name, tool_input)


def _git_root(path: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    if result.returncode != 0:
        return None
    root = result.stdout.strip()
    return Path(root) if root else None


def _display_path(path: Path) -> str:
    root = _git_root(path)
    if root:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            pass
    return str(path).replace("\\", "/")


def _is_target(path: Path) -> bool:
    return path.name in CONTEXT_FILENAMES


def _clean_reference(raw: str) -> str:
    if "<" in raw or ">" in raw:
        return ""
    ref = raw.strip().strip("<>").strip()
    if not ref or ref.startswith("#"):
        return ""
    ref = ref.split("#", 1)[0]
    if not ref:
        return ""
    match = re.match(r"^(.*\.[A-Za-z0-9]+):\d+(?::\d+)?$", ref)
    if match:
        ref = match.group(1)
    return ref.strip()


def _reference_candidates(text: str) -> list[str]:
    refs: list[str] = []
    refs.extend(match.group(1) for match in MD_LINK_RE.finditer(text))
    for match in INLINE_CODE_RE.finditer(text):
        token = match.group(1).strip()
        if "\n" in token or len(token) > 180:
            continue
        if INLINE_PATH_RE.search(token):
            refs.append(token)
    return refs


def _missing_references(path: Path, text: str) -> list[str]:
    missing: list[str] = []
    seen: set[str] = set()
    for raw in _reference_candidates(text):
        ref = _clean_reference(raw)
        if not ref or ref in seen:
            continue
        seen.add(ref)
        if URL_RE.match(ref) or ref.startswith(("mailto:", "data:", "~/")):
            continue
        if any(ch in ref for ch in "*?"):
            continue
        ref_path = Path(ref).expanduser()
        candidate = ref_path if ref_path.is_absolute() else path.parent / ref_path
        if not candidate.exists():
            missing.append(ref)
    return missing


def _issues(path: Path, text: str) -> list[str]:
    issues: list[str] = []
    display = _display_path(path)
    line_count = len(text.splitlines())
    if path.name in {"AGENTS.md", "CLAUDE.md"} and line_count > MAX_ALWAYS_ON_LINES:
        issues.append(
            f"{display}: always-on context is {line_count} lines "
            f"(>{MAX_ALWAYS_ON_LINES}); consider push-down or skill routing."
        )
    if path.name == "SKILL.md" and line_count > MAX_SKILL_LINES:
        issues.append(
            f"{display}: SKILL.md is {line_count} lines (>{MAX_SKILL_LINES}); "
            "consider progressive disclosure."
        )
    if not READER_TRIGGER_RE.search(text):
        issues.append(
            f"{display}: reader/trigger signal is weak; name who reads this and when."
        )
    root = _git_root(path)
    if root and path.parent != root and path.name in {"AGENTS.md", "CLAUDE.md"}:
        rel_parent = path.parent.relative_to(root).as_posix()
        issues.append(
            f"{display}: nested context surface under {rel_parent}; verify this is "
            "the narrowest scope and parent routing points here."
        )
    missing = _missing_references(path, text)
    if missing:
        shown = ", ".join(missing[:8])
        suffix = "" if len(missing) <= 8 else f", +{len(missing) - 8} more"
        issues.append(f"{display}: missing relative references: {shown}{suffix}.")
    return issues


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, EOFError):
        return 0

    tool_name = _tool_name(payload)
    if tool_name not in {"Edit", "Write", "MultiEdit"}:
        return 0

    tool_input = _tool_input(payload)
    raw_path = _file_path(tool_input)
    if not raw_path:
        return 0

    path = Path(raw_path)
    if not _is_target(path):
        return 0

    text = _read_current_text(path, tool_name, tool_input)
    if not text.strip():
        return 0

    issues = _issues(path, text)
    if not issues:
        return 0

    print("[context-surface-guard] context surface needs review:", file=sys.stderr)
    for issue in issues:
        print(f"  - {issue}", file=sys.stderr)
    print(
        "  Suggested next action: run context-novelist for semantic placement and "
        "minimal-sufficient-context review. Hook did not run an LLM.",
        file=sys.stderr,
    )
    return 2 if os.environ.get("METHODOS_CONTEXT_GUARD_STRICT") == "1" else 0


if __name__ == "__main__":
    raise SystemExit(main())
