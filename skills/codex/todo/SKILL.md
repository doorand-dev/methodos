---
name: todo
description: |
  Per-project persistent to-do list — `.Codex/todos.md` (persists across sessions).

  Triggers (automatic): "todo", "할 일", "할일", "해야 할 거", "뭐 해야 돼", "뭐 남았어"; operations "작업 추가/목록/빼/완료", "TODO 정리"; deferral remarks (ADR 0014) "나중에 하자", "이건 다음에", "지금은 X만", "후순위", "일단 이거부터", "TODO로", "미뤄두자", "지금 말고", "별도로 빼서".

  Do not append on a deferral remark immediately — wait one turn to confirm *which item* before adding (avoids false positives). Coexists with TodoWrite (volatile, within-session steps) — this skill is only for to-dos that cross sessions.
---

# Todo 스킬

프로젝트 루트 `.Codex/todos.md` 영속 할 일 관리. *설계·WHY는* → [METHODOLOGY.md](METHODOLOGY.md).

> ADR 0014 — todo = 유일 작업 layer. handoff·ADR이 backlink로 가리킴.

## 저장 형식 — 이 헤더를 lazy 생성 시 그대로 emit

```markdown
# Todos

> 규약: `#NNN` 3자리. 추가 시 max+1. close돼도 번호 재사용 X (backlink 안정).
> 형식: 한 줄 린하게(제목 + grep앵커 1-2개: 심볼·파일경로·에러문자열).
>       맥락 3줄+ 넘으면 `.Codex/todo-ctx/NNN.json` 사이드카로 (줄은 린 유지).
>       관련 todo 묶음 = 줄에 공유 토큰(예 `(roi8)`) — grep로 묶고 [x] 세서 진척.

- [ ] #001 <제목 + grep앵커>
- [x] #002 <완료 항목>

## Notes
```

**규약은 SKILL.md가 아니라 이 헤더에 산다** — todo 쓸 때 보는 건 todos.md 그 파일이라 헤더 규약만 실제로 따라짐 (point-of-use, ADR 0026).

## 동작

1. **조회**: todos.md 읽어 그대로 표시.
2. **추가**: 하단에 `- [ ] #NNN <제목 + grep앵커>` append. 맥락 3줄+ → 사이드카로 빼고 줄 린 유지. (헤더 규약대로)
3. **완료**: `- [ ]` → `- [x]`. id 유지.
4. **삭제**: 가급적 X (backlink). 필요시 `## Archive`로 이동.
5. **정리**: `- [x]` 전부 `## Archive`로.

## 보류 발화 1턴 대기 ([ADR 0014])

보류 패턴 감지 → **즉시 append 금지.** 1턴 기다려:
> *"이거 todo로 박을까요? 한 줄 알려주세요."*

받으면 `#NNN` 부여 append. "아니" → skip. (false positive 방지 — WHY는 METHODOLOGY.)

## 파일 없을 때

- `.Codex/` 없으면 생성. `todos.md` 없으면 위 헤더(규약 박스 포함)로 lazy 생성.
- 기존 todos.md 헤더에 형식 줄 없으면 *다음에 만질 때* 추가 (convert-on-touch, 일괄전환 X).

## 작업 후 확인

추가/완료 후 한 줄 보고 ("추가됨: #NNN — <한 줄>"). 다건 동시 지원.

## 연동

| 스킬/훅 | 연동 |
|---|---|
| `handoff` | open todo surface → `referenced_todos` |
| `decision`(ADR) | ADR 작성 시 "작업화 todo?" → `#NNN` + ADR header `Tracking todo:` |
| `todo-auto-close` (hook) | 커밋 `closes todo #NNN` → `[x]` 자동 + 미close 시 same-session 넛지 |
| `session-trio-load` (hook) | SessionStart open todo **카운트** 주입(리스트 덤프 X) |

## 더 깊이 (설계할 때만)

단위 묶음(산문 토큰)·사이드카·합성회상·정비·grep발견성 설계와 WHY →
**[METHODOLOGY.md](METHODOLOGY.md)** (ADR 0017/0019/0020/0026).

## CONV-GATE 위임

[CONV-GRAPH.md](../../CONV-GRAPH.md). 추가 직전 → [0] 안 만들면 / 보류 감지 직후 → [WHAT/HOW] 1턴 확인.
