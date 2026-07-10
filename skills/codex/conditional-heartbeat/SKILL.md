---
name: conditional-heartbeat
description: Create one-shot Codex Desktop heartbeat wakeups with the public automation API. Use when Codex should wake a thread later or avoid hand-written schedule syntax. Provider-specific completion handling belongs to the owning skill; this skill does not run external condition watchers or mutate automation storage.
---

# Conditional Heartbeat

Use this skill for Codex Desktop heartbeat scheduling that must fire once.

## Boundary

- This skill only defines how to create, update, verify, and delete one-shot Codex Desktop heartbeat automations.
- Do not use this skill as the source of project orchestration policy, thread state judgment, Methodos DONE criteria, blocked handling, commit decisions, merge decisions, or next-action policy.
- Put project-specific status categories, wake checklists, and decision rules in the heartbeat prompt or project docs.
- Do not run external watchers that attempt to reschedule a heartbeat. If a provider-specific finality check is needed, its owning skill must retain the session identity and perform collection in the wakeup turn.

## Rules

- Use the `automation_update` tool for initial heartbeat create/update.
- Use `kind = "heartbeat"` and `destination = "thread"` for thread wakeups.
- Prefer updating an existing relevant heartbeat over creating a duplicate.
- Generate every one-shot RRULE with `scripts/codex-heartbeat-rrule.ps1` for inspection and future API compatibility.
- Do not write RRULE strings from natural-language time.
- Current blocker: `automation_update(mode=create)` rejects `DTSTART`, while `mode=suggested_create` only renders a card. Do not use direct storage mutation to bypass this.
- Until the public API accepts an exact future one-shot time or a relative delay, report scheduled heartbeat creation as blocked rather than claiming an automatic fallback exists.
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

`$wake.rrule` documents the intended UTC instant. If `automation_update` rejects it, stop and report the public scheduling blocker; do not replace it with direct TOML edits or a bare relative RRULE.

Use this heartbeat prompt shape:

```text
One-shot heartbeat wakeup.

Automation id: use the automation id from this heartbeat envelope.

Do this first:
1. Delete this heartbeat automation.
2. Continue the requested task.
```

## Verification

- View the automation with `automation_update`.
- Confirm `target_thread_id` is the intended thread.
- If the API accepts a schedule, confirm the heartbeat fires in the target thread and deletes itself after wakeup.
