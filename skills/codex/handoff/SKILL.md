---
name: handoff
description: |
  Split part of the current session's work into a **new session** by capturing only the *minimal* context that specific task needs as JSON, then create that session directly with `create_thread` and bootstrap it from the JSON.

  Trigger on these natural-language cues (confirm with the user first before saving or creating anything — see body):
  - "이거 새 세션에서 하는 게 낫지 않을까", "다음 세션에서 마저 하자"
  - "여기서 끊자", "별도 세션으로 빼자", "이거 길어질 것 같으니까 나눠서"
  - "handoff 만들어", "다음 세션에 넘길 거 정리해줘", "새 세션 만들어서 넘겨"

  For same-session preservation right before `/compact`, use the `snapshot` skill — do not confuse them. To add a persistent to-do, use `todo`.
---

# Handoff

작업을 새 세션으로 넘길 때 쓰는 **task-scoped** 핸드오프 스킬. 산출물은 handoff
JSON 하나와, 그 JSON으로 부트스트랩되는 **새 스레드**다.

저장 위치: `<workspace>/.claude_context/handoff/<short-task-id>.json` (세션 스냅샷용
`sessions/`와 분리).

**즉시 저장·즉시 스레드 생성 금지 — 먼저 확인** (아래 §Trigger Behavior 대사 그대로 사용).

**cold start + JSON 부트스트랩이지 대화 이어붙이기가 아니다.** 새 스레드는 현재
세션의 대화 히스토리를 물려받지 않는다. fork가 아니다. 넘어가는 것은 오직 handoff
JSON과 그것을 읽으라는 짧은 프롬프트뿐이다. 대화 맥락이 필요하면 그 맥락을 JSON
필드로 옮기고, 그래도 안 되면 handoff 대상이 아니다.

---

## When to use

- 현 세션에서 일부 작업만 **다른 세션으로 분리**할 때
- 사용자가 "이거 새 세션에서 마저 하자" 같이 split 의향을 보일 때
- 명시적 "handoff" 요청

## When NOT to use

- **같은 세션 /compact 직전 보존** → `snapshot`. 판별 기준은 환경이 아니라 **대화
  맥락**이다. `create_thread`가 프로젝트·워크트리를 지정하므로 cwd·env는 새 스레드가
  이어받는다(살아 있는 dev 서버·터미널 상태는 여전히 안 따라온다). 그러니
  *현재까지의 대화 흐름 없이 JSON만으로 성립하면* handoff, 그 흐름 자체를 남겨야
  이어갈 수 있으면 snapshot.
- 그냥 이번 세션에서 계속 진행 가능 → handoff 불필요
- 영속 할 일 추가 → `todo`
- **한 todo의 맥락을 todo 일생 동안** 남기기 → `todo-ctx` 사이드카. 같은 JSON schema 가족이나 별개: handoff=세션 분리·프롬프트 有·age-out / todo-ctx=todo 일생·프롬프트 無·close시 삭제.

---

## Trigger Behavior — 절대 즉시 저장 금지

사용자가 task split을 시사하는 발화를 했을 때:
- "이거 새 세션에서 하는 게 낫나?"
- "다음 세션에서 이어가자"
- "여기서 끊고 별도로"

→ **즉시 저장하거나 스레드를 만들지 말고 먼저 확인:**

```
handoff 스킬 구동할까요? 새 세션에서 어떤 작업 하실 건지 알려주시면
그에 맞는 컨텍스트만 골라서 JSON으로 남기고, 그 JSON을 읽는 새 스레드까지
제가 바로 만들어 드릴게요.
```

사용자 동의 → 진행. 거부/모호 → 그냥 답변 계속. **사용자 동의 없이 스레드를 만들지
않는다.**

---

## Workflow

### 1. Task Scope 확정

이미 명확하지 않으면 사용자에게 묻는다:

- **새 세션에서 정확히 무슨 작업?** (한 문장)
- **산출물은 뭐?** (코드 변경, 문서, 분석 결과, 보고 등)
- **종료 조건은 뭐?** (어떤 상태가 되면 done인지)

### 1a. open todo surface

`.Codex/todos.md` 존재 시 open 항목(`[ ]`) 목록을 사용자에게 보임. **줄에 공유 grep
토큰(예 `(cp949-sweep)`)으로 묶인 게 보이면 단위로 묶어** 보임:

> *"열린 todo: (cp949-sweep) [#014, #015, #016], 무묶음 [#009] — 다음 세션으로 가져갈 거? (묶음 전체 'cp949-sweep' 또는 #N 콤마, 없으면 'skip')"*

사용자 답 → `referenced_todos: ["#014", "#015"]` JSON 필드 (단위 일부만도 가능). 없으면 필드 생략.

**입자 분리 유지**: handoff가 todo를 *만들지는 않음*. 참조만. 신규 todo 생성은 todo 스킬 책임.
**status 저장 금지**: handoff는 단위 status를 어디에도 쓰지 않는다 — 새 세션이 끝낸 todo를 close하면 단위 진척은 자동 재파생.

### 1b. orphan check

산출물 정리 직전, 이번 세션에서 *논의·언급만 되고 어디에도 박히지 않은 항목*이
있는지 스스로 점검한다. handoff 발동 시점엔 세션 컨텍스트가 살아 있으니 그것을
그대로 읽고 판단. 발견 시 사용자에게 출처 라벨([self] / [user-deferred]) 붙여
표로 surface하고 4분기 제시:

- (a) todo 등재
- (b) 현재 산출물(handoff JSON)에 포함
- (c) subagent 즉시 위임 — "단일 파일·독립 실행 가능·세션 문맥 불필요" 셋 다 만족 시 우선 제안
- (d) discard (의도적 종결)
- (e) **finding 졸업** — 코드가 못 담는 *영속* 외부시스템 지식(막힘/우회·시도했으나 실패)이면 `/finding`(`docs/findings/`). 아래 §3 `do_not_redo`의 *영속 부분*이 전형(handoff JSON은 휘발→부트스트랩 후 stale이라, 영속 사실은 거기 두면 같이 죽음). **surface→제안만, silent write X** (todo-ctx 졸업과 동일 경계).

[self] 항목(AI가 plan/spec 쓰면서 분리한 후속)만 있으면 "정말 필요한가요?" 묻고
보통 종결 권유. 결정 자체는 끝났는데 형식 후속만 남은 항목은 그 사실 명시
("결정 완료, status 갱신만").

### 2. 필요 컨텍스트 선별 + 분류

그 task에 정말 필요한 것만 골라서 분류:

| 카테고리 | 처리 방법 |
|---|---|
| 코드/문서에 이미 있는 사실 | **grep 경로·명령어만 기록. inline 절대 금지** |
| 현 세션에서 내려진 결정 | inline (이유 한 줄 포함) |
| 미해결 unknowns | inline |
| 안전 제약 | inline |
| 이미 시도해서 막힌 길 | inline (재시도 방지) |
| 사용자 선호 | 짧게 inline 또는 memory 위치 지시 |

**원칙: inline은 적을수록 좋다.** 코드·문서 grep으로 도달 가능한 사실은 무조건
grep 지시로. 새 세션 Codex가 cold start 시 `rg`/`Read`로 직접 가져온다.

### 3. JSON 작성

저장 위치: `<workspace>/.claude_context/handoff/<short-task-id>.json`

```json
{
  "kind": "handoff",
  "created_at_local": "YYYY-MM-DDTHH:MM:SS+09:00",
  "workspace": "absolute path",
  "tool_origin": "Codex",
  "next_task": {
    "summary": "한 문장",
    "deliverable": "산출물",
    "done_when": "종료 조건"
  },
  "must_read_first": [
    {"path": "src/foo.py", "why": "X 함수 구조 확인"},
    {"path": "knowledge/erp/Y.md", "why": "Z 정책"}
  ],
  "grep_pointers": [
    {"cmd": "rg -n 'pattern' src/", "why": "기존 구현 위치"},
    {"cmd": "rg 'X' knowledge/", "why": "관련 정책"}
  ],
  "session_decisions": [
    {"decision": "...", "reason": "..."}
  ],
  "open_unknowns": ["..."],
  "safety_constraints": ["..."],
  "do_not_redo": ["이미 시도해서 막힌 길"],
  "referenced_todos": ["#001", "#007"]
}
```

작성 절차:
1. `.claude_context/handoff/` 디렉토리 없으면 생성
2. 같은 task-id 파일이 존재해도 그냥 덮어쓰기 (handoff는 휘발성·1회용 — 부트스트랩 후 stale)
3. UTF-8, indent=2로 작성
4. 작성 후 다시 읽어 JSON 파싱 확인

### 4. 새 스레드 생성 (`create_thread`)

JSON 저장이 끝나면 **직접** 새 스레드를 만든다. 사용자에게 프롬프트를 복사시키지
않는다. 도구가 안 보이면 `tool_search`로 스레드 도구를 먼저 로드한다.

#### 4a. target 결정

`list_projects`로 현재 workspace에 해당하는 project를 찾고 `projectId`와
`isGitRepository`를 읽는다. 도구 인자는 기억으로 쓰지 말고 로드된 스키마를 확인해
맞춘다.

| 상황 | target |
|---|---|
| 등록된 project, git repo, 새 브랜치/격리 필요 | `{type:"project", projectId, environment:{type:"worktree", ...}}` |
| 등록된 project, 같은 체크아웃에서 계속 | `{type:"project", projectId, environment:{type:"local"}}` |
| project 미등록 / repo 아님 | `{type:"projectless", directoryName:"<작업 폴더>"}` |

cwd·env는 이 target 선택으로 넘어간다 — 프롬프트에 경로 이동 지시를 쓰지 않는다.
예외는 *새로 만든 워크트리*의 gitignored 런타임 파일(`.env.local` 등)뿐이며, 그때만
"메인에서 복사" 한 줄을 프롬프트에 넣는다.

#### 4b. model / thinking 명시

`create_thread` 호출에 `model`과 `thinking`을 **반드시 명시**한다. 값은 호출 직전에
라우팅 정본에서 읽는다: 사용자 명시 지시 → 프로젝트 role/model 계약 → 전역
`~/.codex/rules/model-routing.json` 및 활성 `plan`/`impl` 계약. **이 문서에 모델 ID를
적지 않는다.** 어떤 역할로 넘기는지(계획/진단/통합 리드인지 one-slice 실행자인지)를
먼저 정하고, 그 역할에 해당하는 route를 그대로 쓴다.

#### 4c. 첫 프롬프트 = JSON 경로 + 역할 + POU 진입점

새 스레드는 대화 맥락이 아니라 **point-of-use 계약**으로 역할을 받는다. 프롬프트는
반드시 이 셋을 담는다:

1. **handoff JSON 경로** — `.claude_context/handoff/<id>.json`
2. **새 세션이 맡을 역할** — 한 문장 (예: "이 슬라이스의 구현 담당")
3. **그 역할의 POU 진입점** — 프로젝트에 역할 crosswalk(`AGENTS.md` 등)가 있으면 그
   파일을 가리키고 "거기서 이 역할 계약을 읽어라"라고 지시한다. crosswalk가 없으면
   역할만 명시하고 없다는 사실을 적는다.

형식 예시:

```
[task summary]를 진행해. 이 세션의 역할은 [역할 한 문장]이다.

먼저 `.claude_context/handoff/<id>.json` 읽어줘. must_read_first 경로와
grep_pointers 명령어가 있으니 그것부터 확인하고 컨텍스트 적재 끝나면
[첫 단계]부터 시작하면 돼. `do_not_redo`에 있는 건 다시 시도하지 마.

역할 계약은 [crosswalk 경로]에서 읽어라. (crosswalk 없으면 이 줄 생략)

작업 끝나면(JSON의 `done_when` 충족 시) 끝낸 `referenced_todos` 항목을 커밋
메시지에 `closes todo #NNN`으로 닫고, 이 handoff JSON은 삭제해.
```

프롬프트는 짧고 구체적으로. JSON 내용을 다시 inline으로 풀어 쓰지 않고, 이전 세션의
대화 요약도 넣지 않는다.

`referenced_todos`가 있으면 프롬프트에 한 줄 추가:
> *"`.Codex/todos.md`의 #001, #007 항목과 연결된 작업이야. 그 항목들도 같이 surface해."* (단, SessionStart hook이 이미 모든 open todo inject하므로 중복일 수 있음 — 짧게)

`title`은 task summary 기반 짧은 라벨로 준다.

### 4.5 execution trace (FORCE)

§5 출력 *직전*, 위 단계 중 건너뛰기 쉬운 것의 **결과를 한 줄씩** 먼저 출력한다. 빈
체크박스(`[ ]`)가 아니라 *결과 기입형* — 결과가 없으면(`skip`/`해당없음`) 그 이유도 한 줄.
trace 없이 JSON·스레드 생성으로 직행 금지 (이게 단계 skip 차단의 본체 — 산문 지시가 아니라
증거 강제, methodos 게이트 "Evidence (FORCE)"와 동일 정신).

```
- [x] 1a open todo surface: <surface한 항목 → referenced_todos 결과, 또는 todos.md 없음/skip>
- [x] 1b orphan check: <발견 항목+출처라벨+분기, 또는 orphan 없음>
```

결과 칸이 비어 보이면 그 단계를 안 한 것 — 모델 자신과 사용자 양쪽이 즉시 포착한다.

### 5. 사용자에게 출력

최종 응답에 다음만 간결히 보고한다:

- 저장 경로 `.claude_context/handoff/<id>.json`
- 생성된 스레드의 제목, 선택한 model·thinking과 그 근거(어느 라우팅 정본을 따랐는지)
- 새 세션이 맡은 역할과 POU 진입점

생성이 성공하면 그 응답에 `::created-thread{threadId="..."}`를 한 줄로 emit한다.
워크트리 준비가 진행 중이라 `clientThreadId`만 돌아왔으면
`::created-thread{clientThreadId="..."}`를 대신 쓴다.

프롬프트 본문을 복사용 코드블록으로 다시 내보내지 않는다 — 이미 스레드에 주입됐다.
생성이 실패했을 때만 프롬프트 본문을 fenced code block(언어 태그 없이 ` ``` `)으로
보여주고 수동 시작을 안내한다.

---

## Anti-patterns

| 안티패턴 | 대신 |
|---|---|
| 사용자 발화·AI 응답을 통째로 옮김 | task에 필요한 결정만 inline |
| 이미 코드에 있는 정보 inline | grep 명령어만 기록 |
| task scope 모호한데 그냥 진행 | 묻기 |
| JSON만 저장하고 스레드는 사용자에게 떠넘김 | 동의 확인 후 `create_thread`까지 수행 |
| 새 스레드에 이전 대화 요약·히스토리 주입 | JSON + 역할 + POU 진입점만 |
| model·thinking 생략하거나 본문에 모델 ID 하드코딩 | 호출 시 명시하되 값은 라우팅 정본에서 |
| snapshot과 혼동해 풀 dump | handoff는 lean, 풀 dump는 snapshot |
| 1a/1b 건너뛰고 JSON·프롬프트 직행 | §4.5 execution trace로 단계 결과 강제 출력 |

---

## Safety

- 쿠키, 토큰, 비밀번호, 개인키 절대 금지. 위치/갱신 방법만 언급.
- 사용자/사번/책임자/참석자 이름은 role 라벨로.
- private repo에 들어가도 안전한 수준만 담는다.
- live ERP 쓰기·결재 작업은 handoff 후 새 세션에서도 fresh 확인 필요.

---

## CONV-GATE 위임

매핑 정본 → [`mine/CONV-GRAPH.md`](../../CONV-GRAPH.md).

- `create_thread` 호출 직전 → [WHAT/HOW] 분리 (사용자 체감 시나리오로 핸드오프 형식 강제)

신규 시점 추가 시 CONV-GRAPH.md 매핑 표 한 줄 갱신.
