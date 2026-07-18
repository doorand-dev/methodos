# Codex Hook Registration

Codex hook support is real. The Methodos hook scripts in this repository are
inactive only because this reference kit does not install or register policy for
you.

Use `hooks.example.json` as the registration shape. It is intentionally named
`.example.json` so cloning this repository does not activate hooks by surprise.

## Activate Manually

1. Copy `hooks.example.json` to one of Codex's hook config locations:
   - user-wide: `~/.codex/hooks.json`
   - project-local: `<target-repo>/.codex/hooks.json`
2. Replace every `/absolute/path/to/methodos` and
   `C:\absolute\path\to\methodos` placeholder with this checkout path.
3. Start a new Codex thread and review/trust the hook definitions when Codex
   asks.

Copying `*.py` files alone does not activate anything. The registration file is
what tells Codex which event should run which script.

## Included Hooks

| Hook | Event | Matcher | Purpose |
|---|---|---|---|
| `../common/context_surface_guard.py` | `PostToolUse` | `Edit|Write|MultiEdit` | Warn on suspicious hot-context edits and suggest `context-novelist` review |

The context-surface hook is a mechanical guard. It does not replace Methodos
planning, user approval, or risk review. Registration still requires a manual
review of the copied configuration before activation.
