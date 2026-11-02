---
name: gc
description: "사용자가 “gc”나 “/gc”라고 말할 때만 프로젝트의 임시 파일·끝난 계획·죽은 코드·중복·깨진 문맥 참조를 점검하고 정리한다. “정리” 같은 일반 표현에는 쓰지 않는다."
---

# /gc (전역 스킬)

어느 워크스페이스에서든 동작. 프로젝트별 보완은 `<workspace>/.Codex/gc.toml` 로.

## 실행 절차

### 1. review 스캔 보고

```
py -3 ~/.agents/skills/gc/gc_check.py --review-only --report-json
```

review 후보를 사람이 읽기 쉽게 보고:
- **끝난 .plans 후보** (mtime > 30일 + VERIFIED PASS 또는 DoD 모두 체크): 사용자 확인 후 일괄/개별 삭제
- **stale handoff 후보** (`.claude_context/handoff/*.json` mtime > 14일 + `kind=="handoff"`): 1회용·휘발성. 사용자 확인 후 삭제
- **stale todo-ctx 후보**: `.Codex/todo-ctx/NNN.json` 중 연결 todo가 (`#NNN [x]`) 또는 (`#NNN 줄 부재`=orphan)인 것 → 삭제. *handoff와 분리* — todo-ctx는 age-out 아니라 todo 종결/소멸 기준. (handoff/*.json 의 age-out 룰과 헷갈리지 말 것.)
- **ruff 위반** (F401 unused import / F841 unused variable): 우선순위와 함께 제안

### 2. 첫 실행 유도 (gc.toml 없을 때만)

`<workspace>/.Codex/gc.toml` 파일이 **없으면** 1회 한정:

```
py -3 ~/.agents/skills/gc/gc_check.py --detect-large-dirs --report-json
```

100MB 이상 top-level 폴더가 1개 이상 발견되면 사용자에게 묻기:

> 큰 폴더 감지: `data/` (1.2 GB), `project/` (480 MB).
> 스캔에서 제외할까요? (`.Codex/gc.toml` 자동 생성)
> [y] 두 폴더 모두 제외 / [c] 선택해서 제외 / [n] 그냥 두기 (다음에도 또 물어봄) / [s] 다시 묻지 마 (빈 toml 생성)

선택에 따라 `<workspace>/.Codex/gc.toml` 작성:

```toml
# 이 프로젝트에서 GC 스캔 시 제외할 폴더 (큰 데이터·산출물 등)
skip_dirs = ["data", "project"]

# (선택) 작업용 임시 파일 위치·접두사 — 있을 때만 자동 삭제 대상
# work_temp_dir = "project/*/_work"
# work_temp_prefixes = ["_test_", "_tmp_"]
```

`n` 거부 시 toml 생성 X. `s` 시 빈 toml 만 생성 (다음 실행 시 재유도 안 함).

### 3. safe-fix 확인 + 실행

```
py -3 ~/.agents/skills/gc/gc_check.py --dry-run --report-json
```

safe 후보(pycache·.pyc·.tmp·.DS_Store 등) 보고 → "삭제할까요?" 확인 후:

```
py -3 ~/.agents/skills/gc/gc_check.py --safe-fix
```

### 4. AST 죽은 코드·중복·임계치 감지

```
py -3 ~/.agents/skills/gc/gc_audit.py
```

`<workspace>/.Codex/gc_report.md` 결과 읽고 보고:
- 죽은 코드 후보 (정의만 있고 외부 미참조)
- Cross-file 중복 함수 (body 해시 동일)
- **임계치 초과** (파일 > N줄 / 함수 > M줄) — *누더기 방지 4단계 ③ 임계치 트리거*

자동 삭제·자동 리팩토링 X — 사용자가 보고 판단. 임계치 초과는 *리팩토링 후보 신호*. 단위마다 심의 X, *커진 것*만.

임계치 디폴트 (조정은 `gc.toml`):
- `file_lines`: 400
- `function_lines`: 80

### 5. 기록과 현재 코드의 종합 감사

`.Codex/friction.md`가 있으면 현재 코드·호출부·위 검사 결과와 대조해 반복 원인, 미해결 문제, 해결 이후 재발을 확인한다. 항목 수·비율만으로 문제를 판정하거나 다음 스킬 실행을 요구하지 않는다. 기록이 없어도 요청 범위의 죽은 코드·중복·현재 오류를 감사하며, 정적 분석 후보는 실제 사용 여부를 확인한다.

감사만 요청하면 근거와 권고를 반환한다. 정리까지 맡겼으면 승인 범위의 확인된 국소 문제와 참조를 수정하고 관련 최소 검증까지 수행한다. 기록 형식을 보존해 처리 결과를 반영하며 불확실한 후보는 삭제하지 않는다. 큰 구조 변경은 영향과 권고를 제시하되 GC만으로 임의 재설계하지 않는다. 기록에 맞추려고 규칙·훅·검수 절차를 추가하지 않는다.

### 6. 컨텍스트 표면 신호

AGENTS.md·SKILL.md·MEMORY.md·settings.json에서 명백히 존재하지 않는 파일이나
경로 참조를 읽기 전용으로 surface한다. 점검 범위의 큰 JSON·JSONL 등 구조화 상태는 `py -3 ~/.agents/skills/gc/gc_check.py --state-files`로 크기·변경 시점과 파일명을 참조하는 코드 위치를 먼저 보고 후보를 찾는다. 이 검색은 skip_dirs 안의 데이터도 크기만 확인하고 본문은 읽지 않는다. 경로를 조립하거나 glob으로 읽는 코드는 찾지 못하므로, 참조 미발견은 미사용 확정이 아니다. 반복 실행의 입력으로 쓰이는지 확인하기 전에는 본문 전체를 읽거나 정리 대상으로 확정하지 않는다. 큰 원자료·설정 파일은 그 자체로 결함이 아니다. 과거 기록 때문에 매회 조회 결과가 커지는 후보는 `improve-context`로 연결하고 크기만으로 자동 삭제·분리하거나 새 예약을 만들지 않는다. 범용 `gc`는 문서 계약·작업 절차의
실제 consumer, runtime ingress, authority, lifetime, stale 의미를 전수 감사하지
않는다.

`<workspace>/.Codex/context-friction.md`가 있으면 전체 항목 수와 `status: open`,
`context-fault: uncertain` 개수만 한 줄로 보고한다. open 또는 uncertain이 하나라도
있으면 `improve-context`에서 해당 사건과 실제 소비 경로를 함께 확인할 후보로 알린다. 파일이 없으면 생성하지 않는다.

다음 중 하나면 후보 수와 대표 경로만 보고하고 `/improve-context <scope>`를 권장한다:

- 깨진 참조가 여러 context surface에 걸쳐 있음
- 문서 절차와 현재 runtime/code가 다르다는 증거가 있음
- 중복 authority, 죽은 trigger, orphan target, stale workflow 조사가 필요함
- 사용자가 범위 지정 또는 전수 context 감사를 원함

이 표면 검사만으로 컨텍스트를 수정·삭제하지 않는다. 사용자가 컨텍스트 종합 감사·정리도 요청했다면 [improve-context](../improve-context/SKILL.md)의 기준으로 해당 범위를 처리하며 별도 재승인 단계를 만들지 않는다.

## 환경별 호출

- Windows: `py -3 ~/.agents/skills/gc/...` (또는 절대경로 `C:/Users/<user>/.agents/skills/gc/...`)
- Linux/macOS: `python3 ~/.agents/skills/gc/...`

## 프로젝트 보완 (`<workspace>/.Codex/gc.toml`)

| 키 | 설명 |
|----|------|
| `skip_dirs` | 추가로 스캔에서 제외할 폴더 이름 목록 (기본 `.git`, `node_modules`, `.venv`, `venv` 위에 추가) |
| `work_temp_dir` | 작업용 임시 디렉토리 glob (예: `project/*/_work`) — 있을 때만 임시 파일 자동 삭제 |
| `work_temp_prefixes` | `work_temp_dir` 안에서 자동 삭제할 파일 접두사 (예: `["_test_", "_tmp_"]`) |
| `[thresholds] file_lines` | 임계치 — 파일 줄 수 초과 시 리포트. 디폴트 `400` |
| `[thresholds] function_lines` | 임계치 — 함수 줄 수 초과 시 리포트. 디폴트 `80` |
| `[thresholds] state_file_mb` | `--state-files` 후보 크기 하한(MB). 디폴트 `1` |
| `[thresholds] state_file_limit` | `--state-files`가 큰 순서로 보고할 최대 개수. 디폴트 `40` |

예시 (`gc.toml`):
```toml
skip_dirs = ["data", "models"]

[thresholds]
file_lines = 500
function_lines = 100
```
