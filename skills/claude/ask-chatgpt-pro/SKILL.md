---
name: ask-chatgpt-pro
description: Ask a logged-in ChatGPT web session for a second opinion or review through agbrowse.
---

# Ask ChatGPT Pro

Use only for an explicit external second opinion. Short questions use direct
`agbrowse web-ai query` or `send` then `collect`; no heartbeat/watcher is
created unless the user requests asynchronous monitoring.

Ask approval before any external upload. Reject secrets and `.env` paths. After
send, inspect the actual sent turn and verify requested attachment names and
count. Collect only when provider status is complete, a completion time exists,
and the answer is non-empty/substantive; otherwise say it is not final.

Session ids and conversation URLs are transient continuation targets only. Do
not report them as provenance. Provider role flags are selection hints, not
completion proof. The helper reports status, completion time, answer
text/length, and attachment checks without hashes, ledgers, or report schemas.
