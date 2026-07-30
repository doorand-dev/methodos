---
name: blame-context
description: |
  Capture and classify a context-caused misread at the moment it occurs, using the current session's evidence, and append one compact incident to the workspace-local .Codex/context-friction.md. Explicit trigger only: use when the user directly says "blame context", "blame-context", "/blame-context", "컨텍스트 탓해봐", "컨텍스트 귀책으로 기록해", or explicitly asks whether the current misread was caused by context. Never auto-trigger from generic corrections such as "아니", "잘못 봤어", or "헷갈렸네". Never spawn a subagent, fresh reviewer, or thread for this skill.
---

# Blame Context

Record one live context-friction incident while the session still has the exact
prompt, loaded artifacts, recent decision, and user correction. Judge the
incident in the current session; isolation would discard the evidence this
collector exists to preserve.

## Hard boundary

- Never call a subagent, create a thread, or delegate the judgment.
- Do not scan the repository broadly. Read only the exact artifact or runtime
  output directly implicated by the misread.
- Do not repair the context system or propose a new architecture here.
- Allow `model-misread`, `not-context`, and `unresolved` as normal outcomes. A
  context collector that blames context every time is itself bad evidence.

## Procedure

1. Identify the single current incident from the assistant's mistaken decision
   and the user's correction. If the mistaken proposition is ambiguous, ask for
   one-line confirmation before recording it.
2. Reconstruct only what was available at that decision: injected instructions,
   explicitly loaded files, hook output, route metadata, and the recent action.
   Do not treat model memory as a reliable required-context ingress.
3. Classify the incident with exactly one value:
   `missing-context`, `stale-context`, `wrong-routing`, `wrong-authority`,
   `over-context`, `ambiguous-contract`, `model-misread`, `not-context`, or
   `unresolved`.
4. Decide `context-fault: yes | no | uncertain` from concrete evidence. Name the
   failed edge when possible as:

   ```text
   From | Trigger | Action | To | Lifetime | Authority | Failure
   ```

5. Append one entry to `<workspace>/.Codex/context-friction.md`. Create the file
   lazily when it does not exist; do not create it merely because this skill was
   loaded.
6. Report only the new incident id, classification, and `context-fault` value.

## Context friction store

The workspace-local `.Codex/context-friction.md` is the sole incident store for
this context trio. On lazy creation, add the title `# Context Friction` and then
append entries in this schema:

```markdown
## CTX-001
- trigger: <exact user invocation>
- misread: <X was mistaken for Y>
- expected-context: <minimum context that should have governed the decision>
- available-context: <what the session actually had>
- failed-edge: <edge tuple or unresolved>
- classification: <enum value>
- context-fault: yes | no | uncertain
- evidence: <path:line, exact field, hook output, or user correction>
- next-guard: <smallest candidate guard, not an implemented fix>
- status: open | closed | resolved
```

Use the next zero-padded id. Set `status: open` for `yes` or `uncertain`, and
`closed` for `no`. Preserve `no` incidents so `context-gc` can detect systematic
self-exoneration or over-attribution instead of seeing only selected failures.
This collector never writes `resolved`; `improve-context-architecture` may change
an open incident to `resolved` only after the selected change is implemented and
its verification passes.

## Companion routing

- `context-gc` audits the store together with scoped or full context surfaces.
- `improve-context-architecture` processes repeated structural patterns.
- `context-novelist` validates a specific point-of-use packet or changed route;
  it is not part of this immediate collector.
