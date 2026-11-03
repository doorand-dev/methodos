# Worktree

사용자가 승인한 범위와 프로젝트의 생성·통합·정리 담당을 따른다. 기존 checkout·worktree를 우선 재사용하고, 새로 필요하면 앱의 `create_worktree`를 우선한다. 기준 commit·목적을 정하고 미커밋 변경은 옮기지 않으며 새 브랜치는 worktree 안에서 만든다.

## 통합

검증이 끝난 source commit과 base, 통합할 범위·경로, 양쪽 staged·unstaged·untracked 상태를 확인한다. 양쪽 index에 staged 변경이나 진행 중인 merge·rebase·cherry-pick이 있으면 그 작업을 대신 정리하지 않고 통합을 멈춘다.
기존 unstaged·untracked가 통합 경로·의미적 계약·검증 전제와 겹치지 않고 덮어쓰기·writer 경합 없이 보존되면 진행한다. Source 미커밋 변경에 의존한 검증은 commit의 검증으로 인정하지 않는다.
충돌·소유권·기준 commit이 불명확하면 구체적인 blocker를 보고한다. Git의 로컬 변경 보호를 force나 자동 stash로 우회하지 않는다. 승인된 commit만 통합하고 ancestry 또는 patch 동등성, 기존 변경 보존, 영향받는 결과를 확인한다. clean 상태를 만들려고 다른 세션 변경을 복원·삭제·이동·stash·일괄 커밋하지 않는다.

## 정리

앱 관리 worktree는 `archive_worktree`를 우선하고 필요한 ignored 파일은 먼저 별도 보존한다. 앱 도구가 지원하지 않는 worktree는 아래 CLI의 queue를 사용한다. 현재 cwd 대상에 `git worktree remove`를 직접 시도하지 않는다.

| disposition | 사용 조건 |
|---|---|
| merged | clean이며 통합 완료. push는 정리 조건이 아님 |
| verification | clean 검증 전용 worktree |
| discarded | 사용자가 해당 worktree의 폐기를 명시. 미통합·미커밋 내용도 폐기 대상 |
| preserved | 승인된 정리·통합 범위에서 통합 완료, 필요한 tracked·untracked·index 고유 내용·ignored의 외부 보존과 내용 일치, active writer 종료를 caller가 확인 |

`preserved`의 실제 copy·compare는 caller 책임이며 queue 등록이 그 증거를 대신하지 않는다. 조건이 충족되면 dirty/untracked 자체로 재승인을 요구하지 않는다. CLI는 lease·worktree identity·HEAD·내용 snapshot과 필요한 통합 상태를 다시 확인하고, 변경된 항목은 보류한다. `preserved` snapshot에는 index·ignored도 포함된다.

PowerShell에서 다음 변수를 정하고 필요한 동작 하나만 실행한다. `--base-ref`는 통합 대상이 primary의 현재 브랜치와 다를 때 지정한다.

```powershell
$cleanupScript = Join-Path $env:USERPROFILE '.codex/rules/scripts/worktree-cleanup.py'
python $cleanupScript --enqueue '<absolute-worktree-path>' --disposition merged
python $cleanupScript --dequeue '<absolute-worktree-path>'
python $cleanupScript --reap
```

Queue(`~/.codex/worktrees/cleanup.md`)는 정리 승인과 identity-bound lease다. 재사용 전에 dequeue 성공을 확인하고, 재사용 종료 뒤 조건을 다시 확인해 새 lease로 enqueue한다.
`--reap`은 정리 요청이나 해당 작업 종료 때 대상 밖에서만 실행하며 앱 시작·resume에서 자동 실행하지 않는다. 현재 cwd 항목을 만나면 CLI는 삭제 대신 queue·lease를 취소하므로 나중에 조건을 다시 확인해 등록한다. 잠금·변경으로 보류된 항목은 다음 승인된 정리에서 재처리한다.
등록된/내용 있는 worktree는 queue 밖에서 제거하지 않는다. CLI는 `~/.codex/worktrees` 아래 빈 orphan 디렉터리도 정리할 수 있다. 잠금으로 남으면 경로·원인·다음 담당을 보고하고, 결과의 보존·통합 완료와 물리 정리 완료를 구분한다.
