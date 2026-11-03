# Codex Hook Registration

The Methodos hook scripts are optional examples. They require Python 3.11+
and a Codex version with the corresponding hook events and tool names. See
the [official hook configuration guide](https://developers.openai.com/codex/hooks)
for discovery, trust, matchers, and command fields. This repository does not
register policy for you.

Use `hooks.example.json` as a reference registration shape. Select only the
entries you have reviewed; this file is not a mirror of an active personal
hook configuration. It is intentionally named
`.example.json` so cloning this repository does not activate hooks by surprise.

## Activate Manually

1. Review selected entries from `hooks.example.json` and merge them into your
   existing hook configuration, preserving unrelated entries. For a new
   configuration, use one of the runtime-supported locations:
   - user-wide: `~/.codex/hooks.json`
   - project-local: `<target-repo>/.codex/hooks.json`
2. Replace every `/absolute/path/to/methodos` and
   `C:\absolute\path\to\methodos` placeholder with this checkout path.
3. Confirm that your installed Codex version supports these events, tool
   matchers, and command fields. Start a new chat and review/trust the selected
   definitions when Codex asks. Check a harmless matching event before relying
   on a hook; a JSON parse or offline test is not runtime activation evidence.

Copying `*.py` files alone does not activate anything. The registration file is
what tells Codex which event should run which script.

## Included Hooks

| Hook | Event | Matcher | Purpose |
|---|---|---|---|
| `wait_agent_timeout.py` | `PreToolUse` | `multi_agent_v1__wait_agent` | Raise omitted or short waits to 3,600,000 ms without issuing another wait |
| `context_scenario_guard.py` | `PreToolUse` | `apply_patch` | Detect hot context targets mechanically and provide a placement self-check |
| `spawn-resource-gate.py` | `PreToolUse` | Codex spawn and task creation | Block creation without explicit model resources or a resource-bearing fixed profile |
| `worktree-advisory.py` | `SessionStart` | `startup|resume` | Show shared-checkout Git state with Codex-native ownership guidance |

The context scenario hook detects patch and move headers for `AGENTS.md`,
`SKILL.md`, `MEMORY.md`, `hooks.json`, and context-contract files under rules,
agents, hooks, skills, or handoffs paths. When it finds one, it gives a
post-edit self-check: verify the reader and trigger,
choose the minimum global/project/subtree scope, check the existing SSOT and
duplicates, and name the actual consumer/load path. Only when semantic placement
remains ambiguous should the operator run `context-novelist` before the next edit.
The hook performs no automatic LLM invocation and does not replace Methodos
planning, user approval, or risk review. Registration still requires a manual
review of the copied configuration before activation.

The spawn resource gate checks only `multi_agent_v1__spawn_agent` and
`codex_app__create_thread`. A subagent call must provide `model` and
`reasoning_effort`, unless its named fixed profile declares `model` and
`model_reasoning_effort`. A new task call must provide `model` and `thinking`.
The gate does not choose a model or duplicate the routing contract; it only
fails closed when the call reaches the creation boundary without those values.

## Explicit worktree retirement CLI

`../common/worktree-cleanup.py` follows the current
[worktree rules](../../contract/codex/rules/worktree.md). It is not a
`SessionStart` hook and is omitted from `hooks.example.json`. If you adopted an
older example, remove its startup/resume cleanup registration; invoking the
current script without an explicit action returns a usage error.

For optional CLI use, follow the
[Codex installation guide](../../contract/codex/START-HERE.md). The tool accepts
`--enqueue PATH --disposition ...`, `--dequeue PATH`, or `--reap`. Reaping is
explicit and must run outside the retired worktree after integration or
preservation, writer shutdown, and cleanup authorization are confirmed.

The queue binds worktree identity, HEAD, content, and a lease marker. A queued
worktree must not be reused until dequeued. `preserved` additionally snapshots
the index and ignored files; the caller must first copy and compare all needed
content outside the worktree. Queue registration does not perform that backup.
A changed lease remains pending, and an invocation from inside a queued
worktree cancels its retirement. No deletion should be retried through another
tool after a lock or permission rejection.

## Optional Windows Desktop MCP Reaper

Codex Desktop can retain one `node_repl.exe` process per resumed thread. For a
Windows user who does not run Browser, Chrome, or Computer Use concurrently,
`reap-stale-node-repl.ps1` provides an opt-in process cap. It only considers
`node_repl.exe` processes owned directly by a live Codex `app-server` and keeps
the newest instance by default.

Preview without stopping anything:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
  "C:\path\to\methodos\hooks\codex\reap-stale-node-repl.ps1" -WhatIf
```

Run once:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
  "C:\path\to\methodos\hooks\codex\reap-stale-node-repl.ps1" -MaxNodeRepl 1
```

To cap the processes periodically, register the same command with Windows Task
Scheduler. Keep registration explicit: Methodos does not install or enable this
maintenance task automatically. Stopping a process can disconnect Browser or
Chrome tools in an older thread; reopen that thread before using those tools.
