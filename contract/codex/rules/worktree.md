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

- 현재 cwd가 제거 대상 worktree 안이면 직접 제거하지 않는다.
- 모든 세션이 아래 cleanup 대기열 경로를 사용한다. dirty·untracked·unmerged·무참조 고유 commit 항목은 대기열에 넣지 말고 정확한 blocker만 보고한다.
- clean + merge/push 완료 worktree는 다음 명령으로 `~/.codex/worktrees/cleanup.md` 대기열에 넣는다.
  `C:\Users\hjcha\AppData\Local\Programs\Python\Python311\python.exe C:\Users\hjcha\.codex\hooks\worktree-cleanup.py --enqueue <path> --disposition merged`
- 사용자가 "폐기"를 명시한 worktree는 미커밋 변경이 있어도 같은 명령에 `--disposition discarded`를 써 대기열에 넣는다. 추측으로 폐기 대기열에 넣지 않는다.
- clean 검증 전용 worktree는 `--disposition verification`으로 대기열에 넣는다.
- SessionStart hook이 대기열을 다른 cwd에서 처리한다. 잠겨 있으면 항목을 유지하고 다음 시작에 재시도한다.
- `cleanup.md`에 없는 worktree와 현재 cwd worktree는 자동 삭제하지 않는다.
