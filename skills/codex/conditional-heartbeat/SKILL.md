---
name: conditional-heartbeat
description: Create one-shot Codex Desktop heartbeat wakeups with a broad fallback and optional condition-based acceleration. Use when Codex should wake a thread later, set a single follow-up for a specific delay, attach a mechanical readiness command that accelerates an existing heartbeat, or avoid hand-written RRULE/timezone scheduling for heartbeat automations. This skill defines heartbeat scheduling mechanics only; project-specific orchestration policy and thread state judgment stay in the caller's prompt or project docs.
---

# Conditional Heartbeat

Use this skill for Codex Desktop heartbeat scheduling that must fire once.

## Boundary

- This skill only defines how to create, update, accelerate, verify, and delete one-shot Codex Desktop heartbeat automations.
- Do not use this skill as the source of project orchestration policy, thread state judgment, Methodos DONE criteria, blocked handling, commit decisions, merge decisions, or next-action policy.
- Put project-specific status categories, wake checklists, and decision rules in the heartbeat prompt or project docs.
- **Provider ownership exclusion**: do not start this generic watcher for an `automationId` owned by `ask-chatgpt-pro`; that skill runs its own provider-finality watcher. Different sessions have different ids and do not conflict.
- Use `ConditionCommand` only for cheap, read-only, mechanically observable readiness checks such as file existence, process completion, artifact creation, or a read-only git/worktree signal.
- Do not encode human or project judgment into `ConditionCommand`. If readiness requires reading thread transcripts or making a project judgment, set a fallback heartbeat and perform that judgment in the wakeup turn.

## Rules

- Use the `automation_update` tool for initial heartbeat create/update.
- Use `kind = "heartbeat"` and `destination = "thread"` for thread wakeups.
- Prefer updating an existing relevant heartbeat over creating a duplicate.
- Generate every one-shot RRULE with `scripts/codex-heartbeat-rrule.ps1`.
- Do not write RRULE strings from natural-language time.
- Do not use bare relative RRULE strings such as `RRULE:FREQ=MINUTELY;INTERVAL=20;COUNT=1`.
- Do not use local wall-time `DTSTART`.
- Do not use `DTSTART;TZID=...`.
- Pass the helper output `rrule` to `automation_update` unchanged.
- Put the automation id in the heartbeat prompt.
- Make the first wakeup step delete the same automation id.
- Judge success by the wakeup turn and deleted automation, not by UI display text alone.

## One-Shot Wakeup

Resolve the helper:

```powershell
$skillDir = "<installed conditional-heartbeat skill folder>"
$rruleHelper = Join-Path $skillDir "scripts\codex-heartbeat-rrule.ps1"
```

Generate a one-shot RRULE:

```powershell
$wake = powershell -NoProfile -ExecutionPolicy Bypass -File $rruleHelper -DelaySeconds 60 | ConvertFrom-Json
$wake.rrule
```

Use `$wake.rrule` unchanged in `automation_update`.

Use this heartbeat prompt shape:

```text
One-shot heartbeat wakeup.

Automation id: use the automation id from this heartbeat envelope.

Do this first:
1. Delete this heartbeat automation.
2. Continue the requested task.
```

## Fallback Then Accelerate

Create or update the fallback heartbeat first:

```powershell
$fallback = powershell -NoProfile -ExecutionPolicy Bypass -File $rruleHelper -DelayMinutes 20 | ConvertFrom-Json
$fallback.rrule
```

Start a watcher only after the heartbeat exists:

```powershell
$skillDir = "<installed conditional-heartbeat skill folder>"
$watcher = Join-Path $skillDir "scripts\condition-heartbeat-watch.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File $watcher `
  -AutomationId "<automationId>" `
  -ConditionCommand "<command that exits 0 only when ready>" `
  -WakeDelaySeconds 60 `
  -PollSeconds 30 `
  -TimeoutSeconds 1200
```

The watcher polls `ConditionCommand`. When the command exits `0`, it applies a new one-shot RRULE to the same automation id with `codex-heartbeat-rrule.ps1 -Apply`.

Write `ConditionCommand` so it exits `0` only when ready and exits nonzero otherwise:

```powershell
-ConditionCommand "if (Test-Path -LiteralPath 'C:\tmp\done.json') { exit 0 } else { exit 1 }"
```

Boolean readiness commands are allowed:

```powershell
-ConditionCommand "Test-Path -LiteralPath 'C:\tmp\done.json'"
```

## Apply Existing Automation

Move an existing heartbeat to a new one-shot time:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $rruleHelper `
  -AutomationId "<automationId>" `
  -DelaySeconds 60 `
  -Apply
```

## Verification

- View the automation with `automation_update`.
- Inspect `%USERPROFILE%\.codex\automations\<automationId>\automation.toml` only when direct file verification is needed.
- Confirm `target_thread_id` is the intended thread.
- Confirm the heartbeat fires in the target thread.
- Confirm the automation is deleted after wakeup.
