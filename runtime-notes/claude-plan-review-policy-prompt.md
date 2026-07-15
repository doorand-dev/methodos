# Claude 담당자 실행 프롬프트 — plan 검증 비용 축소

Claude Code 쪽 Methodos 정본에 아래 정책을 반영하라. Codex 쪽 파일과 전역 설치본은 수정하지 않는다.

## 읽을 정본

- `skills/claude/plan/SKILL.md`
- `skills/claude/plan-verify/SKILL.md`
- `skills/claude/decision/SKILL.md`
- `skills/claude/impl-verify/SKILL.md`
- `agents/claude/decision-reviewer.md`
- `agents/claude/plan-verify-reviewer.md`
- `agents/claude/impl-verify-reviewer.md`
- `contract/SKILL-ARTIFACTS.md`
- Codex 참고(동일 topology 아님): `hooks/common/plan_preflight.py`, `hooks/common/test_plan_preflight.py`, `skills/codex/plan/SKILL.md`, `agents/codex/decision-reviewer.toml`, `runtime-notes/codex.md`. Codex는 automatic plan-verify를 제거했으므로 preflight와 decision predicate만 참고한다.

## 금지 경계

- `~/.claude/**`, `~/.codex/**`, 설치된 전역 skill/agent/hook/settings 파일을 수정하지 말 것.
- Codex source(`skills/codex/**`, `hooks/codex/**`)를 수정하지 말 것.
- runtime artifact watcher나 heartbeat를 reviewer 완료 회수 용도로 쓰지 말 것.

## 수정 목표

1. 최초 approved plan만 full plan-verify한다. 이미 DONE인 baseline의 amendment는 `amendment.baseline_status: DONE`와 변경 slice `scope`를 사용해 baseline 전체가 아닌 delta만 scoped review한다.
2. semantic reviewer 전에 `hooks/common/plan_preflight.py <plan> --repo <project_root>`를 실행한다. FAIL은 planner가 고치며 reviewer attempt를 소모하지 않는다. preflight PASS를 review artifact evidence에 인용한다.
3. source spec SHA, 사용자 체감 동작, 권한/데이터, 비가역 작업, public contract, cross-slice ownership 변화 또는 scope 밖 가정이 나오면 scoped review를 full로 승격한다.
4. `decision_needed=false`, M2 delta 없음, public behavior/authority/data 변화 없음인 behavior-preserving 구조 보정은 decision-reviewer를 skip한다. “architecture change” 단독은 조건이 아니다. 보안·권한·공개 계약·사용자 자산·비가역·cross-slice ownership과 다수의 사용자 결정만 decision-reviewer 대상이다.
5. DONE baseline amendment의 semantic review는 기본 1회, preflight로 고친 기계 결함 뒤 scoped re-review 1회까지만 허용한다. 동일 critical 반복 또는 실제 사용자 결정이 새로 필요할 때만 full/escalate한다.
6. decision-reviewer와 plan-verify-reviewer의 중복을 없앤다. decision-reviewer가 [0]/[1A]/[1B]/[3H]/[3J]을 검토했다면 plan-verify는 해당 evidence의 해결 여부만 확인하고 [1C]/[1D]/[2H]/[3I], ADR, 글로벌 룰, 내부 정합성을 담당한다.
7. reviewer dispatch 뒤에는 parent controller가 Agent 결과를 직접 회수한다. Claude 런타임의 정상 completion primitive를 사용하고 watcher/heartbeat polling으로 완료를 판정하지 않는다.
8. `contract/SKILL-ARTIFACTS.md`의 plan frontmatter schema와 Claude plan skill의 schema를 같이 갱신한다. `line_budget: 1..200`, `public_contracts`, `public_callers` 및 amendment 메타를 반영한다.

## 검증

먼저 아래 회귀 검사를 RED로 확인하고, 수정 후 GREEN을 확인한다.

```powershell
py -3 -m unittest hooks/common/test_plan_preflight.py
```

그 다음 `rg`로 Claude skill/agent와 contract의 predicate, scoped/full 승격 조건, preflight command, completion 회수 규칙이 일치하는지 확인한다. 변경 파일만 명시 pathspec으로 stage하고, WHY를 담은 한글 커밋을 만든다. branch/worktree/push는 하지 않는다.
