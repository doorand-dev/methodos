# todo 스킬 — 설계·WHY (METHODOLOGY)

코어 동작은 [SKILL.md](SKILL.md). 이 파일은 *왜 이렇게 설계됐나* — 설계·변경할 때만 읽음.
정본 WHY는 ADR; 여기는 운영-수준 합성 + 백링크.

## 관련 todo 묶음 — 산문 공유 토큰 (관련 설계 결정, @unit 강등 관련 설계 결정)

여러 todo가 한 덩어리(버그 sweep·정리·한 기능)일 때 **줄에 공유 grep 토큰**을 박아 묶는다
(예 `(roi8)`·`(sources-decomp)`). 별도 roadmap/status 문서 만들지 않는다.

- **status는 저장 말고 파생** (관련 설계 결정 핵심): `rg '<토큰>' .claude/todos.md` 후 `[x]`
  카운트. status 컬럼/표/README 저장 금지 (저장 = todos와 drift). 파생값은 X/N 체크리스트일
  뿐 "holistically done" 아님 — `[ ]`도 미close일 수 있음(directive 누락·세션외·revert), 의심 시 수동 확인.
- **`@unit:slug` 전용 문법 폐기 (관련 설계 결정)**: 클러스터-식별은 결국 *공유 grep 토큰*이라
  grep앵커 원칙의 한 사례로 흡수됨. 산문 토큰이 동일하게 grep·카운트됨 (youtube 실증:
  `(ROI#8)`로 이미 묶음, @unit은 0건). 전용 문법은 ceremony였음 — 단, "status 파생·별도
  문서 금지" *원칙*은 위에 유지.

## 린 줄 + todo-ctx 사이드카 (관련 설계 결정, 강등 관련 설계 결정)

todo 줄 = 린 인덱스. 맥락(왜·시도·관점·결정·grep)이 ~3줄 넘으면 opt-in 사이드카로.

- 위치 `.claude/todo-ctx/NNN.json` (경로는 `#NNN` 규약 파생, 줄에 저장 X). 포맷 =
  handoff schema − {prompt, first_step} = `{decisions, perspectives, grep_pointers, do_not_redo}`.
- **disjoint 가드**: 사이드카에 구조 필드(status·dep·cluster) 재기재 금지 → drift 구조적 불가.
- **opt-in, 강제 없음 (관련 설계 결정)**: nudge 훅(todo-ctx-nudge) *드롭* — 헤더 줄만 측정해
  자식불릿 벽을 구조적으로 못 잡았고, point-of-use 헤더 규약이 더 나은 예방 레버. 사이드카는
  *유지+강등*: 휘발 작업맥락은 findings(관련 설계 결정)/handoff가 안 덮는 고유 영역이라 삭제 X
  ("잉여" 아니라 "미채택").
- **close 졸업**: 영속 *결정* → ADR(`decision`), 영속 *사실* → finding(`/finding`, 관련 설계 결정)
  로 졸업 *후* 사이드카 삭제. (휘발 맥락=사이드카, 영속=ADR/finding.) `gc`가 (`#NNN [x]`)
  또는 (`#NNN 줄 부재`)일 때 삭제.

> handoff JSON과 같은 schema 가족이나 별개 트리거·수명: handoff=세션 분리(프롬프트 有,
> age-out) / todo-ctx=todo 일생(프롬프트 無, close시 삭제).

## point-of-use enforcement — 헤더가 레버 (관련 설계 결정)

규약은 *쓰는 자리*에 있어야 따라진다. 사람/AI는 todo 추가 시 SKILL.md를 다시 안 읽고
todos.md를 본다. 증거 [추정 n=2]: 헤더에 있는 `#NNN`·형식은 따라지고, SKILL.md-only 규약은
안 따라진다 (youtube 자식불릿 벽 = 그 파일 헤더의 `(SKILL)` 태그를 따른 것). → 포맷 규약을
todos.md 헤더로 이주(SKILL.md lazy생성이 emit). grep앵커·finding 막힘과 같은 point-of-use 원칙.

## grep 발견성 — 미래 세션의 자연 grep에 걸리게 (관련 설계 결정)

todo 회상 경로 = SessionStart 덤프가 아니라 *작업 중 모델이 치는 grep*. 새 작업 받으면 어차피
코드를 grep → 줄에 실제 식별자(심볼·파일경로·에러문자열) 박혀 있으면 관련 todo가 덤으로 걸림
(관련성=모델 몫, hook 퍼지매칭 X — 오탐·judge-to-regex 회피). 작성 세션은 그 식별자를 막 본
참이라 비용 0. grep 스코프가 `.claude/`(todos.md + todo-ctx/)를 포함해야 함.

## 의존·우선순위·합성회상·정비 (관련 설계 결정)

- **의존 = 산문 한 줄**("#012 끝나고"). `@after:#MMM` 전용 문법 폐기 (관련 설계 결정) — grep로
  읽힘. **우선순위·순서 = 저장 X**(생성 때 모름) → 합성회상 시점 AI 제안·사용자 확정.
- **합성회상**: 매 세션 X. 핸드오프가 세션 *안 끌 때*(첫 메시지 막연) 또는 명시 호출 시만.
  `{열린 todo + 최근커밋}`로 "최근·중요도·순서" 제안, ctx는 고른 것만 lazy. 스코프됨
  (관련 설계 결정 — 전체 재랭킹 X).
- **정비(triage)** = full 검토(rot 방지): "정비하자" 또는 열린 todo ~15건+ 넛지. *가치
  검토*(유효·중복·우선순위)지 기계적 재포맷 아님.
- **마이그레이션**: 기존 todo 강제 전환 X. 린=유지, 비대=convert-on-touch(다음에 그 todo
  작업할 때 린화).

## 보류 1턴 대기 WHY (관련 설계 결정)

보류 발화는 자주 발생하지만 *모든 게 todo 가치* 아님 — 흘려보낼 것도 많다. 1턴 사용자 확인 =
false positive 방지. (코어가 강제하는 동작, WHY는 여기.)

---

## 관련 ADR

- [0014] todo 단일 작업 layer
- [0017] scoped (합성회상 전체 재랭킹 X)
- [0019] 단위·파생status·close넛지
- [0020] 린줄·사이드카·grep발견성·합성회상
- [0024] finding 졸업처
- [0026] 경량화(@unit/@after 폐기·nudge 드롭·헤더 이주·이 분리)
