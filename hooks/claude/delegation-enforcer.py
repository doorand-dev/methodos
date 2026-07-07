#!/usr/bin/env python3
"""
delegation-enforcer.py -- PreToolUse hook for Anthropic Claude Code.

Guarantees every Agent call carries an explicit, correct `model` -- by
INJECTING it from agent md frontmatter when available, and BLOCKING the call
when it cannot be resolved. Hybrid of two earlier hooks (inject-on-omit +
block-on-omit) merged into one so a single canonical hook covers all agents.

WHY: Claude Code does NOT auto-apply an agent definition's `model:` frontmatter
(FACTS.md L5). Without enforcement, `model: opus` in agent md is decorative and
the subagent silently inherits the parent model -- so prose ("Sonnet으로 검증")
and the real execution model diverge.

Two failure surfaces, two responses:
  - Custom agent WITH `model:` frontmatter, caller omits model
      -> INJECT frontmatter model (zero ceremony; define once, applied always).
  - No resolvable model (built-in agent like general-purpose/Explore -- no md;
    or custom agent md without `model:`), caller omits model
      -> BLOCK (exit 2) so the caller must write model explicitly. Closes the
         hole the pure inject-on-omit hook left for built-in agents.

BEHAVIOR (in order):
  - tool_name != "Agent"                 -> no-op (exit 0)
  - subagent_type absent                 -> no-op (built-in helper, inherit ok)
  - subagent_type starts with "codex"    -> no-op (wrapper model unrelated to
                                            the real exec model, e.g. gpt-5.x)
  - model already in tool_input          -> no-op (preserve caller's choice)
  - frontmatter `model:` resolved        -> INJECT via updatedInput (allow)
  - model unresolvable                   -> BLOCK (exit 2 + stderr guidance)

INPUT (stdin JSON, per Anthropic hooks spec):
  {"tool_name": "Agent",
   "tool_input": {"subagent_type": "<name>", "model": "<optional>", ...}, ...}

OUTPUT (stdout JSON when injecting):
  {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                          "permissionDecision": "allow",
                          "updatedInput": {<tool_input with model added>}}}
"""

import io
import json
import re
import sys
from pathlib import Path

if sys.stderr and hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

AGENTS_DIR = Path.home() / ".claude" / "agents"


def extract_model(agent_name: str) -> str | None:
    """Read ~/.claude/agents/<name>.md frontmatter, return `model:` value."""
    # Plugin-namespaced names (contain ":") have no local md here -> None,
    # which routes to BLOCK (explicit model required), matching all other agents.
    if ":" in agent_name:
        return None
    agent_path = AGENTS_DIR / f"{agent_name}.md"
    if not agent_path.is_file():
        return None
    try:
        text = agent_path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.lstrip().startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    frontmatter = parts[1]
    match = re.search(r"^model:\s*(\S+)\s*$", frontmatter, re.MULTILINE)
    return match.group(1).strip() if match else None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, EOFError):
        sys.exit(0)

    if payload.get("tool_name") != "Agent":
        sys.exit(0)

    tool_input = payload.get("tool_input") or {}
    subagent_type = (tool_input.get("subagent_type") or "").strip()
    # No subagent_type -> generic helper (built-in skills etc); inherit allowed.
    if not subagent_type:
        sys.exit(0)

    # Codex family exempt: wrapper `model` is unrelated to the real exec model
    # (codex config's gpt-5.x) -> enforcing it is meaningless. (2026-05-29)
    if subagent_type.lower().startswith("codex"):
        sys.exit(0)

    # Caller already specified a model -> preserve their explicit choice.
    if (tool_input.get("model") or "").strip():
        sys.exit(0)

    model = extract_model(subagent_type)
    if model:
        updated_input = dict(tool_input)
        updated_input["model"] = model
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "allow",
                        "updatedInput": updated_input,
                    }
                }
            )
        )
        sys.exit(0)

    # Unresolvable model -> BLOCK. Caller (or agent frontmatter) must specify.
    print(
        f"[delegation-enforcer] Agent('{subagent_type}') 호출에 model 인자 필수.\n"
        "  부모 세션 모델 상속 = 본문 표기와 실제 실행 모델 어긋남 위험.\n"
        f"  '{subagent_type}'.md frontmatter에 `model:`이 있으면 자동 주입되지만,\n"
        "  빌트인 agent(general-purpose, Explore 등)나 frontmatter 미지정 시엔 명시 필요.\n"
        "  예: Agent(subagent_type='general-purpose', model='sonnet', ...)\n"
        "  (Codex 계열은 면제 — 래퍼 model이 실제 실행 모델과 무관.)",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
