# Codex context lifetimes

This reference is lazy: read it only for a Codex runtime or a task about Codex
session, turn, skill, hook, compaction, or memory loading.

- `AGENTS.md` instruction discovery is assembled once per run; in the TUI this
  normally means once per launched session. The chain is layered from global to
  project/current-directory guidance, with closer files later in the prompt.
- A skill initially exposes its name and description metadata. Codex loads the
  full `SKILL.md` when the request matches the skill or the user invokes it.
- `SessionStart` and `SubagentStart` are start events. `UserPromptSubmit` and
  tool/compaction lifecycle hooks such as `PreToolUse`, `PostToolUse`,
  `PreCompact`, and `PostCompact` are turn events.
- After compaction, a `SessionStart` hook matching `source: "compact"` can add
  context before the next model request, including the immediate continuation
  of an automatic mid-turn compaction.
- Memory is a recall layer, not the sole source for required guidance. Keep
  required rules in `AGENTS.md` or another explicit persistent surface.

Authoritative Codex manual source pages:

- [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md.md)
- [Skills](https://developers.openai.com/plugins/concepts/skills.md)
- [Hooks](https://learn.chatgpt.com/docs/hooks.md)
- [Memories](https://learn.chatgpt.com/docs/customization/memories.md)
- [Codex manual](https://developers.openai.com/codex/codex-manual.md)
