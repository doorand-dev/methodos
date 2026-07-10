---
name: ask-chatgpt-pro
description: Delegate a question, code review, implementation review, or second opinion to ChatGPT Pro running in a real logged-in ChatGPT web session through the `agbrowse` CLI. Use when the user asks "ChatGPT한테도 물어봐", "GPT로 교차검토", "second opinion", "ChatGPT 검토 받아줘", "GPT Pro한테 리뷰시켜", "이 파일/코드 첨부해서 물어봐", or when Codex should compare its own reasoning against ChatGPT Pro. Supports local file attachments, many-file context bundles, images, docs, zips, and short inline prompts. Not for bulk scraping, not the OpenAI API, and not the CodexPro MCP bridge unless the user explicitly asks for MCP setup.
---

# Ask ChatGPT Pro

Send a bounded prompt to a logged-in ChatGPT Pro web session through `agbrowse web-ai`, then fold the answer back into the current Codex work.

## Rules

- Use `--model pro --effort extended` unless the user asks for a faster or lower-effort pass.
- Model/effort enforcement is version-gated: on agbrowse >= 0.1.15, `--model pro --effort extended` is enforced and the send output's `reasoning effort selected: ...` line confirms it; on 0.1.14 it was silently not enforced (flags accepted but ignored, window kept whatever tier it already had). Always confirm via that output line — never infer the tier from the answer text.
- Each ask/review request starts a fresh ChatGPT session by default.
- A fresh session is not a clean room: ChatGPT's account-level memory / "reference chat history" can leak facts across separate conversations, so thread isolation does not guarantee model isolation. If a review must not see prior context, have the user disable "Reference saved memories / chat history" in ChatGPT settings, or use a Temporary Chat, before sending.
- Continue an existing review session only when the user explicitly asks to continue that specific session, or provides a `sessionId` / conversation URL to continue.
- Treat review, deep research, file-attachment review, many-file context review, and second opinions as long reviews unless the user asks for a short answer.
- In Codex Desktop, long reviews use `send -> retain sessionId -> collect only after mechanical finality`. A scheduled collect wakeup requires a public Automation API capability that is currently unavailable for an exact future one-shot time.
- Use `-NoWatch` on send by default. A hidden `agbrowse web-ai watch` is only a diagnostic/process helper; it does not wake the current Codex thread by itself.
- Provider finality is mechanical: `provider status = complete`, `completedAt`, `MinAnswerChars`, and a stable answer hash across `StabilitySeconds` (default 30 seconds) are all required before reporting an answer.
- Do not use `watch-accelerate` or an external watcher to reschedule a heartbeat. The public `automation_update(mode=create)` API rejects `DTSTART`, and `suggested_create` only renders a card; an external PowerShell watcher therefore cannot safely advance an existing heartbeat.
- Treat Codex Desktop automation UI time text as display-only. Verify heartbeat scheduling by letting a test heartbeat fire.
- Do not add artificial marker text to the ChatGPT prompt for identity or finality checks. Use `sessionId` for identity; finality is mechanical: complete provider state, completed timestamp, enough text, and unchanged answer hash.
- Do not use `codex exec resume` as the wake bridge for this skill.
- Report the returned `sessionId`. Collect later by that `sessionId`.
- Do not report draft, streaming, preview, preamble, or partial transcript text as the answer.
- Use the bundled `collect` action for long reviews. It returns `answerText` only when the answer is complete, substantive, and stable.
- If `answerText` is null, report that the session is not final yet.
- If the user asks for send-only or no heartbeat, say the review is intentionally unmonitored.
- If the user explicitly keeps a foreground `agbrowse web-ai watch` terminal open, its return may trigger collection in that owning turn. This is wall-clock/process wait, not a provider completion event connected to a closed Codex turn. Otherwise end after reporting the durable sessionId and do not resend.
- Parallel reviews are allowed when each Codex thread uses its own ChatGPT `sessionId`. Do not treat prompt text or artificial markers as identity. Do not run two collectors for the same `sessionId`.
- Treat copy-markdown collection as a desktop-global critical section because it may use the OS clipboard. If several reviews finish at once, serialize `collect` calls or prefer provider/session text that does not touch the clipboard.

## Setup

Verify before sending:

```powershell
agbrowse --version
agbrowse status
```

If Chrome is not running under agbrowse:

```powershell
agbrowse start --headed
```

The user must log in to ChatGPT by hand in that Chrome profile. Do not automate credentials.

Resolve the helper relative to this skill:

```powershell
$skillDir = "<installed ask-chatgpt-pro skill folder>"
$script = Join-Path $skillDir "scripts\pro-review.ps1"
$rruleHelper = Join-Path $skillDir "scripts\codex-heartbeat-rrule.ps1"
```

The `$rruleHelper` path is a compatibility wrapper. Keep RRULE generation logic in the sibling `conditional-heartbeat` skill at `scripts\codex-heartbeat-rrule.ps1`.

## Send

Fresh review:

```powershell
powershell -ExecutionPolicy Bypass -File $script -Action send -NoWatch -Prompt "리뷰 요청 전문"
```

With files:

```powershell
powershell -ExecutionPolicy Bypass -File $script -Action send -NoWatch `
  -File .\src\server.ts -File .\docs\spec.md `
  -Prompt "첨부한 코드와 스펙을 함께 보고 correctness 중심으로 리뷰해줘."
```

With many files:

```powershell
powershell -ExecutionPolicy Bypass -File $script -Action send -NoWatch `
  -ContextFromFiles "src/**/*.ts" `
  -ContextExclude "**/*.test.ts" `
  -ContextTransport upload `
  -Prompt "첨부된 코드 묶음을 보고 regression risk를 리뷰해줘."
```

After send, attempt a one-shot Codex heartbeat only through `automation_update`. The current public API rejects the required `DTSTART` in `mode=create`; `mode=suggested_create` renders a card and does not create a fallback. When that happens, report the blocker, retain the `sessionId`, and do not create a direct-file workaround or a duplicate ChatGPT request.

Do not hand-write heartbeat RRULE strings from a natural-language delay. Generate the fallback heartbeat RRULE mechanically:

```powershell
$fallback = powershell -NoProfile -ExecutionPolicy Bypass -File $rruleHelper -DelayMinutes 5 | ConvertFrom-Json
$fallback.rrule
```

Use the helper output as the requested schedule. If `automation_update(mode=create)` rejects its `DTSTART`, do not retry with a bare relative RRULE or `suggested_create` as though either installed a heartbeat. Record the `sessionId` and the rejection instead.

Recommended heartbeat prompt shape:

```text
ChatGPT Pro review collect wakeup.
Automation id: use the <automation_id> from the heartbeat envelope.
Session id: <sessionId>.
If a future public API creates this automation, first delete it, then run:
powershell -ExecutionPolicy Bypass -File "<script>" -Action collect -SessionId <sessionId> -MinAgeMinutes 0
If answerText is final, report it as ChatGPT Pro's second opinion. If not final, keep the same sessionId and request or await an explicit later collect; never send the original request again unless the user explicitly asks for a new review.
```

`agbrowse` may write progress lines such as `[poll] ... streaming...` to stderr while the provider is still working. Treat those lines as non-fatal progress output; decide failure from the process exit code and final JSON/session state, not from stderr presence.

When collecting long Pro answers on Windows, keep native command output as UTF-8 and do not rely only on Windows PowerShell `ConvertFrom-Json` for huge `answerText` payloads. The helper has a Node JSON fallback that extracts required fields and decodes answer text safely.

After send, report:

- `sessionId`
- conversation URL if available
- heartbeat automation id and fallback time if created
- attached files or context package
- model/effort verification status

Do not imply the review is complete after send. If a heartbeat was created, stop after this report so the next action happens through the heartbeat wakeup, not through same-turn manual polling.

## Collect

Collect only by the reported `sessionId`:

```powershell
powershell -ExecutionPolicy Bypass -File $script -Action collect -SessionId $sid
```

Close a completed tab when no follow-up is needed:

```powershell
powershell -ExecutionPolicy Bypass -File $script -Action collect -SessionId $sid -CloseTabOnComplete
```

The helper checks:

- session age is at least `MinAgeMinutes` unless `-Force` is used
- provider status is `complete`
- `completedAt` exists
- answer length is at least `MinAnswerChars`
- answer hash is stable across two reads separated by `StabilitySeconds` (default 30)

Only report `answerText` when the helper returns it.

For narrow questions where a valid final answer may be shorter than 1500 characters, pass a lower `-MinAnswerChars` rather than forcing a follow-up:

```powershell
powershell -ExecutionPolicy Bypass -File $script -Action collect -SessionId $sid -MinAnswerChars 500
```

## Explicit Continuation

Use an existing ChatGPT conversation only when the user explicitly asks.

For follow-up turns, include fresh context or reattach the needed files. Do not rely on files from a previous turn being available.

## Short Questions

For genuinely short questions, `query` is allowed:

```powershell
agbrowse web-ai query --vendor chatgpt --model pro --effort extended --new-tab --inline-only --prompt "짧은 질문" --timeout 300
```

## Reporting

Present the result as ChatGPT Pro's second opinion. Compare it with Codex's own judgment and call out disagreement, uncertainty, or missing evidence.

When provider execution matters, distinguish:

- requested Pro/extended but UI verification unavailable
- sent with heartbeat fallback
- sent with heartbeat fallback and acceleration watcher
- sent but intentionally unmonitored
- not final yet
- final answer collected
