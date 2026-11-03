# First run: keep a Codex task moving

Start with **context-novelist** for a read-only review in the current chat.
Choose **handoff** when you explicitly want a new chat, or **orch** when
independent work benefits from workers. Each is a separate choice.

This guide is in English. The [catalog](START-HERE.md) and skill instructions
are currently in Korean; the practice requests below ask for English responses.
Expected outputs are examples to check against, not transcripts of a live run.

## Check your runtime

| Job | Required capability | If it is unavailable |
|---|---|---|
| context-novelist | Codex can read the selected context and its local references | Report inaccessible references and limit conclusions to what was read |
| handoff | Codex app tools can list chats/projects, create a chat, and inspect its creation state; sidebar tools are needed for the applicable location transfer | The automatic new-chat workflow is unavailable. Report the missing tool; a saved JSON file is not a completed handoff. Use the skill's manual-start fallback only after creation fails |
| orch | Subagent spawn, wait, and close tools expose supported models/efforts and the `task-worker` role | Stop the worker example and report the missing capability; do not pretend that local work was delegated |

The copy examples below use **Windows PowerShell**. On another OS, copy the same
folders to the user locations in the installation table. The first context
review needs no Python helper. The full repository test suite requires Python 3.11+.

Local helper checks use temporary files. App tools and their names vary by
runtime; confirm they are available in the adopting session before the chat and
worker examples. See the official [skills](https://developers.openai.com/codex/skills)
and [custom agents](https://developers.openai.com/codex/subagents#custom-agents)
documentation for discovery and configuration.

## Install only the required components

Clone the repository once, or open your existing reviewed checkout:

```powershell
git clone https://github.com/doorand-dev/methodos.git
Set-Location methodos
```

| Selection | Copy from this repository | Install at / merge into |
|---|---|---|
| context-novelist | `skills/codex/context-novelist/` | `~/.agents/skills/context-novelist/` |
| handoff | `skills/codex/handoff/` | `~/.agents/skills/handoff/` |
| orch | `skills/codex/orch/` | `~/.agents/skills/orch/` |
| handoff or orch | `contract/codex/rules/model-routing.json` | `~/.codex/rules/model-routing.json`; configure before use |
| handoff | `contract/codex/rules/thread-orchestration.md` | `~/.codex/rules/thread-orchestration.md` |
| orch | `agents/codex/task-worker.toml` | `~/.codex/agents/task-worker.toml` |
| Optional global instructions | `contract/codex/AGENTS.example.md` | Merge selected rules into `~/.codex/AGENTS.md` |
| Optional blame-code reviewers | `agents/codex/blame-code-reader.toml`, `agents/codex/blame-code-judge.toml` | `~/.codex/agents/`, retaining each filename |
| Only when selecting the worktree cleanup CLI/queue | `contract/codex/rules/worktree.md`, `hooks/common/worktree-cleanup.py` | `~/.codex/rules/worktree.md`, `~/.codex/rules/scripts/worktree-cleanup.py` |

Copy complete skill folders, including any `agents/openai.yaml`, scripts, and
references. Keep an existing file's activation policy. The table describes a
user-level installation because the skills reference these user paths; a
project-only adoption must adapt those references too. `context-novelist` does not
require `task-worker`, the model policy, or any hook.

For a first `context-novelist` installation, run this from the checkout root. It refuses
to overwrite an existing destination:

```powershell
$skillName = 'context-novelist'
$skillSource = Join-Path (Get-Location) "skills/codex/$skillName"
$skillDestination = Join-Path $env:USERPROFILE ".agents/skills/$skillName"
if (-not (Test-Path -LiteralPath (Join-Path $skillSource 'SKILL.md'))) {
    throw 'Open the Methodos checkout root first.'
}
if (Test-Path -LiteralPath $skillDestination) {
    throw 'Already installed: compare the existing folder before updating.'
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $skillDestination) | Out-Null
Copy-Item -LiteralPath $skillSource -Destination $skillDestination -Recurse
```

For another selected skill, change only `$skillName` and repeat the guarded
copy, then copy its table dependencies individually after checking for existing
files. The rule folders and your global `AGENTS.md` are shared surfaces; do not
replace them wholesale. The [AGENTS example](AGENTS.example.md) is optional.
A first run needs only the selected skill and its dependencies, not that whole
example or any unrelated skills it mentions. These AGENTS and agent TOML examples
are already included in the repository. Do not copy a personal `config.toml`
wholesale; retain local settings and change only what the selected feature needs.

### Configure the model policy for handoff or orch

If you installed only context-novelist, [skip to its first run](#1-review-a-context-entrypoint).

The [model policy](rules/model-routing.json) records the user's preferred models
and efforts for new owners and workers. It is separate from proxy or API request
routing. Preserve existing preferences when adopting it on another machine,
including a company PC used by the same person; verify actual model and effort
support there before dispatch. Do not force one model or delete the whole policy.

For a new installation, configure `tiers.main.model`, `main.parent_effort`, and
`main.worker_effort` using values supported by the corresponding create/spawn
tool, then set `configured` to `true`. Do not dispatch an unconfigured route.
Retain other user routes and the template's rules and `worker_agent_type`.
For these examples, the new handoff chat is an owner: pass `main.parent_effort`
as its supported `thinking` value. Pass `main.worker_effort` as the effort for
orch workers. Check each value against the corresponding tool before dispatch.

This minimum does not enable another provider or a review route. Add and
configure another tier when a later task actually requires it; a required
cross-provider review must not fall back to the main model silently. Existing
user or project routing choices take precedence over this template.

Open a new chat and confirm that the selected skill is discoverable. For orch,
confirm that the spawn tool exposes `task-worker`; a copied TOML file alone does
not prove it loaded. If it is missing, check the required TOML fields, the user
agent directory, and runtime discovery, then restart if needed. Do not create
more profile copies as a workaround.

## 1. Review a context entrypoint

Use this request in the current chat on the Methodos checkout:

```text
Use context-novelist to review README.md as the entrypoint for an AI helping
someone select a Methodos skill. Check whether it can find the installation
steps, permission boundaries, and completion checks. Read local references as
needed. Reply in English with evidence and proposed improvements only.
Do not edit files, run helpers, delegate, create chats, or send messages.
```

**Expected result:** findings linked to the actual entrypoint and relevant
references, explaining what the next AI can decide and where it would have to
guess. The review can conclude that no change is needed.

**Check:** findings distinguish evidence read from behavior inferred. The review
stays in this chat and proposes changes without applying them. No custom agent,
model policy, helper, or new-chat permission is needed. The skill's optional
independent review does not override this request's no-delegation boundary.

## 2. Move work to a new chat

After installing handoff and its dependencies, use the app environment with the
required chat tools. This request explicitly authorizes creating one new chat:

```text
Use handoff to create a new chat for this read-only task:
compare README.md with contract/codex/START-HERE.md and report any mismatch
in the starting jobs. This is a parallel split: keep the original
chat's pin and sidebar position. Use this same local checkout; no new worktree.
Do not archive the original chat or delete the handoff packet, even after
completion. The new chat must not edit source files, create
GitHub issues, publish, or send messages to other chats. Include these
constraints in its initial instructions. Use the configured model policy.
Reply in English with the handoff path, new chat identity, and confirmed
creation state.
```

**Expected result:** the scoped handoff JSON and a new chat that receives its
path, role, and first documents to read. New packets use
`<workspace>/.codex_context/handoff/<short-task-id>.json`. Existing
`.claude_context/` data remains readable for compatibility; do not bulk-move or
delete it. Check project ignore rules before saving private task context. The new
chat receives only the selected context, without the old chat's full history.
Optional GitHub issue integration is unnecessary here.

**Check:** open the new chat, confirm that it reads the packet and performs the
read-only comparison. A queued creation ID means creation was accepted; it is
not evidence that the new chat ran or finished. If creation fails, keep the
packet, inspect existing state before retrying, and use the skill's manual-start
prompt. This example explicitly keeps the packet and the original chat's
pin/location. The skill's replacement-handoff behavior is unnecessary for this
parallel practice task; the initial instructions must carry those constraints
into the new chat.

## 3. Divide two independent checks

After installing orch and its dependencies, verify its worker role and model
policy as above. This small example deliberately requests two workers so you
can observe the complete dispatch and collection path:

```text
Use orch with two task-worker agents for independent read-only checks.
Worker A: read README.md and list the starting jobs and their results.
Worker B: read contract/codex/START-HERE.md and identify the installation dependencies and
permission boundaries for handoff and orch.
Use only the configured main route. Do not edit files, create reports,
create chats, use a worktree, or delegate again. Return each worker's result,
what it checked, and any gaps; close both workers and combine the findings
in this chat. Reply in English.
```

**Expected result:** two scoped worker results, their verification and gaps,
then the parent's combined answer. Creating a worker is not task completion.

**Check:** the actual spawn calls name `task-worker`, an available model and
effort, and the assigned scope. The parent collects completed results, closes
the workers, and reconciles any disagreement. If tools or the role are missing,
stop this example and report which capability is absent. In ordinary work,
orch may keep small, tightly coupled tasks local when delegation adds no value.

## Coordinate only when the next step depends on it

When the current turn needs another chat's result, use `wait_threads` to collect
it. For a long task where A manages and B performs the work, a user-authorized
short completion notice from B can wake idle A to continue the next step.
Independent chats do not send unnecessary reports. Follow the
[thread messaging rules](rules/thread-orchestration.md) and preserve existing
message permissions; do not create a watcher or schedule for routine coordination.
[Codex wake](codex-wake.md) is for external server events, not ordinary chat completion.

## Update or remove selected components

Keep track of which rows in the installation table you adopted. Follow each
selected component across skill, profile, and shared rules when updating it.

**Update:** inspect the new source revision in the checkout, compare each
installed file, preserve your local edits and activation settings, and replace
only the reviewed components. Preserve configured model values while merging
policy changes. Open a new chat and repeat the relevant first-run check. File
copying does not confirm that an already-running chat loaded the new version.

**Remove or disable:** first finish any active writer or worker using the
component. Use your runtime's skill-disable setting if you want to stop using a
skill while keeping its files; official configuration supports disabling a
specific skill path. For file removal, compare your installed copy, then move
only that selected skill folder out of all discovery roots or remove it under
your own cleanup policy. A project copy or symlink can still make the same skill
appear; check the listed source path before changing another installation.

| Selection being removed | Preserve / inspect separately |
|---|---|
| handoff | Keep packets needed by unfinished tasks; new chats have their own lifecycle |
| orch | `task-worker` and the model policy may serve other work; remove only if no consumer remains |
| any shared rule or AGENTS addition | Remove only references you added and no longer need; preserve unrelated rules and settings |

Do not delete an entire user skills directory, agent directory, model policy,
`config.toml`, or task-data folder to remove one skill. If cleanup is blocked,
report the actual failure and follow the adopting environment's cleanup policy.
