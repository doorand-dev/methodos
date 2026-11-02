# Worktree

사용자가 승인한 범위와 프로젝트의 생성·통합·정리 담당을 따른다. 기존 checkout·worktree를 우선 재사용하고, 새로 필요하면 앱의 `create_worktree`를 우선한다. 기준 commit·목적을 정하고 미커밋 변경은 옮기지 않으며 새 브랜치는 worktree 안에서 만든다.

## 통합

검증이 끝난 source commit과 base, 통합할 범위·경로, 양쪽 staged·unstaged·untracked 상태를 확인한다. 양쪽 index에 staged 변경이나 진행 중인 merge·rebase·cherry-pick이 있으면 그 작업을 대신 정리하지 않고 통합을 멈춘다.
기존 unstaged·untracked가 통합 경로·의미적 계약·검증 전제와 겹치지 않고 덮어쓰기·writer 경합 없이 보존되면 진행한다. Source 미커밋 변경에 의존한 검증은 commit의 검증으로 인정하지 않는다.
충돌·소유권·기준 commit이 불명확하면 구체적인 blocker를 보고한다. Git의 로컬 변경 보호를 force나 자동 stash로 우회하지 않는다. 승인된 commit만 통합하고 ancestry 또는 patch 동등성, 기존 변경 보존, 영향받는 결과를 확인한다. clean 상태를 만들려고 다른 세션 변경을 복원·삭제·이동·stash·일괄 커밋하지 않는다.

## 정리

앱 관리 worktree는 현재 앱의 `archive_worktree`를 우선한다. 작업 결과 통합, 필요한 tracked·untracked·ignored 파일 보존, active writer 종료와 사용자 정리 권한을 확인한다. 현재 cwd 대상은 밖으로 나온 뒤 처리한다. 통합 완료와 물리 정리 완료를 구분하고 push를 정리의 필수 조건으로 삼지 않는다.

이 공개 규칙은 자동 삭제 훅을 설치하지 않는다. 저장소의 기존 cleanup 스크립트는 선택 자료이며 이 안내만 복사했다고 사용 가능하거나 승인된 것이 아니다. 별도 채택 시 지원 인수·복구·보존 조건과 설치 경로를 검토하고, 명시적으로 승인된 대상만 처리한다. 잠금·권한 거부는 강제 삭제나 다른 도구로 우회하지 않는다.
