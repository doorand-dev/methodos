# 웹 모델 검토 실행 세부

명령은 설치된 스킬 위치를 지정해 어느 프로젝트에서든 실행한다. 현재 작업에 필요한 절만 읽는다.

## 설치와 의존성

Methodos의 `skills/codex/web-model-review` 폴더 전체를 `~/.agents/skills/web-model-review`로 복사한다. 기존 설치가 있으면 덮어쓰기 전에 차이를 확인한다. Python 3.10+와 Node.js, PATH의 Aside CLI, 별도 `aside-browser` 스킬과 로그인된 Aside 프로필이 필요하다. 브라우저 설치·로그인은 이 스킬에 포함하지 않는다.

Wake를 쓰는 경우 Methodos의 `hooks/common/codex-wake/codex_wake.py`와 라이선스를 자신이 선택한 위치에 둔다. 기본 탐색 위치는 `$CODEX_HOME/tools/codex_wake.py`, CODEX_HOME이 없으면 `~/.codex/tools/codex_wake.py`다. 다른 위치는 `CODEX_WAKE_PATH` 환경변수에 파일 절대 경로를 지정한다. 이미 있는 공통 Wake 도구를 무조건 덮어쓰지 않는다.

공통 Wake는 비공식 Windows 앱 bridge에 의존한다. 원본 저장소의 `contract/codex/codex-wake.md`에서 현재 설치·연결 계약을 확인한다. 실제 읽기 probe로 호환성을 확인한 뒤 전송하며, 앱 업데이트 후에는 다시 확인한다. 이 스킬은 앱이나 Aside를 자동 시작하지 않는다.

```powershell
$reviewTools = Join-Path $env:USERPROFILE '.agents/skills/web-model-review/scripts'
python -B "$reviewTools/review_packet.py" --help
python -B "$reviewTools/web_review.py" --help
# 아래는 별도 위치에 설치한 경우에만 자신의 실제 경로로 지정한다.
$env:CODEX_WAKE_PATH = 'C:/path/to/codex_wake.py'
python -B $env:CODEX_WAKE_PATH probe --thread '<현재 채팅 UUID>' --caller '<실제 호출 채팅 UUID>'
```

## 검토 자료 만들기

대상 프로젝트의 cwd에서 실행하거나 `--root`에 절대 경로를 전달한다. `--context`는 root 내부 파일만 명시적으로 선택한다. 내용을 읽고 외부에 보낼 범위를 확인한다.

```powershell
python -B "$reviewTools/review_packet.py" --root . --reviewer flash `
  --question '이 변경의 실제 결함과 최소 수정을 근거 코드로 제안해줘.' `
  --context src/example.py --context tests/test_example.py `
  --out "$env:TEMP/review-packet-001"
```

`entry.md`는 질문과 범위, `details.md`는 선택 원문, `prompt.txt`는 합친 전송 본문, `packet.json`은 출처와 해시다. 정해진 문자 예산을 넘으면 조용히 자르지 않고 중단한다. 큰 파일은 필요한 함수와 호출자를 별도 발췌해 선택한다. 알려진 민감 경로를 차단하지만 범용 비밀 탐지기는 아니다.

## 새 AI Studio 검토와 Wake

아래 명령은 실제로 선택 본문을 외부 모델에 전송한다. 검토 전송과 이 채팅 재개가 승인된 경우에만 실행한다. `--user-request-file`에는 원래 승인 요청을 저장한다. 현재 채팅 UUID를 명시하며 임의의 caller를 만들지 않는다.

모델·Thinking Level은 새 AI Studio UI의 현재 값과 일치해야 한다. `--reasoning`은 AI Studio에서 값을 검증하며 변경하지 않는다. 예제의 `gemini-3.8-flash`·`Medium`은 2026-11-05 실측 설정이다. 다른 설치의 선택 가능 여부는 `inspect`로 확인한다.

```powershell
python -B "$reviewTools/web_review.py" submit `
  --account '<account:profile-id>' --model gemini-3.8-flash --reasoning Medium `
  --prompt "$env:TEMP/review-packet-001/prompt.txt" `
  --out "$env:TEMP/review-job-001" --thread '<이 채팅 UUID>' `
  --user-request-file '<승인 원문 UTF-8 파일>'
python -B "$reviewTools/web_review.py" status "$env:TEMP/review-job-001"
```

Windows detached worker가 Aside REPL과 새 임시 탭을 소유해 제출과 회수를 실행한다. 다른 탭·프로필·Vault를 바꾸지 않는다. CLI의 `starting`은 worker 시작 접수다. `events.jsonl`의 제출 반환과 `run/manifest.json`의 `submission_confirmed`로 입력 수락을 확인한 뒤 턴을 끝낸다. 아직 전송 전 차단됐다면 원인을 확인한다.

최종 완료·본문 안정성·단일 제출·해시를 확인하면 `run/output.txt`를 저장하고 기존 최종 watcher를 시작한다. watcher는 원래 채팅의 idle 상태를 기다린 뒤 공통 Wake를 한 번 호출한다. 중간 답변·시간 초과·수집 실패에는 Wake를 보내지 않는다. 실패 시 자동으로 깨우는 기능은 없으므로, 사용자가 결과가 오지 않는다고 알려주거나 다시 작업할 때 상태를 조회한다. OS 재시작 후 자동 복구하지 않는다.

## 직접 실행

Aside 일반 탭의 빈 임시 채팅을 새 REPL에서 확인한 뒤 사용한다. `--tab`은 현재 목록에서 확인한 target ID다. 다른 사람의 대화나 기존 초안에는 전송하지 않는다.

```powershell
python -B "$reviewTools/web_generation.py" --account '<account:profile-id>' inspect aistudio --tab '<target-id>'
python -B "$reviewTools/web_generation.py" --account '<account:profile-id>' inspect chatgpt --tab '<target-id>'
python -B "$reviewTools/web_generation.py" --account '<account:profile-id>' configure chatgpt `
  --tab '<target-id>' --model '<실제 모델 이름>' --reasoning Pro
```

ChatGPT configure는 메시지 없이 모델과 추론량을 설정하고 메뉴를 다시 읽어 확인한다. AI Studio는 API 키 미선택·도구 꺼짐·빈 시스템 지침을 확인한다. 키 연결·결제·Drive·첨부·계정 전역 설정으로 확장하지 않는다.

`run`은 같은 턴에서 한 번 제출하고 최종을 기다린다. `send`는 한 번 제출한 영수증만 반환하고, `poll`은 같은 run을 회수한다. ChatGPT는 정확한 UI 모델명과 원하는 `--reasoning`을 지정한다. Python 표준 라이브러리 CLI이며 provider API를 사용하지 않는다.

```powershell
python -B "$reviewTools/web_generation.py" --account '<account:profile-id>' send aistudio `
  --tab '<target-id>' --model '<확인한 모델 ID>' --reasoning '<확인한 Thinking Level>' `
  --prompt '<prompt.txt>' --out '<새 run 폴더>'
python -B "$reviewTools/web_generation.py" status '<run 폴더>'
python -B "$reviewTools/web_generation.py" poll '<run 폴더>'
```

이미 제출된 일반 탭에만 `web_review_wake.py start --run <run> --thread <원래 채팅> --user-request-file <승인 원문>`을 사용한다. 다른 REPL이 소유한 임시 탭이 종료 후에도 남을 것으로 전제하지 않는다. 새 Gemini 검토는 위 `web_review.py submit`으로 소유권을 유지한다.

## 상태와 제약

- `job.json`: worker 상태. `reviewing`은 실행 중, `wake_started`는 최종 watcher 시작이며 수신 증거가 아니다.
- `run/manifest.json`: 단일 제출과 최종 수집 상태. `completed`·`output_obtained`·본문 해시를 확인한다.
- `run/wake/state.json`: Wake 접수·실패·불명 결과. `wake_accepted`도 새 턴 재개는 별도로 확인한다.
- `events.jsonl`: 제출·관측·최종 저장 시각. 모델의 순수 연산 시간이 아니라 브라우저와 CLI에서 관측한 시간이다.

기존 폴더를 덮어쓰지 않는다. `worker.started`, `run/.active.lock`, 탭 잠금이 남으면 다른 프로세스의 작업 여부부터 조사한다. 잠금을 자동으로 깨거나 동일 job을 재실행하지 않는다. 제출·Wake 결과 불명에서는 기존 기록을 조사하며 자동 재발송·다른 transport 우회를 하지 않는다.

실패했거나 시간 초과된 REPL 소유 임시 탭은 worker가 닫힐 때 사라질 수 있다. 일반 탭으로 제출한 실행만 그 탭이 남아 있을 때 같은 run을 `poll`할 수 있다. 원문·계정·탭·대화·모델이 바뀌면 회수를 중단한다.

## 확인한 범위

2026-11-05 Windows 로컬에서 Gemini 3.8 Flash·Medium에 42,888자 검토를 실제 전송했다. 중간 본문 중에는 Wake 호출이 없었고, UI 완료·본문 안정성 확인 후 약 137초에 최종 저장, 이어 Wake 접수와 원래 채팅의 새 턴 재개를 확인했다. 이는 한 실행의 결과이며 다른 크기·모델·OS의 지연이나 동작을 보장하지 않는다. Pro의 별도 실행 측정과 확인 범위는 [chatgpt.md](chatgpt.md#확인-상태)에서 확인한다.

오프라인 검증은 scripts 폴더에서 `python -B -m unittest test_review_packet test_web_generation test_web_review test_web_review_wake -q`, `node --test test_web_generation_browser.js`로 실행한다. 모의 테스트는 실제 앱·브라우저 연결 호환성의 대체가 아니다.
