# AG Browse adapter

Use this adapter when the router selected `agbrowse`. Always pass
`--vendor chatgpt --model pro`. Use `send`, keep the returned session and target
binding, schedule the common heartbeat, and end the initiating turn. A
heartbeat uses session-bound `poll` or `watch`; a recoverable poll timeout means
the request is still generating, not that the request failed.

```powershell
agbrowse web-ai send --vendor chatgpt --model pro --inline-only `
  --new-tab --system "<common proportional-verification instruction>" `
  --prompt "<request>" --json
```

Continue an existing saved conversation only with its returned `--session`.
Attachments use repeatable `--file` after the common upload gate; omit
`--inline-only` when files are present. Inspect the sent turn's attachment
result rather than trusting the requested path list.

Keep collection bound to the returned session and target. Do not run a generic
snapshot or routine `sessions doctor --navigate` while that target is healthy
and generating. On timeout, poll or resume the same session. Use `sessions
doctor` only for a missing/recovery target, and never navigate a live target to
a bare provider origin. A failed recovery is a transport failure, not permission
to switch adapters.

The existing `scripts/pro-review.ps1` is an optional AG Browse send helper, not
a common router or collection owner. Use its no-watch send path only; never run
its watcher alongside the common heartbeat. The heartbeat is the sole collector.
