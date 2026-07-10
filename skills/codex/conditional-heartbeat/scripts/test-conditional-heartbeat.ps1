$ErrorActionPreference = "Stop"

$skillRoot = Split-Path -Parent $PSScriptRoot
$helper = Join-Path $PSScriptRoot "codex-heartbeat-rrule.ps1"
$watcher = Join-Path $PSScriptRoot "condition-heartbeat-watch.ps1"
$askRoot = Join-Path (Split-Path -Parent $skillRoot) "ask-chatgpt-pro"
$askScript = Join-Path $askRoot "scripts\pro-review.ps1"
$automationRoot = Join-Path $env:USERPROFILE ".codex\automations"
$id = "conditional-heartbeat-test-" + [guid]::NewGuid().ToString("N")
$automationDir = Join-Path $automationRoot $id
$toml = Join-Path $automationDir "automation.toml"

foreach ($delay in @(30, 45, 60)) {
    $raw = & powershell -NoProfile -ExecutionPolicy Bypass -File $helper -DelayMinutes $delay
    if ($LASTEXITCODE -ne 0) { throw "RRULE generation failed delay=$delay output=$raw" }
    $result = ($raw | Out-String) | ConvertFrom-Json
    if ($result.delaySeconds -ne ($delay * 60)) { throw "Unexpected delaySeconds delay=$delay" }
    if ($result.rrule -notmatch '^DTSTART:\d{8}T\d{6}Z\nRRULE:FREQ=MINUTELY;COUNT=1$') { throw "Unexpected RRULE shape" }
}

New-Item -ItemType Directory -Path $automationDir | Out-Null
@"
version = 1
id = "$id"
kind = "heartbeat"
name = "$id"
prompt = "disposable conditional heartbeat test"
status = "PAUSED"
rrule = "RRULE:FREQ=HOURLY;BYMINUTE=0;BYSECOND=0"
target_thread_id = "disposable"
created_at = 1
updated_at = 1
"@ | Set-Content -LiteralPath $toml -Encoding UTF8

try {
    $apply = & powershell -NoProfile -ExecutionPolicy Bypass -File $helper -AutomationId $id -DelaySeconds 75 -Apply | ConvertFrom-Json
    if (-not $apply.applied -or $apply.toml -ne $toml) { throw "Direct TOML apply did not report the disposable automation" }
    $after = Get-Content -Raw -LiteralPath $toml
    if ($after -notmatch 'status = "ACTIVE"' -or $after -notmatch 'rrule = "DTSTART:\d{8}T\d{6}Z\\nRRULE:FREQ=MINUTELY;COUNT=1"') {
        throw "Direct TOML apply did not activate the one-shot schedule"
    }

    $watch = & powershell -NoProfile -ExecutionPolicy Bypass -File $watcher -AutomationId $id -ConditionCommand 'exit 0' -WakeDelaySeconds 75 -PollSeconds 1 -TimeoutSeconds 30 -RruleHelper $helper | ConvertFrom-Json
    if (-not $watch.triggered -or $watch.conditionExitCode -ne 0) { throw "Condition watcher did not accelerate on a true condition" }

    $watchText = Get-Content -Raw -LiteralPath $toml
    if ($watchText -notmatch 'status = "ACTIVE"') { throw "Condition watcher did not preserve active heartbeat status" }
} finally {
    Remove-Item -LiteralPath $automationDir -Recurse -Force -ErrorAction SilentlyContinue
}

$askText = Get-Content -Raw -LiteralPath $askScript
foreach ($required in @('watch-accelerate', 'provider_complete_and_completedAt_and_min_chars_and_hash_stable', 'sessionId')) {
    if ($askText -notmatch [regex]::Escape($required)) { throw "ask-chatgpt-pro lost required acceleration contract: $required" }
}

[pscustomobject]@{
    status = "passed"
    directTomlApply = $true
    conditionAcceleration = $true
    providerFinalityContractPresent = $true
} | ConvertTo-Json -Depth 3
