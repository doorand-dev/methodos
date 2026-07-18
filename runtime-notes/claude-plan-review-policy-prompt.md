# Claude plan review policy prompt

Use this prompt only when a plan changes a public/user flow, shared contract or
permission/data behavior, an irreversible operation, external state/
concurrency/migration, or when the user explicitly asks for a semantic review.

Read the plan and its public callers, producers, consumers, and failure paths.
Run the stated preflight/tests and return concise `PASS`, `NEEDS_CONTEXT`, or
path/line findings to the caller. Routine plans close with local checks and an
exact changed-path list.

Do not use reports, lineage/SHA fields, model/effort/session/transport
attestation, terminal packets, watcher/heartbeat polling, or automatic repair
loops as completion gates. Preserve explicit user approval for external effects
and state when the provider actually reports completion.
