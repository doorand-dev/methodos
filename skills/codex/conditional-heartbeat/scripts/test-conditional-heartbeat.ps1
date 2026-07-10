$ErrorActionPreference = "Stop"

$skillRoot = Split-Path -Parent $PSScriptRoot
$helper = Join-Path $PSScriptRoot "codex-heartbeat-rrule.ps1"
$watcher = Join-Path $PSScriptRoot "condition-heartbeat-watch.ps1"
$skillPath = Join-Path $skillRoot "SKILL.md"
$agentPath = Join-Path $skillRoot "agents\openai.yaml"
$askRoot = Join-Path (Split-Path -Parent $skillRoot) "ask-chatgpt-pro"
$askSkillPath = Join-Path $askRoot "SKILL.md"
$askScript = Join-Path $askRoot "scripts\pro-review.ps1"

foreach ($delay in @(30, 45, 60)) {
    $raw = & powershell -NoProfile -ExecutionPolicy Bypass -File $helper -DelayMinutes $delay
    if ($LASTEXITCODE -ne 0) { throw "RRULE generation failed delay=$delay output=$raw" }
    $result = ($raw | Out-String) | ConvertFrom-Json
    if ($result.delaySeconds -ne ($delay * 60)) { throw "Unexpected delaySeconds delay=$delay" }
    if ($result.applied -or $null -ne $result.toml) { throw "RRULE helper must be generation-only" }
}

$savedErrorAction = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$applyOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $helper -DelayMinutes 45 -AutomationId "disposable-test" -Apply 2>&1
$applyExitCode = $LASTEXITCODE
$ErrorActionPreference = $savedErrorAction
if ($applyExitCode -eq 0 -or ($applyOutput | Out-String) -notmatch '-Apply is unsupported') {
    throw "-Apply must direct callers to automation_update"
}

if (Test-Path -LiteralPath $watcher) { throw "Generic condition watcher must not mutate automations: $watcher" }

$helperText = Get-Content -Raw -LiteralPath $helper
if ($helperText -match 'WriteAllText|\.codex\\automations') { throw "RRULE helper still mutates automation storage" }

$askScriptText = Get-Content -Raw -LiteralPath $askScript
if ($askScriptText -match 'automation\.toml|\.codex\\automations') { throw "ask-chatgpt-pro still mutates automation storage" }

$skillText = Get-Content -Raw -LiteralPath $skillPath
if ($skillText -match 'Fallback Then Accelerate|condition-heartbeat-watch|-Apply') { throw "Generic skill still advertises external acceleration" }

$agentText = Get-Content -Raw -LiteralPath $agentPath
if ($agentText -match 'acceleration') { throw "Agent metadata still advertises acceleration" }

$askSkillText = Get-Content -Raw -LiteralPath $askSkillPath
if ($askSkillText -match 'Action watch-accelerate|direct `%USERPROFILE%\\.codex\\automations|condition acceleration') {
    throw "ask-chatgpt-pro still advertises unsupported automation acceleration"
}

$ErrorActionPreference = "Continue"
$watchOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $askScript -Action watch-accelerate -SessionId "disposable-test" -AutomationId "disposable-test" 2>&1
$watchExitCode = $LASTEXITCODE
$ErrorActionPreference = $savedErrorAction
if ($watchExitCode -eq 0 -or ($watchOutput | Out-String) -notmatch 'watch-accelerate is unsupported') {
    throw "ask-chatgpt-pro watch-accelerate was not rejected"
}

[pscustomobject]@{
    status = "passed"
    sourceUsesAutomationUpdateOnly = $true
    unsupportedAccelerationRejected = $true
} | ConvertTo-Json -Depth 3
