---
name: web-model-review
description: "Aside REPL로 AI Studio Gemini Flash 또는 ChatGPT Pro에 선택한 코드·문서를 검토받고, 필요하면 최종 답변에서 기존 Codex 채팅을 재개한다. 자료 준비만 요청받으면 전송하지 않는다."
---

# Web Model Review

브라우저에 로그인된 외부 모델로 검토할 때 사용한다. 모델·검토 질문·선택 파일은 사용자의 요청과 현재 작업에서 정한다. 사용자가 다른 전송 방식을 지정했다면 이 스킬로 바꾸지 않는다.

## 시작할 때

- 설치된 `aside-browser` 스킬과 `aside guide`, `aside guide repl`을 읽는다. Google 앱은 Aside의 `google-accounts` 스킬도 읽는다. 브라우저 조작은 `aside repl`을 사용하며 별도 에이전트에 위임하거나 다른 브라우저로 조용히 전환하지 않는다.
- Python 3.10+와 PATH의 Aside CLI가 필요하다. 턴 종료 후 Wake 실행은 Windows 로컬 Codex 앱 및 별도 `codex_wake.py`가 필요하다. 설치·연결 조건과 명령은 [실행 세부](references/operations.md#설치와-의존성)를 해당 상황에서 읽는다.
- 모델과 추론량을 현재 UI에서 확인한다. 이름이 없거나 접근이 막히면 다른 모델로 대체하지 않는다. Flash 모델명은 고정 지원 목록이 아니다.

## 자료 준비

질문에는 목표·변경 가능 범위·판단 기준을 적고, 필요한 원문 파일만 선택한다. 전체 채팅·운영 지침을 기본으로 넣지 않는다.

`scripts/review_packet.py --root <대상 프로젝트> --question … --context <파일> --reviewer flash|pro --out <새 폴더>`가 진입점과 세부 원문을 나눈다. `entry.md`로 범위를, 필요할 때 `details.md`로 근거를 확인한다. 외부에 보낼 `prompt.txt`에는 두 내용이 함께 들어간다. `--reviewer`는 라우팅 표기이며 모델 설정을 바꾸지 않는다.

## 검토 실행

실제 검토 전송이 승인된 경우에만 선택 본문을 전송한다. 파일 업로드나 API 호출 대신 선택한 UTF-8 본문을 웹 UI로 보낸다. 비밀·인증정보·브라우저 프로필은 검토 자료에 포함하지 않는다.

| 필요한 흐름 | 진입점 |
|---|---|
| 새 Gemini 검토 후 턴 종료, 최종에서 이 채팅 재개 | [Gemini 실행](references/operations.md#새-ai-studio-검토와-wake): `web_review.py submit --service aistudio` |
| 새 ChatGPT Pro 검토 후 턴 종료, 최종에서 이 채팅 재개 | [Pro 실행과 검증 범위](references/chatgpt.md): `web_review.py submit --service chatgpt --reasoning Pro` |
| 모델 확인 또는 같은 턴에서 제출·대기 | [직접 실행](references/operations.md#직접-실행): `web_generation.py inspect/configure/run` |
| 이미 전송한 검토 회수 | 같은 job/run의 `status`·`poll`. 새 `send`나 `submit`을 만들지 않는다. |

Wake도 사용자가 승인한 대상·범위에서만 사용한다. 원래 요청을 UTF-8 파일에 보존하고 실제 호출 채팅 UUID를 전달한다. 백그라운드 시작 접수, 모델의 입력 수락, 최종 답변 저장, Wake 접수, 새 턴 재개는 서로 다른 상태다.

## 완료와 복구

UI 완료 표시와 연속 관측에서 안정된 공개 답변, 전송한 입력·모델·본문 해시를 확인한 뒤에만 최종으로 저장한다. 중간 본문이나 시간 초과는 최종 답변이 아니다. 숨은 추론을 읽거나 생성을 중지하지 않는다.

실행 폴더 하나가 제출 한 번이다. 실패·전송 결과 불명·Wake 결과 불명에서는 기존 상태부터 확인하며 자동 재전송하지 않는다. REPL 소유 임시 탭은 worker 종료 뒤 회수할 수 있다고 가정하지 않는다. 상세 복구는 [상태와 제약](references/operations.md#상태와-제약)을 읽는다.

깨어나면 `run/output.txt`와 manifest를 읽고 원래 작업을 이어간다. 외부 모델의 지적은 근거를 대조한 뒤 반영한다. Wake 접수 영수증만으로 채팅 재개나 후속 작업 완료를 주장하지 않는다.
