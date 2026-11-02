---
name: todo
description: Manage a project's persistent `.Codex/todos.md` when the user asks to save, list, update or complete tasks across sessions. A status question about current work or a deferral remark alone does not invoke this skill.

---

# Todo 스킬

프로젝트 루트 `.Codex/todos.md` 영속 할 일 관리. *설계·WHY는* → [METHODOLOGY.md](METHODOLOGY.md).

> todo = 유일 작업 layer. handoff·결정 기록이 backlink로 가리킴.

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

**규약은 SKILL.md가 아니라 이 헤더에 산다** — todo 쓸 때 보는 건 todos.md 그 파일이라 헤더 규약만 실제로 따라짐 (point-of-use).

## 동작

1. **조회**: todos.md 읽어 그대로 표시.
2. **추가**: 하단에 `- [ ] #NNN <제목 + grep앵커>` append. 맥락 3줄+ → 사이드카로 빼고 줄 린 유지. (헤더 규약대로)
3. **완료**: `- [ ]` → `- [x]`. id 유지.
4. **삭제**: 가급적 X (backlink). 필요시 `## Archive`로 이동.
5. **정리**: `- [x]` 전부 `## Archive`로.

## 호출과 기록 범위

사용자가 다음 세션에도 남길 할 일을 저장·조회·수정·완료하도록 요청했을 때 사용한다.
현재 작업의 진행 상황이나 남은 단계 질문은 현재 대화로 답한다. “나중에”, “지금은 X만” 같은 보류만으로 파일을 만들거나 추가하지 않고, 자동으로 기록 여부를 묻는 다음 턴도 예약하지 않는다. 사용자가 기록할 항목을 명시하면 그 항목만 저장한다.

## 파일 없을 때

- `.Codex/` 없으면 생성. `todos.md` 없으면 위 헤더(규약 박스 포함)로 lazy 생성.
- 기존 todos.md 헤더에 형식 줄 없으면 *다음에 만질 때* 추가 (convert-on-touch, 일괄전환 X).

## 작업 후 확인

추가/완료 후 한 줄 보고 ("추가됨: #NNN — <한 줄>"). 다건 동시 지원.

## 연동

| 스킬/훅 | 연동 |
|---|---|
| `handoff` | open todo surface → `referenced_todos` |

## 더 깊이 (설계할 때만)

단위 묶음(산문 토큰)·사이드카·합성회상·정비·grep발견성 설계와 WHY →
**[METHODOLOGY.md](METHODOLOGY.md)**.
