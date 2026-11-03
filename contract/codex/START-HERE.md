# 필요한 작업부터 골라 쓰는 Codex 스킬

긴 대화가 압축된 뒤 중요한 결정을 잊거나, 새 작업마다 같은 자동화를 다시 만들거나, 담당 채팅을 사람이 계속 깨워야 한다면 이 묶음에서 필요한 기능만 골라 쓸 수 있습니다. 스킬은 작업을 판단하는 지침이고, Codex wake는 실제 이벤트를 기존 채팅에 전달하는 Python 도구입니다.

처음 설치한다면 [영문 Quickstart](QUICKSTART.md)에서 `snapshot` 하나로 시작합니다. 같은 채팅의 압축 대비, 새 채팅 인계, 작업 분담을 각각 요청문 → 예상 결과 → 확인 방법으로 따라갈 수 있습니다. 스킬 본문과 이 목록은 현재 한국어이며, 영문 안내의 예제는 영어 응답을 요청합니다.

이 문서는 전체 선택 목록과 추가 도구 안내입니다. 아래 작업별 스킬과 선택 도구 중 필요한 것만 설치합니다.

| 하고 싶은 일 | 선택할 스킬 |
|---|---|
| 독립적인 작업을 나눠 맡기고 결과 회수 | `orch` |
| 같은 채팅의 압축 대비 / 새 채팅 인계 / 장기 할 일 | `snapshot` / `handoff` / `todo` |
| 특정 실수 원인 확인 / 세션의 반복 낭비 개선 | `blame-context` / `retro` |
| 코드 구조의 오독 유발 확인 / 프로젝트 청소 | `blame-code` / `gc` |
| 다음 AI 입력 검토 / 문맥 소비 경로 개선 | `context-novelist` / `improve-context` |
| 제품 사용 흐름의 빠진 요구 찾기 | `product-novelist` |
| UI 처음 만들기 / 화면 리뷰 / 기존 디자인 전후 비교·개선 | [`design-ui`](../../skills/codex/design-ui/SKILL.md) |
| 코드 구조 개선 / 반복 실행 재사용 | `improve-codebase-architecture` / `workflow-reuse` |
| 외부 시스템의 막힘·우회법 기록 / 지식 위치 선택 | `finding` / `ai-knowledge-routing` |
| 독자가 이해하는 한국어 글 / 최신 사례와 적용 한계 조사 | `purposeful-writing` / `trend-research` |

## 선택 도구

| 도구 | 남기는 용도와 실행 조건 |
|---|---|
| `model-router` | 명시적으로 요청한 실행 관측·모델 비교. 계측 환경과 모델 지원을 확인하고 API 단가는 실행 시 공식 자료에서 확인합니다. |
| `ask-chatgpt-pro` | 명시적으로 요청한 ChatGPT Pro 검토. 로그인과 별도 브라우저 어댑터가 필요하며 현재 연결 호환성은 설치 환경에서 확인합니다. 사용자 브라우저 정책이 우선입니다. |
| `report-kit` | 명시적으로 선택하는 HTML 템플릿 시제품. 표본 데이터는 사용자의 실제 자료로 교체합니다. |
| `add-youtube-channel` | 채널 온보딩 문서·CapCut 연결을 갖춘 YouTube 파이프라인용 지침. 범용 채널 생성 도구가 아니며 적용 전 프로젝트 구조와 필수 입력을 확인합니다. |

## 먼저 하나만 설치하고 호출하기

1. `skills/codex/<선택한 이름>/SKILL.md`에서 호출 조건과 산출물을 읽습니다. 필요한 supporting 파일까지 해당 폴더를 `~/.agents/skills/<이름>/`로 복사합니다. 이 묶음의 전역 규칙은 이 사용자 경로를 참조하므로, 프로젝트 범위의 `.agents/skills/`를 선택하면 참조도 함께 조정합니다. 이미 있으면 차이를 검토해 필요한 부분만 반영합니다.
2. `agents/openai.yaml`이 있는 스킬은 해당 파일도 함께 둡니다. 설치가 기존 비활성 설정을 자동으로 해제하지는 않습니다. 자신의 Codex 설정과 새 채팅의 스킬 목록에서 노출 여부를 확인합니다.
3. `snapshot` 단독에는 모델 정책이나 custom agent가 필요하지 않습니다. `orch`와 `handoff`의 최소 구성은 [Quickstart 설치 표](QUICKSTART.md#install-only-the-required-components)를 따릅니다. [모델 정책 예시](rules/model-routing.json)는 실제 사용하는 등급의 placeholder를 지원되는 모델·effort로 채우고 사용하지 않는 등급을 제외한 뒤 `configured`를 true로 바꿉니다. `blame-code`까지 선택하면 reader/judge 프로필과 그 작업에 필요한 모델 경로도 준비합니다.
4. 규칙은 `contract/codex/rules/`에서 필요한 것만 `~/.codex/rules/`로 옮깁니다. [전역 AGENTS 예시](AGENTS.example.md)는 전체 덮어쓰기 대신 기존 권한·작업 방식에 맞게 합칩니다.
5. 작은 실제 작업에서 결과와 재작업을 확인합니다. 모델명이나 스킬 개수 자체가 품질을 보장하지는 않습니다.

Codex CLI·IDE에서는 `$snapshot`처럼 이름을 명시하거나 자연어로 요청할 수 있습니다. `agents/openai.yaml`에 `allow_implicit_invocation: false`가 있으면 명시 호출이 필요합니다. 예를 들어 `gc`는 “gc”·“/gc”를 요청했을 때만, `handoff`는 새 채팅 인계가 필요할 때 읽습니다. 호출 문법과 발견 경로는 [공식 스킬 안내](https://developers.openai.com/codex/skills), 프로필 형식은 [공식 custom agent 안내](https://developers.openai.com/codex/subagents#custom-agents)에서 확인할 수 있습니다.

서로 참조하는 스킬은 해당 기능을 사용할 때 함께 설치합니다. `context-novelist`의 로딩 참고는 `improve-context`, 문맥·재사용 개선의 HTML 기준은 `improve-codebase-architecture`에 있습니다. `blame-code`는 reader 2명과 judge 프로필이 필요합니다. 참조가 없으면 그 기능을 실행하기 전에 설치·경로를 확인합니다.

`model-router`의 Pro 검토 참조에는 `ask-chatgpt-pro`가 필요합니다. 추가 실행 도구는 해당 기능을 선택할 때만 설치합니다. 아래 원본 경로는 저장소 루트 기준입니다.

| 선택 기능 | 원본 → 설치 위치 | 확인할 점 |
|---|---|---|
| worktree 정리 CLI | `hooks/common/worktree-cleanup.py` → `~/.codex/rules/scripts/worktree-cleanup.py` | `--help`로 명시적 동작 인수를 확인합니다. 시작·resume 훅에는 등록하지 않습니다. |
| wake 운영 안내 | `contract/codex/codex-wake.md` → `~/.codex/rules/codex-wake.md` | 코드 설치 위치는 안내에서 선택합니다. 저장소 상대 링크는 원본 저장소에서 엽니다. |
| Pro 예약 보조 | `contract/codex/rules/scripts/codex-heartbeat-rrule.ps1` → `~/.codex/rules/scripts/codex-heartbeat-rrule.ps1` | `AutomationId`는 경로가 아닌 단일 ID입니다. 앱 도구와의 호환성과 예약·전송 권한을 별도로 확인합니다. 설치만으로 실행되지 않습니다. |


예약 helper의 `-Apply`는 대상 파일이나 상위 경로에 junction·symlink·hardlink가 있으면 거절합니다. 링크로 옮긴 사용자 폴더도 해당하므로 이 기능을 선택하기 전에 설치 경로를 확인합니다.

`trend-research`는 사용자가 설치한 Aside 진입점을 사용합니다. 브라우저 스킬과 로그인 환경은 이 묶음에 포함하지 않습니다. `ai-knowledge-routing`의 `<knowledge-root>`는 자기 프로젝트 지도에 선언해야 합니다. 예시의 `.Codex/`·`.claude_context/` 같은 산출 위치는 스킬 계약이므로 임의로 바꾸기 전에 소비 경로를 확인합니다.

`design-ui`는 생성·리뷰·개선 중 필요한 절차만 읽습니다. `references/`와 `agents/openai.yaml`을 함께 복사하고, 실제 화면 검증에는 자기 환경의 브라우저 진입점을 준비합니다. Aside를 쓰는 환경이면 별도 설치된 `aside-browser`를 따릅니다. Taste의 방향 설정·비평 절차를 참고했으며 Taste 설치나 독립 실행 스크립트는 필요하지 않습니다.

## 작업이 끝났을 때 채팅이 이어받게 하기

[Codex wake 사용 안내](codex-wake.md)는 다운로드·빌드·외부 대기 조건이 끝났을 때 기존 담당 채팅을 재개하는 방법을 설명합니다. Python 표준 라이브러리 도구, 읽기 전용 probe, 오프라인 테스트를 함께 제공합니다. 설치된 앱 bridge를 이용하는 별도 도구이며 기본 Codex의 안정 API로 가정하지 않습니다.

## 업데이트와 선택 제거

[Quickstart의 관리 절차](QUICKSTART.md#update-or-remove-selected-components)에서 설치한 스킬·프로필·공유 규칙별로 갱신과 제거 범위를 확인합니다. 기존 스냅샷·handoff 자료와 사용자 모델 정책은 설치 파일과 구분해 보존합니다. 공유 파일을 스킬 하나의 전용 파일로 보고 지우지 않습니다.

## 공개 범위

이 게시본은 재사용 가능한 지침·프로필·도구입니다. 개인 작업 기록, 계정·쿠키·로그인 상태, 실제 채팅 ID, 모델 배정값, 자동화 예약, 프로젝트 데이터는 포함하지 않습니다. 설치·실행·외부 전송은 사용자의 선택과 권한 범위 안에서 이루어집니다.
