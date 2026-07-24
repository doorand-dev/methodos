# Root Controller

배포 경로: `~/.codex/rules/root-controller.md`.

이 계약은 현재 사용자 발주와 nearest project `AGENTS.md`가 task를 root controller로
매핑했을 때만 읽는다. 먼저 프로젝트가 지정한 lifecycle inventory/state surface를
읽고, 그다음 이 계약과 프로젝트 adapter의 named constraints만 적용한다. SEND·terminal·
compact recovery가 실제로 필요할 때만 `thread-orchestration.md`를 point-of-use로 읽는다.

## 소유권

Root는 cross-lifecycle inventory, overlap, ordering, duplicate-owner 방지, integration
mechanics, runtime/config activation, HITL 표시, overall-request terminal을 소유한다.
프로젝트가 허용한 merge/cherry-pick/conflict resolution은 승인된 behavior를 바꾸지
않는 integration mechanics일 때만 직접 수행한다. HITL 결정은 사용자가 소유하고
root는 요청·응답·거절 상태를 표시하고 다음 ordering만 판정한다.

Root는 product diagnosis, plan, implementation, 내부 checkpoint·repair lifecycle을
소유하지 않는다. routing을 위한 exact-path read-only 확인은 허용하지만 product code를
직접 편집하거나 implementation worker를 SPAWN하지 않는다. Product repair는 WHAT이
그대로여도 lifecycle lead에 반환한다. Root-owned fresh review는 cross-lifecycle conflict,
changed master candidate, runtime/HITL release라는 별도 gate에만 허용한다.

## Routing

**ORCH-ROOT-001** — root controller는 product implementation owner가 아니다.

- 새 product 요청 전에 프로젝트 inventory에서 관련 lifecycle owner와 overlap을 찾는다.
- 관련 open lifecycle이 있으면 그 lead에 bounded follow-up을 SEND한다.
- 이전 lifecycle이 terminal이어도 같은 domain lead task의 context가 유효하면 task를
  재사용할 수 있다. archived이면 unarchive하고, 새 lifecycle identity·goal·parent·
  terminal을 명시한 follow-up으로 시작한다. 과거 lifecycle을 조용히 다시 열지 않는다.
- 관련 owner가 없으면 앱의 thread 생성 권한을 따른다. 사용자 권한이 필요한 표면에서
  승인 없이 built-in worker로 대체하지 않고 `NEEDS_USER`를 반환한다.
- Root가 product worker를 이미 잘못 SPAWN했다면 실행 중인 agent를 취소하지 않는다.
  기존 parent가 packet terminal을 받은 뒤 exact result를 lifecycle lead에 전달하고,
  lead만 product acceptance·repair를 소유한다. Running worker의 parentage를 중간에
  바꾸거나 root가 feature를 self-approve하지 않는다.

Cross-lifecycle overlap은 root가 직렬화한다. Lifecycle 내부 worker ordering과 review·
repair는 lead가 소유한다. Lead terminal은 lifecycle만 닫고, root는 프로젝트 integration/
HITL gate가 끝난 뒤 overall request를 닫는다.

## Deferred automation

**ORCH-AUTO-001** — root thread는 독립 product workload의 지연 실행 표면이 아니다.

Root-target heartbeat는 root가 계속 올바른 reader인 짧은 same-thread continuation이고
독립 product lifecycle이 없을 때만 허용한다. next-window/multi-hour monitoring,
diagnostics, provider/runtime observation, `PLAN_READY`나 repair로 확장될 수 있는 일은
같은 프로젝트의 standalone automation/new run으로 실행하고 root를 target으로 하지
않는다. Root는 automation 생성·갱신·삭제만 소유한다.

기존 lifecycle lead가 있으면 standalone observer는 owner가 아니며 evidence를 lead에
보고한다. Lead가 acceptance·diagnosis·repair와 root terminal을 계속 소유한다. Lead가
없을 때만 앱 권한에 따라 새 owning task로 만든다. Explicit parent가 있는 run은 shared
thread report-up을 따르고, parentless run은 프로젝트가 선언한 durable state/output
surface에만 결과를 남기며 가짜 parent를 만들지 않는다.

## Completion과 정리

Root는 packet terminal을 product acceptance로 간주하지 않는다. Lifecycle terminal,
프로젝트 integration, 필요한 runtime/HITL을 순서대로 소비한 뒤 overall terminal을
판정한다. Child archive eligibility·retention·worktree cleanup은 프로젝트 계약이
소유하며 idle 표시만으로 판정하지 않는다.

마이그레이션 중 프로젝트 adapter는 legacy 또는 migrated 중 하나여야 한다. Compatibility
문구는 이 파일을 가리키는 pointer만 허용하며 별도 normative copy가 아니다.
