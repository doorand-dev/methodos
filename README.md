# Methodos

Methodos is a reference kit for AI coding agents. It turns unclear requests
into explicit user decisions, small implementation slices, tests, and exact
changed-path checks. It is not an installer or a central router.

## Profiles

| Profile | Start with | Add when |
|---|---|---|
| `bootstrap` | `setup-methodos` | first adoption |
| `core` | `grill-me`, `plan`, `impl`, `decision` | normal coding work |
| `core+novelists` | `core` plus `spec-novelist` | several actors or flows |
| `continuity` | `handoff`, `snapshot`, `todo`, `context-novelist` | work across sessions |
| `learning-loop` | `blame-code`, `finding`, `gc`, `improve-codebase-architecture` | recurring friction |
| `optional` | `conditional-heartbeat`, `ask-chatgpt-pro`, `report-kit` | explicitly requested extensions |
| `hooks` | runtime-specific hook examples | after manual trust and registration |

Codex skills live in `skills/codex/`; Claude skills and agents live in
`skills/claude/` and `agents/claude/`.

## Walkthrough

```text
Idea
  -> grill-me clarifies the observable goal when WHAT is unresolved
  -> plan (when useful) names vertical slices and tests
  -> impl routes simple work directly and otherwise follows the active runtime
  -> local tests + exact changed paths close routine work
  -> one conditional semantic review is selected only for real high-risk seams
```

Safety checks remain concrete: test execution, exact paths, explicit user
approval for external work/user data/permissions/database or schema/public
contract/concurrency/migration/external state, provider completion state, and
requested attachment name/count checks. Model, effort, transport, session,
commit message, or temporary artifact details are not completion evidence.

## Skill families

Core skills are `setup-methodos`, `using-methodos`, `grill-me`, `plan`, `impl`,
`decision`, `spec-novelist`, and conditional `impl-novelist`. Claude's
`plan-verify` and `impl-verify` are optional advisory checks. `ask-chatgpt-pro`
uses a logged-in browser only after explicit user approval; short questions use
direct calls and long monitoring is opt-in.

Continuity skills preserve only the context needed to continue a real task.
Learning-loop skills preserve durable external facts or friction when their
explicit triggers apply. Hooks are reference scripts and remain inactive until
the adopting runtime registers and trusts them.

## Adoption

1. Read the relevant runtime skill and choose roots that the runtime actually
   reads.
2. Copy/adapt only the selected skills and agents.
3. Register hooks manually after reviewing their scope.
4. Run local tests and inspect the exact changed paths.

## Repository layout

```text
skills/claude/         Claude skill realizations
skills/codex/          Codex skill realizations
agents/claude/         Claude reviewer and novelist definitions
hooks/common/          Reference hooks shared by runtimes
hooks/claude/          Claude hooks
hooks/codex/           Codex hooks and registration example
```

MIT. See [`LICENSE`](LICENSE).
