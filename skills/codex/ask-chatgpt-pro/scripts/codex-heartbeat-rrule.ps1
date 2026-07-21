param(
    [int]$DelaySeconds,
    [int]$DelayMinutes,
    [string]$AutomationId,
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$helper = Join-Path $env:USERPROFILE ".codex\rules\scripts\codex-heartbeat-rrule.ps1"
if (-not (Test-Path -LiteralPath $helper)) {
    throw "Missing global RRULE helper: $helper"
}

$invokeArgs = @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $helper,
    "-DelaySeconds",
    $DelaySeconds,
    "-DelayMinutes",
    $DelayMinutes
)
if (-not [string]::IsNullOrWhiteSpace($AutomationId)) {
    $invokeArgs += @("-AutomationId", $AutomationId)
}
if ($Apply) {
    $invokeArgs += "-Apply"
}

& powershell @invokeArgs
exit $LASTEXITCODE
