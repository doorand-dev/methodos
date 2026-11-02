# Codex Wake — 일이 준비됐을 때 기존 채팅 이어가기

**판단 요약:** 작업 완료나 인증 해소 같은 실제 이벤트를 기존 Codex 채팅에 전달하는 독립 Python 도구입니다. Windows에서 실행 중인 로컬 Codex 앱과 호환되는 내부 bridge·queue CLI가 필요합니다. 비공식 어댑터이며, 전송 접수가 실행이나 업무 완료를 보장하지 않습니다.

긴 빌드가 끝났거나 사용자가 로그인을 마쳤을 때, 담당 채팅이 그 결과를 읽고 다음 작업을 이어가게 할 수 있습니다. 에이전트가 매번 “끝났나요?”를 확인하는 대신, 완료를 아는 worker나 watcher가 한 번 알려주는 방식입니다. 기존 채팅의 맥락을 이어갈 수 있고, 반복 확인을 위한 에이전트 호출을 줄일 수 있습니다. 이벤트 감지 자체와 watcher 운영은 프로젝트가 맡습니다.

[단일 실행 파일](../../hooks/common/codex-wake/codex_wake.py)과 [오프라인 테스트](../../hooks/common/codex-wake/test_codex_wake.py)를 제공합니다. 별도 Python 패키지 설치나 스킬 등록은 필요하지 않습니다. 저장소의 [MIT 라이선스](../../LICENSE)를 따르며, 재배포할 때 라이선스를 함께 보존하세요.

## 먼저 확인할 실행 조건

- Python 3와 Node.js, 실행 중이며 대상 채팅에 접근할 수 있는 Windows 로컬 Codex 앱이 필요합니다. Python 코드는 표준 라이브러리만 사용합니다.
- 앱 번들의 `codex-app-tools/server.mjs`가 JSON-lines MCP와 `read_thread`, `send_message_to_thread`를 제공해야 합니다. 앱의 Windows named pipe에도 연결할 수 있어야 합니다.
- running 채팅은 `codex queue --thread ... --message ...`를 지원하는 CLI가 필요합니다. 이 사본은 `Queued message <UUID> for thread <UUID>.` 형태의 출력으로 접수를 판단합니다.
- 이 인터페이스들은 이 도구가 기대하는 **버전 의존 계약**입니다. 표준 Codex 기능이나 OpenAI가 지원하는 공개 API로 보장하지 않습니다. 호환 앱·Node·CLI 버전 범위는 확정하지 않았으며, 특정 최신 버전에서 작동한다고 주장하지 않습니다. macOS/Linux 연결은 이 패키지의 지원 범위 밖입니다.

앱 번들, CLI, pipe 이름이나 응답 구조가 바뀌면 먼저 읽기 `probe`로 확인하세요. `probe` 성공도 실제 전송과 running queue 경로의 호환성을 증명하지는 않습니다. 이 도구는 앱이나 watcher를 자동 시작하지 않으며, 원격 서버만 있는 환경에서 로컬 앱에 직접 연결해 주지 않습니다.

## 최소 사용: copy → probe → send

저장소 루트의 PowerShell에서 실행합니다. 설치 폴더는 사용자가 고릅니다. 예제의 환경변수는 각자 실제 값으로 설정해야 하며, 이 문서에는 계정·개인 경로·채팅 ID가 들어 있지 않습니다.

```powershell
$wakeDir = Join-Path $env:LOCALAPPDATA 'codex-wake'
New-Item -ItemType Directory -Force $wakeDir | Out-Null
Copy-Item .\hooks\common\codex-wake\codex_wake.py $wakeDir
Copy-Item .\LICENSE $wakeDir
$wakeScript = Join-Path $wakeDir 'codex_wake.py'
python $wakeScript --help
```

실행 환경에서 다음 값을 준비합니다. 경로는 현재 설치에서 확인한 실행 파일과 bridge를 가리켜야 합니다.

| 환경변수 | 값과 용도 |
|---|---|
| `CODEX_MCP_NODE_PATH` | Node 실행 파일의 절대 경로 |
| `CODEX_APP_TOOLS_SERVER_PATH` | 앱 번들 `server.mjs`의 절대 경로 |
| `CODEX_APP_TOOLS_PIPE_PATH` | 실행 중인 해당 앱의 named pipe 경로 |
| `WAKE_TARGET_THREAD` | 메시지를 받을 기존 채팅 UUID; 아래 예제용 변수 |
| `WAKE_CALLER_THREAD` | 실제 호출 맥락의 채팅 UUID; 아래 예제용 변수 |
| `WAKE_MESSAGE_FILE` | 승인된 메시지가 담긴 UTF-8 파일 경로; 아래 예제용 변수 |

`--caller`는 MCP 메타데이터의 `openai/threadId`로 전달됩니다. 대상 ID를 임의로 복사하거나 가짜 caller를 만들어 권한을 가장하지 마세요. 실행 가능한 연결과 실제 호출 맥락을 마련할 수 없다면 중단합니다.

```powershell
# 읽기 확인: 메시지를 보내지 않습니다.
python $wakeScript probe --thread $env:WAKE_TARGET_THREAD --caller $env:WAKE_CALLER_THREAD

# 대상 채팅 메시징이 승인되고 이벤트 발생을 확인했을 때만 실행합니다.
python $wakeScript send --thread $env:WAKE_TARGET_THREAD --caller $env:WAKE_CALLER_THREAD --message-file $env:WAKE_MESSAGE_FILE
```

메시지에는 이벤트 식별자, 관측한 결과, 결과 파일이나 미완료 작업의 정본 위치, 승인 범위 안의 다음 단계를 넣습니다. 예: “빌드 완료 이벤트를 확인했습니다. 기록된 결과 파일을 읽고 기존에 승인된 테스트 결과 검토를 이어가세요.” 로그인 완료 이벤트에 비밀번호나 토큰을 담을 필요는 없습니다.

running 경로의 CLI를 명시하려면 `--config`로 로컬 JSON 파일을 지정합니다. 아래 값은 형식 예시이며 실제 설치 경로로 바꿉니다. `command`는 실행 파일과 고정 인수의 배열이고, 도구가 뒤에 `queue` 인수를 붙입니다. 셸 명령 문자열이 아닙니다.

```json
{
  "node_path": "C:/path/to/node.exe",
  "server_path": "C:/path/to/codex-app-tools/server.mjs",
  "pipe_path": "\\\\.\\pipe\\codex-app-tools-INSTANCE",
  "command": ["C:/path/to/node.exe", "C:/path/to/codex.js"]
}
```

```powershell
python $wakeScript send --config .\wake.local.json --thread $env:WAKE_TARGET_THREAD --caller $env:WAKE_CALLER_THREAD --message-file $env:WAKE_MESSAGE_FILE
```

`--node-path`, `--server-path`, `--pipe-path`는 JSON 설정보다 우선합니다. 경로 미지정 시 환경변수와 설치 위치를 탐색합니다. Node는 PATH 또는 앱 runtime 후보, server는 앱 resources 후보를 찾으며 후보가 여러 개면 명시 경로를 요구합니다. queue는 설치된 npm CLI를 우선 찾고 `CODEX_APP_RUNTIME_CLI_PATH`를 대체 후보로 사용합니다. 정확한 선택이 필요하면 `command`를 지정하세요. 설정과 메시지 파일은 프로젝트 저장소에 게시하지 마세요.

pipe 연결 실패 시에는 아직 전송 전인 읽기 단계에서만 유일한 다른 후보를 확인합니다. 복수 후보에서 임의 선택하지 않습니다. 모든 timeout 값은 양의 유한한 초 단위 값이며 `--timeout`으로 지정합니다. timeout은 개별 요청·queue 프로세스의 제한으로, 전체 호출의 총 소요 시간 제한은 아닙니다.

## 상태별 동작과 영수증

| 확인된 상태 | 경로 | 성공 응답 |
|---|---|---|
| idle 또는 최근 turn이 completed/interrupted/failed | 앱 `send_message_to_thread` | `transport_status: accepted` |
| 최근 turn이 inProgress | CLI `codex queue` | `transport_status: queued` |
| 상태 불명·알 수 없는 turn 상태 | 전송하지 않고 종료 | `outcome: rejected` |

`send`도 매번 전송 전에 상태를 읽습니다. 별도 `probe` 결과를 저장해 분기에 재사용하지 않습니다. 읽기와 전송은 원자적이지 않아 그 사이 상태가 바뀔 수 있습니다. queue 접수가 유휴 채팅의 재개를 보장하지 않으므로, 실제 수신 여부는 별도로 확인합니다.

성공 응답의 `execution_status`는 항상 `unconfirmed`입니다. `accepted`/`queued`는 transport 접수만 뜻합니다. 새 turn 관측, 수신 담당의 이벤트 수락, 업무 완료는 서로 다른 증거로 기록하세요. 앱이 message ID를 주지 않으면 `message_id`는 null이며, 임의 ID를 전송 ID로 만들어 내지 않습니다.

| CLI 종료 코드 | 의미 | 호출자의 다음 행동 |
|---|---|---|
| 0 | 읽기 확인 또는 전송 접수 | 응답을 기록하고 수신·실행·완료를 따로 확인 |
| 1 | 검증·연결 실패 등, 전송을 시도하지 못함 | 원인을 확인하고 수정; 무조건 반복하지 않음 |
| 2 | `uncertain`: 전송 여부 불명(unknown) | 기존 전달을 조사하고 자동 재전송 금지 |

인수 문법 오류는 argparse 자체의 종료 코드 2와 텍스트 오류로 끝날 수 있습니다. 전송 결과는 종료 코드만 보지 말고 JSON의 `outcome`도 함께 읽습니다. 프로세스 강제 종료나 결과 유실로 영수증 자체가 없으면 호출자도 unknown으로 취급해야 합니다.

전송 timeout, 다른 대상의 영수증, 인식할 수 없는 queue 출력, queue의 비정상 종료는 이미 전달됐을 가능성을 배제하지 않습니다. 다른 transport로 자동 우회하거나 같은 이벤트를 즉시 다시 보내지 않습니다. 라이브러리에서는 `WakeUncertain`과 `WakeRejected`를 구분할 수 있습니다.

## watcher가 맡을 일과 권한

이 도구는 연결·상태 분기·한 번의 전송과 영수증을 담당합니다. 스케줄러, 이벤트 저장소, 중복 제거 서비스는 포함하지 않습니다. watcher는 전송 전에 이벤트 ID와 attempt를 영속 기록하고, 영수증·수신 수락·업무 완료를 따로 저장해야 합니다. 여러 worker가 같은 이벤트를 보낼 수 있다면 원자적 claim과 수신 측 중복 제거도 프로젝트에서 구현합니다.

unknown 전송을 재개할지는 기존 message·turn·수신 기록을 확인한 뒤 판단합니다. queued 작업의 복구가 필요해도 현재 담당과 기존 이벤트의 미수락 여부부터 확인하고, 동일 업무를 새로 발주하지 않습니다. 이 패키지 자체는 exactly-once 전달이나 durable delivery를 보장하지 않습니다.

**설치나 이벤트 발생은 메시징 승인이 아닙니다.** 사용자가 허용한 대상·목적·범위 안에서만 보냅니다. 인증 해소는 준비 상태의 변화이며 게시·메일 발송·업로드·주문·결제·삭제의 새 승인이 아닙니다. 깨어난 담당도 기존 승인과 보류 조건을 유지해야 합니다. 도구는 조직별 승인 정책을 자동 검증하지 않습니다.

## 오프라인 검증

저장소 루트에서 실행합니다. 앱 연결, 실제 queue, 실제 채팅 발송은 하지 않습니다. stdio 통신 테스트만 임시 Python 가짜 서버를 자식 프로세스로 실행합니다.

```powershell
python -B -m unittest discover -s hooks/common/codex-wake -p 'test_*.py' -v
```

테스트는 idle/running 분기, caller 메타데이터, UTF-8 메시지, 경로 우선순위, stale pipe의 유일 후보 복구, 복수 후보 거절, 불명 상태 차단, timeout·불명 영수증에서 재전송하지 않음, 자식 프로세스 정리를 확인합니다. 오프라인 통과는 설치된 앱과의 실제 호환성 또는 채팅 재개 성공을 증명하지 않습니다.
