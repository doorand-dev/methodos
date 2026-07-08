#!/usr/bin/env python3
"""Claude Code PostToolUse hook — methodos verify-report 모호 표현 advisory.

Edit/Write 대상이 methodos verify-report(`.claude/verify-reports/*`)이고
"should pass"/"probably"/"것으로 보임" 등 hedging을 포함하면 stderr advisory.
**차단하지 않는다 (exit 0)** — 자동 REVISE는 부모 세션이 수행, 본 hook은 감지·격상만.

methodos [2J] Evidence-first의 *write-time shift-left*. 진짜 FORCE는 impl-verify/
plan-verify 게이트(evidence 필드 검사·BLOCK)에 있고, 본 hook은 *게이트 우회·drift*
케이스를 잡는 저비용 보조 그물이다.

적응:
  A. harness_utils 의존 제거 — ensure_utf8_stderr 인라인. 표시 경로는 *편집 파일의*
     git repo root(`git -C <dir> rev-parse --show-toplevel`)로 동적 해소, 비-git이면 raw path.
  B. 보고서 탐지 = 신세대 경로 `.claude/verify-reports/` (구 .review-artifacts/.plans 폐기).
  C. advisory 유지(exit 2 금지). stdin 파싱 실패·비대상 도구 즉시 exit 0.
  D. 본문 키워드 휴리스틱 삭제 — 경로(path)로만 게이트 (cross-workspace 오탐 0 수렴).
"""
import io
import json
import re
import subprocess
import sys
from pathlib import Path


def _ensure_utf8_stderr() -> None:
    """Windows cp949 한글 깨짐 방지. buffer 없는 환경(pytest 캡처)에선 no-op."""
    if sys.stderr and hasattr(sys.stderr, "buffer"):
        if getattr(sys.stderr, "encoding", "").lower().replace("-", "") == "utf8":
            return
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )


_ensure_utf8_stderr()

# hedging 정규식 (영문 + 한글). "아마" 등 과-광범위 토큰은 제외(오탐 억제).
VAGUE_PATTERN = re.compile(
    r"should pass"
    r"|probably"
    r"|seems to"
    r"|잘 반영된 것 같"
    r"|전체적으로 OK"
    r"|것으로 보임"
    r"|적절해 보",
    re.IGNORECASE,
)


def _looks_like_report(file_path: str) -> bool:
    """methodos verify-report 경로인지 — path-primary only (D)."""
    if not file_path:
        return False
    norm = file_path.replace("\\", "/")
    return "/.claude/verify-reports/" in norm or norm.startswith(".claude/verify-reports/")


def _rel_display(file_path: str) -> str:
    """편집 파일의 git repo root 기준 상대 경로. 비-git/실패 시 raw path (크래시 금지)."""
    norm = file_path.replace("\\", "/")
    p = Path(file_path)
    if not p.is_absolute():
        return norm
    try:
        result = subprocess.run(
            ["git", "-C", str(p.parent), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
        )
        if result.returncode == 0:
            top = result.stdout.strip()
            if top:
                try:
                    return str(p.relative_to(top)).replace("\\", "/")
                except ValueError:
                    pass
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return norm


def _extract_text(tool_name: str, tool_input: dict, tool_output) -> str:
    chunks: list[str] = []
    if tool_name == "Edit":
        chunks.append(tool_input.get("new_string", "") or "")
    elif tool_name == "Write":
        chunks.append(tool_input.get("content", "") or "")
    if isinstance(tool_output, dict):
        for key in ("content", "text", "stdout"):
            v = tool_output.get(key)
            if isinstance(v, str):
                chunks.append(v)
    elif isinstance(tool_output, str):
        chunks.append(tool_output)
    return "\n".join(c for c in chunks if c)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, EOFError):
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Edit", "Write"):
        sys.exit(0)

    tool_input = data.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "")
    if not _looks_like_report(file_path):
        sys.exit(0)

    text = _extract_text(tool_name, tool_input, data.get("tool_output", {}))
    if not text:
        sys.exit(0)

    matches = sorted({m.group(0) for m in VAGUE_PATTERN.finditer(text)})
    if not matches:
        sys.exit(0)

    print(
        f"[evidence] {_rel_display(file_path)} 모호 표현 감지: {matches}. "
        f"verify-report evidence는 *실행 명령 + 출력 인용* 필수 — hedging은 [2J] 위반. "
        f"impl-verify/plan-verify가 빈·모호 evidence를 BLOCK함 → 지금 REVISE 권장.",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
