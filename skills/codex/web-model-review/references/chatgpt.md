# ChatGPT Pro 검토와 최종 Wake

공통 설치·자료 구성·실행 상태·복구는 필요한 경우에만 [operations.md](operations.md)를 읽는다. Gemini와 같은 `web_review.py`를 쓰며 서비스만 분기한다. 별도 스킬이나 별도 제출·Wake 구현은 만들지 않는다.

## 전송 전에 확인

전역 `aside-browser`와 현재 Aside guide를 따른다. 새 임시 ChatGPT 탭에서 `web_generation.py inspect chatgpt`로 실제 UI 모델 이름을 확인한다. Pro는 추론량이며 모델 이름이 아니다. `--model`에 현재 UI 이름을 그대로 넣고 `--reasoning Pro`로 슬라이더를 조작한 뒤 다시 읽는다. 접힌 모델 목록의 숨겨진 일반 한도 설명은 활성 Pro 제한으로 해석하지 않는다. 실제 사용량·접근 제한이면 전송 전에 중단하고 다른 모델이나 추론량으로 대체하지 않는다.

검토 전송과 이 채팅 재개가 승인된 경우에만 실행한다. 원래 승인 요청을 UTF-8 파일로 보존하고 실제 호출 채팅 UUID를 전달한다.

```powershell
$reviewTools = Join-Path $env:USERPROFILE '.agents/skills/web-model-review/scripts'
python -B "$reviewTools/web_review.py" submit --service chatgpt `
  --account '<account:profile-id>' --model '<현재 UI에서 확인한 모델 이름>' --reasoning Pro `
  --prompt '<packet/prompt.txt>' --out '<새 job 폴더>' `
  --thread '<이 채팅 UUID>' --user-request-file '<승인 원문 UTF-8 파일>' --timeout 3600
python -B "$reviewTools/web_review.py" status '<job 폴더>'
```

3600초는 긴 검토를 기다리는 예시 제한이며 완료 예상 시간이 아니다. 제한은 호출할 때 정한다. worker가 임시 탭과 REPL을 소유해 최종 회수까지 유지한다. 전송 호출 반환과 실제 대화 생성 여부를 확인한 뒤 턴을 종료한다. 표시명 때문에 `submission_confirmed`가 아직 false여도 새 전송을 만들지 않고 같은 worker가 원문 대조를 이어가게 한다. 같은 run의 최종 본문·단일 제출·해시를 검증한 뒤 기존 공통 Wake가 원래 채팅에 재개를 한 번 요청한다. 접수 영수증과 실제 새 턴은 별도로 확인한다. 중간 답변·시간 초과에는 Wake를 보내지 않는다.

## 입력과 최종 회수

ChatGPT의 URL 자동 링크가 화면용 `innerText`에 줄바꿈을 넣을 수 있다. CLI는 입력창의 문단 원문을 읽어 원래 코드·URL·빈 줄을 대조한다. 입력이 다르면 제출하지 않는다. 큰 본문 뒤의 버튼이 전체 snapshot에서 잘려도 입력·전송·완료 컨트롤은 직접 확인한다.

전송 뒤 변수나 링크가 참조 표시명으로 렌더링되면, Windows에서는 UI의 ‘메시지 복사’를 실행하고 Clipboard 갱신 번호가 바뀐 뒤에만 그 원문을 읽는다. 복사 형식의 Markdown 이스케이프를 한 번 복원한 결과가 코드 공백까지 일치해야 확인한다. 해당 URL·표시 본문·원문 해시에 묶어 재사용하며, 일치하지 않는 Clipboard 내용은 저장하지 않는다. 이 보완 경로는 시스템 Clipboard를 사용한다. 진행 설명과 숨은 검색 캐시는 공개 최종 답변으로 읽지 않는다.

초기화 이후 실패나 결과 불명에서는 기존 job·run을 먼저 확인한다. 이미 전송된 요청을 새 job으로 다시 보내지 않는다. worker가 닫힌 뒤 임시 탭이 남는다고 가정하지 않는다. 숨은 추론을 읽거나 생성을 중지하지 않는다.

## 확인 상태

2026-11-05 Windows 로컬·Aside CLI 1.26.1104.1843·ChatGPT 한국어 UI에서 GPT-6·Pro로 전체 무개입 실행을 확인했다. 같은 스킬과 worker로 2,812자 검토를 한 번 제출하고 생성 중 Codex 턴을 종료했다. UI 완료와 본문 안정성 확인 후 최종 답변 741자를 저장한 뒤에만 Wake를 시작했으며, 원래 채팅의 실제 새 턴 재개를 확인했다. 전송부터 재개까지 약 142초, 턴 종료부터 재개까지 92초였다. 이는 CLI 관측 시간이며 서비스의 순수 연산 시간이 아니다.

제출·Wake는 각각 1회이고 수동 개입과 수집 복구는 0회였다. 실행 전후 스킬·reference·worker·수집기·공통 Wake 도구 등 7개 파일의 해시가 같았으며, 입력·출력 해시와 전송 전후 GPT-6·Pro 설정도 대조했다. 슬라이더 값은 4/4였고 활성 한도 경고는 없었다. 실행 중 코드를 고치거나 중간 답변에서 깨우지 않았다.

이 결과로 Pro의 제출→생성 중 턴 종료→최종 저장→Wake→같은 채팅 재개 흐름을 지원한다. 확인 범위는 위 환경의 한 실행이며 다른 모델·UI·OS의 동작이나 지연을 보장하지 않는다. 입력 검증은 브라우저 DOM과 필요한 경우 UI 복사 원문 기준이며 외부 모델의 내부 직렬화 바이트를 보증하지 않는다. 추가 실제 전송은 자동 재시험하지 않는다.
