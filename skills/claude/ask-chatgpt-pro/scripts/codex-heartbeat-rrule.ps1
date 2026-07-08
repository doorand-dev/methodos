param(
    [int]$DelaySeconds,
    [int]$DelayMinutes,
    [string]$AutomationId,
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$skillsRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$helper = Join-Path $skillsRoot "conditional-heartbeat\scripts\codex-heartbeat-rrule.ps1"
if (-not (Test-Path -LiteralPath $helper)) {
    throw "Missing sibling conditional-heartbeat RRULE helper: $helper"
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
