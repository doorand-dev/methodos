# Common ChatGPT Pro contract

Apply this contract with whichever single transport the router selected.

Put this instruction in the trusted instruction or system block when the
transport supports one; otherwise include it at the start of the request:

> 설계·구현 방안을 제안할 때 과도한 증명·감사·대기업 수준의 강박적
> 검증·증분 검증·메타데이터/증거 체계를 기본으로 추가하지 마라. 실제 결과를
> 바꾸거나 재실행으로 반증 가능한 신호와 필요한 사용자 승인만 남겨라. 구체적
> 위험이나 사용자 요청이 없는 검증 절차로 설계 범위를 확장하지 마라.

Before any external upload, obtain the user's approval for the exact files.
Never upload secrets, credentials, `.env`, or other sensitive paths. After
sending, inspect the actual provider turn or attachment surface and confirm the
attachment names and count; command intent alone is not proof of attachment.

Treat `generating`, streaming text, an injected prompt, or a successful send as
nonterminal. Do not interrupt generation or collect the answer until the
selected adapter's completion signal is final. A timeout is not completion;
preserve the selected conversation/target for that adapter's recovery path.

Run every transport asynchronously. The initiating turn confirms one successful
send and its exact conversation/session/target, schedules an accelerated
heartbeat when available or a per-request five-minute heartbeat, then ends
without waiting for the answer. Each heartbeat checks only that saved identity.
If the result is still generating, end the heartbeat turn and leave the next
heartbeat scheduled. On terminal completion or terminal failure, remove the
heartbeat automation in that terminal heartbeat turn before returning the
result. Never press or invoke `지금 답변 받기`, another
early-answer action, or `답변 중지` while generation continues.

Return the substantive answer, every requested downloaded file that actually
exists, and the actual `/c/...` conversation URL. State when no file was
produced or the URL is unavailable. Session IDs, target IDs, model labels,
transport metadata, and self-reported manifests are routing details, not
completion evidence.
