# Methodos shared planning contract

이 문서는 `/grill-me`, `/plan`, `/impl`이 함께 읽는 최소 계약이다. 계약은
실행 가능한 안전 조건만 정의하며, 별도 보고서·증명서·검증 산출물을 요구하지 않는다.

## 런타임 루트

프로젝트 컨텍스트가 루트를 선언하면 그 값을 사용한다. 선언이 없으면 다음 기본값을
사용한다.

- spec: `docs/specs/`
- plan: `.claude/plans/` 또는 `.Codex/plans/`
- verification: 실행한 테스트와 명령의 실제 출력

폴더는 첫 산출 시 생성하며, 임시 파일과 캐시는 저장하지 않는다.

## Spec 계약

`docs/specs/<slug>.md`는 다음을 포함한다.

- kebab-case `slug`, `status: draft | approved`, 목표 한 문장
- 최소 하나의 user story와 명시적인 out-of-scope
- happy와 edge 시나리오. 사용자 선택이 필요한 시나리오는 선택지와 승인 상태를 적는다.
- 생성·수정할 모듈의 인터페이스 수준 설명과 테스트 우선순위

`approved`는 사용자의 명시적 승인(user approval) 이후에만 사용한다. spec의 본문은 `/plan`이 추가
인터뷰 없이 읽을 수 있을 만큼 자립적이어야 한다.

## Plan 계약

`<plan_root>/<slug>.md`는 다음을 포함한다.

```yaml
slug: <kebab-case>
status: draft | approved
goal: <한 문장>
slices:
  - id: <unique id>
    files:
      create: [<exact path>, ...]
      modify: [<exact path>, ...]
      test: [<exact path>, ...]
    verification:
      type: unit_test | command | fixture | custom
      command: <실행 명령>
      expected_exit_code: 0
    line_budget: <1..200>
    public_contracts: []
    public_callers: []
    review_checkpoint: skip | required
    checkpoint_reason: null | <high-risk predicate>
```

모든 `files` 배열은 명시하며 빈 배열도 허용한다. 한 경로는 한 slice만 소유한다.
`public_contracts`가 비어 있지 않으면 해당 심볼의 `public_callers` inventory를 함께
기록한다. `verification.command`는 대상 플랫폼의 명령 문법을 사용하고, 테스트 실행
또는 다른 재현 가능한 명령과 기대 종료 코드를 적는다.

`status: approved`는 사용자의 명시적 승인(user approval)을 뜻한다. 승인되지 않은 plan은 구현이나
review의 입력으로 사용하지 않는다.

## 기계적 preflight 안전

preflight는 semantic 판단 대신 다음을 검사한다.

1. frontmatter 경계, kebab-case slug, `status: approved`
2. slice가 하나 이상 존재하고 id가 중복되지 않음
3. exact paths가 slice 사이에서 중복 소유되지 않음
4. `line_budget`가 1..200 범위이고 placeholder가 없음
5. PowerShell 실행 환경에서 POSIX 전용 명령 문법을 사용하지 않음
6. `public_contracts`에 대응하는 `public_callers` inventory가 있음
7. `--repo`가 주어지면 declared path가 repo 경계를 벗어나지 않음

이 검사는 파일 개수나 커밋 이력과 무관하다. 변경 후에는 실제 changed-path가 선언된
exact paths와 일치하는지 확인한다.

## 조건부 high-risk review

다음 impact predicate 중 하나라도 해당할 때만 추가 review를 요구한다.

- schema 또는 public contract 변경
- authority, permission, secret, security 영향
- persistence, latest 값, idempotency, concurrency 영향
- migration 또는 external state 변경
- order, capital allocation, financial execution 영향
- 두 개 이상의 후속 slice가 의존하는 downstream foundation

그 외의 크기·복잡도·파일 수만으로 review를 요구하지 않는다. required review에는
해당 predicate와 영향을 받는 caller / producer / consumer / failure 경로, 그리고
검사할 명령을 적는다. `skip`이면 `checkpoint_reason: null`로 둔다.

## 구현 완료 조건

- 사용자가 승인한 범위 안의 exact paths만 변경한다.
- 선언한 verification 명령과 테스트를 실행하고 결과를 확인한다.
- public contract 변경이면 caller inventory를 다시 확인한다.
- 외부 작업·사용자 데이터·권한·database/schema·public contract·concurrency·migration
  또는 external state 선택은 필요한 경우 사용자 승인을 받는다.

구현자 설명이나 별도 artifact는 완료를 증명하지 않는다. 실제 테스트 실행, changed-path
확인, 승인 상태, 그리고 조건부 risk predicate가 판정의 근거다.
