param(
    [Parameter(Mandatory = $true)]
    [string]$AutomationId,

    [Parameter(Mandatory = $true)]
    [string]$ConditionCommand,

    [int]$WakeDelaySeconds = 60,
    [int]$PollSeconds = 30,
    [int]$TimeoutSeconds = 1200,
    [string]$RruleHelper
)

$ErrorActionPreference = "Stop"
$script:Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = $script:Utf8NoBom
[Console]::OutputEncoding = $script:Utf8NoBom

if ($WakeDelaySeconds -lt 1) {
    throw "-WakeDelaySeconds must be 1 or greater."
}
if ($PollSeconds -lt 1) {
    throw "-PollSeconds must be 1 or greater."
}
if ([string]::IsNullOrWhiteSpace($RruleHelper)) {
    $RruleHelper = Join-Path $PSScriptRoot "codex-heartbeat-rrule.ps1"
}
if (-not (Test-Path -LiteralPath $RruleHelper)) {
    throw "Missing RRULE helper: $RruleHelper"
}

function Limit-Text([object[]]$Lines) {
    $text = ($Lines | ForEach-Object { [string]$_ }) -join "`n"
    if ($text.Length -le 4000) {
        return $text
    }
    return $text.Substring($text.Length - 4000)
}

$startedAt = Get-Date
$deadline = $null
if ($TimeoutSeconds -gt 0) {
    $deadline = $startedAt.AddSeconds($TimeoutSeconds)
}
$attempts = 0
$lastExitCode = $null
$lastOutput = ""

while ($true) {
    $attempts += 1
    $raw = & powershell -NoProfile -ExecutionPolicy Bypass -Command $ConditionCommand 2>&1
    $lastExitCode = $LASTEXITCODE
    if ($null -eq $lastExitCode) {
        $lastExitCode = 0
    }
    $lastOutput = Limit-Text $raw

    if ($lastExitCode -eq 0) {
        $applyRaw = & powershell -NoProfile -ExecutionPolicy Bypass -File $RruleHelper -AutomationId $AutomationId -DelaySeconds $WakeDelaySeconds -Apply 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw (($applyRaw | ForEach-Object { [string]$_ }) -join "`n")
        }
        $apply = ($applyRaw | ForEach-Object { [string]$_ }) -join "`n" | ConvertFrom-Json
        [pscustomobject]@{
            ok = $true
            triggered = $true
            automationId = $AutomationId
            attempts = $attempts
            conditionExitCode = $lastExitCode
            conditionOutput = $lastOutput
            wakeDelaySeconds = $WakeDelaySeconds
            targetLocal = $apply.targetLocal
            rawDtstart = $apply.rawDtstart
            rrule = $apply.rrule
            toml = $apply.toml
        } | ConvertTo-Json -Depth 5
        exit 0
    }

    if ($null -ne $deadline -and (Get-Date) -ge $deadline) {
        [pscustomobject]@{
            ok = $true
            triggered = $false
            automationId = $AutomationId
            attempts = $attempts
            conditionExitCode = $lastExitCode
            conditionOutput = $lastOutput
            timedOut = $true
        } | ConvertTo-Json -Depth 5
        exit 0
    }

    Start-Sleep -Seconds $PollSeconds
}
