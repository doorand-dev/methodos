#!/usr/bin/env python3
"""worktree-advisory.py -- SessionStart hook.

세션이 **메인(공유) 체크아웃**에서 시작하거나 재개될 때 그 폴더의 git 상태
스냅샷을 context로 주입한다. 목적은 foreign dirty 경로를 보존하고 현재 checkout
또는 별도 worktree를 선택하기 전에 실제 겹침을 확인하게 하는 advisory다.

새 인프라(lock/heartbeat) 없음 — git이 이미 기록한 흔적만 읽는다
(worktree_git_state.snapshot).

동작:
  - cwd가 워크트리/비-git -> 침묵 (이미 격리됨 or 무의미)
  - level == silent (main/master & clean) -> 침묵 (솔로 마찰 0)
  - level == warn/info -> Codex-native additionalContext 주입

OUTPUT: {"hookSpecificOutput":{"hookEventName":"SessionStart",
                               "additionalContext": <블록>}}
실패 -> 조용히 통과(non-blocking).
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    cwd = payload.get("cwd") or os.getcwd()

    try:
        import worktree_git_state as wg
        if wg.in_primary_checkout(cwd) is not True:
            return 0  # 워크트리/비-git -> advisory 무의미
        ctx = wg.format_advisory(wg.snapshot(cwd))
    except Exception as e:
        sys.stderr.write(f"[worktree-advisory] error: {e}\n")
        return 0

    if not ctx:
        return 0
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": ctx,
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
