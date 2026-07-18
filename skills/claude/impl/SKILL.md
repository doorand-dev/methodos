---
name: impl
description: >-
  승인된 plan을 슬라이스 단위로 하나씩 구현하는 model-driven 자율주행. 산출은 WHY: commit.
  Self-trigger: plan 승인 + 그 슬라이스 미구현일 때 "구현", "implement", "이 슬라이스 만들어".
  실행모드(inline vs fresh 서브에이전트)는 상황 판단(OPEN). [1C] 누더기 거부(FORCE).
---

# /impl — 슬라이스 자율 구현

승인된 plan의 슬라이스를 **한 번에 하나씩** 구현한다. 각 슬라이스의 산출은 로컬 검증을
통과한 `WHY:` commit 하나다. 별도 보고서·JSON·provenance·해시는 만들지 않는다 — 완료의
근거는 *실제로 돌린 테스트 출력*과 *changed-path가 범위 안*이라는 사실이다.

## 실행모드 — inline vs fresh 서브에이전트 (G-A, OPEN)

슬라이스마다 *짤지 말지*가 아니라 *어디서 짤지*만 판단한다:

- **inline** (컨트롤러가 직접): 이 세션이 관련 코드를 이미 쥐고 있고 공유·의존 파일과
  얽혀 있을 때. dispatch 격리이득 < 재로딩 비용.
- **fresh 서브에이전트** (Agent tool로 격리 dispatch): 독립적이고 큰 슬라이스(대략
  touched ≥ 5 또는 긴 작업)이고 이 세션이 코드를 안 쥐고 있을 때. fresh context가 맹점을 줄인다.

판단축은 context-locality(이미 쥐었나) + coupling(공유/의존). 규칙이 아니라 상황 신호 —
*call은 모델의 것*.

**서브에이전트 격리 불변식**: dispatch된 서브에이전트는 세션 상속이 없어 *프롬프트에 적힌
것만* 안다. 위임 시 슬라이스의 exact paths, 실행할 테스트/명령, changed-path 경계, (테스트
오라클이면) TDD red→green 관찰을 프롬프트에 *명시 echo*한다.

## TDD red-green (verification.type이 test-oracle일 때)

실패 테스트 먼저 → 실행해 **RED 관찰** → 최소 구현 → 실행해 **GREEN 관찰** → commit.
양방향 출력을 실제로 봐야 한다 — 한 방향만으로 "테스트 작동함" 주장 금지. inline·dispatch 동일.

## 조건부 review 라우팅

기본은 review 없음 — 로컬 테스트 + exact changed-path 확인으로 종결한다. **아래 위험
predicate 중 하나라도 걸릴 때만** fresh-context 리뷰어를 Agent tool로 한 번 dispatch한다:

- schema 또는 public contract 변경
- authority / permission / secret / security 영향
- persistence / latest 값 / idempotency / concurrency 영향
- migration 또는 external state 변경
- order / capital allocation / financial execution 영향
- 두 개 이상 후속 슬라이스가 의존하는 downstream foundation

슬라이스 단위 위험은 `impl-verify-reviewer` 에이전트. 다파일·다flow 골의 최종 통합 점검은
`impl-novelist` 에이전트(조건부, 맨 끝 1회). 리뷰어는 선언된 경로 + public
caller/producer/consumer/failure만 보고, 테스트를 *직접 실행*해 `PASS`/`NEEDS_CONTEXT`/이슈
bullet(path:line + repair 힌트)을 반환한다. JSON·해시·세션·model/effort provenance를 요구하지 않는다.

repair가 필요하면 원 owner에게 stable 이슈 + 최소 repair 범위를 보내고, 영향받은
selector·명령만 1회 재확인한다. acceptance·public contract·권한/데이터 동작·impact graph가
바뀌면 멈추고 새 승인 plan을 받는다.

## [1C] 누더기 거부 (FORCE)

슬라이스 밖 파일을 건드리거나 plan 의도를 넘는 신호(out-of-slice touch, 범위 초과)가 보이면
**멈추고 보고**한다. 우회해 impl 직행하지 않는다.

## 완료 조건

- 선언된 테스트/명령을 *실제로 실행*하고 결과를 확인한다.
- changed-path가 승인 범위의 exact paths 안에 머문다.
- public contract 변경이면 caller inventory를 다시 확인한다.
- 외부 작업·사용자 데이터·권한·DB/schema·concurrency·migration·external state 선택은 필요
  시 사용자 승인을 받는다.

구현자의 "완료" 선언이나 별도 artifact는 완료를 증명하지 않는다 — 실행된 테스트,
changed-path 확인, 조건부 risk predicate가 판정 근거다.
