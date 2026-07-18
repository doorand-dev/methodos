---
name: using-methodos
description: Passive orientation for Methodos gates and their safety boundaries; it does not route work on their behalf.
---

# using-methodos — 분산 게이트 하네스 안내

이 문서는 패시브 안내서다. 중앙 라우터나 작업 크기 의례를 만들지 않으며,
각 게이트가 자기 조건으로 발동한다.

## 기본 흐름

작업 시작 전에 목표, acceptance, callers/producers/consumers, write paths와
검증 명령을 읽는다. 이 정보가 하나의 닫힌 execution packet을 이루고,
새 user flow·schema/public contract·권한/보안·user data·비가역 변경·미결정
WHAT가 없으면 `/impl`의 direct 경로를 쓴다. 파일 수는 cutoff가 아니다.
테스트 실행과 exact changed-path 확인은 항상 남긴다.

packet이 닫히지 않으면 `/plan`으로 구조화한 뒤 `/impl`에서 slice를 위임한다.
기본 위임은 Luna/high이고, 분해 후에도 복구하기 어려운 구체적 고비용 불확실성이
남을 때만 Luna/max를 선택한다.

## 게이트 선택

| 게이트 | 발동 조건 | 핵심 산출 |
|---|---|---|
| `grill-me` | 새 capability, 새 user-visible flow, 미결정 WHAT | 승인된 spec |
| `plan` | 승인 spec, 독립 slice, 고위험 또는 불명확한 변경 | exact paths와 commands가 있는 plan |
| `impl` | 승인 plan slice 또는 닫힌 execution packet | 구현, 테스트, changed-path 확인 |
| `decision-reviewer` | 고위험 또는 복수 사용자 결정 | 선택지와 잔여 위험 |
| `spec-novelist` | 여러 actor/flow의 spec | 누락 actor·flow |

Checkpoint review는 schema/public contract, permission/security, user data,
persistent/latest/idempotency/concurrency, migration/external state, financial
execution, 또는 여러 독립 slice가 공유하는 foundation일 때만 선택한다.
Final review는 새 public/user flow, shared contract, permission/data,
external-state/concurrency/migration, 또는 독립 slice 통합 누락 위험이 있을
때만 선택한다. 그 밖에는 local verification으로 닫는다.

## 안전 경계

테스트 실행, exact changed-path 확인, 외부 작업 승인, user data/permission/
database/schema/public contract/concurrency/migration/external-state의 승인과
검토는 유지한다. 실제 실행에서 확인할 수 없는 model·effort·transport·session
값은 검증 완료나 gate 근거로 기록하지 않는다. Transport metadata, generated
artifacts, and commit prose are not required outputs.

이 문서는 역할을 설명할 뿐 실행을 대신하지 않는다. 구현·계획 문서의
point-of-use 조건이 충돌하면 해당 문서를 따른다.
