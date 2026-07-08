param(
    [int]$DelaySeconds,
    [int]$DelayMinutes,
    [string]$AutomationId,
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$script:Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = $script:Utf8NoBom
[Console]::OutputEncoding = $script:Utf8NoBom

if ($DelaySeconds -lt 0) {
    throw "-DelaySeconds must be zero or greater."
}
if ($DelayMinutes -lt 0) {
    throw "-DelayMinutes must be zero or greater."
}
if ($DelaySeconds -eq 0 -and $DelayMinutes -eq 0) {
    throw "Provide -DelaySeconds or -DelayMinutes."
}

$totalSeconds = $DelaySeconds + ($DelayMinutes * 60)
if ($totalSeconds -lt 1) {
    $totalSeconds = 1
}

$targetLocal = (Get-Date).AddSeconds($totalSeconds)
$stampUtc = $targetLocal.ToUniversalTime().ToString("yyyyMMddTHHmmss") + "Z"
$rrule = "DTSTART:$stampUtc`nRRULE:FREQ=MINUTELY;COUNT=1"
$epochMs = [DateTimeOffset]::Now.ToUnixTimeMilliseconds()
$toml = $null

if ($Apply) {
    if ([string]::IsNullOrWhiteSpace($AutomationId)) {
        throw "-AutomationId is required with -Apply."
    }
    $root = [System.IO.Path]::GetFullPath((Join-Path $env:USERPROFILE ".codex\automations"))
    $toml = [System.IO.Path]::GetFullPath((Join-Path $root (Join-Path $AutomationId "automation.toml")))
    if (-not $toml.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Unexpected automation path: $toml"
    }
    if (-not (Test-Path -LiteralPath $toml)) {
        throw "Missing automation.toml: $toml"
    }

    $content = [System.IO.File]::ReadAllText($toml, $script:Utf8NoBom)
    if ($content -notmatch '(?m)^rrule\s*=') {
        throw "automation.toml has no rrule line: $toml"
    }

    $newRruleLine = 'rrule = "' + $rrule.Replace("`n", "\n") + '"'
    $content = [regex]::Replace($content, '(?m)^rrule\s*=\s*"[^"]*"', $newRruleLine)
    if ($content -match '(?m)^status\s*=') {
        $content = [regex]::Replace($content, '(?m)^status\s*=\s*"[^"]*"', 'status = "ACTIVE"')
    } else {
        $content += "`nstatus = `"ACTIVE`""
    }
    if ($content -match '(?m)^updated_at\s*=') {
        $content = [regex]::Replace($content, '(?m)^updated_at\s*=\s*\d+', ('updated_at = ' + $epochMs))
    } else {
        $content += "`nupdated_at = $epochMs"
    }
    [System.IO.File]::WriteAllText($toml, $content, $script:Utf8NoBom)
}

[pscustomobject]@{
    ok = $true
    automationId = $(if ([string]::IsNullOrWhiteSpace($AutomationId)) { $null } else { $AutomationId })
    delaySeconds = $totalSeconds
    targetLocal = $targetLocal.ToString("yyyy-MM-dd HH:mm:ss K")
    rawDtstart = "DTSTART:$stampUtc"
    rrule = $rrule
    toml = $toml
    applied = [bool]$Apply
    updatedAt = $epochMs
} | ConvertTo-Json -Depth 4
