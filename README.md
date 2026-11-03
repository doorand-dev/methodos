# Methodos

Methodos is a reference kit for Codex: reusable skills, custom agent profiles,
rule examples, and optional local tools. Choose the pieces that fit your work,
adapt their dependencies, and verify them in your environment.

Skills keep their own triggers; Methodos does not add a central runtime
router. Cloning this repository does not install skills, enable hooks, or start
automations.

## Start with the task you have

The [Codex selection and installation guide](contract/codex/START-HERE.md)
lists the available skills, dependencies, installation paths, and invocation
rules. Start with one task rather than copying the whole kit.

| What you need | Start with |
|---|---|
| Preserve work before compaction / move work to a new chat | `snapshot` / `handoff` |
| Divide independent work and collect the results | `orch` |
| Check what the next AI reader needs / improve context loading | `context-novelist` / `improve-context` |
| Find missing product requirements | `product-novelist` |
| Investigate a specific mistake / recurring process waste | `blame-context` / `retro` |
| Inspect code-misreading friction / clean a project | `blame-code` / `gc` |
| Improve code structure / reuse a repeated workflow | `improve-codebase-architecture` / `workflow-reuse` |
| Record external facts / choose where knowledge belongs | `finding` / `ai-knowledge-routing` |
| Write clear Korean prose / investigate current examples | `purposeful-writing` / `trend-research` |
| Keep work across sessions | `todo` |

Optional tools are `model-router`, `ask-chatgpt-pro`, `report-kit`, and
`add-youtube-channel`. They have additional environment or project requirements;
read their conditions in the guide before selecting them.

## Install and invoke one skill

1. Read `skills/codex/<name>/SKILL.md`, then copy the selected folder, including
   supporting files, to `~/.agents/skills/<name>/`. Compare existing files before
   updating them.
2. Follow the [installation guide](contract/codex/START-HERE.md) for any required
   profiles under `~/.codex/agents/`, configured model policy, and rule files.
   Keep existing activation settings and permission boundaries.
3. Confirm that your runtime discovers the skill. In Codex CLI or the IDE,
   mention a skill with `$snapshot`, or ask for it by name in your request.
   Each skill's description and invocation policy determine when it applies.
   `gc` and `blame-code`, for example, require explicit requests.
4. Try one small task, run relevant checks, and inspect the exact changed paths.
   A model name, report, or transport receipt does not prove completion.

[Codex wake](contract/codex/codex-wake.md) is a separate, unofficial Windows
Python helper for resuming an authorized existing chat after a real event.
It needs a compatible installed app bridge and queue CLI. Offline tests do not
establish compatibility with your installed app version.

## Optional hooks and local verification

Review selected entries in the [Codex hook guide](hooks/codex/README.md) before
registration. Worktree retirement uses an explicit CLI action; it is not a
startup hook. Nothing in this repository grants permission for deletion,
scheduling, browser access, or message delivery.

The hook test suite needs Python 3.11+ and `pytest`. It uses disposable test
repositories and fake bridge responses. The GC safety suite also starts
PowerShell with an isolated temporary user directory; it does not change real
automations.

```powershell
python -B -m pytest -q -p no:cacheprovider hooks/common hooks/codex skills/codex/gc/tests
```

Actual app delivery, external review, login, scheduling, and hook registration
need checks in the adopting environment.

## Repository layout

```text
skills/codex/          Task-specific skills and optional tools
agents/codex/          task-worker and blame-code reader/judge profiles
contract/codex/        Installation guide, rule examples, and wake guide
hooks/common/         Local helpers, explicit worktree cleanup CLI, and wake
hooks/codex/          Optional hook registration examples and tests
docs/specs/           Superseded design notes, not active installation rules
.Codex/plans/         Superseded plans, not active execution instructions
```

Public examples omit personal accounts, chat identifiers, project data, model
assignments, and login state. Configure your own paths, supported models, and
permissions. MIT; see [LICENSE](LICENSE).
