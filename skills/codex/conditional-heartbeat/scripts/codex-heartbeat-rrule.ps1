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

if ($Apply) {
    throw "-Apply is unsupported. Pass the generated rrule to automation_update instead."
}

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
[pscustomobject]@{
    ok = $true
    automationId = $(if ([string]::IsNullOrWhiteSpace($AutomationId)) { $null } else { $AutomationId })
    delaySeconds = $totalSeconds
    targetLocal = $targetLocal.ToString("yyyy-MM-dd HH:mm:ss K")
    rawDtstart = "DTSTART:$stampUtc"
    rrule = $rrule
    toml = $null
    applied = $false
    updatedAt = [DateTimeOffset]::Now.ToUnixTimeMilliseconds()
} | ConvertTo-Json -Depth 4
