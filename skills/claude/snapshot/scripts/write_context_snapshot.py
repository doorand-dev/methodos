#!/usr/bin/env python3
"""Write a same-session pre-compact context snapshot (Claude).

Writes to ``<workspace>/.claude_context/sessions/<session-id>.json``. The
``resume_instruction`` field is tool-neutral; readers should accept either
``resume_instruction`` or ``resume_instruction_for_codex``.

NOTE: 공유 단일 인덱스(``current_findings.json``)는 제거됨 — 멀티세션/워크트리에서
last-writer-wins 덮어쓰기 충돌을 유발하던 안티패턴(전역 가변 포인터). 재개는
세션별 스냅샷 경로를 명시하면 충분하며, 그 경로는 작성 직후 보고에 출력된다.
(decision: ADR snapshot-drop-shared-index.)
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SystemExit("Snapshot input must be a JSON object.")
    return data


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "session"


def now_local() -> datetime:
    return datetime.now(ZoneInfo("Asia/Seoul"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write a session-specific .claude_context snapshot safely (Claude)."
    )
    parser.add_argument("--input", required=True, help="Path to a JSON object to write as the snapshot.")
    parser.add_argument("--workspace", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--output", help="Explicit snapshot output path. Relative paths are resolved from workspace.")
    parser.add_argument("--session-id", help="Stable session/task id for .claude_context/sessions/<session-id>.json.")
    parser.add_argument("--no-backup", action="store_true", help="Overwrite without archiving an existing snapshot.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    input_path = Path(args.input).resolve()
    context_dir = workspace / ".claude_context"
    session_id = slugify(args.session_id) if args.session_id else now_local().strftime("%Y%m%d_%H%M%S")

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = workspace / output_path
    else:
        output_path = context_dir / "sessions" / f"{session_id}.json"

    data = load_json(input_path)
    data.setdefault("schema_version", "1.0")
    data.setdefault("kind", "context_snapshot")
    data.setdefault("workspace", str(workspace))
    data.setdefault("session_id", session_id)
    data.setdefault("tool", "claude")
    data.setdefault("created_at_local", now_local().isoformat(timespec="seconds"))
    data.setdefault(
        "resume_instruction",
        "Post-compact: re-read this snapshot, then continue from in_flight.next_immediate_step.",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    archive_dir = context_dir / "archive"
    if output_path.exists() and not args.no_backup:
        archive_dir.mkdir(parents=True, exist_ok=True)
        stamp = now_local().strftime("%Y%m%d_%H%M%S")
        backup_path = archive_dir / f"{output_path.stem}_{stamp}{output_path.suffix}"
        output_path.replace(backup_path)
    else:
        backup_path = None

    with output_path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    with output_path.open("r", encoding="utf-8") as f:
        validated = json.load(f)

    print(json.dumps({
        "ok": True,
        "path": str(output_path),
        "schema_version": validated.get("schema_version"),
        "kind": validated.get("kind"),
        "tool": validated.get("tool"),
        "backup": str(backup_path) if backup_path else None,
        "session_id": session_id,
        "top_level_keys": len(validated),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
