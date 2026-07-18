---
slug: codex-slice-owner-controller-review
status: superseded
---

# Superseded plan

Use the current `impl` routing and contract. An owner edits only its declared
paths, runs local tests, and checks the exact changed-path list. Select one
semantic review only for a new public/user flow, shared contract or
permission/data behavior, external state/concurrency/migration, or a real
multi-slice seam. Routine work does not need a controller final review.

Keep explicit user approval for external effects and inspect provider completion
state and requested attachment names/counts where relevant. Do not require
lineage, SHA, session/model/effort provenance, report/terminal artifacts, or a
WHY completion ceremony.
