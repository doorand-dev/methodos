# narrative-dry-run — 실사용 서사 self-check 렌즈 (정본, [1D])

> methodos 파이프라인의 *cross-cutting* 발견(discovery) 렌즈.
> grill-me / plan / methodos SKILL은 이 파일을 *3줄로 참조*만 — 절차 복붙 금지 ([1D] 정본 단일).

## 본질

실사용 시나리오를 **prose 서사로 끝까지 걷는다**. 한 줄 요약("X를 표시한다")은 빈칸을 숨기지만, end-to-end 서사("6/11에 목록 친다 → **어떻게** 뜨지?")는 미정 자리를 강제로 노출한다. 그래서 *없던 디테일을 길어올린다*.

- **AI 자율 self-check** — 사용자에게 *안 묻는다*. 승인 게이트 추가 0. 산출은 기존 artifact로 auto-route.
- **자세**: reviewer(적대, "틀렸다")와 다름. novelist는 **순진-생성**(naive-use, "없다 · 못 쓴다 · 아무도 이 경로 생각 안 함"). 둘은 상보적.

## 모드 2종

| 모드 | 언제 | 입력 | 산출 |
|---|---|---|---|
| **full** | 전체 실사용을 처음부터 끝까지 | spec.user_stories 또는 조립된 실물 | happy + 주요 분기 서사 전체 |
| **delta** | 리뷰로 *뭔가 바뀐* 직후 | 변경 전/후 (SHA diff) | "기존 → 변경"을 *실사용자 시점 서사*로 |

## 체크포인트 (methodos 파이프라인)

| # | 시점 | 모드 | 실행 주체 | 환류처 |
|---|---|---|---|---|
| #2 | spec 직후 (grill-me §6) | full | **외부 `spec-novelist` agent** (fresh, sonnet) | spec `user_stories` / `edge_cases` / `modules`. 확인은 §7 *기존* review gate에 흡수 |
| #3 | semantic plan 보정 후 delta | delta | **inline** (Claude plan-verify 또는 Codex decision-reviewer fold 뒤) | 체감 변화면 사용자 결정 / 새 보완점은 spec `edge_cases`·plan slice |
| #4 | 최종 구현 후 (model-driven 최종 게이트) | full | **fresh `impl-novelist` agent** (runtime route 명시) | 깨짐/regression → 게이트(아래) / polish → `<todo_root>/todos.md` |

> #1 "방향 합의 직후"는 artifact가 아직 없어 *독립 스텝 아님* — grill-me §3 stress-test에 흡수.

## "깨짐(broken)" 사다리 — #4 게이트 판정 기준

Claude #4는 per-slice impl-verify 다음에 온다. Codex #4는 별도 per-slice reviewer를
두지 않고 requirements/scope, impact/quality, fresh commands/full regression,
actor/user-story seam을 한 fresh final pass에서 함께 소유한다.

| 등급 | 뜻 | #4 처리 |
|---|---|---|
| **polish** | 동작은 함, 지저분 | `todos.md` 적재, 통과 |
| **deferred decision** | 미뤘던 결정이 별로 | `todos.md` 적재, 통과 |
| **깨짐 (broken)** | **spec user_story/Success가 조립 실물에서 안 됨 / 틀린 결과** (per-slice 통과에도) | **게이트: 골 완료(ADR) 보류** |
| **regression** | 기존에 되던 게 이번 변경으로 망가짐 | 깨짐과 동급 (게이트) |

> 정의: **#4가 spec의 user_story·Success criterion을 *조립된 실물*에 대고 end-to-end로 걸었을 때 완료가 안 되거나 틀린 결과가 나오는 것.**
> 좁게 못 박을 것 — "요청한 X가 실물에서 안 됨"만 깨짐. 타이트해서 빈도가 거의 0 → 자율주행 손실 거의 없음.

## 게이트 동작 (#4, 승인 게이트 추가 0)

- 정상(DONE) → model-driven 흐름 정상 종료. 평소와 동일.
- **깨짐/regression(BROKEN)** → 골 완료 결정 보류. **impl 재시도 auto-loop** (사용자 대답 강제 X — 알림 한 줄). runtime retry ceiling 도달 시 escalate.
- polish/deferred → `<todo_root>/todos.md` 자동 적재 후 통과. **`friction.md`에 쓰지 말 것** — `blame-code` 명시 트리거 전용 불변식.

## #4 attempt·route 계약

- 같은 `approved_plan_revision`과 `parent_candidate_sha → candidate_sha` BROKEN-fix chain만 같은 lineage다. 새 approved revision 또는 사용자 결정 cycle은 attempt 1의 새 lineage다.
- attempt 1은 모든 actor/user_story와 regression 범위를 걷는 유일한 baseline full review다. attempt M+1은 stable prior issue, fix changed paths, 영향받은 actor/entrypoint/flow selector만 fresh scoped reverify한다.
- Claude full reverify는 Claude owner contract를 따른다. Codex attempt 2+는 항상
  scoped다. 요구사항, acceptance/oracle, public contract, authority/data behavior,
  impact graph가 바뀌면 scoped를 full로 넓히지 않고 새 lineage attempt 1 full로 시작한다.
- dispatch 직전 nearest `AGENTS.md`가 지시한 project machine route가 있으면
  point-of-use로 다시 읽는다. 외부 provider route는 현재 사용자의 명시 요청이 있을
  때만 쓴다. 기본 Codex full은 `model`/`model_reasoning_effort`를 생략한 fresh
  `impl-novelist`가 부모 세션 값을 상속하고, scoped는
  `impl-novelist-scoped-reviewer(gpt-5.6-sol/medium)`을 쓴다.
- local reviewer를 실행할 수 없거나 context packet이 부족하면 외부 provider로
  fallback하지 않고 `NEEDS_CONTEXT`로 닫는다. 사용자가 Pro/Claude 검토를 명시하면
  해당 provider의 session/model/finality 계약을 point-of-use로 읽고 별도 fresh
  review로 실행한다. 그 실패도 자동 fallback 사유가 아니다.
- artifact에는 approved plan revision, current/parent candidate SHA, `review_scope`,
  실제 provider/transport/model/effort/session을 기록한다. 기본 local route의
  fallback 사유는 null이다.

## novelist agent 페르소나 (순진성 강제)

> "너는 이 기능의 **구현 논의를 본 적 없는 실사용자**다. 사용자가 아는 것만 안다. 주어진 것(spec 또는 조립된 코드)으로 X를 실제로 해보고, 어디서 막히는지·뭐가 안 알려져 있는지·어느 경로가 빠졌는지 서사로 말하라."

- 대화 컨텍스트 **상속 금지** — 상속하면 재오염되어 *의도된 flow*를 narrate하게 됨 (기법 무력화).
- read-only. 산출은 JSON(stdout) — controller가 verify-report 기록.

## 발동 범위 (상황 신호 — 런타임 tier 아님)

외부 novelist agent(#2/#4)는 **신규 기능이 다파일 ∨ 다flow(복합 실사용 경로)일 때만**. 자명한 1-2파일·단일 flow는 skip. 게이트가 *조립 복잡도를 직접 보고* 판단한다.

## Reeval

Reeval은 실제 사용 결과가 쌓일 때 이 파일에서 직접 갱신한다.
