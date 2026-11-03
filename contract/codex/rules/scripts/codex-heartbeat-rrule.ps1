param(
    [int]$DelaySeconds,
    [int]$DelayMinutes,
    [string]$AutomationId,
    [switch]$Apply
)

# Public source. Deploy to ~/.codex/rules/scripts/codex-heartbeat-rrule.ps1.

$ErrorActionPreference = "Stop"

# Accept one literal Windows path component, never a path or device name.
if ($Apply -or -not [string]::IsNullOrEmpty($AutomationId)) {
    if ([string]::IsNullOrWhiteSpace($AutomationId) -or
        $AutomationId -match '[\\/:*?"<>|\x00-\x1f]' -or
        $AutomationId -in @('.', '..') -or
        $AutomationId -ne $AutomationId.Trim() -or $AutomationId.EndsWith('.') -or
        $AutomationId -match '^(CON|PRN|AUX|NUL|COM[0-9\u00b9\u00b2\u00b3]|LPT[0-9\u00b9\u00b2\u00b3])(?:\.|$)') {
        throw "-AutomationId must be a single safe path component."
    }
}

if ($Apply) {
    $root = [System.IO.Path]::GetFullPath((Join-Path $env:USERPROFILE ".codex\automations"))
    $automationDir = [System.IO.Path]::GetFullPath((Join-Path $root $AutomationId))
    $rootBoundary = $root.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    $toml = [System.IO.Path]::GetFullPath((Join-Path $automationDir "automation.toml"))
    if (-not $automationDir.StartsWith($rootBoundary, [System.StringComparison]::OrdinalIgnoreCase) -or
        [System.IO.Path]::GetDirectoryName($automationDir) -ne $root) {
        throw "Unexpected automation path: $toml"
    }
    # Check the file and every ancestor: normalization alone cannot detect junctions/symlinks.
    $checkPath = $toml
    while ($checkPath) {
        $item = Get-Item -LiteralPath $checkPath -Force -ErrorAction Stop
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -or
            $item.LinkType -eq 'HardLink') {
            throw "Linked automation path is not allowed: $checkPath"
        }
        $checkPath = [System.IO.Path]::GetDirectoryName($checkPath)
    }
}
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
if ($totalSeconds -gt 86340) {
    throw "One-shot grid rule cannot express delays over 23h59m. Use a shorter delay and re-arm on wake."
}

# Codex Desktop automation_update rejects DTSTART and bare relative COUNT=1 rules.
# Use a whole-minute grid rule: first whole minute at or after now+delay.
# <=59min uses FREQ=HOURLY;BYMINUTE. Longer delays pin the hour with FREQ=DAILY;BYHOUR;BYMINUTE.
$nowLocal = Get-Date
$targetLocal = $nowLocal.AddSeconds($totalSeconds)
if ($targetLocal.Second -gt 0 -or $targetLocal.Millisecond -gt 0) {
    $targetLocal = $targetLocal.AddSeconds(60 - $targetLocal.Second).AddMilliseconds(-$targetLocal.Millisecond)
}
$byMinute = $targetLocal.Minute
$byHour = $targetLocal.Hour
if (($targetLocal - $nowLocal).TotalSeconds -lt 3600) {
    $rrule = "RRULE:FREQ=HOURLY;BYMINUTE=$byMinute;BYSECOND=0;COUNT=1"
} else {
    $rrule = "RRULE:FREQ=DAILY;BYHOUR=$byHour;BYMINUTE=$byMinute;BYSECOND=0;COUNT=1"
}
$epochMs = [DateTimeOffset]::Now.ToUnixTimeMilliseconds()
if (-not $Apply) { $toml = $null }

if ($Apply) {
    $content = [System.IO.File]::ReadAllText($toml, $script:Utf8NoBom)
    if ($content -notmatch '(?m)^rrule\s*=') {
        throw "automation.toml has no rrule line: $toml"
    }

    $newRruleLine = 'rrule = "' + $rrule + '"'
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
    byMinute = $byMinute
    byHour = $byHour
    rawDtstart = $null
    rrule = $rrule
    toml = $toml
    applied = [bool]$Apply
    updatedAt = $epochMs
} | ConvertTo-Json -Depth 4
