---
name: ask-chatgpt-pro
description: Delegate a question, code review, or second-opinion to ChatGPT Pro (GPT-5.5 Pro) running in a real logged-in browser, via the `agbrowse` CLI — no API key. Can attach local files directly (code, docs, images, zip — one or many). Use when the user wants ChatGPT's take alongside Claude ("ChatGPT한테도 물어봐", "GPT로 교차검토", "second opinion", "ChatGPT 검토 받아줘", "이거 GPT Pro한테 리뷰시켜", "이 파일/코드 GPT한테 첨부해서 물어봐"), or to cross-check Claude's own answer against ChatGPT Pro. NOT for bulk scraping. Skip if the user explicitly wants the OpenAI API instead of the web UI.
---

# Ask ChatGPT Pro (via agbrowse)

Sends a prompt to a **logged-in ChatGPT Pro web session** and returns the reply as plain text on stdout, so Claude can read it and fold it into the work. The mechanism is `agbrowse` — an npm CLI that drives a local Chrome over CDP (no API key, no OpenAI API billing). Use it to get a **second opinion / review** from GPT-5.5 Pro next to Claude.

## One-time prerequisites (verify, don't assume)

1. **agbrowse ≥ 0.1.15 installed**: `agbrowse --version`. If missing/older → `npm install -g agbrowse@latest` (Node ≥ 18, MIT). **Version matters**: 0.1.14 could NOT switch model/effort on the Korean ChatGPT UI (model-selector not found); 0.1.15 added a `pro-effort-simplified-direct` selector that fixes it (verified 2026-06-24). On < 0.1.15, flags are silently ignored — update first.
2. **Chrome running under agbrowse**: `agbrowse status` → expect `running: true`. If not → `agbrowse start --headed` (launches a visible Chrome on a persistent profile at `~/.browser-agent/browser-profile`; login survives across calls).
3. **Logged into ChatGPT Pro**: the user must log in once, by hand, in that Chrome window — you cannot enter credentials. To check: `agbrowse text` and look for a logged-in surface vs a "로그인 / Log in" prompt. If logged out, **stop and tell the user to log in** in the agbrowse Chrome window, then continue. Login persists after that.

## The call

> ✅ **On agbrowse ≥ 0.1.15, `--model pro --effort extended` IS enforced** (verified 2026-06-24: send output reports `reasoning effort selected: extended` and the ChatGPT tab's model button shows `Pro 확장`). On 0.1.14 it was NOT (selector not found). **Always confirm via the send output**: a `reasoning effort selected: …` line = applied; a `not enforced` / `model selector not found` line = you're on an old build (update) — then fall back to setting the model manually in the window + a flagless send. Never infer the tier from the answer text alone.

ChatGPT Pro (the only working model here) is SLOW — a real review runs minutes. So **do NOT default to a blocking `query`**; split into a fast `send` + a background `watch`. (This is the original agbrowse skill's prescribed pattern for Pro/Thinking/Deep-Research, and it fixes the exact failure we hit: a blocking `query` froze the turn ~10 min with no feedback and the user couldn't tell whether the prompt had even been sent.)

### Default for Pro: send → background watch (non-blocking)

1. **send** (returns in seconds): submits the prompt, returns a sessionId. The prompt **visibly appears in the Chrome tab** — that is your ground-truth confirmation it actually went. *If nothing shows up in Chrome, the send failed* — don't claim it's "waiting for a response".
   ```
   SID=$(agbrowse web-ai send --vendor chatgpt --model pro --effort extended --new-tab --inline-only --prompt "질문/리뷰 전문" --json | node -pe 'JSON.parse(require("fs").readFileSync(0,"utf8")).sessionId')
   ```
2. **watch in the background** (does NOT block your turn): run it via the Bash tool with `run_in_background: true`. When the watcher process exits it injects a completion notification that re-activates you — **no polling needed**.
   ```
   agbrowse web-ai watch --session "$SID" --json --navigate
   ```
3. On completion, **collect through the mechanical gate — never read `.session.answer` directly.** The background watcher's completion notification can fire *during* a thinking pause, so a fresh re-activation does NOT by itself mean the answer is done. The `collect_final` function below writes ChatGPT's answer to **stdout only when the session is truly final** (status `complete` + `completedAt` set + answer non-empty + length stable across a 4 s re-read); otherwise stdout is empty and the reason goes to stderr. **Empty stdout ⇒ nothing to quote** — `watch` again, then re-run it. It uses `node` (never jq/python/temp files: jq is often absent on Windows and agbrowse *is* a Node CLI, so `node` is always present); it also handles the shape trap that `sessions show` nests the answer under `.session.answer` while `sessions list` is flat `.answer`.
   ```
   SID="01K…"   # the id captured at send
   collect_final(){ SID="$SID" node -e '
     const {execSync}=require("child_process");
     const rd=()=>{try{return (JSON.parse(execSync(`agbrowse web-ai sessions show "${process.env.SID}" --json`,{encoding:"utf8",maxBuffer:1<<26,stdio:["ignore","pipe","ignore"]})).session)||{};}catch(e){return {status:"read-error"};}};
     const a=rd(); try{execSync("agbrowse wait 4000",{stdio:"ignore"});}catch(e){} const b=rd();
     process.stderr.write(`gate read1: ${a.status} len=${(a.answer||"").length} completedAt=${a.completedAt||"-"}\n`+
                          `gate read2: ${b.status} len=${(b.answer||"").length} completedAt=${b.completedAt||"-"}\n`);
     const final=b.status==="complete"&&b.completedAt&&(b.answer||"").length>0&&(a.answer||"").length===(b.answer||"").length;
     if(!final){process.stderr.write("NOT FINAL — preamble or still streaming. Do NOT quote. watch again, then re-run collect_final.\n");process.exit(3);}
     process.stdout.write(b.answer);'; }
   collect_final          # stdout = the final answer; empty ⇒ not ready (read the stderr gate lines)
   ```
   `agbrowse wait` = cross-platform sleep (ms; prefer over shell `sleep` on Windows). ⚠️ `sessions show` is **READ-ONLY — it never advances the session**; only `watch`/`poll` drive the DOM to completion. `collect_final` only *reads and gates* — if it prints NOT FINAL, run `watch` (which advances), not `collect_final` in a loop. (If you must save the answer to a file, use the harness scratchpad's **absolute Windows path**, not `/tmp` — Git-Bash `/tmp` ≠ a path Windows tools resolve.)

4. **Why the gate exists — do not weaken it.** Pro extended has long "thinking" pauses; `watch`/`poll` can fire terminal *during* such a pause and hand back only the intro (e.g. an answer that stops at "새 결함만 추리겠습니다"). `.lastStreamingState` is unreliable — it reads `"unknown"` even when genuinely complete (verified 2026-07-01) — so **do NOT trust it**, and do not treat a short first reply as the answer just because a notification arrived. The gate's two `gate read…` stderr lines are your visible trace; if it exits NOT FINAL, keep the session and `watch` again rather than quoting a preamble. Mechanically withholding the text on stdout (not prose you must remember to obey) is the whole defense against the "short first reply mistaken for the answer" failure.

### When it doesn't go clean (these are the branches — don't loop or guess)

- **`send` shows nothing in the Chrome tab** → the send failed. Re-check `agbrowse status`, retry the send **once**; still nothing → report the raw send output to the user and stop. Never `watch` a send you can't see landed.
- **Completion notification never arrives** (background `watch` died / notification suppressed): after ~10–15 min, manually `sessions show "$SID" --json`; if status isn't `complete`, run `watch` again. Don't wait forever on the notification alone.
- **`watch` exits but status ≠ `complete`** (`error`/`cancelled`/`timeout`/…): stop, report the status **verbatim** to the user, do NOT extract an answer.
- **Length never settles** (still grew on 3 consecutive re-watches): stop looping — surface the partial answer with an explicit "may be incomplete" warning instead of spinning.
- **`node -pe` prints `undefined`/`null`**: this is NOT the answer — the session isn't ready or the JSON path is wrong. Re-check `.session.status`; if it's `complete` yet `.session.answer` is undefined you're reading the wrong shape (`sessions show` nests under `.session`; `sessions list` is flat `.answer`). Never present `undefined`/`null` as ChatGPT's reply.
- **Answer is empty string or a refusal**: report that ChatGPT returned no usable content and tell the user to check the Chrome tab — don't emit an empty attribution block.
- **Logged out mid-run** (answer stays empty, status never completes): run `agbrowse text`; if the login page shows, tell the user to re-log in in the agbrowse Chrome window, then re-send.

### Attaching files directly (code, docs, images, zip)

You can hand ChatGPT real local files instead of pasting their contents — this is verified working. Use `--file <path>`, **repeatable** for several files of mixed types (e.g. a code file + a doc + a screenshot + a zip) in one turn. When you use `--file`, **drop `--inline-only`** (the two are mutually exclusive — `--inline-only` means "no files").

```
SID=$(agbrowse web-ai send --vendor chatgpt --model pro --effort extended --new-tab \
  --file ./src/server.ts --file ./docs/spec.md --file ./screenshot.png \
  --prompt "첨부한 코드/스펙/스크린샷을 함께 보고 리뷰해줘" --json | node -pe 'JSON.parse(require("fs").readFileSync(0,"utf8")).sessionId')
```

**Attach vs inline — pick by size:**
- **Attach (`--file`)** when handing over whole files, large code/docs, binaries, or images — the file goes up as a real ChatGPT attachment, no token cost in the prompt and the original formatting/structure is preserved.
- **Inline (`--inline-only` + put text in `--prompt`)** for a short snippet or a focused question.

**Many files by glob** (instead of listing each): `--context-from-files "src/**/*.ts"` (repeatable; pair with `--context-exclude <glob>`), and `--context-transport upload|inline` controls whether the package is uploaded as a file or inlined.

**Windows paths**: quote paths containing spaces and use forward slashes — `--file "C:/Dev/my project/server.ts"`. Run `--context-from-files` globs from Git-Bash (or rely on agbrowse's own expansion), not PowerShell, whose globbing differs.

After `send`, the attachment(s) and prompt **visibly appear in the Chrome tab** — that's your confirmation the upload landed. Then background-`watch` for the answer as above.

### Quick path: blocking query (ONLY for fast/short)

For `--effort standard` or a short question where a few-minute block is acceptable, the combined call is fine — output is the assistant text on stdout:
```
agbrowse web-ai query --vendor chatgpt --model pro --effort standard --new-tab --inline-only --prompt "..." --timeout 300000   # --timeout is ms (300000 = 5 min)
```
**Never use blocking `query` for `--effort extended` / deep reviews** — use send→watch above.

## Continue a conversation vs start a fresh one

**DEFAULT = a fresh conversation.** When the user does NOT name a specific chat, always pass `--new-tab` so each review/question starts clean and prior unrelated context can't bleed in. Do NOT rely on agbrowse's raw default: with neither `--session` nor `--new-tab`, agbrowse auto-binds to the *current active tab / latest session* (i.e. it CONTINUES, not starts new) — which is the wrong behavior for an isolated second-opinion. Only continue when the user explicitly refers to an existing chat.

Every `send`/`query` is persisted (sessionId + conversation URL) in `~/.browser-agent/web-ai-sessions.json`; list them with `agbrowse web-ai sessions list`.

- **Continue a specific conversation** (keep its full context): `agbrowse web-ai query --vendor chatgpt --session <id> --prompt "후속 질문"`. Verified: this resumes the SAME conversation URL and the model recalls everything in that thread.
- **Start a brand-new conversation**: add `--new-tab` (with `--model pro --effort extended`). Verified: this really does create a new conversation (distinct `/c/<id>` URL).
- **Omitting `--session` auto-binds** in priority: `--session` > current active tab > that vendor's latest session > legacy baseline. So with no `--session` it continues the *last/active* chat — pass `--session <id>` explicitly whenever you mean a specific one.
- **Resume / reattach / prune**: `sessions show <id>`, `sessions resume`, `sessions reattach --navigate`, `sessions prune`. You can also attach to a conversation you made by hand in the browser via its URL (`--url https://chatgpt.com/c/<id>`).
- **First turn returns the id** for later resume: `SID=$(agbrowse web-ai send --vendor chatgpt --model pro --effort extended --inline-only --prompt "..." --json | node -pe 'JSON.parse(require("fs").readFileSync(0,"utf8")).sessionId')` then `agbrowse web-ai query --vendor chatgpt --session "$SID" --model pro --effort extended --prompt "후속"` (**`--model pro` is mandatory whenever `--effort` is present — see the rule below**).

**The user will refer to a chat by its content/title, not by the ULID — resolve it for them.** Don't ask the user for a sessionId. When they say e.g. "continue the PRO_STD_OK chat": run `agbrowse tabs` (shows each open tab's TITLE + conversation URL), match the title to find the URL, then map that URL to its sessionId via `agbrowse web-ai sessions list`, and call `query --session <id>`. (Or, for an open tab, target it directly with `--url https://chatgpt.com/c/<conversation-id>`.) Note the two distinct ids: agbrowse **sessionId** is a 26-char ULID (`01K…`, used with `--session`); the **conversation id** is ChatGPT's own (the `/c/<id>` URL slug, used with `--url`). If several open tabs could match, list the candidates and confirm which one before sending.

⚠️ **A "new" conversation is NOT a clean room.** Verified 2026-06-21: a fresh `--new-tab` conversation still recalled a secret from an *earlier, separate* conversation — because ChatGPT's account-level **memory / "reference chat history"** leaks facts across conversations. Thread isolation ≠ model isolation. If a review must not see prior context, have the user turn off "Reference saved memories / chat history" in ChatGPT settings (or use a Temporary Chat) — agbrowse cannot guarantee this.

## Hard-won rules (these WILL bite if ignored)

- **Model/effort: pass `--model pro --effort extended` (the default for reviews) — enforced on agbrowse ≥ 0.1.15.** Verified 2026-06-24 on 0.1.15: send output reports `model selected: pro` + `reasoning effort selected: extended` (selector `pro-effort-simplified-direct`), and the ChatGPT tab's model button reads `Pro 확장` — both agree. On **0.1.14 it was NOT enforced** (selector not found → it sent at whatever the window already had; this caused the earlier "got 매우높음/default effort" failures). So: keep agbrowse ≥ 0.1.15 (prereq #1), pass the flags, and **confirm via the send output's `reasoning effort selected:` line** every time. If you instead see `not enforced` / `model selector not found`, you're on an old build → update; as a last-resort fallback, have the user set the model manually in the window and send WITHOUT flags (inherits the window selection). Never infer the tier from the answer text alone.
- **Prompt must be `--prompt`.** A positional prompt is silently ignored and the call dies with `context.over-budget: prompt required`.
- **`--inline-only` is mandatory when there are no `--file`s.** Otherwise: `provider.attachment-preflight: require --inline-only or --file`.
- **`--effort` ALWAYS requires `--model pro` — pair them every time, including on `--session` resume/continue.** `--effort` alone dies at parse (`--effort requires a model`): agbrowse only touches the effort menu when `--model` tells it which menu maps efforts. So a continuation is `send/query --session "$SID" --model pro --effort extended --prompt …`, never `--effort` by itself. (To inherit whatever the window already has, omit BOTH flags — but then the tier isn't guaranteed.) This is the #1 resume mistake: passing `--effort extended` on a follow-up while dropping `--model pro`.
- **Model alias: only `pro` is valid.** `instant`/`thinking` and Korean labels (`--model 즉시`) error at parse (`model option not found` / `unsupported model selection`) — don't pass them. Within pro, `--effort extended` (프로 확장) and `--effort standard` (프로 표준) are the two tiers; extended is the review default. (Historical note: a 2026-06-21 "extended/standard verified" claim was a mis-read — those `UP_OK`/`PRO_STD_OK` tokens were prompt-dictated, and 0.1.14 wasn't enforcing at all. Genuine enforcement is verified only from 0.1.15 — see the rule above.)
- **Pro is slow → don't block the turn.** For `--effort extended` / deep reviews use **send → background `watch`** (see "The call"), never a blocking `query`. Only `--effort standard`/short questions may use the blocking `query` (with `--timeout 300000`). A blocked `query` gives no feedback for minutes and hides whether the prompt even sent — the user reads it as hung.
- **One active session at a time is simplest.** Multiple open provider tabs make `poll`/`stop` ambiguous; pass `--session <id>` to disambiguate, or `agbrowse tab-cleanup` / `agbrowse tabs` to tidy.
- **Under concurrency, always drive/read/gate by the explicit `$SID` you sent — never the active tab or "latest session".** The one logged-in Chrome and its `sessions list` are shared across every project/session; several reviews can be in flight at once. With no `--session`, agbrowse auto-binds to the *current active tab / latest session*, which under concurrency may be **another project's** review — so `watch`/`sessions show`/extract on it collects the wrong answer (or a preamble). Capture `$SID` at `send` and carry it through every later call; when in doubt, `agbrowse web-ai sessions list` and match by your own sessionId, not by which tab is frontmost.

## After use

- Leave Chrome up to keep the session warm for the next call, or `agbrowse stop` to close it. The login persists either way.
- Present ChatGPT's answer as **a second opinion, clearly attributed to ChatGPT Pro** — do not silently merge it into Claude's own voice. Compare/contrast with Claude's view so the user sees both.

## Limits

- Automating a logged-in ChatGPT web session is an OpenAI-ToS grey area; it's the user's account and risk. Use for occasional review/second-opinion, not bulk or unattended scraping.
- Verified working 2026-06-21 (logged-in Pro, Korean UI): pro extended/standard round-trips, `--file` upload round-trip. Tool is pre-1.0 and ChatGPT's UI shifts — if model selection breaks, re-check the menu against agbrowse's expected `--model`/`--effort` vocabulary.
