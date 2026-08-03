# AG Browse adapter

Use this adapter only when the user selected `agbrowse`. Always pass
`--vendor chatgpt --model pro`. Use `query` for a short foreground request. For
long work, use `send`, keep the returned session and target binding, then use
session-bound `poll` or `watch`.

```powershell
agbrowse web-ai query --vendor chatgpt --model pro --inline-only `
  --system "<common proportional-verification instruction>" `
  --prompt "<request>" --timeout 300

agbrowse web-ai send --vendor chatgpt --model pro --inline-only `
  --new-tab --system "<common proportional-verification instruction>" `
  --prompt "<request>" --json
agbrowse web-ai poll --session <session-id> --timeout 300 --json
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

The existing `scripts/pro-review.ps1` is an optional AG Browse helper, not a
common router or authority for the other adapters.
