---
slug: emergency-self-execution
created_at: 2026-07-16
status: approved
spec_ref: docs/specs/emergency-self-execution.md
source_spec:
  path: docs/specs/emergency-self-execution.md
  approved_at: 2026-07-16T00:00:00+09:00
  sha: e1133f03ee606b0985a37e0c6d4734bdecbd3ec2
approved_plan_revision: f480fd15c54c4d5be3f62b5c2db5f11e93110374
goal: 단순·닫힌 수정은 직접 실행하고, 위임이 필요한 일반 구현은 Luna/high를 기본으로 하되 고비용 실패 위험이 크면 Luna/max를 선택한다.
architecture: impl이 직접 실행 predicate와 worker effort 선택의 단일 정본이다. Luna/medium은 비교 실측 전 기본값에서 제외하고, high/max만 실제 라우팅에 사용한다. 다른 스킬과 contract는 기준을 복제하지 않고 impl을 참조하거나 허용 effort 범위를 반영한다. 정본 변경 뒤 동일 skill 및 agent 디렉터리를 활성 설치본으로 동기화한다.
tech_stack: [Markdown, PowerShell, Git]
slices:
  - id: 1
    title: 직접 실행과 Luna high/max 선택 계약을 모든 중복 설명에 일치시킨다
    files:
      create: []
      modify:
        - skills/codex/impl/SKILL.md
        - skills/codex/using-methodos/SKILL.md
        - skills/codex/plan/SKILL.md
        - skills/codex/setup-methodos/SKILL.md
        - contract/SKILL-ARTIFACTS.md
        - agents/codex/impl-checkpoint-reviewer.toml
        - C:/Users/hjcha/.agents/skills/impl/SKILL.md
        - C:/Users/hjcha/.agents/skills/using-methodos/SKILL.md
        - C:/Users/hjcha/.agents/skills/plan/SKILL.md
        - C:/Users/hjcha/.agents/skills/setup-methodos/SKILL.md
        - C:/Users/hjcha/.codex/agents/impl-checkpoint-reviewer.toml
      test: []
    verification:
      type: command
      command: "각 정본/활성 설치본 디렉터리의 file-set·SHA-256 일치 확인, rg로 직접 실행·Luna high/max 선택 정본과 참조 문구 확인"
      expected_exit_code: 0
    estimated_minutes: 15
    line_budget: 180
    public_contracts: []
    public_callers: ["impl", "using-methodos", "plan", "setup-methodos"]
    review_checkpoint: skip
    checkpoint_reason: null
    decision_needed: false
    user_facing_scenario: "작은 저위험 수정은 즉시 끝내고, 더 큰 변경만 필요한 수준의 worker에게 맡긴다."
    recommended: "impl에만 기준을 두고 나머지는 참조한다."
    options: []
self_review:
  coverage_gaps: []
  placeholders_found: []
  type_inconsistencies: []
---

## Slice 1

`impl`에 직접 실행 predicate, Luna high/max 선택 기준, 사용자 지정 실행 주체 우선, 직접 실행의 commit·검증·중단 조건을 둔다. Luna/medium은 비교 실측 전 기본 경로에서 제외한다. 다른 세 스킬과 contract는 `impl`을 유일한 기준 정본으로 참조하거나 선택 effort 범위를 반영한다. 활성 설치본은 정본 전체 디렉터리를 동기화하며, 각 파일 집합과 SHA-256을 비교한다.

PASS: 네 source/active skill 디렉터리와 checkpoint agent 쌍이 정확히 일치하고, 직접 실행·Luna high/max 기준은 `impl` 한 곳에만 상세 정의되며, 모든 설명·contract가 그 기준을 참조하거나 정확한 effort 범위를 반영한다.
