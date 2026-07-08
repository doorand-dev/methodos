---
name: gc
description: 프로젝트 GC 스캔 + 정리. pycache/임시파일 삭제, 끝난 .plans·stale handoff 탐지, ruff 위반 보고, 죽은 코드·중복 감지, friction.md 백로그 surface, 컨텍스트 표면(CLAUDE.md/SKILL.md/settings) stale·중복·오배치 감사. 첫 실행 시 큰 폴더 자동 감지·스캔 제외 유도. **명시 트리거 전용** — 사용자가 "gc" 또는 "/gc" 라고 직접 말할 때만 발동. "정리" 같은 일반어로는 트리거 안 함(오발동 방지).
---

# /gc (전역 스킬)

어느 워크스페이스에서든 동작. 프로젝트별 보완은 `<workspace>/.claude/gc.toml` 로.

## 실행 절차

### 1. review 스캔 보고

```
py -3 <this-skill-dir>/gc_check.py --review-only --report-json
```

review 후보를 사람이 읽기 쉽게 보고:
- **끝난 .plans 후보** (mtime > 30일 + VERIFIED PASS 또는 DoD 모두 체크): 사용자 확인 후 일괄/개별 삭제
- **stale handoff 후보** (`.claude_context/handoff/*.json` mtime > 14일 + `kind=="handoff"`): 1회용·휘발성. 사용자 확인 후 삭제
- **stale todo-ctx 후보** (관련 설계 결정): `.claude/todo-ctx/NNN.json` 중 연결 todo가 (`#NNN [x]`) 또는 (`#NNN 줄 부재`=orphan)인 것 → 삭제. *handoff와 분리* — todo-ctx는 age-out 아니라 todo 종결/소멸 기준. (handoff/*.json 의 age-out 룰과 헷갈리지 말 것.)
- **ruff 위반** (F401 unused import / F841 unused variable): 우선순위와 함께 제안

### 2. 첫 실행 유도 (gc.toml 없을 때만)

`<workspace>/.claude/gc.toml` 파일이 **없으면** 1회 한정:

```
py -3 <this-skill-dir>/gc_check.py --detect-large-dirs --report-json
```

100MB 이상 top-level 폴더가 1개 이상 발견되면 사용자에게 묻기:

> 큰 폴더 감지: `data/` (1.2 GB), `project/` (480 MB).
> 스캔에서 제외할까요? (`.claude/gc.toml` 자동 생성)
> [y] 두 폴더 모두 제외 / [c] 선택해서 제외 / [n] 그냥 두기 (다음에도 또 물어봄) / [s] 다시 묻지 마 (빈 toml 생성)

선택에 따라 `<workspace>/.claude/gc.toml` 작성:

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
py -3 <this-skill-dir>/gc_check.py --dry-run --report-json
```

safe 후보(pycache·.pyc·.tmp·.DS_Store 등) 보고 → "삭제할까요?" 확인 후:

```
py -3 <this-skill-dir>/gc_check.py --safe-fix
```

### 4. AST 죽은 코드·중복·임계치 감지

```
py -3 <this-skill-dir>/gc_audit.py
```

`<workspace>/.claude/gc_report.md` 결과 읽고 보고:
- 죽은 코드 후보 (정의만 있고 외부 미참조)
- Cross-file 중복 함수 (body 해시 동일)
- **임계치 초과** (파일 > N줄 / 함수 > M줄) — *누더기 방지 4단계 ③ 임계치 트리거*

자동 삭제·자동 리팩토링 X — 사용자가 보고 판단. 임계치 초과는 *리팩토링 후보 신호*. 단위마다 심의 X, *커진 것*만.

임계치 디폴트 (조정은 `gc.toml`):
- `file_lines`: 400
- `function_lines`: 80

### 5. friction.md 백로그 surface

`<workspace>/.claude/friction.md` 있으면 한 줄 통계 보고 (없으면 skip — 생성은 안 함, [blame-code](../blame-code/SKILL.md) 스킬이 lazy 생성 담당):

- **누적 카운트** — 항목 수 (예: "friction 12개")
- **top 3 카테고리** — 빈도순 (예: "상위: stale-comment 5, naming 4, dead-code 2")
- **code-clean=yes 비율** — escape valve 모니터링 (예: "code-clean=yes 비율 18%")

**alert 임계치**:
- 누적 카운트 > 20: *"처리할 시점 — /improve-codebase-architecture 호출 권장"*
- code-clean=yes 비율 < 10%: *"모든 걸 코드 탓하는 패턴 — 합리화 도구화 점검 필요"*

본 단계는 *읽기 전용 surface*, friction.md 수정 안 함.

3-layer trio 흐름: blame-code(수집, ms) → **gc(감사, 본 단계)** → improve-codebase-architecture(처리, 의도 발동). 관련 결정: `docs/adr/0001-conv-friction-trio.md` (워크스페이스 기준).

### 6. 컨텍스트 표면 감사 (auto-inject 파일 stale·중복·오배치)

step 4의 AST 스캐너는 *코드*만 본다. auto-inject 컨텍스트 파일(AGENTS.md·CLAUDE.md·SKILL.md·MEMORY.md·settings.json)은 매 세션/트리거 시 비용을 무는데, 여기 쌓인 누적은 코드 그래프에 안 잡힌다. 읽기 전용 surface, 수정은 사용자 판단.

**(a) stale 참조 (스크립트 가능):** 각 AGENTS.md/CLAUDE.md/SKILL.md가 가리키는 경로·파일이 실재하나 — 죽은 링크·없어진 파일 묘비 탐지.
```
# AGENTS.md/CLAUDE.md류가 참조하는 상대경로 추출 → 존재 확인 (예시 recipe)
grep -rEoh '\[[^]]+\]\(([^)]+)\)|`[^`]+\.(md|py|ps1|toml|json)`' --include=CLAUDE.md --include=SKILL.md . \
  | <경로 정규화> | while read p; do [ -e "$p" ] || echo "MISS $p"; done
```

**(b) 중복·오배치 (의미 판단, 스크립트 불가):** 줄마다 absence-test — *"없으면 어느 시나리오·관객이 깨지나?"*
- **중복**: always-on 파일(루트/전역 AGENTS.md/CLAUDE.md)의 내용이 *스킬 body/description이 이미 덮는* 것이면 → 포인터화 후보. (예: finding 골격이 finding 스킬과 global CLAUDE.md에 이중)
- **scope 오배치**: 전역 settings/CLAUDE.md에 박힌 *한 프로젝트 전용* 항목, 또는 관객이 한 서브트리뿐인 내용 → 해당 프로젝트·nested로 push-down 후보.
- **죽은 묘비**: "구 X 폐기"식 역사 산문 — 가리키는 대상 부재면 컷(역사는 ADR 소관).

보고만 — "지울 때: 없으면 뭐 깨지나 / 만들 때 대체분 같이" 원칙은 사용자 글로벌 룰이 보유, gc는 surface만.

## 환경별 호출

- Windows: `py -3 <this-skill-dir>/...` (또는 절대경로 `C:/Users/<user>/.claude/...`)
- Linux/macOS: `python3 <this-skill-dir>/...`

## 프로젝트 보완 (`<workspace>/.claude/gc.toml`)

| 키 | 설명 |
|----|------|
| `skip_dirs` | 추가로 스캔에서 제외할 폴더 이름 목록 (기본 `.git`, `node_modules`, `.venv`, `venv` 위에 추가) |
| `work_temp_dir` | 작업용 임시 디렉토리 glob (예: `project/*/_work`) — 있을 때만 임시 파일 자동 삭제 |
| `work_temp_prefixes` | `work_temp_dir` 안에서 자동 삭제할 파일 접두사 (예: `["_test_", "_tmp_"]`) |
| `[thresholds] file_lines` | 임계치 — 파일 줄 수 초과 시 리포트. 디폴트 `400` |
| `[thresholds] function_lines` | 임계치 — 함수 줄 수 초과 시 리포트. 디폴트 `80` |

예시 (`gc.toml`):
```toml
skip_dirs = ["data", "models"]

[thresholds]
file_lines = 500
function_lines = 100
```
