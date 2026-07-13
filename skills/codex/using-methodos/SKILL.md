---
name: using-methodos
description: |
  Methodos — this workspace's distributed AI-coding harness (an umbrella name, no central router). When work begins, the gates *each self-trigger*: grill-me (new-feature spec) · plan (pre-impl planning) · plan-verify/impl-verify (isolated verification) · impl (slice autonomous drive). This meta-skill does *not* route the gates on their behalf — it fires only to explain/orient the whole framework.
  Fires: "methodos가 뭐야", "이 하네스/게이트 어떻게 동작", "어떤 게이트 있어", `/using-methodos` explicit call.
  Does not fire: "X 추가해줘", "Y 구현해줘", "Z 만들자" (← the grill-me/plan gates self-trigger *directly*. This skill is not a router — do not call it).
---

# using-methodos — 분산 게이트 하네스 오리엔테이션

> **Methodos** (μέθοδος = *meta* 따라 + *hodos* 길). 우산 *이름*이지 스킬이 아니다. 앞단=메소드 *연기*(사용자 체화 서사로 빠진 디테일 발굴), 뒷단=*방법론*/규율(편향 교정·Deep Module [3I]·수직슬라이싱 [3H] 자율주행).
> 이 파일은 **패시브 메타-doc**이다 — 프레임워크를 설명할 때만 읽는다. 작업을 *시작*하면 아래 게이트들이 알아서 켜진다 (중앙 라우터 없음).

## 핵심 — 라우터가 없다

**각 게이트가 자기 상황 조건으로 자동발동**한다 — quick fix는 무거운 게이트에 *안 걸리고*(창발 XS), 대형 기능은 grill-me부터 걸린다. 사용자는 `/methodos`·"tier M" 같은 프레임워크 의례를 *체감하지 않는다* (AC5).

→ 그래서 이 메타-스킬은 *부르는 게 아니다*. "X 추가해줘"에 이 스킬을 호출하면 그게 곧 라우터 부활이다. 게이트가 알아서 engage하게 둘 것.

## 게이트 지도 (각자 self-trigger)

| 게이트 (top-level 스킬) | self-trigger 시점 | 산출 artifact |
|---|---|---|
| `grill-me` | 신규 기능·비-trivial 작업, *코드 작성 전* | `docs/specs/<slug>.md` (approved) |
| `plan` | spec 있거나 다슬라이스 비-trivial, *구현 전* | `<plan_root>/<slug>.md` (approved) |
| `plan-verify` | plan approved 직후, impl 전 (격리 적대 검증) | `<verify_root>/plan-<slug>-..json` |
| `impl` | plan approved, 슬라이스 구현·자율주행 | git commit (`WHY:` prefix) |
| `impl-verify` | 슬라이스 commit 후 "통과" 단언 전 (오라클 판정 내장, batch seam 가능) | `<verify_root>/slice-<N>-..json` 또는 batch seam artifact |
| `impl-novelist` (#4) | 모든 slice와 configured impl-verify gates 후, 다파일 ∨ 다flow 최종 통합 서사 | `<verify_root>/narrative-<slug>-final-attempt-<M>.json` |
| runtime advisory review (impl 내부) | 별도 reviewer runtime이 설정된 대형·아키텍처 변경, *마무리 직전* 1회 | `<verify_root>/<review-runtime>-impl-<slug>.json` |
| `spec-novelist` (#2) | spec 직후, 다파일 ∨ 다flow 실사용 서사 | spec fold |
| `decision` (governance) | 옵션 비교·비가역·임시방편 자리 | `docs/adr/NNNN-*.md` 또는 `WHY:` 주석 |
| `/simplify` (optional external helper, G-D) | 전체 diff 마무리 *선택* 1회 | (working tree 정리) |

순서·강도는 **트리거 조건에서 창발**한다 (plan은 spec 있을 때, impl은 plan approved일 때). 라우터가 순서를 *보장*하지 않는다.
## 스킬 패밀리

| 성격 | 스킬 | Methodos에서의 역할 |
|---|---|---|
| Core gates | `grill-me`, `plan`, `plan-verify`, `impl`, `impl-verify`, `spec-novelist`, `impl-novelist` | spec → plan → verified slice → final narrative 흐름을 직접 만든다 |
| Governance | `decision` | gate는 아니지만 핵심 판단 렌즈. 옵션 비교, 비가역, 임시방편, FORCE/OPEN 판단을 닫는다 |
| Continuity | `handoff`, `snapshot`, `todo`, `context-novelist` | 긴 작업을 세션·압축·문서 경계 너머로 잃지 않게 한다 |
| Learning loop | `blame-code`, `finding`, `gc`, `improve-codebase-architecture` | 혼란·발견·stale 표면을 축적하고 구조 개선으로 되돌린다 |
| Extensions | `conditional-heartbeat`, `ask-chatgpt-pro`, `report-kit` | heartbeat wakeup, 외부 second opinion, 보고서 산출처럼 상황 의존 기능을 붙인다 |

`decision`은 보조가 아니다. 중앙 라우터는 아니지만 Methodos의 core governance다. 반대로 `handoff`/`snapshot`/`todo`는 파이프라인 산출물을 읽고 쓰지 않는 운영층이라 core gate가 아니다.

기본은 **사용자 결정 공간을 보존한 model-driven 자율주행**이다. spec review approval, M1 결정 리스트, plan review approval, plan-verify escalation, M2 scenario delta approval은 사용자가 확인한다. 그 결정 공간이 해소된 뒤에는 특별한 중단 지시가 없는 한 impl → configured impl-verify gates → impl-novelist까지 이어간다.

사용자에게 결정을 물을 때는 항상 쉬운 언어를 쓴다. 내부 하네스 용어보다 "사용자/운영자가 무엇을 보게 되는지", "무엇이 덮이거나 멈출 수 있는지", "나중에 되돌리기 어려운지"를 먼저 설명한다.

`context-novelist`는 narrative novelist 대체물이 아니다. AI가 읽는 문서·절차·프롬프트·handoff·review/dispatch packet이 scope일 때만 추가로 쓰고, 순수 제품 코드 spec에는 기본으로 붙이지 않는다.

## Codex 스킬 루트

Codex에는 성격이 다른 스킬 루트가 둘 있을 수 있다. `~/.agents/skills`는 methodos/agent 하네스 스킬(`grill-me`, `plan`, `impl`, `impl-verify`)의 런타임 정본이고, `~/.codex/skills`는 Codex 사용자·시스템·보조 스킬(`context-novelist` 등)의 런타임 정본이다. 둘 다 존재하는 것은 정상이다.

단, 같은 `name:`이 두 루트에 동시에 생기면 wrong-reader 위험이다. 그때는 어느 루트가 현재 세션에 노출됐는지 먼저 확인하고, 내용 hash 동기화가 아니라 **행동 계약 drift**를 점검한다.

## tier = 트리거 *설계 근거* (런타임 라벨 아님, /)

tier(XS~L)는 v1에선 라우터가 사용자에게 선언하던 런타임 라벨이었다. v2에선 **런타임에 존재하지 않는다** — 대신 *각 게이트의 트리거·right-sizing 조건을 일관되게 짜기 위한 설계 근거*로만 여기 보존한다. 게이트는 상황(touched_files·결정 자리·flow)을 *조용히 자체 평가*해 무게를 정하지, "tier M입니다"라고 알리지 않는다 (AC5).

| tier | 상황 (게이트 자체 평가) | 어느 게이트가 걸리나 (창발) |
|---|---|---|
| **XS** | touched=1·결정0·flow無 | 어느 무거운 게이트도 안 걸림 → 바로 수정 + verify 1개 |
| **S** | ≤3·결정0-1·flow minor | grill-me 짧게(Q≤3) 또는 skip + plan + 검증 권장 |
| **M** | 4-10·결정2-4·flow有 | grill-me + plan + plan-verify + impl + impl-verify + (조건부) decision-reviewer·codex |
| **L** | >10 or architectural/security or 결정≥5 | 풀 + decision-reviewer + impl-verify THOROUGH + codex 1회 + narrative #2/#4 |

→ 이 표는 "왜 grill-me가 다파일 신규기능에만 HARD-GATE이고 quick fix엔 안 걸리나"의 *근거*다. 게이트 트리거 조건을 수정할 때 이 right-sizing 의도와 어긋나지 않게 맞춘다. 사용자 "S로 해줘" 식 명시 발화는 해당 게이트가 무게를 낮추는 escape hatch.

## FORCE vs OPEN (거버닝 원칙 — 모든 게이트 설계를 지배,  AC6)

하네스는 모델(세션 Opus)이 *체계적 bias로 틀리는* 자리만 HARD-GATE로 강제하고(FORCE), 모델이 context로 잘 판단하는 자리는 *trade-off만 surface*하고 판단은 모델에 연다(OPEN).

| | **FORCE** (강제·HARD-GATE) | **OPEN** (surface·판단 열기) |
|---|---|---|
| 언제 | 모델이 *체계적 bias*로 틀림 | 모델이 context로 잘 판단 |
| 예 | Evidence([2J] "passed" 위조 본능), 누더기([1C] patch 쌓기), 검증 *존재*(skip 방지), 신규기능 spec-before-multifile | 실행모드 inline/dispatch(G-A), oracle *타입*(G-B), batch 여부, right-sizing, *어떤* 검증일지 |
| 하네스 행위 | 차단·"MUST" | trade-off를 떠올리게 surface, **답은 모델** |

**⚠️ OPEN ≠ 무규율**: OPEN 결정도 `decision` 원칙을 통과해 판단한다 (decision 렌즈는 답을 강제하지 않고 쉬운/어려운 길·비용/부채·Evidence·"안 만들면?"을 반드시 거치게 함). 즉 **OPEN = decision-gated judgment**. decision 렌즈를 빼고 "OPEN=모델 맘대로"로 구현하면 열린 판단이 편향 디폴트(over-process·누더기·시간 과대평가)로 회귀한다. → G-A/G-B/G-C/G-D는 전부 OPEN으로 배선 (rigid rule 금지).

## 강제력 = 격리 적대 reviewer + 영속 artifact

"이렇게 해라" advisory 마크다운은 압박 시 건너뛴다. 진짜 강제력 두 가지:
- **격리 적대 reviewer** — 별도 컨텍스트 AI가 "틀렸다"를 잡음 (plan-verify-reviewer · impl-verify-reviewer · decision-reviewer · novelist 2종, agent prompt는 `agents/claude/`를 런타임에 맞게 변환).
- **영속 artifact** — `<verify_root>/*.json` · `WHY:` commit · `docs/adr/` 존재. "통과"는 명령 출력 *직접 인용*([2J])으로만 인정.

이게 분산 트리거의 *2차 방어*이기도 하다 — 게이트가 켜야 할 때 안 켜지는 mis-fire가 나도, 검증 artifact가 없으면 "통과"를 단언 못 한다.

Codex의 full reviewer 기본 route는 fresh ChatGPT Pro 웹 세션이고, 같은 lineage의
fix reverify는 fresh local Sol/medium scoped다. Pro가 issue/BLOCKED/BROKEN을
반환한 것은 정상 review 결과이며, 결과 자체를 얻지 못한 transport/finality 실패에만
fresh local Sol/xhigh fallback을 허용한다. 프로젝트 machine route가 있으면 이 기본보다
우선한다.

## 핵심 리스크 = 분산 트리거 신뢰성

라우터의 중앙 통제를 버린 대가는 *게이트가 제때 안 켜질 수 있음*이다. 완화: (1) 게이트 description의 HARD-GATE 강제어, (2) 위 영속 artifact 2차 방어, (3) 이 메타-doc의 description이 always-loaded 리마인더로 게이트 존재를 환기. **수용하되 실사용로 mis-fire 관측**( Reeval).
