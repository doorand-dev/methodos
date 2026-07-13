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
| #3 | plan-verify 후 delta (plan M2) | delta | **inline** (기계적 diff, 오염 여지 적음) | 체감 변화면 기존 M2 게이트 / 새 보완점은 spec `edge_cases`·plan slice |
| #4 | 최종 구현 후 (model-driven 최종 게이트) | full | **외부 `impl-novelist` agent** (fresh, runtime route 명시) | 깨짐/regression → 게이트(아래) / polish → `<todo_root>/todos.md` |

> #1 "방향 합의 직후"는 artifact가 아직 없어 *독립 스텝 아님* — grill-me §3 stress-test에 흡수.

## "깨짐(broken)" 사다리 — #4 게이트 판정 기준

#4는 impl-verify(per-slice) *다음*에 온다. 각 slice가 plan대로임은 이미 통과된 상태. #4가 더 잡는 건 **slice 사이 이음새(seam)** — 전체를 사용자처럼 한 번에 걷는 유일한 자리라서.

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
- **깨짐/regression(BROKEN)** → 골 완료 결정 보류. **impl 재시도 auto-loop** (사용자 대답 강제 X — D34식 알림 한 줄). N 천장 도달 시 escalate (impl-verify ralph와 동일).
- polish/deferred → `<todo_root>/todos.md` 자동 적재 후 통과. **`friction.md`에 쓰지 말 것** — `blame-code` 명시 트리거 전용 불변식.

## #4 attempt·route 계약

- 같은 `approved_plan_revision`과 `parent_candidate_sha → candidate_sha` BROKEN-fix chain만 같은 lineage다. 새 approved revision 또는 사용자 결정 cycle은 attempt 1의 새 lineage다.
- attempt 1은 모든 actor/user_story와 regression 범위를 걷는 유일한 baseline full review다. attempt M+1은 stable prior issue, fix changed paths, 영향받은 actor/entrypoint/flow selector만 fresh scoped reverify한다.
- full reverify는 acceptance/oracle 변경, public/caller/decision graph 변경, out-of-scope touch, selector로 닫히지 않는 shared output, impact radius 미폐쇄 중 하나일 때만 허용한다. `escalation_reason`에 predicate를 기록한다. attempt 증가나 unchanged contract 안의 새 issue는 full 사유가 아니다.
- scoped reviewer가 위 predicate로 `NEEDS_CONTEXT`를 반환하면 그 응답은 routing
  envelope이며 terminal artifact로 저장하지 않는다. 같은 attempt/candidate/parent를 유지해 full route로
  재dispatch하고 full 결과 하나만 저장한다. 다른 `NEEDS_CONTEXT`는 terminal이다.
- dispatch 직전 nearest `AGENTS.md`가 지시한 project machine route가 있으면
  point-of-use로 다시 읽어 provider/model/reasoning effort를 모두 명시한다. route가
  없으면 Codex full은 fresh `ask-chatgpt-pro(pro/extended)`가 primary이고
  `impl-novelist(gpt-5.6-sol/xhigh)`는 transport/finality fallback 전용이다. scoped는
  `impl-novelist-scoped-reviewer(gpt-5.6-sol/medium)`을 쓴다.
- Pro의 final `BROKEN`/`NEEDS_CONTEXT`/issue verdict는 성공한 review이며 fallback하지
  않는다. local full fallback은 `provider_send_failure`,
  `model_or_effort_unconfirmed`, `timeout`, `finality_failure`,
  `attachment_or_context_failure` 중 하나로 결과 자체를 얻지 못했을 때만 fresh/
  read-only로 한 번 허용한다. 둘 다 실패하면 `NEEDS_CONTEXT`다.
- artifact에는 approved plan revision, current/parent candidate SHA, `review_scope`,
  실제 provider/transport/model/effort/session과 fallback 사유를 기록한다.

## novelist agent 페르소나 (순진성 강제)

> "너는 이 기능의 **구현 논의를 본 적 없는 실사용자**다. 사용자가 아는 것만 안다. 주어진 것(spec 또는 조립된 코드)으로 X를 실제로 해보고, 어디서 막히는지·뭐가 안 알려져 있는지·어느 경로가 빠졌는지 서사로 말하라."

- 대화 컨텍스트 **상속 금지** — 상속하면 재오염되어 *의도된 flow*를 narrate하게 됨 (기법 무력화).
- read-only. 산출은 JSON(stdout) — controller가 verify-report 기록.

## 발동 범위 (상황 신호 — 런타임 tier 아님)

외부 novelist agent(#2/#4)는 **신규 기능이 다파일 ∨ 다flow(복합 실사용 경로)일 때만**. 자명한 1-2파일·단일 flow는 skip. 게이트가 *조립 복잡도를 직접 보고* 판단한다.

## Reeval

Reeval은 실제 사용 결과가 쌓일 때 이 파일에서 직접 갱신한다.
