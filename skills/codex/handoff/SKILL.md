---
name: handoff
description: "현재 작업 일부를 새 채팅으로 넘길 때 사용한다. “handoff”, “새 세션에서 하자”, “여기서 끊자”, “다음 세션에 넘길 거 정리해줘” 같은 요청이 해당한다. 같은 채팅의 압축 대비는 snapshot을 쓴다."
---

# Handoff

작업을 새 세션으로 넘길 때 쓰는 **task-scoped** 핸드오프 스킬. 산출물은 handoff
JSON 하나와, 그 JSON으로 부트스트랩되는 **새 스레드**다.

저장 위치: `<workspace>/.claude_context/handoff/<short-task-id>.json` (세션 스냅샷용
`sessions/`와 분리).

새 task 생성이 명시 요청되었고 범위가 닫혔으면 바로 수행한다. 분리 가능성을 묻는
발화만으로 생성하지 않는다. 기존 승인과 앱의 생성 조건을 먼저 확인한다.

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

- **같은 세션 /compact 직전 보존** → [snapshot](../snapshot/SKILL.md).
  새 세션에 독립된 작업을 넘기면 handoff, 같은 세션에서 압축 뒤 이어갈 우선순위를
  보존하면 snapshot이다. 둘 다 필요한 결정·미결·참조만 담으며 전체 대화를 덤프하지 않는다.
  cwd·env·dev 서버의 상태는 이 구분 기준이 아니며, 새 세션에 필요한 실행 전제는 별도로 확인한다.
- 그냥 이번 세션에서 계속 진행 가능 → handoff 불필요
- 영속 할 일 추가 → `todo`
- **한 todo의 맥락을 todo 일생 동안** 남기기 → `todo-ctx` 사이드카. 같은 JSON schema 가족이나 별개: handoff=세션 분리·프롬프트 有·age-out / todo-ctx=todo 일생·프롬프트 無·close시 삭제.

---

## Trigger Behavior

"새 세션 만들어서 넘겨"처럼 명시 요청이고 대상 작업이 정해졌으면 재확인 없이
저장·생성한다. "새 세션에서 하는 게 낫나?"처럼 제안이나 질문이면 현재 작업과
분리했을 때의 차이를 설명하고 생성 의사를 확인한다. 새 task가 사용자 소유인지
부모에게 결과를 반환하는지 정하고, 기존 독립 task의 no-report를 바꾸지 않는다.

---

## Workflow

### 1. Task Scope 확정

이미 명확하지 않으면 사용자에게 묻는다:

- **새 세션에서 정확히 무슨 작업?** (한 문장)
- **산출물은 뭐?** (코드 변경, 문서, 분석 결과, 보고 등)
- **종료 조건은 뭐?** (어떤 상태가 되면 done인지)

### 1a. 관련 미완료 작업

`.Codex/todos.md`가 있으면 인계 대상과 직접 관련된 항목만 확인해
`referenced_todos`로 연결한다. 이미 범위가 명확하면 전체 목록 선택 질문을 하지 않는다.
논의만 된 항목은 다음 작업의 완료에 필요할 때만 포함하고, 무관한 TODO·finding 생성이나
별도 점검 보고를 인계의 gate로 삼지 않는다. 새 목표를 조용히 추가하지 않는다.

### 2. 필요 컨텍스트 선별 + 분류

그 task에 정말 필요한 것만 골라서 분류:

| 카테고리 | 처리 방법 |
|---|---|
| 코드/문서에 이미 있는 사실 | **grep 경로·명령어만 기록. inline 절대 금지** |
| 사용자 결정 | 사용자가 실제로 쓴 문장을 `user_quote`로 인용. 자기 요약을 사용자 결정처럼 쓰지 않는다 |
| 현 세션에서 내려진 결정 | inline (이유 한 줄 포함) |
| 현재 진행 상태·우선순위 | 프로젝트에 진행 정본(단계 등록부·작업 DB·조회 명령)이 있으면 그 위치를 `must_read_first`나 `grep_pointers`에 둔다. 대화에서 정한 다음 순서는 그 정본과 맞는지 확인한 뒤 `session_decisions`에 적는다 |
| 미해결 unknowns | inline |
| 직접 확인하지 않은 추정 | `unverified`에 근거와 함께 적고 사실 필드에 섞지 않는다 |
| 과거 진단·해시·delivery ID·옛 전달문 | 넣지 않는다. 필요하면 조회 경로만 `grep_pointers`에 둔다 |
| 안전 제약 | inline. 작성 시점의 일시 상태(서버 중지·보류 등)를 조건으로 쓸 때는 지금 사실인지와 새 세션이 확인할 방법을 함께 적는다 |
| 이미 시도해서 막힌 길 | inline (재시도 방지) |
| 사용자 선호 | 짧게 inline 또는 memory 위치 지시 |
| 새 세션이 처음부터 지켜야 할 작업 규칙 | `rules_from_start`에 짧게. 정본 문서가 있으면 경로만 |

**원칙: inline은 적을수록 좋다.** 코드·문서 grep으로 도달 가능한 사실은 무조건
grep 지시로. 새 세션 Codex가 cold start 시 `rg`/`Read`로 직접 가져온다.

JSON을 쓰기 직전에 인계 범위의 최근 대화를 다시 훑어, 앞선 결론을 뒤집은 사용자 정정과
결정이 빠지지 않았는지 확인한다. 인계 범위의 작업이 여러 채팅에 걸쳐 있으면 해당 채팅의
최근 결정도 같은 기준으로 본다. 새 세션이 폐기된 순서를 다시 잡는 가장 흔한 원인이 이 누락이다.

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
    {"decision": "...", "reason": "...", "user_quote": "사용자 원문(사용자 결정일 때만)"}
  ],
  "open_unknowns": ["..."],
  "unverified": [{"claim": "...", "basis": "..."}],
  "rules_from_start": ["..."],
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

생성 전에 `list_threads`로 원본 채팅의 ID·프로젝트·고정 여부·사이드바 섹션과
바로 다음 항목을 확인한다. 인계 유형에 따른 사이드바 승계 기준과 적용 절차는
4.6을 따른다.

#### 4a. target 결정

`list_projects`로 현재 workspace에 해당하는 project를 찾고 `projectId`와
`isGitRepository`를 읽는다. 도구 인자는 기억으로 쓰지 말고 로드된 스키마를 확인해
맞춘다.

| 상황 | target |
|---|---|
| 등록된 project, git repo, 새 브랜치/격리 필요 | `{type:"project", projectId, environment:{type:"worktree", ...}}` |
| 등록된 project, 같은 체크아웃에서 계속 | `{type:"project", projectId, environment:{type:"local"}}` |
| project 미등록 | `{type:"projectless", directoryName:"<작업 폴더>"}` |

cwd·env는 이 target 선택으로 넘어간다 — 프롬프트에 경로 이동 지시를 쓰지 않는다.
예외는 *새로 만든 워크트리*의 gitignored 런타임 파일(`.env.local` 등)뿐이며, 그때만
"메인에서 복사" 한 줄을 프롬프트에 넣는다.

#### 4b. model / thinking 명시

`create_thread` 호출에 `model`과 `thinking`을 **반드시 명시**한다. 값은 호출 직전에
라우팅 정본에서 읽는다: 사용자 명시 지시 → 프로젝트 role/model 계약 → 전역
`~/.codex/rules/model-routing.json`. **이 문서에 모델 ID를
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

작업 끝나면(JSON의 `done_when` 충족 시) 완료한 `referenced_todos` 항목을
`.Codex/todos.md`에서 `[x]`로 갱신하고, 이 handoff JSON은 삭제해.
```

프롬프트는 짧고 구체적으로. JSON 내용을 다시 inline으로 풀어 쓰지 않고, 이전 세션의
대화 요약도 넣지 않는다.

`referenced_todos`가 있으면 프롬프트에 한 줄 추가:
> *"`.Codex/todos.md`의 #001, #007 항목과 연결된 작업이야. 그 항목들도 같이 surface해."*

`title`은 task summary 기반 짧은 라벨로 준다.

### 4.5 생성과 실행 구분

JSON 저장은 인계 준비이고, clientThreadId는 생성 접수다. 실제 task ID와 상태가
확인되기 전 실행 중이라고 말하지 않는다. 생성 지연·실패는 기존 앱 상태/조회로
확인하고, 동일 요청을 중복 생성하지 않는다. 사용자 요청이 생성까지면 생성 상태를
보고하고 끝낼 수 있다. 계속 실행·완료까지 맡긴 요청이면 현재 owner가 실행 확인과
결과 회수 책임을 유지한다; 인계 파일 수정만으로 그 목표를 완료 처리하지 않는다.
사용자 소유 독립 task의 no-report는 유지하며 상태 확인을 보고 의무로 바꾸지 않는다.

### 4.6 사이드바 위치 이전

현재 세션을 대체해 새 세션에서 이어가는 인계는 **원본의 고정 상태와 위치 승계를
기본으로 수행**한다. "핸드오프하고 새 세션에서 다음 런 가자", "여기서 끊고 새 세션에서
이어서 하자"처럼 진행을 넘기는 요청에 별도의 사이드바 이전 지시를 요구하지 않는다.
일부 작업만 별도로 맡기고 원본 작업도 계속하는 **병행 작업 분리**는 원본의 고정·위치를
유지한다. 사용자가 고정 유지·해제나 다른 위치를 명시하면 그 지시를 우선한다.

승계는 실제 새 `threadId`가 확인된 뒤 적용한다. 생성 실패·접수만 된 상태에서는
원본을 고정 해제하거나 이동하지 않는다.

1. 원본이 고정됐다면 `move_thread_to_sidebar_section`으로 새 채팅을 `pinned`에
   넣고 원본 바로 앞에 배치한다(`beforeThreadId=원본 ID`). 이어 원본만 기본
   섹션으로 옮겨 고정 해제한다. 사용자 지정 섹션도 같은 방법으로 자리를 넘긴다.
2. 원본이 고정되지 않았다면 새 채팅을 임의 고정하지 않는다. 원본 프로젝트·섹션과
   수동 정렬이 지원하는 위치를 유지한다. 사용자가 별도 위치를 지정하면 그것을 따른다.
3. `list_threads`로 새 채팅의 고정·섹션·인접 항목과 원본 고정 해제를 확인한다.
   자동 정렬이나 도구 제한으로 정확한 위치를 보존할 수 없으면 가능한 배치만
   적용하고 제한을 알린다. 이를 위해 전체 사이드바 정렬 설정을 바꾸지 않는다.

원본 채팅 보관·삭제는 별도 요청이 있을 때만 한다. 원본에 연결된 예약이 있으면
인계 범위의 예약만 확인한다. 미완료 예약은 새 채팅으로 대상을 이전하며 중복을
만들지 않고, 이미 완료·PAUSED인 예약은 재개하지 않는다.
프로젝트가 서버 routing처럼 채팅 ID를 담당으로 저장하면 그 이전도 인계 범위다.
예약 대상과 routing을 옮긴 뒤 다시 조회해 새 채팅을 가리키는지 확인하고, 옮기지
못했으면 인계 진행 중으로 보고한다. 예약 프롬프트에 과거 경위가 쌓여 있으면
`~/.codex/rules/thread-orchestration.md`의 정기 예약 프롬프트 기준으로 새 담당이
다시 쓰게 한다.

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
| JSON만 저장하고 스레드는 사용자에게 떠넘김 | 명시 요청 확인 후 `create_thread`까지 수행 |
| 새 스레드에 이전 대화 요약·히스토리 주입 | JSON + 역할 + POU 진입점만 |
| model·thinking 생략하거나 본문에 모델 ID 하드코딩 | 호출 시 명시하되 값은 라우팅 정본에서 |
| snapshot과 혼동해 풀 dump | 새 세션 인계는 handoff, 같은 세션 압축 대비는 snapshot. 둘 다 필요한 맥락만 보존 |
| 생성 접수/인계 파일을 실행 완료로 보고 | 실제 task 상태와 목표 결과를 구분 |
| 추정을 사실처럼 적음("미완료 패치가 X에 있다") | `unverified`에 근거와 함께 |
| 인계 문장을 사용자 결정 인용으로 씀 | 사용자 원문만 `user_quote` |

---

## Safety

- 쿠키, 토큰, 비밀번호, 개인키 절대 금지. 위치/갱신 방법만 언급.
- 사용자/사번/책임자/참석자 이름은 role 라벨로.
- private repo에 들어가도 안전한 수준만 담는다.
- live ERP 쓰기·결재는 기존 승인의 대상·범위·유효성을 확인하고, 빠진 권한이나 달라진 효과만 새로 확인한다.

---
