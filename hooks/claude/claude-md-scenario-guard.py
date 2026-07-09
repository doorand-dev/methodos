#!/usr/bin/env python3
"""PreToolUse hook: Edit/Write/MultiEdit on context-injection files (CLAUDE.md,
AGENTS.md, settings.json, hooks/*) trigger a scenario-walk reminder.

Non-blocking: outputs JSON with hookSpecificOutput.additionalContext so the
reminder is appended to Claude's context before the tool runs. Claude can
still proceed but is nudged to verify scenario walk.
"""
import json
import sys
import re
from pathlib import PurePosixPath

TRIGGER_BASENAMES = {
    "CLAUDE.md", "AGENTS.md", "settings.json", "settings.local.json",
    "SKILL.md", "MEMORY.md",
}
TRIGGER_PATH_PATTERNS = [
    re.compile(r"(^|/)\.claude/hooks/[^/]+\.(py|sh|ps1)$", re.IGNORECASE),
    re.compile(r"(^|/)global-hooks/[^/]+\.(py|sh|ps1)$", re.IGNORECASE),
    re.compile(r"(^|/)agents/[^/]+\.md$", re.IGNORECASE),
    re.compile(r"(^|/)memory/[^/]+\.md$", re.IGNORECASE),
]
TARGET_TOOLS = {"Edit", "Write", "MultiEdit"}

REMINDER = (
    "[scenario-guard] 매턴 컨텍스트 자동 로드 파일(CLAUDE.md / AGENTS.md / SKILL.md / MEMORY.md / settings.json / hooks / agents)을 수정하려고 합니다.\n"
    "편집 진행 전 자기 점검:\n"
    "  1. 시나리오 — 이 규칙/정보가 어떤 상황에서 발동되는가?\n"
    "  2. 트리거 — 특정 폴더·파일·작업으로 한정되는가?\n"
    "  3. 관객 — 누가 봐야 하나? (Claude 매 세션 / 그 폴더 작업 시만 / 사람만)\n"
    "  4. 발동 범위 — 이 자산/규칙이 *어느 워크스페이스에서* 의미를 갖나? 전역(모든 프로젝트)? 한 워크스페이스 한정? → 등록 위치(~/.claude/ vs 워크스페이스 .claude/) 결정\n"
    "  5. push-down — 관객이 한 서브트리·한 작업뿐이면 루트·전역 말고 *그 scope의 nested CLAUDE.md/스킬*로 내려라 (lazy-load, 매 세션 비용 0).\n"
    "위 다섯이 출력 안 됐으면 멈추고 시나리오부터. 점프 금지. '이미 합의됐다'로 dismiss 금지 — 합의 자체가 잘못된 가정 위였을 수 있음."
)


def normalize(path: str) -> str:
    return path.replace("\\", "/")


def matches(file_path: str) -> bool:
    if not file_path:
        return False
    norm = normalize(file_path)
    basename = PurePosixPath(norm).name
    if basename in TRIGGER_BASENAMES:
        return True
    return any(p.search(norm) for p in TRIGGER_PATH_PATTERNS)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # malformed input -> don't break tool flow

    tool = payload.get("tool_name", "")
    if tool not in TARGET_TOOLS:
        return 0

    file_path = payload.get("tool_input", {}).get("file_path", "")
    if not matches(file_path):
        return 0

    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": REMINDER,
        }
    }
    json.dump(response, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
