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

> 과도한 증명·감사·대기업 수준의 강박적 검증·증분 검증(incremental
> verification) 패턴을 배제하고, 실제 동작하는 가장 단순한 최적 방안
> 하나를 제시하라. 완전 재설계·다중 폴백·2후보 비교·메타데이터 체계·과한
> 계약은 제안하지 마라. 결론은 (a) 권고 방식 한 줄, (b) 왜 그게 최적인지
> 근거, (c) 실패 케이스와 최소 대비만으로 제한하라.

Preserve any stricter user-supplied output contract. If the user explicitly asks
for alternatives, comparison, or a broader audit, follow that request instead of
silently forcing the single-option shape.

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
  --system "<mandatory minimal-single-option contract>" `
  --prompt "짧은 질문" --timeout 300
powershell -File .\skills\codex\ask-chatgpt-pro\scripts\pro-review.ps1 `
  -Action send -NoWatch -ApproveExternalUpload `
  -Prompt "<mandatory contract + review request>" -File .\src\main.ts
```
