---
name: finding
description: 코드가 담을 수 없는 "현실이 어떻게 동작하나 / 뭐가 막혀있나"류 영속 지식(외부 시스템 동작·하드원 우회·시도했으나 실패)을 `docs/findings/NNNN-slug.md`에 file-per-finding으로 누적. 결정(ADR)·friction(휘발 백로그)·todo-ctx(휘발 맥락)와 구분되는 *영속 참조 사실* 아티팩트. explicit 1급 트리거(`/finding`·"finding 박아"·"이거 발견 기록") + 발견 발화 soft 넛지(자동, opt-in 기록). 외부시스템 reverse-engineering 지식을 다음 세션 재삽질로부터 보존.
---

# /finding (전역 스킬)

어느 워크스페이스에서든 동작. *코드가 못 담는 발견*(택한 길이 아니라 *버린 길*·*막힌 길*)을 영속 파일로 박아 다음 세션의 재삽질을 차단.

> **이름 vs 산출 분리**: 스킬 `finding`(자연 발화 "발견 기록"), 산출 `docs/findings/NNNN-slug.md`. `blame-code → friction.md`, `decision → docs/adr/`와 같은 분리 패턴.

> 도입 결정: [`docs/adr/0024-conv-findings-as-folder-artifact.md`]. 형태(file-per-finding) 외부조사 근거·생애주기 거기.

## 무엇이 finding인가 (타입 경계)

| 타입 | 질문 | 집 | 생애주기 |
|---|---|---|---|
| 결정 | 왜 A를 택했나 (tradeoff) | `docs/adr/` | 영속·supersede |
| friction | AI가 코드를 왜 잘못 읽었나 | `.claude/friction.md` | **휘발**(처리되면 삭제) |
| todo-ctx | 이 todo의 작업 맥락 | `.claude/todo-ctx/NNN.json` | **휘발**(todo 닫히면 삭제) |
| **finding** | **현실이 어떻게 동작하나 / 뭐가 막혀있나** | **`docs/findings/`** | **영속·supersede** |
| 큰 의도 조사 | (한 주제 깊게 파기) | `docs/research/RESEARCH-*.md` | 영속 (입도 큼) |

finding의 핵심 = **네거티브 스페이스**. 코드는 *택한 길*만 담고 *버린/막힌 길*은 절대 안 담는다. `막힘:`이 없으면 finding이 아니다(그냥 코드 주석으로 충분).

## 발동 트리거

| 신호 | 예시 |
|---|---|
| 명시 호출 (수동) | `/finding`, "finding 박아", "이거 발견 기록해", "발견 남겨" |
| 발견 발화 (자동 → soft 넛지) | "알고 보니 ~", "이게 막혀있네", "~로 우회하면 되네", "직접은 안 되고 ~ 하면", "한참 헤맸는데 ~", "삽질 끝에" |
| 프로젝트 보완 | `<workspace>/.claude/finding.toml`의 `extra_triggers` |

자동 감지 시 *바로 쓰지 말고* 한 줄 넛지: *"이거 finding으로 박을까? (막힘/되는 길 한 줄씩)"* → 사용자 confirm 후 기록. (blame-code와 동형 — false positive·노이즈 차단.)

## 실행 절차

### 1. 폴더 lazy 생성·번호 할당

- `docs/findings/` 없으면 생성. `docs/` 자체가 없는 repo면 루트 `findings/`.
- 번호 = 기존 `NNNN-*.md` max+1 (4자리 zero-pad, 재사용 X — 백링크·supersede 안정).
- 파일명 `NNNN-<slug>.md`. slug = 태그+요지 kebab (예: `0001-iherb-wishlist-price.md`).

### 2. 발견 1건 작성

```markdown
# [태그] 한 줄 요지

날짜: YYYY-MM-DD
상태: active

- 막힘: <뭐가/왜 안 되나 — 코드가 못 담는 핵심. 필수>
- 되는 길: <우회/해법>
- 코드: <path 또는 "없음">
- 미검증: <확인 안 한 가정 — 로그인 필요 여부·레이트리밋 등. 없으면 생략>
```

- `[태그]` 머리 = grep 앵커(`[iherb]` 등 도메인/외부시스템). 파일명에도 반영.
- `막힘:` 비면 작성 거부 — 사용자에게 "막힌 게 뭐였어?" 1줄 확인.
- 출처 reverse-engineering이면 `미검증:`에 *날짜 의존성* 명시(외부 사이트는 부패함).

### 3. supersede / stale (현실이 바뀌면)

- 외부 시스템 개편으로 발견이 틀려지면 **편집 말고** 새 finding 작성 후 옛 것:
  - 옛 파일 `상태: superseded → #NNNN` (새 번호 가리킴). 본문 유지("한때 사실").
- 검증 못 해 부패 의심이면 `상태: stale (last-verified: YYYY-MM-DD)`.
- *삭제 안 함* — friction과 달리 영속(과거 사실의 기록 가치).

### 4. todo-ctx 졸업 수령 (둘째 출구, 관련 설계 결정 결정 6 확장)

todo 닫을 때 `todo-ctx/NNN.json`의 load-bearing 내용이:
- *결정*이면 → `decision` 스킬로 ADR 승격
- **사실 발견**이면(`do_not_redo`·`grep_pointers` 필드가 전형) → **여기로 졸업**(finding 작성)
- 졸업 후 json 삭제 (휘발 맥락 → 영속 지식 이전 완료).

### 5. recall 모드 ("X 관련 발견 있어?")

```
grep -rn "\[<태그>\]" docs/findings/
```
열린 작업이 외부 시스템 건드리기 시작하면 *먼저* 해당 태그 grep — 재삽질 차단이 이 아티팩트의 본분.

## 안 하는 것

- **단일 `FINDINGS.md`에 append** — merge 충돌·비대·supersede 불가(관련 설계 결정 A 기각). file-per-finding 유지.
- `docs/research/`에 섞기 — 입도 다름(큰 의도조사 vs 작은 우연발견), 별 폴더(관련 설계 결정 B 기각).
- `막힘:` 없는 1줄 stub — 그건 코드 주석감. finding은 네거티브 스페이스가 본체.
- 결정을 finding으로 / 사실을 ADR로 오分류 — 졸업 분기 기준(§4) 준수.
- 부패 finding 삭제 — supersede/stale로 보존(영속).

## 프로젝트 보완 (`<workspace>/.claude/finding.toml`, 선택)

| 키 | 설명 | 디폴트 |
|----|------|------|
| `extra_triggers` | 프로젝트별 발견 발화 패턴 | (없음) |
| `root_override` | 산출 폴더 경로 override | `docs/findings/` (없으면 루트 `findings/`) |
