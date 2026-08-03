# In-app browser adapter

Use this adapter when the user explicitly chooses the in-app browser or when the
router applies its default. It is preferred for long generation, visual work,
ordinary chat attachments, and downloadable results that the user should be
able to revisit in the visible ChatGPT conversation.

Claim the exact existing ChatGPT tab and conversation named or established by
the current request. If more than one visible tab or conversation is plausible,
ask which one; do not guess. Use Browser Use DOM reading, input, and click for
normal control. Do not use Computer Use coordinate clicks merely to operate the
chat UI.

Start a new conversation unless continuation of a specific existing `/c/...`
conversation was requested or already established. Confirm Pro in the visible
model control, send once, and keep observing that same tab and conversation.
While the page is generating, do not press `지금 답변 받기` or `답변 중지`.

For an attachment, verify the visible attachment chips before sending. For a
download, use the provider's completed result and verify the local file exists.
For an explicitly requested delayed handoff, a heartbeat may revisit this same
conversation; it must not create a replacement conversation or switch
transport. Otherwise do not create monitoring automation by default.

Completion requires the final assistant turn in the DOM, not merely changing
button text or partial streaming. Return the visible `/c/...` URL with the final
answer and any verified download.
