# Worktree

배포 경로: `~/.codex/rules/worktree.md`.

활성 프로젝트 오케 계약이 worktree 생성·통합·정리를 금지하거나 별도 소유하면 그 계약이 이 문서보다 우선한다.

## 진입

- 기준 브랜치와 목적을 확인한다.
- 현재 checkout의 미커밋 변경은 옮기지 않는다.
- 새 브랜치가 필요하면 worktree 안에서 만든다.

## 퇴장 / merge

- 여러 worktree가 병렬로 같은 저장소를 고친다. 병합 전 base와 작업 worktree가 clean인지 확인한다.
- 내 변경만 안전하게 base에 얹는다. 다른 세션 변경을 되돌리거나 덮지 않는다.
- 충돌, 의미상 겹침, dirty 상태, base 불확실이 있으면 통합하지 않고 보고한다.

## 정리

- 현재 cwd가 제거 대상 worktree 안이면 직접 제거하지 않는다. 이 경우 `git worktree remove`를 시도하지도 않는다. 시도하면 git 등록과 `.git` 파일이 먼저 삭제된 뒤 디렉터리 삭제만 실패해, 대기열 등록과 소유권 검증이 모두 막힌 고아 경로가 남는다.
- 그 밖의 worktree가 clean이고 통합까지 끝났으면 `git worktree remove --force`로 즉시 제거한다. 대기열은 현재 cwd worktree와 즉시 제거가 실패한 경우에만 쓴다.
- dirty·untracked·unmerged·무참조 고유 commit 항목은 제거하지도 대기열에 넣지도 말고 정확한 blocker만 보고한다.
- `--disposition merged`는 통합이 실제로 끝났을 때만 쓴다. 대기열 등록 명령이 미통합 commit을 발견하면 거부하므로, 거부되면 등록을 우회하지 말고 통합 상태를 먼저 해결한다.
- 이미 고아가 된 경로는 해당 worktree를 cwd로 쥔 세션이 살아 있는 동안 삭제되지 않는다. 그 세션을 보관(archive)해 잠금이 풀린 뒤 빈 디렉터리를 제거한다.
- clean + merge/push 완료 worktree는 다음 명령으로 `~/.codex/worktrees/cleanup.md` 대기열에 넣는다.
  `C:\Users\hjcha\AppData\Local\Programs\Python\Python311\python.exe C:\Users\hjcha\.codex\hooks\worktree-cleanup.py --enqueue <path> --disposition merged`
- 사용자가 "폐기"를 명시한 worktree는 미커밋 변경이 있어도 같은 명령에 `--disposition discarded`를 써 대기열에 넣는다. 추측으로 폐기 대기열에 넣지 않는다.
- clean 검증 전용 worktree는 `--disposition verification`으로 대기열에 넣는다.
- SessionStart hook이 대기열을 다른 cwd에서 처리한다. 잠겨 있으면 항목을 유지하고 다음 시작에 재시도한다.
- `cleanup.md`에 없는 worktree와 현재 cwd worktree는 자동 삭제하지 않는다.
