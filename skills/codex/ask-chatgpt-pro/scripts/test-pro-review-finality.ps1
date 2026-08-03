$ErrorActionPreference = "Stop"

$script = Join-Path $PSScriptRoot "pro-review.ps1"
$mockDir = Join-Path $env:TEMP ("pro-review-finality-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $mockDir | Out-Null
$mock = Join-Path $mockDir "agbrowse.cmd"

@'
@echo off
echo {"session":{"sessionId":"test-session","status":"%MOCK_STATUS%","completedAt":%MOCK_COMPLETED_AT%,"answer":"%MOCK_ANSWER%"}}
'@ | Set-Content -LiteralPath $mock -Encoding ASCII

$originalPath = $env:PATH
try {
    $env:PATH = "$mockDir;$originalPath"

    $env:MOCK_STATUS = "streaming"
    $env:MOCK_COMPLETED_AT = "null"
    $env:MOCK_ANSWER = "short preamble"
    $temporary = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -Action collect -SessionId test-session -MinAgeMinutes 0 -MinAnswerChars 20 -StabilitySeconds 1 | ConvertFrom-Json
    if ($temporary.status -ne "preamble_or_incomplete" -or $null -ne $temporary.answerText) {
        throw "Streaming placeholder was treated as final: $($temporary | ConvertTo-Json -Depth 4)"
    }

    $env:MOCK_STATUS = "complete"
    $env:MOCK_COMPLETED_AT = '"2026-07-10T14:00:00Z"'
    $env:MOCK_ANSWER = "substantive final answer with enough content"
    $final = & powershell -NoProfile -ExecutionPolicy Bypass -File $script -Action collect -SessionId test-session -MinAgeMinutes 0 -MinAnswerChars 20 -StabilitySeconds 1 | ConvertFrom-Json
    if ($final.status -ne "complete" -or -not $final.stable -or -not $final.substantive -or [string]::IsNullOrWhiteSpace($final.answerText)) {
        throw "Complete stable response was not collected: $($final | ConvertTo-Json -Depth 4)"
    }
    if ($final.sessionId -ne "test-session" -or [string]::IsNullOrWhiteSpace($final.answerHashSha256)) {
        throw "Final result lost session identity or stable hash"
    }
} finally {
    $env:PATH = $originalPath
    Remove-Item -LiteralPath $mockDir -Recurse -Force -ErrorAction SilentlyContinue
}

[pscustomobject]@{
    status = "passed"
    streamingPlaceholderRejected = $true
    completedStableAnswerAccepted = $true
} | ConvertTo-Json -Depth 3
