# 필요한 작업부터 골라 쓰는 Codex 스킬

긴 대화가 압축된 뒤 중요한 결정을 잊거나, 새 작업마다 같은 자동화를 다시 만들거나, 담당 채팅을 사람이 계속 깨워야 한다면 이 묶음에서 필요한 기능만 골라 쓸 수 있습니다. 스킬은 작업을 판단하는 지침이고, Codex wake는 실제 이벤트를 기존 채팅에 전달하는 Python 도구입니다.

이 문서는 이번 Codex 게시본의 진입점입니다. 저장소 루트의 공통 프로필과 이전 스킬은 별도 기존 자료이며, 모두 설치할 필요는 없습니다. Claude 영역은 이번 갱신 대상이 아닙니다.

| 하고 싶은 일 | 선택할 스킬 |
|---|---|
| 독립적인 작업을 나눠 맡기고 결과 회수 | `orch` |
| 같은 채팅의 압축 대비 / 새 채팅 인계 / 장기 할 일 | `snapshot` / `handoff` / `todo` |
| 특정 실수 원인 확인 / 세션의 반복 낭비 개선 | `blame-context` / `retro` |
| 코드 구조의 오독 유발 확인 / 프로젝트 청소 | `blame-code` / `gc` |
| 다음 AI 입력 검토 / 문맥 소비 경로 개선 | `context-novelist` / `improve-context` |
| 제품 사용 흐름의 빠진 요구 찾기 | `product-novelist` |
| 코드 구조 개선 / 반복 실행 재사용 | `improve-codebase-architecture` / `workflow-reuse` |
| 외부 시스템의 막힘·우회법 기록 / 지식 위치 선택 | `finding` / `ai-knowledge-routing` |
| 독자가 이해하는 한국어 글 / 최신 사례와 적용 한계 조사 | `purposeful-writing` / `trend-research` |

## 먼저 하나만 적용하기

1. `skills/codex/<선택한 이름>/SKILL.md`에서 호출 조건과 산출물을 읽습니다. 필요한 supporting 파일까지 해당 폴더를 `~/.agents/skills/<이름>/`로 복사합니다. 이미 있으면 차이를 검토해 필요한 부분만 반영합니다.
2. `agents/openai.yaml`이 있는 스킬은 해당 파일도 함께 둡니다. 설치가 기존 비활성 설정을 자동으로 해제하지는 않습니다. 자신의 Codex 설정과 새 채팅의 스킬 목록에서 노출 여부를 확인합니다.
3. `orch`·`handoff`·`blame-code`를 쓰면 [모델 정책 예시](rules/model-routing.json)의 placeholder를 현재 도구가 지원하는 모델·effort로 채우고 `configured`를 true로 바꿉니다. 값이 미설정인 채 실행하지 않습니다. `task-worker`와 blame-code의 reader/judge 프로필은 `agents/codex/`에서 필요한 것만 `~/.codex/agents/`로 복사하고 새 채팅의 생성 도구에 해당 역할이 노출되는지 확인합니다.
4. 규칙은 `contract/codex/rules/`에서 필요한 것만 `~/.codex/rules/`로 옮깁니다. wake를 사용할 때는 `contract/codex/codex-wake.md`도 `~/.codex/rules/codex-wake.md`로 복사합니다. 이 안내의 저장소 상대 링크는 원본 저장소에서 열고, 설치된 코드 위치는 안내에 따라 별도로 정합니다. [전역 AGENTS 예시](AGENTS.example.md)는 전체 덮어쓰기 대신 기존 권한·작업 방식에 맞게 합칩니다.
5. 작은 실제 작업에서 결과와 재작업을 확인합니다. 모델명이나 스킬 개수 자체가 품질을 보장하지는 않습니다.

서로 참조하는 스킬은 해당 기능을 사용할 때 함께 설치합니다. `context-novelist`의 로딩 참고는 `improve-context`, 문맥·재사용 개선의 HTML 기준은 `improve-codebase-architecture`에 있습니다. `blame-code`는 reader 2명과 judge 프로필이 필요합니다. 참조가 없으면 그 기능을 실행하기 전에 설치·경로를 확인합니다.

`trend-research`는 사용자가 설치한 Aside 진입점을 사용합니다. 브라우저 스킬과 로그인 환경은 이 묶음에 포함하지 않습니다. `ai-knowledge-routing`의 `<knowledge-root>`는 자기 프로젝트 지도에 선언해야 합니다. 예시의 `.Codex/`·`.claude_context/` 같은 산출 위치는 스킬 계약이므로 임의로 바꾸기 전에 소비 경로를 확인합니다.

## 작업이 끝났을 때 채팅이 이어받게 하기

[Codex wake 사용 안내](codex-wake.md)는 다운로드·빌드·외부 대기 조건이 끝났을 때 기존 담당 채팅을 재개하는 방법을 설명합니다. Python 표준 라이브러리 도구, 읽기 전용 probe, 오프라인 테스트를 함께 제공합니다. 설치된 앱 bridge를 이용하는 별도 도구이며 기본 Codex의 안정 API로 가정하지 않습니다.

## 공개 범위

이 게시본은 재사용 가능한 지침·프로필·도구입니다. 개인 작업 기록, 계정·쿠키·로그인 상태, 실제 채팅 ID, 모델 배정값, 자동화 예약, 프로젝트 데이터는 포함하지 않습니다. 설치·실행·외부 전송은 사용자의 선택과 권한 범위 안에서 이루어집니다.
