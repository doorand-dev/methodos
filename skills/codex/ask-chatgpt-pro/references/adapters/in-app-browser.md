# In-app browser adapter

Use this adapter when the router selected `in-app-browser`. It is suited to
visual work, ordinary chat attachments, and downloadable results that the user
should be able to revisit in the visible ChatGPT conversation.

Claim the exact existing ChatGPT tab and conversation named or established by
the current request. If more than one visible tab or conversation is plausible,
ask which one; do not guess. Use Browser Use DOM reading, input, and click for
normal control. Do not use Computer Use coordinate clicks merely to operate the
chat UI.

Start a new conversation unless continuation of a specific existing `/c/...`
conversation was requested or already established. Confirm Pro in the visible
model control, send once, save the exact `/c/...` URL, schedule the common
heartbeat, and end the initiating turn. Each heartbeat revisits only that URL
and reads its DOM; it does not claim another visible ChatGPT tab.

For an attachment, verify the visible attachment chips before sending. For a
download, use the provider's completed result and verify the local file exists.
The heartbeat must not create a replacement conversation or switch transport.

Completion requires the final assistant turn in the DOM, not merely changing
button text or partial streaming. Return the visible `/c/...` URL with the final
answer and any verified download.
