---
name: handoff
description: >
  현재 세션의 작업 일부를 **새 세션으로 넘기기** 위해, 그 특정 task에 필요한
  *최소* 컨텍스트만 골라 self-contained 스폰 프롬프트로 합성한다. 지금 시작 가능한
  작업은 spawn_task 칩으로 새 세션을 띄우고(현재 체크아웃 — 워크트리 아님, 파일 미저장),
  지금 스폰 불가(입력대기·인간게이트·사용자가 나중에 직접 이어감)면 칩 대신
  프로젝트 `HANDOFF.md`에 그 프롬프트를 기록한다.

  세션 전체 상태를 다 옮기지 않는다 — 새 세션이 *그 task*를 시작하는 데 필요한
  것만 선별하고, 이미 코드·문서에 있는 사실은 grep 경로/명령어만 남긴다.

  다음 자연어 트리거에서 **즉시 저장하지 말고 사용자에게 먼저 확인**:
  - "이거 새 세션에서 하는 게 낫지 않을까", "다음 세션에서 마저 하자"
  - "여기서 끊자", "별도 세션으로 빼자", "이거 길어질 것 같으니까 나눠서"
  - "handoff 만들어", "다음 세션에 넘길 거 정리해줘", "새 세션 시작 프롬프트"

  사용자에게 먼저 "handoff 스킬 구동할까요? 새 세션에서 어떤 작업을 할지 알려주시면 그 task에 맞는 컨텍스트만 골라 self-contained 스폰 프롬프트로 합성하겠습니다"라고 확인하고 동의받은 뒤 진행.

  같은 세션 내 `/compact` 직전 보존용은 `snapshot` 스킬 — 헷갈리지 말 것.
  영속 할 일 추가는 `todo`.
---

# Handoff

작업을 새 세션으로 넘길 때 쓰는 **task-scoped** 핸드오프 스킬. 핵심 산출은
self-contained 스폰 프롬프트다. 전달 방식은 둘 — 지금 시작 가능하면 **spawn_task 칩**
(현재 체크아웃에 새 세션, 파일 미저장), 지금 스폰 불가면 그 프롬프트를 프로젝트
**`HANDOFF.md`**에 기록(§5b).

**spawn_task는 격리 워크트리를 만들지 않는다** — 현재 체크아웃에 새 세션을 띄운다
(2026-06-13 실측: `git-dir`==`git-common-dir`, `.git`=디렉터리, `worktree list` 단일 엔트리).
그래서 새 세션은 *같은 working tree*를 공유한다 — uncommitted 편집·gitignored 런타임
파일이 그대로 보인다. (도구 설명의 "fresh worktree" 문구는 이 로컬 하네스와 안 맞음.)

---

## When to use

- 현 세션에서 일부 작업만 **다른 세션으로 분리**할 때
- 사용자가 "이거 새 세션에서 마저 하자" 같이 split 의향을 보일 때
- 명시적 "handoff" 요청

## When NOT to use

- **같은 세션 /compact 직전 보존** → `snapshot`. 판별: 새 세션은 cwd·env·dev 서버를 못 물려받으니 — *시작 프롬프트에 환경 전제조건을 적어줘야 하면* handoff, 환경이 그대로 살아있어 "읽고 이어가" 한 줄이면 snapshot.
- 그냥 이번 세션에서 계속 진행 가능 → handoff 불필요
- 영속 할 일 추가 → `todo`
- **한 todo의 맥락을 todo 일생 동안** 남기기 → `todo-ctx` 사이드카 (관련 설계 결정). 별개다: handoff=세션 분리·spawn_task 칩으로 스폰·프롬프트 有·파일 미저장 / todo-ctx=todo 일생·프롬프트 無·close시 삭제.

---

## Trigger Behavior — 절대 즉시 저장 금지

사용자가 task split을 시사하는 발화를 했을 때:
- "이거 새 세션에서 하는 게 낫나?"
- "다음 세션에서 이어가자"
- "여기서 끊고 별도로"

→ **즉시 저장하지 말고 먼저 확인:**

```
handoff 스킬 구동할까요? 새 세션에서 어떤 작업 하실 건지 알려주시면
그에 맞는 컨텍스트만 골라 self-contained 스폰 프롬프트로 합성해 — 지금 시작 가능하면
spawn_task 칩으로 띄우고, 스폰 불가(입력대기·인간게이트)면 HANDOFF.md로 남길게요.
```

사용자 동의 → 진행. 거부/모호 → 그냥 답변 계속.

---

## Workflow

### 1. Task Scope 확정

이미 명확하지 않으면 사용자에게 묻는다:

- **새 세션에서 정확히 무슨 작업?** (한 문장)
- **산출물은 뭐?** (코드 변경, 문서, 분석 결과, 보고 등)
- **종료 조건은 뭐?** (어떤 상태가 되면 done인지)

### 1a. open todo surface (관련 설계 결정)

`.claude/todos.md` 존재 시 open 항목(`[ ]`) 목록을 사용자에게 보임. **줄에 공유 grep
토큰(예 `(cp949-sweep)`)으로 묶인 게 보이면 단위로 묶어** 보임 (관련 설계 결정, 산문토큰 관련 설계 결정):

> *"열린 todo: (cp949-sweep) [#014, #015, #016], 무묶음 [#009] — 다음 세션으로 가져갈 거? (묶음 전체 'cp949-sweep' 또는 #N 콤마, 없으면 'skip')"*

사용자 답 → 스폰 프롬프트의 `referenced_todos` 줄 (예 `#014, #015`, 단위 일부만도 가능). 없으면 생략.

**입자 분리 유지**: handoff가 todo를 *만들지는 않음*. 참조만. 신규 todo 생성은 todo 스킬 책임.
**status 저장 금지**: handoff는 단위 status를 어디에도 쓰지 않는다 — 새 세션이 끝낸 todo를 close하면 단위 진척은 자동 재파생 (관련 설계 결정).

### 1b. orphan check

산출물 정리 직전, 이번 세션에서 *논의·언급만 되고 어디에도 박히지 않은 항목*이
있는지 스스로 점검한다. handoff 발동 시점엔 세션 컨텍스트가 살아 있으니 그것을
그대로 읽고 판단. 발견 시 사용자에게 출처 라벨([self] / [user-deferred]) 붙여
표로 surface하고 4분기 제시:

- (a) todo 등재
- (b) 스폰 프롬프트에 포함
- (c) subagent 즉시 위임 — "단일 파일·독립 실행 가능·세션 문맥 불필요" 셋 다 만족 시 우선 제안
- (d) discard (의도적 종결)
- (e) **finding 졸업** — 코드가 못 담는 *영속* 외부시스템 지식(막힘/우회·시도했으나 실패)이면 `/finding`(`docs/findings/`). 아래 §3 `do_not_redo`의 *영속 부분*이 전형(스폰 프롬프트는 1회 소비 휘발이라, 영속 사실은 거기 두면 같이 죽음). **surface→제안만, silent write X** (관련 설계 결정 결정6 = todo-ctx 졸업과 동일 경계).

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
grep 지시로. 새 세션 Claude가 cold start 시 `rg`/`Read`로 직접 가져온다.

### 3. 스폰 페이로드 합성 (in-memory, 파일 미저장)

아래 필드를 *메모리에서* 조립해 §4 스폰 프롬프트로 fold한다 — **JSON 파일로 쓰지 않는다.**
능동 칩 경로는 self-contained 프롬프트가 곧 페이로드라, 파일은 잉여다. 중간 산물도 파일로
영속화하지 않는다 (단일 소스: 파일 0).

조립할 필드 (구조 참고 — 이건 *프롬프트 내용*이지 디스크 레코드가 아님):

```
next_task:          { summary: 한 문장, deliverable: 산출물, done_when: 종료 조건 }
must_read_first:    [ {path: src/foo.py, why: X 함수 구조 확인}, ... ]
grep_pointers:      [ {cmd: "rg -n 'pattern' src/", why: 기존 구현 위치}, ... ]
session_decisions:  [ {decision: ..., reason: ...}, ... ]
open_unknowns:      [ ... ]
safety_constraints: [ ... ]
do_not_redo:        [ 이미 시도해서 막힌 길 ]
referenced_todos:   [ #001, #007 ]
```

**경로 권장 (cwd-상대)** — `must_read_first`/`grep_pointers`는 **cwd-상대 경로·rg 명령**으로
쓴다. 칩은 같은 체크아웃에 스폰되니 절대경로도 해석은 되지만, cwd-상대가 이식성이 좋다
(특히 `cwd=`로 다른 repo에 스폰하면 메인 체크아웃 절대경로는 깨진다). 커밋된 트리의 rg
명령은 새 세션에서 그대로 작동한다. (※ `EnterWorktree`로 *진짜* 워크트리를 쓸 때의 절대경로
탈출 사고는 [finding 0001] — 그건 별개 메커니즘이고 spawn_task엔 해당 없음.)

휘발 메타(`session_decisions`·`open_unknowns`·`safety_constraints`·`do_not_redo`)는 코드·문서에
없으니 프롬프트에 직접 fold한다.

### 4. 스폰 프롬프트 합성 (self-contained inline fold)

§3에서 조립한 페이로드를 *프롬프트 본문에 직접 fold*해, 새 세션이 외부 파일 없이 cold
start하게 한다. 형식 예시:

```
[task summary]를 진행하려고 해.

먼저 읽을 것:
- `src/foo.py` — X 함수 구조 확인
- `rg -n 'pattern' src/` — 기존 구현 위치

이번 세션 결정: [session_decisions 한 줄씩 inline]
미해결: [open_unknowns inline]
안전 제약: [safety_constraints inline]
다시 시도하지 마(막힌 길): [do_not_redo inline]

컨텍스트 적재 끝나면 [첫 단계]부터 시작.

작업 끝나면(`done_when` 충족 시) 끝낸 `referenced_todos` 항목을 커밋 메시지에
`closes todo #NNN`으로 닫아줘 (단위 status 자동 갱신 — 별도 문서 손대지 마).
```

프롬프트는 짧고 구체적으로. **휘발 메타(결정·unknowns·막힌 길)는 코드·문서에 없으니
프롬프트에 직접 fold한다** — 이게 self-contained의 핵심이다(새 세션이 읽을 외부 JSON이
없다). 단, 코드·문서로 도달 가능한 사실은 fold하지 말고 위 'rg 명령·경로'로만 (cwd-상대,
절대경로 금지 — §3 불변식).

**gitignored 런타임 파일**: 칩은 같은 체크아웃에 스폰되므로 `.env.local`·dev 설정 등
gitignored 파일이 *그대로 있다* — 복사 지시 불필요. (단 `cwd=`로 다른 repo에 스폰하면
그 repo 기준이니, 거기 없는 런타임 파일은 프롬프트에 위치만 한 줄.)

`referenced_todos`가 있으면 프롬프트에 한 줄 추가:
> *"`.claude/todos.md`의 #001, #007 항목과 연결된 작업이야. 첫 발화 후 그 항목들도 같이 surface해."* (단, SessionStart hook이 이미 모든 open todo inject하므로 중복일 수 있음 — 짧게)

### 4.5 execution trace (FORCE)

§5 출력 *직전*, 위 단계 중 건너뛰기 쉬운 것의 **결과를 한 줄씩** 먼저 출력한다. 빈
체크박스(`[ ]`)가 아니라 *결과 기입형* — 결과가 없으면(`skip`/`해당없음`) 그 이유도 한 줄.
trace 없이 스폰 칩으로 직행 금지 (이게 단계 skip 차단의 본체 — 산문 지시가 아니라
증거 강제, methodos 게이트 "Evidence (FORCE)"와 동일 정신).

```
- [x] 1a open todo surface: <surface한 항목 → referenced_todos 결과, 또는 todos.md 없음/skip>
- [x] 1b orphan check: <발견 항목+출처라벨+분기, 또는 orphan 없음>
- [x] commit-first: <git status --porcelain → clean이면 '스폰 진행' / dirty면 '커밋 안내함: N개 변경'>
- [x] 전달 방식: <칩이면 title+cwd / 스폰불가면 'HANDOFF.md (이유)' / 사용자 거부>
```

결과 칸이 비어 보이면 그 단계를 안 한 것 — 모델 자신과 사용자 양쪽이 즉시 포착한다.

### 5. 전달 — 지금 시작 가능하면 spawn_task 칩

다음 작업이 **지금 자율로 시작 가능**(외부 입력·인간 승인 대기 없음)하면 복붙 단계 없이
**`spawn_task` 칩**으로 새 세션을 띄운다 (현재 체크아웃 — 워크트리 아님). 지금 스폰
불가면 칩 대신 §5b로 간다.

**commit-first 전제 (칩 직전 권장)**: `git status --porcelain`을 확인한다. dirty면 —
스폰된 세션은 *같은 working tree를 공유*하므로 커밋 안 된 편집이 그대로 보인다(누락은
아님). 다만 두 세션이 같은 dirty 표면을 만지면 충돌·혼선이 나니(수시 커밋 규율), 넘길
작업분은 커밋하고 스폰하는 게 깔끔하다. 사용자에게:

> "현재 커밋 안 된 변경 N개가 있어요. 새 세션은 같은 체크아웃을 공유해 이 편집을 그대로
> 보지만, 두 세션이 같은 dirty 파일을 만지면 엉킵니다. 넘길 작업분 커밋하고 스폰할까요?"

→ 커밋 후 진행. (clean이면 바로 진행.)

그다음 `spawn_task` 호출:

```
spawn_task(
  title:  "<task summary, 60자 이내 명령형>",
  prompt: "<§4에서 합성한 self-contained 스폰 프롬프트 전체>",
  tldr:   "<1-2문장 평문 요약 — 무엇을 왜>",
  cwd:    <기본 생략 = 현재 프로젝트(현 체크아웃에 새 세션 — 워크트리 아님). 다른 repo면 그 절대경로>
)
```

- `prompt`는 §4 합성물 그대로 — 외부 파일 의존 0 (self-contained라 새 세션에서 바로 cold start).
- 칩이 뜨면 사용자가 1클릭으로 스폰, 또는 거부. 거부 시 그냥 대화 계속.
- 다른 repo의 작업이면 `cwd`에 그 repo 절대경로 (그 외엔 생략).

### 5b. 전달 — 지금 스폰 불가면 HANDOFF.md

다음 작업이 **지금 시작될 수 없으면** 칩을 띄우지 않는다. 판별 신호(하나라도):

- **외부 입력 대기** — 사람·제3자가 줄 자료·결정에 막혀 있어 스폰해도 idle.
- **인간 게이트 앞단** — 승인·실존 ID·톤 결재 등 자율 에이전트가 앞서 달리면 안 되는 단계.
- **사용자가 나중에 직접 이어감** — "지금 병렬 분리"가 아니라 "세션 끝 저장 → 나중에 내가 시작".

이 경우 §4에서 합성한 self-contained 프롬프트를 **프로젝트 루트 `HANDOFF.md` 최상단에
날짜 섹션으로 기록**(자기완결 — cold start 가능)하고 커밋한다. 새 세션은 `HANDOFF.md`만
읽고 이어간다. (이 경로는 칩의 "파일 0" 원칙의 *의도된 예외* — 지금 못 스폰하니 프롬프트를
디스크에 남겨야 산다.)

**up-front surface 강제**: 칩을 생략한다는 판단은 handoff 시작 시(§Trigger 확인 단계)에
*먼저* 말한다 — "이 작업은 스폰 불가(이유)라 칩 대신 HANDOFF.md로 갑니다." 스킬의 핵심
산출(칩)을 건너뛰는 건 강한 근거가 있어야 하고 *드러내야* 한다 — 사후 통보 금지.

---

## Anti-patterns

| 안티패턴 | 대신 |
|---|---|
| 사용자 발화·AI 응답을 통째로 옮김 | task에 필요한 결정만 inline |
| 이미 코드에 있는 정보 inline | grep 명령어만 기록 |
| task scope 모호한데 그냥 진행 | 묻기 |
| 복붙 코드블록으로 폴백 | 칩(스폰 가능) 또는 HANDOFF.md(스폰 불가) — self-contained 프롬프트 |
| 칩 생략하면서 그 일탈을 사후 통보 | 스폰 불가면 §5b·up-front surface (시작 시 먼저 말함) |
| dirty인데 commit-first 안 묻고 스폰 | 같은 체크아웃 공유 — dirty 충돌 방지 위해 커밋 안내 먼저 |
| 칩 경로인데 JSON 파일 저장 | 칩은 in-memory·파일 0 (스폰 불가 HANDOFF.md만 예외) |
| snapshot과 혼동해 풀 dump | handoff는 lean, 풀 dump는 snapshot |
| 1a/1b/commit-first 건너뛰고 스폰 칩 직행 | §4.5 execution trace로 단계 결과 강제 출력 |

---

## Safety

- 쿠키, 토큰, 비밀번호, 개인키 절대 금지. 위치/갱신 방법만 언급.
- 사용자/사번/책임자/참석자 이름은 role 라벨로.
- private repo에 들어가도 안전한 수준만 담는다.
- live ERP 쓰기·결재 작업은 handoff 후 새 세션에서도 fresh 확인 필요.
