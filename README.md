# Methodos

Review the context an AI receives, hand a bounded task to a new chat, or divide
independent work. Methodos provides task-specific instructions, agent profiles,
and local helpers. Choose what fits your task; each skill keeps its own trigger.

## Start with one job

| When you need to… | Use | What a successful run gives you |
|---|---|---|
| Check whether the next AI has enough context | [`context-novelist`](contract/codex/QUICKSTART.md#1-review-a-context-entrypoint) | Missing decisions, ambiguous permissions, and concrete improvements tied to evidence |
| Move a bounded task into a new chat | [`handoff`](contract/codex/QUICKSTART.md#2-move-work-to-a-new-chat) | A handoff file, an explicitly requested new chat, and its confirmed creation state |
| Divide independent work inside the current task | [`orch`](contract/codex/QUICKSTART.md#3-divide-two-independent-checks) | Worker results, their checks and gaps, and the parent's combined answer |

The [English quickstart](contract/codex/QUICKSTART.md) starts with a read-only
context review, a guarded copy command, and request → result → check examples.
It also explains how to [update or remove your selections](contract/codex/QUICKSTART.md#update-or-remove-selected-components).
The repository already includes an optional [global AGENTS example](contract/codex/AGENTS.example.md)
and [custom agent TOMLs](agents/codex/); the quickstart maps each to its user installation path.

**Language:** onboarding is in English; the [catalog](contract/codex/START-HERE.md)
and skill instructions are currently in Korean. Example requests ask for English responses.

## First run: review a context entrypoint

After installing `context-novelist`, try this in the current chat:

```text
Use context-novelist to review README.md as the entrypoint for an AI helping
someone select a Methodos skill. Check whether it can find the installation
steps, permission boundaries, and completion checks. Read local references as
needed. Reply in English with evidence and proposed improvements only.
Do not edit files, run helpers, delegate, create chats, or send messages.
```

Check that each finding identifies the supplied context and the decision it
supports or leaves unclear. This first review needs no custom agent, model
policy, new chat, or helper execution. See the [complete example](contract/codex/QUICKSTART.md#1-review-a-context-entrypoint).

## More tasks

The [catalog](contract/codex/START-HERE.md) covers task skills and
optional tools. It includes context review, product requirements, mistake
analysis, code structure, reusable workflows, durable findings, writing, and
research. Choose these as the need arises.

`ask-chatgpt-pro`, `report-kit`, and `add-youtube-channel` have
additional environment or project requirements described in the catalog.
[Codex wake](contract/codex/codex-wake.md) is a separate, unofficial Windows
helper that delivers a real event to an authorized existing chat. Its app bridge
and queue CLI must be compatible with the installed environment.

## Local checks and optional hooks

[Hook registration](hooks/codex/README.md) is opt-in. Worktree retirement uses
an explicit CLI action. Installing a skill does not activate hooks, create a
schedule, or grant permission to send messages or delete data.

The combined Python suite needs Python 3.11+ and `pytest`. On Windows, the GC
safety tests also use Windows PowerShell with a temporary user directory.

```powershell
python -B -m pytest -q -p no:cacheprovider hooks/common hooks/codex skills/codex/gc/tests
```

These checks use disposable files and repositories and fake app responses.
They verify the local helpers; actual new-chat creation and event
delivery need confirmation in the adopting runtime. The quickstart lists the
required capabilities and what to do when they are unavailable.

## Repository layout

```text
skills/codex/          Task-specific skills and optional tools
agents/codex/          Custom worker and blame-code reader/judge profiles
contract/codex/        Quickstart, catalog, rules, and wake guide
hooks/common/         Local helpers, explicit worktree cleanup CLI, and wake
hooks/codex/          Optional hook examples and tests
docs/specs/           Superseded design notes
.Codex/plans/         Superseded plans
```

Public examples omit personal accounts, chat identifiers, project data, model
assignments, and login state. Keep your own paths, supported models, permissions,
and activation settings. MIT; see [LICENSE](LICENSE).
