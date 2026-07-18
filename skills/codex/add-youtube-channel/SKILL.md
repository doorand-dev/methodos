---
name: add-youtube-channel
description: Use this skill whenever a user asks to add, create, register, bootstrap, audit, or re-run a new YouTube channel or a Shorts/long-form channel pair. Read the current project channel matrix and code before deciding what to change; do not trust a copied channel list. In 점검 mode, stay read-only and return a blocked preflight when required accounts, brand assets, or an approved CapCut source are missing. In 추가/만들기 mode, execute only after the preflight is closed, then validate runtime routing, branding, CapCut, and upload-target interpretation without uploading externally.
---

# 신규 YouTube 채널 추가

이 스킬은 현재 프로젝트의 채널 매트릭스와 코드를 point-of-use로 재탐색해 신규 채널의 등록 지점, 숏폼·롱폼 연결, 브랜드 자산, CapCut, 외부 대상 해석을 누락 없이 닫는다. 채널 ID, 현재 파일 목록, 설정값을 이 문서에 복제하지 않는다.

## 모드와 입력

요청의 동사를 먼저 판정한다.

- `점검`: 읽기 전용 사전점검만 수행한다. 파일·설정·템플릿·외부 시스템을 바꾸지 않는다.
- `추가` 또는 `만들기`: 필수 입력·충돌·승인 조건이 닫혀 `ready_to_change: true`일 때만 변경까지 수행한다. `new`·`partial` 상태의 신규/부분 등록도 이 조건을 충족하면 실행 대상이다.

항상 수집할 입력은 브랜드 표시명, 영문 런타임 기준명, 영상 형식 조합, 언어와 프로필이다. 형식별로 대상 계정 식별자, 산출물 위치, 승인된 CapCut 정본 위치와 승인 상태를 수집한다. 조건부로 기존 브랜드 자산 위치·브랜드 설명·외부 교차게시 대상을 수집한다.

결과를 바꾸는 입력이 비어 있으면 점검은 계속하되, 실제 변경 전에 누락값을 한 번에 질문한다. 쇼츠 없이 롱폼만 요청하면 현재 소스→롱폼 계약과 맞지 않으므로 변경하지 않고 별도 기능 확장으로 차단한다.

## 사전점검

다음 순서를 지킨다. 각 단계는 현재 저장소를 다시 읽어야 하며, 이 스킬의 예시나 기억을 정본으로 삼지 않는다.

1. `AGENTS.md`와 `.claude/rules/routing.md`를 읽고, 라우팅이 지시하는 문서·코드 소비자를 따른다.
2. `docs/channel_matrix.md` §4.5를 읽어 현재 형식 식별, 숏↔롱 연결, CapCut 배경·시간축 공백, 채널 ID 열거, 외부 배포 검증, 재실행 규칙을 확인한다.
3. 현재 코드에서 정의자·호출자·소비자를 `rg`로 다시 찾는다. 설정 블록 하나가 생겼다는 이유로 완료 처리하지 말고, 새 런타임·프로필·프롬프트·캐시·템플릿·업로드 대상이 실제 요청 경로에 전달되는지 추적한다.
4. 입력과 현재 값을 비교해 충돌을 분류한다. 런타임명, 표시명, 외부 대상, CapCut 식별자가 기존 값과 같거나 모호하면 덮어쓰지 말고 신규 추가인지 기존 채널 보정인지 확인한다.
5. 상태를 `new`(등록 없음), `partial`(일부 등록 또는 일부 검증), `candidate-complete`(요청 형식과 필수 산출물이 검증 직전까지 닫힘) 중 하나로 판정한다.
6. 등록 상태와 실행 준비를 분리한다. 필수 입력·충돌·승인된 정본·필요한 자산 증거가 모두 닫히면 `ready_to_change: true`로 표시하며, 그렇지 않으면 `false`로 둔다. `candidate-complete`만을 실행 전제처럼 사용하지 않는다.

사전점검 결과는 다음 필드를 모두 포함한다.

```text
mode, state, missing_inputs, conflicts
discovered_registration_categories, planned_change_categories
validation_commands, stop_conditions
```

`점검` 모드의 필수값 부족은 `blocked` 사전점검으로 반환한다. 계정·브랜드 자산·승인된 CapCut 정본이 없으면 부분 변경을 시작하지 않는다.

## 실행과 위임

`추가`·`만들기`에서만 승인된 범위의 최소 변경을 수행한다. 이미 올바른 항목은 보존하고, 빠졌거나 잘못된 항목만 수정하며, 중복 런타임·매핑·폴더를 만들지 않는다. 실행 전 관련 `AGENTS.md`, 라우팅, 매트릭스와 현재 코드 탐색 결과를 다시 확인한다.

- 브랜드 자산이 없으면 `$build-youtube-channel-kit`에 브랜드 설명, 필요한 산출물, 반환 파일과 승인 증거를 명시해 위임한다. 반환 증거가 닫히지 않으면 완료하지 않는다.
- 승인된 CapCut 정본이 있을 때만 프로젝트의 CapCut 포맷 캡처 프로토콜을 읽고 역할 추출·어댑터·검증을 수행한다. 승인 없는 템플릿을 추론하거나 자동 생성하지 않는다.
- 화면의 검정 배경 레이어와 시간축의 빈 프레임은 별도 입력·검증 항목으로 취급한다. 매트릭스 정책이 명시하지 않으면 시간축 프레임을 임의로 넣지 않는다.
- 요청하지 않은 형식의 런타임·롱폼 연결·템플릿을 만들지 않는다. 외부 계정 생성이나 업로드는 이 스킬의 실행에 포함하지 않는다.

### CapCut 상속 preflight와 검증

- 승인된 기존 채널/정본 draft를 상속하면 먼저 역할 inventory를 만들고 각 역할을 `inherit`·`replace`·`remove`로 분류한다. 최소 대상은 main/body video, silent hook visual, cut gaps(head/tail), date bar, title/subtitle/event box, channel text, image logo, reaction/parking cards, audio, `tracks[]` 배열 z-order다. 분류되지 않은 역할은 완료로 보지 않는다.
- 신규 채널 runtime에서 모든 channel-ID feature gate/allowlist를 `rg`로 재탐색하고 명시적으로 opt-in/out한다. 특히 hook visual, `cut_gaps`/gap cut, layout-specific logo injection을 확인하며, 상속된 기본값이나 allowlist 누락을 통과시키지 않는다.
- 승인된 image asset을 쓰는 brand-sensitive text→image 교체는 asset path와 SHA256, donor segment/material, clip transform/scale/render_index, full duration, local/OneDrive의 `draft_content.json`·`draft_meta_info.json` 경로 매핑을 acceptance evidence로 고정한다. 교체된 text segment는 active와 parked 모두 제거한다.
- parked 또는 out-of-timeline도 사용자에게 보이는 CapCut timeline surface로 취급한다. unwanted reaction/parking cards는 `0`이어야 하며, 남으면 실패다.

## 검증과 완료 판정

설정 블록 존재만 확인하지 말고 요청 형식별 실행 경로를 검증한다. 런타임 요청이 새 채널을 유지하는지, 기존 대표 브랜드의 표시명·태그·로고·경로가 후보·픽·CapCut·업로드 메타에 남지 않는지, 숏↔롱 소스 연결과 후보 메타가 새 정체성을 유지하는지 확인한다. CapCut 산출물을 생성·수정한 경우 레이어·전체 지속시간·z-order와 육안 승인 증거를 확인하며, 증거가 없으면 `complete`를 반환하지 않는다. CapCut을 요청하지 않은 형식은 N/A로 명시한다.

CapCut 산출물은 실제 승인된 reference draft와 역할 matrix로 differential 검사한다. active date bar, hook visual, cut gaps/head-tail, text/image 교체, unwanted cards, track-array z-order는 각각 별도 oracle로 판정하고, z-order는 `render_index`가 아니라 정본 `tracks[]` 배열 순서와 대조한다. 기존 reference channel template/runtime/draft의 hash와 mtime은 변경 전후 불변 회귀로 확인한다. 기계검증만 통과한 상태에서 `complete`를 반환하지 않으며, visual HITL 스크린샷 피드백이 생기면 기존 mechanical `DONE`을 재개방하고 누락 역할을 다음 inventory checklist에 환류한다.

업로드 검증은 전송 직전까지만 한다. 제목·미디어·런타임·대상 계정·외부 프로필·`draft`/`queue`/`scheduled` 해석과 상태 링크를 확인하되 실제 YouTube·TikTok 전송은 하지 않는다.

모든 필수 검사 통과 시에만 아래 형식으로 반환한다.

```text
status: complete | blocked | failed
state: new | partial | candidate-complete
evidence: 형식별 공통·형식별·브랜드·CapCut·외부 대상 검사
last_valid_artifact: 마지막으로 유효한 산출물과 검증
remaining_changes: 남은 변경 또는 없음
resume_when: blocked/failed일 때의 재개 조건
```

필수 검사가 하나라도 미통과면 `complete`를 쓰지 않는다. 실패 시 실패 단계, 마지막 유효 산출물, 남은 변경, 재개 조건을 기록한다. 재실행은 같은 사전점검에서 시작하고 정상 항목을 보존한다.
