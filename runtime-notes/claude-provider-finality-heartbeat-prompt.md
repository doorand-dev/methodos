# Claude 담당자 실행 프롬프트 — provider finality와 heartbeat

Claude Code 정본에 다음 정책을 반영하라. Codex source, 전역 설치본, `.claude/**`, `~/.claude/**`는 수정하지 않는다.

## 읽을 정본

- `skills/claude/ask-chatgpt-pro/SKILL.md`
- `skills/claude/conditional-heartbeat/SKILL.md`
- `skills/claude/ask-chatgpt-pro/scripts/pro-review.ps1`
- `skills/claude/conditional-heartbeat/scripts/codex-heartbeat-rrule.ps1`
- Codex 참조: `docs/adr/0001-provider-finality-heartbeat.md`, `skills/codex/ask-chatgpt-pro/SKILL.md`, `skills/codex/conditional-heartbeat/SKILL.md`

## 목표

1. ChatGPT Pro finality는 `sessionId`, provider `complete`, `completedAt`, 최소 길이, 두 읽기 stable hash로 판정한다. streaming/preamble/짧은 placeholder는 final이 아니다.
2. 동일 sessionId가 unresolved인 동안 재-send하지 않는다. final 뒤 heartbeat를 삭제하고 필요한 경우 tab을 닫는다.
3. 외부 watcher가 automation storage를 직접 수정하거나 hidden watcher 완료만으로 thread를 깨우지 않는다. `automation_update(mode=create)`는 `DTSTART`를 받지 않고, `suggested_create`는 자동 설치가 아니라 카드 렌더링이라는 현재 capability 한계를 문서화한다.
4. 현재 공개 API는 exact future one-shot create 자체를 닫고 있으므로, watcher acceleration과 5분 자동 collect cycle 모두 구현하지 않는다. `DTSTART` create rejection과 `suggested_create` 카드 렌더링을 blocker로 보고하고 같은 sessionId의 later collect만 안내한다.
5. provider terminal event를 owning turn으로 직접 전달하는 API가 생기면 foreground wait 또는 external watcher acceleration을 재검토한다.

## 검증과 커밋

`pro-review`의 streaming fixture가 `answerText: null`을 반환하고 complete+stable fixture만 answerText를 반환하는 회귀 검사를 추가한다. RRULE helper의 `-Apply`가 실패하고 direct storage mutation 문구가 없는지도 검사한다. 변경 파일만 명시 pathspec으로 stage하고 WHY를 담은 한글 커밋을 만든다. branch/worktree/push는 하지 않는다.
