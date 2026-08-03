# OpenCLI adapter

Use this adapter when the router selected `opencli`. Isolate parallel jobs:
use an ephemeral site session for each adapter command or a distinct named
`opencli browser` session and exact target. Do not run parallel collection in
one persistent site session; concurrent `detail` calls there can resolve the
same default tab.

```powershell
opencli chatgpt model pro --window background --site-session persistent --keep-tab true
opencli chatgpt ask "<request>" --new true --wait false `
  --window background --site-session ephemeral --keep-tab true -f json
```

For a known existing conversation, pass its ID or `/c/...` URL with
`--conversation`. `ask --wait false` is the new-conversation send path because
it returns the conversation identity without holding the initiating turn. Each
heartbeat reads that identity with `detail <id-or-url> --wait false` in its own
ephemeral site session. Collect only after the assistant turn exists and
`Generating` is false. `status` proves only page/login connectivity, not answer
completion.

Current `ask` and `send` help exposes no ordinary conversation attachment
option. `project-file-add` uploads project knowledge and is not a substitute.
If the request needs a chat attachment, stop and offer a named transport change.

Use the returned conversation ID/URL for continuation. If `ask` fails before
returning one, do not assume the prompt was sent. Inspect only the retained
OpenCLI tab through its own `status`/`read` surface; if identity or completion
remains unknown, report the timeout or missing target. Do not switch adapters.
