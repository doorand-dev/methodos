---
name: ask-chatgpt-pro
description: Ask a logged-in ChatGPT web session for a second opinion or review through agbrowse.
---

# Ask ChatGPT Pro

Use this only when the user asks for an external second opinion. Short text-only
questions should use `agbrowse web-ai query` or a direct `send` followed by
`collect`; do not create a heartbeat or watcher by default. Long asynchronous
monitoring remains an explicit user choice.

Before uploading files, obtain user approval and reject secrets, `.env`, and
other sensitive paths. Send only the requested files, then inspect the sent turn
to confirm the actual attachment names and count. If the provider exposes a
completion status and `completedAt`, collect the substantive answer only after
that state is complete; otherwise report that it is not final.

`-SessionId` and a conversation URL are transient routing inputs for continuing
the selected chat. Do not present them as provenance or completion evidence.
Flags may select a provider role, but do not claim model or effort verification.

The helper returns status, completion time, answer length/text, and attachment
checks. It does not return hashes, manifest/exec-evidence ledgers, terminal
packets, or reviewer schemas.

Example:

```powershell
agbrowse web-ai query --vendor chatgpt --prompt "짧은 질문" --timeout 300
powershell -File .\skills\codex\ask-chatgpt-pro\scripts\pro-review.ps1 `
  -Action send -NoWatch -ApproveExternalUpload -Prompt "검토해 주세요" -File .\src\main.ts
```
