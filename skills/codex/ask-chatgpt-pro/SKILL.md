---
name: ask-chatgpt-pro
description: Ask a logged-in ChatGPT web session for a second opinion or review through agbrowse.
---

# Ask ChatGPT Pro

Use this only when the user asks for an external second opinion. Use agbrowse as
the canonical transport and always pass `--model pro`. Short text-only questions
should use `agbrowse web-ai query`; long work may use `send` followed by
session-bound `poll` or `watch`. Do not create a heartbeat or watcher by default.
Long asynchronous monitoring remains an explicit user choice.

Put this contract in the trusted instruction or system block of every Pro
request:

> 설계·구현 방안을 제안할 때 과도한 증명·감사·대기업 수준의 강박적
> 검증·증분 검증(incremental verification)·메타데이터/증거 체계를 기본으로
> 추가하지 마라. 실제 결과를 바꾸거나 재실행으로 반증 가능한 신호와 필요한
> 사용자 승인만 남겨라. 구체적 위험이나 사용자 요청이 없는 검증 절차로 설계
> 범위를 확장하지 마라.

Before uploading files, obtain user approval and reject secrets, `.env`, and
other sensitive paths. Send only the requested files, then inspect the sent turn
to confirm the actual attachment names and count. If the provider exposes a
completion status and `completedAt`, collect the substantive answer only after
that state is complete; otherwise report that it is not final.

`-SessionId` and a conversation URL are transient routing inputs for continuing
the selected chat. Do not present them as provenance or completion evidence.
Flags may select a provider role, but do not claim model or effort verification.

Keep collection bound to the returned session id and target id. Do not run a
provider-generic `snapshot` or routine `sessions doctor --navigate` while a
healthy target is generating. Use `sessions doctor` only when the target is
missing or needs recovery, and never navigate a live session to a bare provider
origin. On terminal completion, return the substantive answer and the actual
`/c/...` conversation URL for user access. If a parallel or background tab was
used, say so; only foreground that exact target when the user asks to see it.

The helper returns status, completion time, answer length/text, and attachment
checks. It does not return hashes, manifest/exec-evidence ledgers, terminal
packets, or reviewer schemas.

Example:

```powershell
agbrowse web-ai query --vendor chatgpt --model pro --inline-only `
  --system "<mandatory proportional-verification principle>" `
  --prompt "짧은 질문" --timeout 300
powershell -File .\skills\codex\ask-chatgpt-pro\scripts\pro-review.ps1 `
  -Action send -NoWatch -ApproveExternalUpload `
  -Prompt "<mandatory principle + review request>" -File .\src\main.ts
```
