# Methodos

Keep long Codex tasks moving through compaction, handoffs, and parallel work.
Methodos packages the instructions, agent profiles, and local helpers behind
those three jobs. Pick the one you need; each skill keeps its own trigger.

## Start with one job

| When you need to… | Use | What a successful run gives you |
|---|---|---|
| Continue the same chat after compaction | [`snapshot`](contract/codex/QUICKSTART.md#1-save-before-compaction) | Saved priorities, the next action, and a prompt to reload them after compaction |
| Move a bounded task into a new chat | [`handoff`](contract/codex/QUICKSTART.md#2-move-work-to-a-new-chat) | A handoff file, a new chat, and its confirmed creation state |
| Divide independent work inside the current task | [`orch`](contract/codex/QUICKSTART.md#3-divide-two-independent-checks) | Worker results, their checks and gaps, and the parent's combined answer |

Start with `snapshot`; it needs no model policy or custom agent profile.
The [English quickstart](contract/codex/QUICKSTART.md) gives a guarded copy
command, prerequisites, and a request → result → check example for each job.
It also explains how to [update or remove your selections](contract/codex/QUICKSTART.md#update-or-remove-selected-components).

**Language:** onboarding is available in English; the
[full skill catalog and advanced setup notes](contract/codex/START-HERE.md)
and the skill instructions are currently written in Korean. The example
requests in the quickstart ask for English responses.

## First run: preserve the next action

After installing `snapshot`, use it in a real task when compaction is imminent:

```text
Use snapshot before compaction. Keep the next action, unresolved questions,
and the constraints for this task. Reply in English and give me the exact
prompt to paste after compaction.
```

Check the saved file and keep the returned reload prompt. After compaction,
paste that prompt into the same chat and check that Codex resumes the recorded
next action. Reload is a manual step; saving a file alone does not restore the
chat's working context. See the [complete example](contract/codex/QUICKSTART.md#1-save-before-compaction).

## More tasks

The [catalog](contract/codex/START-HERE.md) covers task skills and four
optional tools. It includes context review, product requirements, mistake
analysis, code structure, reusable workflows, durable findings, writing, and
research. Choose these as the need arises.

`model-router`, `ask-chatgpt-pro`, `report-kit`, and `add-youtube-channel` have
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
python -B -m pytest -q -p no:cacheprovider hooks/common hooks/codex skills/codex/gc/tests skills/codex/snapshot/tests
```

These checks use disposable files and repositories and fake app responses.
They verify the local helpers; actual compaction, new-chat creation, and event
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
