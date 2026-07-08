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

function Invoke-ConditionCommand([string]$Command) {
    $runner = @"
`$ErrorActionPreference = "Stop"
try {
    `$global:LASTEXITCODE = `$null
    `$result = & ([scriptblock]::Create(@'
$Command
'@))
    `$nativeExitCode = `$global:LASTEXITCODE
    if (`$null -ne `$nativeExitCode) {
        exit ([int]`$nativeExitCode)
    }

    `$items = @(`$result | Where-Object { `$null -ne `$_ })
    if (`$items.Count -eq 1 -and `$items[0] -is [bool]) {
        if (`$items[0]) {
            exit 0
        }
        exit 1
    }

    if (`$items.Count -gt 0) {
        `$items | ForEach-Object { Write-Output `$_ }
    }
    exit 1
} catch {
    Write-Error `$_
    exit 1
}
"@
    $encoded = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($runner))
    $output = & powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand $encoded 2>&1
    [pscustomobject]@{
        exitCode = $LASTEXITCODE
        output = $output
    }
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
    $condition = Invoke-ConditionCommand $ConditionCommand
    $lastExitCode = $condition.exitCode
    $lastOutput = Limit-Text $condition.output

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
