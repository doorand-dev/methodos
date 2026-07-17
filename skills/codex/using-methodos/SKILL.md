---
name: using-methodos
description: |
  Methodos — this workspace's distributed AI-coding harness (an umbrella name, no central router). Codex directly executes truly simple closed changes; one Luna/max SDD owner carries each non-trivial task from discovery through terminal assembly, dispatching one Luna implementation owner per slice and fixed Sol/medium reviewers. This meta-skill explains the framework; it does not route work on the gates' behalf.
  Fires: "methodos가 뭐야", "이 하네스/게이트 어떻게 동작", "어떤 게이트 있어", `/using-methodos` explicit call.
  Does not fire: "X 추가해줘", "Y 구현해줘", "Z 만들자" (← the grill-me/plan gates self-trigger *directly*. This skill is not a router — do not call it).
---

# using-methodos — 분산 게이트 하네스 오리엔테이션

> **Methodos** (μέθοδος = *meta* 따라 + *hodos* 길). 우산 *이름*이지 스킬이 아니다. 앞단=메소드 *연기*(사용자 체화 서사로 빠진 디테일 발굴), 뒷단=*방법론*/규율(편향 교정·Deep Module [3I]·수직슬라이싱 [3H] 자율주행).
> 이 파일은 **패시브 메타-doc**이다 — 프레임워크를 설명할 때만 읽는다. 작업을 *시작*하면 아래 게이트들이 알아서 켜진다 (중앙 라우터 없음).

## 핵심 — 라우터가 없다

**각 게이트가 자기 상황 조건으로 자동발동**한다 — quick fix는 무거운 게이트에 *안 걸리고*(창발 XS), 대형 기능은 grill-me부터 걸린다. 사용자는 작업 크기를 분류하거나 `/methodos`·"tier M" 같은 프레임워크 의례를 *체감하지 않는다* (AC5).

작업 시작 시 AI가 먼저 코드·호출부를 읽기 전용으로 확인한다. 목표와 성공 검증이
명확하고, 기존 동작 안에서 acceptance·write paths·checks를 하나의 execution
packet으로 닫을 수 있으며, 새 schema/public API·보안/권한·데이터/사용자 자산·
비가역 변경·미해결 WHAT·독립 slice가 없으면 spec·정식 plan을 만들지 않는다.
기존(existing) user-visible flow 수정이나 다파일이라는 사실만으로 이 조건을 깨지 않는다.
1-2파일이면 부모가 direct predicate로 실행하고, 더 큰 하나의 저위험 packet이면
fresh worker가 실행한다. 같은 턴에 최소 수정, 관련 검증 1개 이상, 프로젝트
규칙상 커밋까지 진행하며 “진행할까요?”라고 멈추지 않는다. 조건 하나라도
어긋나면 첫 편집 전에 해당 게이트로 진입한다.

→ 그래서 이 메타-스킬은 *부르는 게 아니다*. "X 추가해줘"에 이 스킬을 호출하면 그게 곧 라우터 부활이다. 게이트가 알아서 engage하게 둘 것.

## 게이트 지도 (각자 self-trigger)

| 게이트 (top-level 스킬) | self-trigger 시점 | 산출 artifact |
|---|---|---|
| `grill-me` | 새 capability·새 user-visible flow·미해결 WHAT가 있는 작업, *코드 작성 전* | `docs/specs/<slug>.md` (approved) |
| `plan` | spec이 있거나 독립 slice·고위험·불명확성이 있는 작업, *구현 전* | `<plan_root>/<slug>.md` (approved) |
| `impl` | 닫힌 저위험 작업은 direct 실행; 그 외 SDD owner가 slice마다 fresh Luna/high worker(증거 기반 max 예외)를 호출해 구현·검증·WHY commit | WHY commit + `impl-worker-report` |
| high-risk slice checkpoint (`impl` 내부) | SDD owner가 schema/public contract, authority/security, persistent/latest/idempotency/concurrency, migration/external state, financial execution, 또는 2개 이상 후속 slice 기반일 때만 fresh 호출 | `<verify_root>/checkpoint-<slug>-slice-<N>-attempt-<M>.json` |
| `impl-novelist` (#4) | SDD owner가 assembled candidate의 모든 구현 report를 기계적으로 닫은 뒤 단 한 번 fresh 호출하는 최종 기술+서사 검증 | `<verify_root>/narrative-<slug>-final-attempt-<M>.json` |
| runtime advisory review (impl 내부) | 사용자가 별도 reviewer runtime 검토를 명시 요청한 경우, *마무리 직전* 1회 | `<verify_root>/<review-runtime>-impl-<slug>.json` |
| `spec-novelist` (#2) | spec 직후, 다중 actor ∨ 다flow일 때 lightweight 1회 | spec fold |
| `decision-reviewer` | 고위험·다중 사용자 결정이 있는 approved plan에 1회 | `<verify_root>/plan-<slug>-decision-attempt-1.json` |
| `decision` (governance) | 옵션 비교·비가역·임시방편 자리 | `docs/adr/NNNN-*.md` 또는 `WHY:` 주석 |
| `/simplify` (optional external helper, G-D) | 전체 diff 마무리 *선택* 1회 | (working tree 정리) |

순서·강도는 **트리거 조건에서 창발**한다 (plan은 spec·독립 slice·위험이 있을 때,
impl은 approved plan 또는 닫힌 execution packet일 때). 라우터가 순서를 *보장*하지
않는다.
## 스킬 패밀리

| 성격 | 스킬 | Methodos에서의 역할 |
|---|---|---|
| Core gates | `grill-me`, `plan`, `impl`, `spec-novelist`, `impl-novelist` | spec → plan → implementation → final verified candidate 흐름을 만든다 |
| Governance | `decision` | gate는 아니지만 핵심 판단 렌즈. 옵션 비교, 비가역, 임시방편, FORCE/OPEN 판단을 닫는다 |
| Continuity | `handoff`, `snapshot`, `todo`, `context-novelist` | 긴 작업을 세션·압축·문서 경계 너머로 잃지 않게 한다 |
| Learning loop | `blame-code`, `finding`, `gc`, `improve-codebase-architecture` | 혼란·발견·stale 표면을 축적하고 구조 개선으로 되돌린다 |
| Extensions | `conditional-heartbeat`, `ask-chatgpt-pro`, `report-kit` | heartbeat wakeup, 외부 second opinion, 보고서 산출처럼 상황 의존 기능을 붙인다 |

`decision`은 보조가 아니다. 중앙 라우터는 아니지만 Methodos의 core governance다. 반대로 `handoff`/`snapshot`/`todo`는 파이프라인 산출물을 읽고 쓰지 않는 운영층이라 core gate가 아니다.

기본은 **사용자 결정 공간을 보존한 model-driven 자율주행**이다. 단순·닫힌 작업은
`impl`의 유일한 predicate로 부모가 직접 작성·로컬 검증·WHY 커밋을 소유한다. 그 외
비단순 작업은 fresh `luna-max-sdd-owner`가 discovery·requirements/spec·plan·assembly·
terminal을 소유한다. 구현은 slice마다 fresh worker가 Luna/high 또는 `impl`의 증거 기반 max로
작성·검증·WHY 커밋을 소유한다. 이 문서는 그 기준을 복제하지 않는다. SDD owner가
그 report를 기계적으로 확인한 뒤 고위험 slice의 Sol/medium checkpoint와 조립된
candidate의 fresh final `impl-novelist`를 직접 호출한다. reviewer가 BROKEN이면 같은
slice owner가 repair하고, SDD owner가 attempt 1 reviewer의 같은 thread/session에
finding ID·repair diff·영향 selector만 scoped follow-up 한다.

루트/프로젝트 오케스트레이터는 inventory, overlap, 작업 순서, HITL 전달,
integration/merge 상태만 소유한다. SDD owner는 task-local model route, owned commit
set/provenance, reviewer terminal, artifact/hash, dirty/index와 terminal packet을
소유한다. spec approval, M1 결정 리스트와 plan approval은 사용자가 확인한다.
조건부 decision-reviewer가 사용자 체감 delta를 만들면 SDD owner가 이를 루트에
surface하고 그 결정만 다시 받는다.

사용자에게 결정을 물을 때는 항상 쉬운 언어를 쓴다. 내부 하네스 용어보다 "사용자/운영자가 무엇을 보게 되는지", "무엇이 덮이거나 멈출 수 있는지", "나중에 되돌리기 어려운지"를 먼저 설명한다.

`context-novelist`는 narrative novelist 대체물이 아니다. AI가 읽는 문서·절차·프롬프트·handoff·review/dispatch packet이 scope일 때만 추가로 쓰고, 순수 제품 코드 spec에는 기본으로 붙이지 않는다.

## Codex 스킬 루트

직접 설치하는 모든 Codex 사용자 스킬의 런타임 정본은 `~/.agents/skills`다.
`grill-me`, `plan`, `impl`뿐 아니라 `context-novelist`, `spec-novelist`,
`impl-novelist` 같은 보조·검증 스킬도 같은 루트에 둔다. `~/.codex/skills`에는
Codex가 관리하는 시스템 스킬만 남기고 사용자 스킬의 active 또는 `.disabled`
사본을 두지 않는다.

## tier = 트리거 *설계 근거* (런타임 라벨 아님, /)

tier(XS~L)는 v1에선 라우터가 사용자에게 선언하던 런타임 라벨이었다. v2에선 **런타임에 존재하지 않는다** — 대신 *각 게이트의 트리거·right-sizing 조건을 일관되게 짜기 위한 설계 근거*로만 여기 보존한다. 게이트는 상황(touched_files·결정 자리·flow)을 *조용히 자체 평가*해 무게를 정하지, "tier M입니다"라고 알리지 않는다 (AC5).

| tier | 상황 (게이트 자체 평가) | 어느 게이트가 걸리나 (창발) |
|---|---|---|
| **XS** | touched=1-2·새 flow/새 schema/API/authority/data/비가역 변화無·목표/검증 명확 | AI가 조용히 판정 → 같은 턴에 바로 수정 + verify 1개 이상 + 프로젝트 규칙상 commit |
| **S** | ≤3·결정0-1 또는 새 flow minor | grill-me 짧게(Q≤3) 또는 닫힌 execution packet + 검증 |
| **M** | 4-10·결정2-4·flow有 | grill-me + plan + impl + 조건부 spec/decision reviewer + final full review |
| **L** | >10 or architectural/security or 결정≥5 | grill-me + spec-novelist + decision-reviewer + impl + final full review |

→ 이 표는 "왜 grill-me가 다파일 신규기능에만 HARD-GATE이고 quick fix엔 안 걸리나"의 *근거*다. 게이트 트리거 조건을 수정할 때 이 right-sizing 의도와 어긋나지 않게 맞춘다. 사용자 "S로 해줘" 식 명시 발화는 해당 게이트가 무게를 낮추는 escape hatch.

## FORCE vs OPEN (거버닝 원칙 — 모든 게이트 설계를 지배,  AC6)

하네스는 현재 세션 모델이 *체계적 bias로 틀리는* 자리만 HARD-GATE로 강제하고(FORCE), 모델이 context로 잘 판단하는 자리는 *trade-off만 surface*하고 판단은 모델에 연다(OPEN).

| | **FORCE** (강제·HARD-GATE) | **OPEN** (surface·판단 열기) |
|---|---|---|
| 언제 | 모델이 *체계적 bias*로 틀림 | 모델이 context로 잘 판단 |
| 예 | Evidence([2J] "passed" 위조 본능), 누더기([1C] patch 쌓기), 검증 *존재*(skip 방지), 신규기능 spec-before-multifile | 실행모드 inline/dispatch(G-A), oracle *타입*(G-B), batch 여부, right-sizing, *어떤* 검증일지 |
| 하네스 행위 | 차단·"MUST" | trade-off를 떠올리게 surface, **답은 모델** |

**⚠️ OPEN ≠ 무규율**: OPEN 결정도 `decision` 원칙을 통과해 판단한다 (decision 렌즈는 답을 강제하지 않고 쉬운/어려운 길·비용/부채·Evidence·"안 만들면?"을 반드시 거치게 함). 즉 **OPEN = decision-gated judgment**. decision 렌즈를 빼고 "OPEN=모델 맘대로"로 구현하면 열린 판단이 편향 디폴트(over-process·누더기·시간 과대평가)로 회귀한다. → G-A/G-B/G-C/G-D는 전부 OPEN으로 배선 (rigid rule 금지).

## 강제력 = 격리 적대 reviewer + 영속 artifact

"이렇게 해라" advisory 마크다운은 압박 시 건너뛴다. 진짜 강제력 두 가지:
- **격리 reviewer** — 중요한 결정의 `decision-reviewer`, spec 누락의 lightweight
  `spec-novelist`, 명시적 high-risk slice checkpoint, 완성 후보 전체를 보는 final
  `impl-novelist`만 별도 컨텍스트로 실행한다. Codex reviewer 호출은 SDD owner가
  소유한다. 일반 slice owner는 로컬 RED/GREEN·선언 검증·diff 범위 확인만 하고
  reviewer를 spawn하지 않는다.
- **영속 artifact** — `<verify_root>/*.json` · `WHY:` commit · `docs/adr/` 존재. "통과"는 명령 출력 *직접 인용*([2J])으로만 인정.

이게 분산 트리거의 *2차 방어*이기도 하다 — 게이트가 켜야 할 때 안 켜지는 mis-fire가 나도, 검증 artifact가 없으면 "통과"를 단언 못 한다.

High-risk checkpoint attempt 1과 Codex final attempt 1은 SDD owner가 Sol/medium으로
고정해 직접 호출하는 fresh local read-only subagent다. Checkpoint는 대상 slice마다
full 1회만 실행한다. BROKEN repair는 같은 owner가 수행하고 SDD owner는 동일 reviewer
thread/session에 scoped follow-up만 보낸다. 사용자가 `검토 1회만`이라고 제한하면
scoped follow-up을 생략하고 잔여 위험을 기록한다.

Final gate는 SDD owner가 조립된 candidate의 요구사항/범위,
caller·producer·consumer·실패경로, 품질/부채, 테스트 oracle·회귀의 4개 기술 lens와
actor/user-story narrative overlay를 한 번에 검토하도록 호출한다. 별도 final full
`impl-verify`를 앞뒤로 붙이지 않는다.

Codex final attempt 1은 SDD owner가 Sol/medium으로 고정해 호출하는 fresh local
read-only subagent다. DONE이면 종료하고 routine second round는 없다. BROKEN fix 뒤
attempt 2+ scoped는 같은 reviewer thread/session follow-up이다. ChatGPT Pro나 Claude Fable/Opus 같은 외부 reviewer는 사용자가
그 검토에 명시적으로 요청했을 때만 쓴다. 외부 reviewer 실패를 다른 provider의 자동
fallback 사유로 쓰지 않는다. 프로젝트 machine route도 이 사용자 명시 조건을
우회하지 못한다.

## 핵심 리스크 = 분산 트리거 신뢰성

라우터의 중앙 통제를 버린 대가는 *게이트가 제때 안 켜질 수 있음*이다. 완화: (1) 게이트 description의 HARD-GATE 강제어, (2) 위 영속 artifact 2차 방어, (3) 이 메타-doc의 description이 always-loaded 리마인더로 게이트 존재를 환기. **수용하되 실사용로 mis-fire 관측**( Reeval).
