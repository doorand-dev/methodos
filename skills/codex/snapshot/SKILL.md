---
name: snapshot
description: |
  Right before compaction (/compact) in the same session, persist as JSON the **in-flight tasks, decisions, and unknowns whose priority must survive compaction**. Not a plain backup — a tool that **re-injects** these items into post-compact Codex's working context.

  /compact is a probabilistic summary that can blur or drop important items. A snapshot is an explicit, human/AI-curated priority list, so it survives compaction intact. When Codex re-reads this file after compaction, those items re-enter (remind) the working context.

  Always invoke this skill on these natural-language triggers:
  - "컴팩트 전에 저장", "/compact 직전", "context 곧 잘릴 것 같아"
  - "압축 전에 정리", "현재 진행 상황 영속화", "현재 in-flight snapshot"
  - "우선순위 재주입", "snapshot"

  **This is not for handing work to a new session** — it re-injects priorities after compaction within the same session. To split a task off for the next session, use the `handoff` skill.
---

# Snapshot (전역 스킬)

같은 세션에서 `/compact` 직전에 **in-flight 작업 + 미해결 항목**을 JSON으로
영속화한다. 압축 후 Codex가 이 파일을 다시 읽고 진행 중이던 우선순위를
working context에 재주입한다.

저장 위치: `<workspace>/.claude_context/sessions/<session-id>.json`.

---

## 핵심 원칙: 메모리가 아니라 우선순위 재주입

snapshot은 단순 백업이 아니라 **압축 후 working context로 다시 강제
주입할 우선순위 리스트**다.

### 두 단계 효과

**1. 작성 시점 (pre-compact)** — AI 자기 작업 상태 강제 정리
- "이건 in-flight인가, 완료됐나?" → 분류
- "압축 후 다시 우선순위로 둬야 하나?" → 판단
- 헷갈리는 결정은 명시화

**2. 읽기 시점 (post-compact)** — 우선순위 재주입
- /compact가 흐릿하게 만들거나 누락한 항목을 다시 elevate
- 사람·AI가 큐레이션한 self-prompt를 working context에 재로드
- 다음 즉시 단계가 명확하게 다시 부상

### 캡처 기준

> "잃지 마"가 아니라 "**압축 후에도 우선순위로 살아야 함**"

| ✅ 재주입 필요 | ❌ 재주입 불필요 |
|---|---|
| **진행 중인 subtask** | 완료된 subtask (git/파일에 있음) |
| **아직 안 내려진 결정** | 이미 적용된 결정 (코드에 있음) |
| **사용자 확인 대기 중 항목** | 사용자 승인 완료 항목 |
| **미해결 unknowns** | 이미 검증된 사실 |
| **다음 즉시 단계** (post-compact 첫 액션) | 이미 끝난 단계 |
| **현재 경로 선택 이유** (잊으면 헷갈릴 것) | 시도하다 버린 경로 상세 |
| **이미 시도해서 막힌 길** (재시도 방지용 한 줄) | 막힌 길의 상세 디버깅 내역 |
| **활성 안전 제약** (지금 task에 영향) | 일반 안전 규칙 (AGENTS.md/스킬에 있음) |

완료된 산출물은 git·파일·코드에 이미 있으니 grep 경로만 가볍게 참조 (재주입 효과 희석 방지).

### Scope 일치 원칙

사용자가 좁은 task를 명시했으면 (예: "Q3만 인계", "이번 bug fix 관련 snapshot")
스냅샷 scope도 그 task에 맞춘다. `completed_for_reference`는 **그 task가 직접
의존하는 것만** 기재한다.

"혹시 모르니까 도움될 수도" 식 사전 작업 grep 포인터는 안티패턴 — 더 큰
컨텍스트는 git log / 파일이 처리. inline은 우선순위 효과 희석.

**작성 직전 self-check:** `completed_for_reference`의 각 항목에 대해
"이게 `next_immediate_step` 실행에 *직접* 필요한가? 없으면 작업이 막히나?" 자문.
"도움될 수도"면 뺀다.

예시 — Q3 rename 인계:
- ✅ `completed_for_reference`: Q3 ripple 표 위치 1개 (정본)
- ❌ `completed_for_reference`: G0/G1/G2/Phase 1+2 변경 grep 포인터 모두
  (Q3 실행에 직접 필요 X — git log로 충분)

---

## When to use

- `/compact`가 **실제 임박**했을 때 — 긴 세션이라고 자동 아님. 1M 컨텍스트(Opus 4.8+)에선 compact가 드물어져 발동 구간이 좁아졌다. "오래 끌었으니 일단 snapshot"은 과발동 — compact가 임박하지 않으면 보류.
- 진행 중인 task의 *고위험* 우선순위가 압축의 확률 요약으로 흐릿해지면 안 될 때 (못 믿을 in-flight 결정·미상)
- 사용자가 "지금까지 저장", "압축 전 정리" 명시 요청

## When NOT to use

- **새 세션으로 task 일부 분리** → `handoff` 스킬 (시작 프롬프트 추천 포함). 판별: *시작 프롬프트에 cwd·env·dev 서버 같은 전제조건을 적어줘야 하면* 환경이 안 살아있다는 뜻 → 새 세션 → handoff. snapshot은 환경이 그대로 살아있어 "스냅샷 읽고 이어가" 한 줄로 충분.
- 영속 할 일 관리 → `todo` 스킬
- 단순 메모, 일회성 상태

---

## Workflow

1. **workspace root 식별** (현재 작업 디렉토리).

2. **orphan check**: 산출물 정리 직전, 이번 세션에서 *논의·언급만 되고 어디에도
   박히지 않은 항목*이 있는지 스스로 점검한다. snapshot 발동 시점엔 세션
   컨텍스트가 살아 있으니 그것을 그대로 읽고 판단. 발견 시 사용자에게 출처
   라벨([self] / [user-deferred]) 붙여 표로 surface하고 4분기 제시:

   - (a) todo 등재
   - (b) 현재 산출물(snapshot JSON `in_flight` / `pending_questions_to_user` 등)에 포함
   - (c) subagent 즉시 위임 — "단일 파일·독립 실행 가능·세션 문맥 불필요" 셋 다 만족 시 우선 제안
   - (d) discard (의도적 종결)
   - (e) **finding 졸업** — 코드가 못 담는 *영속* 외부시스템 지식(막힘/우회)이면 `/finding`(`docs/findings/`). `do_not_redo`의 *영속 부분*이 전형(snapshot은 compaction 후 흐릿해지는 휘발물 → 영속 사실은 거기 두면 손실). pre-compact가 *마지막 안전 시점*이라 여기서 졸업 surface. **제안만, silent write X** (ADR 0024 결정6).

   [self] 항목(AI가 plan/spec 쓰면서 분리한 후속)만 있으면 "정말 필요한가요?"
   묻고 보통 종결 권유. 결정 자체는 끝났는데 형식 후속만 남은 항목은 그 사실
   명시("결정 완료, status 갱신만").

3. **재주입 대상만 추출** (위 매트릭스 기준):
   - 현재 진행 중인 task 한 줄 요약
   - 어디까지 왔는지 (phase)
   - 압축 후 첫 액션 (가장 중요 — 구체적으로)
   - 미해결 결정 + **이유** (재주입 시 무게를 인식하게)
   - 사용자 확인 대기 항목
   - unresolved unknowns
   - 활성 안전 제약
   - 재시도 금지 목록

4. **완료된 일은 grep 참조로만**:
   - 인라인 금지 (재주입 효과 희석)
   - `{"summary": "한 줄", "grep": "rg 'pattern' path/"}` 형식
   - **Scope self-check**: 사용자가 좁은 task를 명시했으면, 각 항목이
     `next_immediate_step`에 *직접* 필요한지 자문. 없으면 작업이 막히는
     것만 박기. "도움될 수도"는 안티패턴.

5. **JSON 작성**: `<workspace>/.claude_context/sessions/<session-id>.json`

6. **기존 파일 백업**: 있으면 `.claude_context/archive/<file>_<timestamp>.json`으로
   옮긴 뒤 덮어쓰기. 사용자가 "백업 없이"라고 명시하지 않는 한.

7. **검증**: 작성 후 파일을 다시 읽어 JSON 파싱 확인.

7b. **execution trace (FORCE)**: step 8 보고 *직전*, 건너뛰기 쉬운 step 2(orphan
   check)의 **결과를 한 줄** 먼저 출력한다. 빈 체크박스가 아니라 *결과 기입형* —
   없으면(`orphan 없음`) 그 사실을, 있으면 항목+출처라벨+분기를. trace 없이 보고로
   직행 금지 (단계 skip 차단의 본체 — 산문 지시가 아니라 증거 강제). 예:
   `[x] step 2 orphan check: do_not_redo 영속 1건 [self] → (e) finding 졸업 제안`.

8. **간결 보고 + 복붙 프롬프트 제공**: 저장 경로 + top-level key 개수.
   그리고 `/compact` 직후 사용자가 그대로 붙여넣을 한 줄을 코드블록으로 출력:

   ````
   ```
   .claude_context/sessions/<session-id>.json 읽고 in_flight.next_immediate_step부터 이어가
   ```
   ````

   자동 재로드 없으므로 이 한 줄이 재주입 트리거. (경로는 위 보고에 그대로
   출력되니 세션 id를 외울 필요 없음 — 공유 인덱스 파일은 제거됨.)

---

## 재주입 효과 극대화 팁

1. **"왜 중요한지" 한 줄 첨부** — 재주입 시 항목 무게를 다시 인식하게.
   `decision`만 적지 말고 `reason`도.
2. **`next_immediate_step` 가장 구체적으로** — 압축 후 첫 액션이 명확해야
   working context가 즉시 정렬됨.
3. **짧고 날카롭게** — 너무 길면 우선순위 효과 희석. 항목당 1~2줄.
4. **AGENTS.md/스킬에 이미 있는 일반 규칙은 복제하지 않기** — 활성 제약은
   *지금 task에만 해당*하는 것만.

---

## JSON Shape

```json
{
  "schema_version": "1.0",
  "kind": "context_snapshot",
  "created_at_local": "YYYY-MM-DDTHH:MM:SS+09:00",
  "workspace": "absolute path",
  "session_id": "short-task-id",
  "tool": "Codex",
  "purpose": "Same-session pre-compact priority re-injection (not full dump).",

  "in_flight": {
    "task": "현재 진행 중인 작업 한 줄 요약",
    "phase": "어디까지 왔는지",
    "next_immediate_step": "압축 후 첫 액션 (구체적으로)"
  },

  "active_decisions": [
    {"decision": "...", "reason": "왜 이렇게 정함 (재주입 시 무게 인식용)", "still_open": false}
  ],

  "pending_questions_to_user": ["..."],

  "unresolved_unknowns": ["..."],

  "active_constraints": ["지금 task에 영향 주는 안전·비즈니스 제약만"],

  "completed_for_reference": [
    {"summary": "한 줄", "grep": "rg 'pattern' src/", "why": "여기 보면 됨"}
  ],

  "do_not_redo": ["이미 시도해서 막힌 길 (한 줄 요약, 재시도 방지)"],

  "resume_instruction": "Post-compact: read in_flight.next_immediate_step first, then continue with these priorities re-injected."
}
```

ASCII 우선. 한글 등 non-ASCII는 UTF-8 valid로 유지.

## Anti-patterns

| 안티패턴 | 대신 |
|---|---|
| 세션 시작~끝까지 다 inline | in-flight·미해결만, 완료는 grep 참조 |
| 완료된 결정도 active_decisions에 | 코드/파일에 적용 끝났으면 빼기 |
| 막힌 길 상세 디버깅 내역 | do_not_redo에 한 줄만 |
| 모든 user 발화 요약 | in_flight.task + 활성 결정만 |
| AGENTS.md/스킬 일반 규칙 복제 | active_constraints는 *지금 task에만* 해당하는 것만 |
| reason 없이 decision만 | 항상 reason 한 줄 — 재주입 시 무게 인식 |
| 사용자가 좁은 task 명시했는데 사전 작업 grep 포인터까지 다 inline | task에 *직접* 필요한 것만. "도움될 수도"는 빼기 — git/파일이 처리 |

---

## Script

`scripts/write_context_snapshot.py`로 저장·검증·백업 자동화:

```powershell
python <installed-snapshot-skill>/scripts/write_context_snapshot.py --input snapshot.json --workspace . --session-id <task-id>
```

스크립트:
- `.claude_context/` 디렉토리 생성
- `--output` 없으면 `.claude_context/sessions/<session-id>.json`에 저장
- 기존 파일은 `.claude_context/archive/`에 타임스탬프 백업
- UTF-8 pretty JSON
- 재파싱 검증

병렬 작업은 서로 다른 `--session-id` (세션별 파일이라 충돌 없음 — 공유 파일 안 씀).

---

## 작동 메커니즘 (참고)

자동 재로드는 **하지 않는다**.

따라서 `/compact` 직후 사용자가 다음 한 줄을 직접 붙이는 게 표준 흐름:

> "스냅샷 읽고 이어가" (`.claude_context/sessions/<session-id>.json` 경로 명시)

스냅샷이 working context에 재진입한다.

---

## Safety

- 쿠키, 세션 ID, 비밀번호, 토큰, 개인키 절대 금지. 위치/갱신 방법만 언급.
- 사용자 이름·사번·책임자·참석자 이름은 role 라벨로.
- private repo에 들어가도 안전한 수준만.
- live ERP 쓰기·결재 동작은 스냅샷 후에도 fresh 확인 필요.

---

## CONV-GATE 위임

매핑 정본 → [`mine/CONV-GRAPH.md`](../../CONV-GRAPH.md).

- 우선순위 큐레이션 시 → [2G] 라벨 [확신/추정/모름] 강제 (압축 후 재진입 시 신뢰도 보존)

신규 시점 추가 시 CONV-GRAPH.md 매핑 표 한 줄 갱신.
