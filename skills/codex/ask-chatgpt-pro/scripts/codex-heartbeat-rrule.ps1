param(
    [int]$DelaySeconds,
    [int]$DelayMinutes,
    [string]$AutomationId,
    [switch]$Apply
)

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
