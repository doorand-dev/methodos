---
name: impl-verify
description: |
  Fresh-context, read-only verification of one implemented slice: spec coverage,
  caller/producer/consumer impact, and code quality when source code changed.
  **Self-trigger** after a slice commit and before saying it is complete when no
  `slice-<N>-attempt-<M>.json` covers the candidate. Classify the slice once as
  `deterministic_artifact_or_command` or `behavior_integration_or_judgment`.
  **Evidence** is actual command output only; an unverified caller or unavailable
  reviewer cannot produce DONE.
---

# /impl-verify — Claude 슬라이스 검증 gate

Claude controller는 매 attempt마다 fresh, read-only `impl-verify-reviewer`
agent를 dispatch한다. 구현자의 DONE 보고나 이전 attempt의 출력은 증거가 아니다.
기본 artifact root는 `.claude/verify-reports`지만, 프로젝트 `CLAUDE.md` 또는 plan이
다른 `verify_root`를 명시하면 그 경로를 따른다.

## 트리거와 산출 artifact

- 슬라이스 commit 뒤 완료 단언 전에 현재 후보를 덮는
  `<verify_root>/slice-<N>-attempt-<M>.json`이 없으면 자동 발동한다.
- controller는 slice 본문, 선언 파일, commit SHA range, 이전 issue의 stable ID만
  reviewer prompt에 붙여 넣는다. reviewer가 plan 파일을 읽게 하지 않는다.
- artifact에는 `kind`, `target`, `attempt`, `status`, `verification_class`,
  `stage_results`, `stage2_skip_reason`, `reviewer_mode=fresh_subagent`,
  `reviewer_role=impl-verify-reviewer`, 실제 `evidence`, `issues`,
  `touched_files`, `out_of_slice_touches`, `terminal_regression`, `self_review`를
  넣는다.
- reviewer를 dispatch할 수 없거나 evidence가 비면 DONE/DONE_WITH_CONCERNS가 아니라
  NEEDS_CONTEXT다. `quality=SKIPPED`에는 구체적인 `stage2_skip_reason`가 필수다.

## 분류와 attempt 1

| 분류 | 판정 | fresh reviewer의 attempt 1 |
|---|---|---|
| `deterministic_artifact_or_command` | 같은 입력에서 artifact, fixture, hash, schema 또는 닫힌 command의 기계적 참/거짓이 나옴 | spec coverage, oracle adequacy, 선언된 producer→consumer→derived-output preflight와 좁은 selector를 독립 재실행한다. source code/abstraction이 없으면 Stage 2/gc/TDD를 SKIPPED하고 이유를 기록한다. |
| `behavior_integration_or_judgment` | public 동작, caller 조합, integration, 외부 시스템 또는 판단이 실행 성공만으로 닫히지 않음 | full Stage 1+2를 실행한다. Stage 1에서 영향 graph를 닫고, Stage 2에서 quality·gc·적용 가능한 TDD를 확인한다. |

`verification.type`은 실행법 메타데이터일 뿐 두 번째 분류 체계를 만들지 않는다.
`unit_test`/`tdd-parity`는 실제 RED와 GREEN 출력이 모두 필요하며, commit log 추정은
증거가 아니다. reviewer는 shared worktree를 revert/restore하지 않는다.

## Stage 1 — spec과 영향

실제 diff, inline slice spec, `touched_files`, `out_of_slice_touches`를 대조한다.
범위 밖 파일, plan 의도 초과, 요구사항 누락·무단 추가·오해는 BLOCKED다.

- deterministic은 spec coverage, oracle adequacy, integrated preflight 재실행만 한다.
  preflight가 선언한 producer→consumer→derived-output edge와 selector를 따라야 한다.
- behavior/integration/judgment는 바뀐 public symbol/artifact의 caller, producer,
  consumer, derived output을 `git grep`/AST와 targeted command로 열거하고 영향 없음도
  직접 확인한다.
- 실제 reviewer output만 `evidence`에 인용한다. 구현자 보고나 이전 attempt의 출력은
  복사하지 않는다.

Stage 1이 PASS일 때만 Stage 2로 간다. Stage 1 FAIL이면 `quality=SKIPPED`와
`stage2_skip_reason`을 기록한다.

## Stage 2 — 필요한 경우의 quality

behavior/integration/judgment attempt 1은 반드시 full Stage 2를 실행한다.
deterministic은 실제 source code/abstraction 변경 경로에 한해 Stage 2를 실행한다.
새 abstraction([3I]/[3J]), 중복 결정([1D]), gc 임계치와 적용 가능한 TDD red-green을
점검한다. source code가 바뀌지 않은 deterministic work만 `quality=SKIPPED`로 쓰며,
`stage2_skip_reason`에 `data-only: source code unchanged`처럼 이유를 남긴다.

| Stage 1 | Stage 2 | status |
|---|---|---|
| FAIL | — | BLOCKED |
| PASS | critical FAIL | BLOCKED |
| PASS | important만 | DONE_WITH_CONCERNS |
| PASS | PASS 또는 정당한 SKIPPED | DONE |

## 재검증과 골 종료

기존 artifact를 덮어쓰지 않고 같은 slice의 `attempt M+1`을 만든다. reviewer는 매번
fresh/read-only다. scoped reverify는 prior issue closure, fix paths, 바뀐
symbol/artifact의 caller·producer→consumer→derived-output 영향만 다시 닫는다. oracle,
acceptance criteria, public graph, scope가 바뀌었거나 aggregate/shared output이 selector로
닫히지 않으면 full slice reverify로 승격한다.

모든 slice gate가 닫힌 뒤 goal owner가 최종 candidate SHA에서 선언된 full-regression
command를 한 번 실행한다. 별도 terminal artifact는 만들지 않고 final slice attempt의
`terminal_regression`에 candidate SHA, owner, command, exit code, 실제 output을 기록한다.
선언 명령이 없으면 `NOT_DECLARED`와 남은 범위를 기록하며 명령을 발명하지 않는다.

## 금지

- Stage 1 전에 Stage 2 시작
- 실행하지 않은 명령·출력 또는 구현자 DONE을 evidence로 사용
- caller/producer/consumer/derived-output 영향 미확인 상태의 DONE
- reviewer가 코드나 shared worktree를 수정
