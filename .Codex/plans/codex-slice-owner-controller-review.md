---
slug: codex-slice-owner-controller-review
created_at: 2026-07-17
status: approved
spec_ref: docs/specs/codex-slice-owner-controller-review.md
source_spec:
  path: docs/specs/codex-slice-owner-controller-review.md
  approved_at: 2026-07-17T00:00:00+09:00
  sha: c389cb08b6a43e9db0504e59a230d26d9959fc7c
approved_plan_revision: 151175c41a5dea8ba1998b220c28acbecfb5b2df
goal: Codex 구현을 한 slice당 한 owner로 닫고 reviewer transport는 controller가 소유하며 repair 재검토는 attempt 1 reviewer thread를 재사용한다.
architecture: impl이 slice owner와 controller의 책임 경계를 단일 정본으로 소유한다. 구현 owner는 RED/GREEN·로컬 검증·WHY commit·report에서 종료하고 controller가 checkpoint와 final reviewer를 호출한다. attempt 2 이상은 attempt 1 reviewer thread에 stable finding만 scoped follow-up한다. Luna/high가 기본이며 max는 분해 뒤 남는 고비용 불확실성이나 high의 실증 실패에만 사용한다.
tech_stack: [Markdown, TOML, Python, PowerShell, Git]
slices:
  - id: 1
    title: slice owner와 controller-owned review topology를 Codex 정본 및 활성 설치본에 일치시킨다
    files:
      create: [.Codex/plans/codex-slice-owner-controller-review.md, docs/specs/codex-slice-owner-controller-review.md]
      modify: [skills/codex/impl/SKILL.md, skills/codex/plan/SKILL.md, skills/codex/using-methodos/SKILL.md, skills/codex/setup-methodos/SKILL.md, skills/codex/impl-novelist/SKILL.md, agents/codex/impl-checkpoint-reviewer.toml, agents/codex/impl-novelist.toml, agents/codex/(remove obsolete scoped reviewer), contract/SKILL-ARTIFACTS.md, README.md, docs/specs/emergency-self-execution.md, .Codex/plans/emergency-self-execution.md, C:/Users/hjcha/.agents/skills/impl/SKILL.md, C:/Users/hjcha/.agents/skills/plan/SKILL.md, C:/Users/hjcha/.agents/skills/using-methodos/SKILL.md, C:/Users/hjcha/.agents/skills/setup-methodos/SKILL.md, C:/Users/hjcha/.agents/skills/impl-novelist/SKILL.md, C:/Users/hjcha/.codex/agents/impl-checkpoint-reviewer.toml, C:/Users/hjcha/.codex/agents/impl-novelist.toml, C:/Users/hjcha/.codex/agents/(remove obsolete scoped reviewer)]
      test: [hooks/common/test_impl_novelist_scope.py]
    verification:
      type: command
      command: "py -3 hooks/common/test_impl_novelist_scope.py"
      expected_exit_code: 0
    estimated_minutes: 25
    line_budget: 200
    public_contracts: ["Codex impl execution and reviewer routing", "implementation review artifact provenance"]
    public_callers: [impl, plan, using-methodos, setup-methodos, impl-novelist, reviewer-profiles]
    review_checkpoint: required
    checkpoint_reason: schema_or_public_contract
    decision_needed: false
    user_facing_scenario: "각 slice 구현자는 구현과 검증 뒤 즉시 반환하고 controller가 필요한 review를 관제하며 repair 재검토는 기존 reviewer 문맥을 재사용한다."
    recommended: "한 slice 한 owner, controller-owned reviewer, same-thread scoped repair review"
    options: []
self_review:
  coverage_gaps: []
  placeholders_found: []
  type_inconsistencies: []
---

## Slice 1

`impl`에 한 slice·한 owner와 controller-owned reviewer 경계를 둔다. Worker는
선언 경로 구현, RED/GREEN, 로컬 검증, WHY commit, `impl-worker-report`에서 종료한다.
Controller는 고위험 checkpoint와 조립 완료 final reviewer를 직접 fresh 호출한다.
BROKEN이면 같은 owner가 repair하고 attempt 1 reviewer의 같은 thread에 finding ID,
repair commit, 영향 selector만 scoped follow-up한다. 별도 scoped reviewer profile은
삭제한다. 다중 slice·교차 모듈·파일 수·plan 존재는 max 조건에서 제거한다.

PASS: 정본과 활성 설치본의 대응 파일 SHA-256이 일치하고 obsolete scoped profile이
양쪽에서 사라지며, 관련 테스트와 plan preflight가 통과하고 legacy nested review
문구 및 구조 규모 기반 max 문구가 남지 않는다.
