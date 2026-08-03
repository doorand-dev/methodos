# OpenCLI adapter

Use this adapter only when the user selected `opencli`. Keep model selection and
conversation operations in the same persistent site session and retained tab.

```powershell
opencli chatgpt model pro --window background --site-session persistent --keep-tab true
opencli chatgpt ask "<request>" --new true --wait true --timeout 300 `
  --window background --site-session persistent --keep-tab true -f json
```

For a known existing conversation, pass its ID or `/c/...` URL with
`--conversation`. `ask --wait` is the preferred new-conversation path because it
returns the conversation identity and response. For asynchronous continuation
of a known conversation, use `send --conversation <id-or-url>` and then
`detail <id-or-url> --wait true`; `Generating` must be false and the response
stable before collection. `status` proves only page/login connectivity, not
answer completion.

Current `ask` and `send` help exposes no ordinary conversation attachment
option. `project-file-add` uploads project knowledge and is not a substitute.
If the request needs a chat attachment, stop and offer a named transport change.

Use the returned conversation ID/URL for continuation. If `ask` fails before
returning one, do not assume the prompt was sent. Inspect only the retained
OpenCLI tab through its own `status`/`read` surface; if identity or completion
remains unknown, report the timeout or missing target. Do not switch adapters.
