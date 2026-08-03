---
name: ask-chatgpt-pro
description: "Ask a logged-in ChatGPT Pro session for a second opinion or review through exactly one selected transport: the in-app browser, AG Browse, or OpenCLI."
---

# Ask ChatGPT Pro

Use this skill only when the user asks for a ChatGPT Pro second opinion, review,
or delegated long-form result.

Before sending anything:

1. Read [references/common.md](references/common.md).
2. Select exactly one transport. An explicit user choice wins. When the user did
   not choose, use `agbrowse`: it provides session-bound asynchronous send and
   collection for text and file requests. Request characteristics do not
   override this default. Do not silently fall back.
3. Read exactly one adapter:
   - `in-app-browser` -> [references/adapters/in-app-browser.md](references/adapters/in-app-browser.md)
   - `agbrowse` -> [references/adapters/agbrowse.md](references/adapters/agbrowse.md)
   - `opencli` -> [references/adapters/opencli.md](references/adapters/opencli.md)

If the selected adapter is unavailable, loses its target, or lacks a required
capability, stop with that limitation and ask whether to use another named
transport. Never continue the same request through a second adapter on your own.
