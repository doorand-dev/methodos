---
name: impl
description: |
  Implement an approved plan one slice at a time and produce a WHY-prefixed git
  commit. Trigger after plan approval and plan-verify completion when a slice is
  unimplemented. Keep work inside the slice, preserve caller impact checks, and
  hand every candidate to the fresh read-only impl-verify reviewer.
---

# /impl — 슬라이스 구현 스킬

## 트리거와 사전 조건

- plan status=approved, plan-verify가 DONE이며 현재 slice의 commit/verify
  artifact가 없을 때 자동 발동한다.
- "구현", "implement", "이 슬라이스 만들어", `/impl <slice>` 요청도 트리거다.
- nearest `AGENTS.md`와 plan frontmatter에서 `plan_root`/`verify_root`를
  정하고, approved plan·최신 plan-verify artifact·slice `touched_files`를
  확인한다. 부족하면 `/plan` 또는 `/plan-verify`로 돌아간다.

## 구현 절차

1. slice 본문을 prompt에 inline으로 붙이고 `touched_files` 밖 수정은 즉시
   멈춘다. plan 의도를 명백히 넘는 파일·모듈 확장은 DONE_WITH_CONCERNS로
   보고하고 임의 분할하지 않는다.
2. public signature/behavior가 바뀌면 `git grep`/AST로 caller를 열거한다.
   함께 고치거나 영향 없음을 직접 확인해야 하며, 닫지 못한 caller는 BLOCKED/
   NEEDS_CONTEXT다.
3. plan의 verification metadata를 읽어 slice의 검증 class를 한 번 정한다:
   `deterministic_artifact_or_command` 또는 `behavior_integration_or_judgment`.
   이 값은 impl-verify에 넘기며 별도 oracle 유형을 만들지 않는다.
4. deterministic artifact/command 계약이면 commit 전에 executable preflight를
   선언·실행한다. command, pass 기준, exit, output, producer→consumer→derived-
   output coverage와 가능한 scope selector를 `implementer_preflight` handoff에
   남긴다. 이것은 early defect detection이며 reviewer의 증거가 아니다.
5. `verification.type=unit_test` 또는 `tdd-parity`이면 테스트 RED를 실제로 관찰한
   출력과 최소 구현 후 GREEN 출력 둘을 남긴다. commit log로 대체하지 않는다.
   실행하지 않은 command/output은 report에 쓰지 않는다.
6. WHY prefix commit을 만들고 즉시 fresh read-only `/impl-verify`를 호출한다.

작은 로컬 slice는 inline으로, 독립적이고 큰 결합 slice는 fresh dispatch로
구현할 수 있다. dispatch하더라도 아래 기준을 prompt에 그대로 붙인다.

```text
You are implementing Task <slice id> from the approved plan.

Context (do not inherit the controller session):
- slice body: <inline paste>
- touched_files: <list>
- verification metadata and commands: <inline paste>
- WHY commit format: <inline paste>

Your job:
- edit only touched_files; stop on an out-of-slice or intent-overrun signal
- enumerate and close caller/producer/consumer/derived-output impact
- for unit_test/tdd-parity, record actual RED then GREEN output
- for deterministic contracts, run and report preflight command/output/exit/coverage
- never report an unrun command or rely on a prior DONE claim
- commit with WHY: and return the actual status
```

## Commit과 verify cycle

커밋은 한 slice만 포함하고 다음 형식을 따른다.

```text
<한 줄 제목>

WHY: <결정> | 비용(지금/부채): Xm/Ym | Reeval: <조건>
Slice: <slice id>
Touched: <touched_files 목록>
```

각 slice commit 뒤 `slice-<N>-attempt-1.json`을 만든다. BLOCKED이면 impl은
fix를 만들고 `attempt M+1`을 호출한다. fresh reviewer는 narrow fix의 issue
closure·changed paths·caller/producer/consumer/derived-output만 scoped로
재검증하며, oracle/acceptance criteria나 public/caller graph가 바뀌거나
scope가 닫히지 않으면 full slice reverify로 올린다. reviewer가 없거나 evidence가
없으면 DONE으로 진행하지 않는다.

reviewer를 dispatch할 때마다 `impl-verify`의 `검증 분류와 attempt 1` 및
`BLOCKED fix 후 재검증`을 point-of-use로 다시 읽는다. attempt 1은 lineage의
baseline full reviewer 한 번이고, attempt M+1은 fresh scoped reviewer와 낮춘
reasoning effort를 명시한다. 직전 reviewer의 model/effort 또는 런타임 기본값을
상속하지 않는다.
verify artifact에는 approved plan revision, current/parent candidate SHA,
full/scoped scope, 실제 reviewer model과 reasoning effort를 기록한다.

모든 slice가 DONE인 뒤 goal owner는 최종 candidate SHA에서 선언된 full regression을
한 번 실행하고 최종 slice artifact의 `terminal_regression`에 기록한다. 별도
terminal artifact를 만들거나 preflight/targeted check를 full regression으로
대체하지 않는다. 명령이 선언되지 않았으면 그 사실과 잔여 범위를 기록한다.

## 안 하는 것

- slice 밖 파일 수정, 임의 추상화·분할, 여러 slice를 한 commit에 묶기
- caller 영향 미확인 상태에서 reviewer를 통과시키기
- 실행하지 않은 evidence, commit log만으로 TDD RED를 주장하기
- reviewer 대신 controller가 DONE 판정을 쓰기

---

## 결정 신호

- commit 직전: 한 slice 단독 구현·검증 가능성과 scope를 확인한다.
- commit 직후: fresh read-only impl-verify artifact가 DONE인지 확인한다.
