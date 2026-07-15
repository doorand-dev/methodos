$ErrorActionPreference = "Stop"

$script = Join-Path $PSScriptRoot "pro-review.ps1"
$fixturePath = Join-Path $PSScriptRoot "fixtures\send-late-url-22-to-20.json"
$fixture = Get-Content -Raw -LiteralPath $fixturePath | ConvertFrom-Json
$mockDir = Join-Path $env:TEMP ("pro-review-send-integrity-" + [guid]::NewGuid().ToString("N"))
$inputDir = Join-Path $mockDir "repo"
$statePath = Join-Path $mockDir "state.json"
$reattachedPath = Join-Path $mockDir "reattached.txt"
New-Item -ItemType Directory -Path $inputDir | Out-Null

$names = 1..20 | ForEach-Object { "context-{0:d2}.txt" -f $_ }
$names += @($fixture.missingNames)
$files = foreach ($name in $names) {
    $path = Join-Path $inputDir $name
    Set-Content -LiteralPath $path -Value ("fixture content for " + $name) -Encoding UTF8
    $path
}

$mockScript = Join-Path $mockDir "mock-agbrowse.ps1"
$mockCommand = Join-Path $mockDir "agbrowse.cmd"
@'
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$CliArgs)
$fixture = Get-Content -Raw -LiteralPath $env:MOCK_FIXTURE | ConvertFrom-Json

function Write-MockJson($value) {
    $value | ConvertTo-Json -Depth 12 -Compress
}

$joined = $CliArgs -join " "
if ($joined -match '^web-ai send ') {
    $paths = @()
    for ($i = 0; $i -lt $CliArgs.Count; $i++) {
        if ($CliArgs[$i] -eq '--file' -and $i + 1 -lt $CliArgs.Count) {
            $paths += $CliArgs[$i + 1]
        }
    }
    $sentNames = @($paths | Select-Object -First ([int]$fixture.providerAttachmentLimit) | ForEach-Object { Split-Path -Leaf $_ })
    [pscustomobject]@{ requestedPaths = $paths; sentNames = $sentNames } |
        ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $env:MOCK_STATE -Encoding UTF8
    $warnings = @()
    foreach ($path in @($paths | Select-Object -Skip ([int]$fixture.providerAttachmentLimit))) {
        $warnings += "sent attachment evidence unavailable after submit ($(Split-Path -Leaf $path)): sent turn has no attachment evidence"
    }
    Write-MockJson ([pscustomobject]@{
        ok = $true
        sessionId = $fixture.sessionId
        targetId = $fixture.targetId
        url = $fixture.rootUrl
        conversationUrl = $fixture.rootUrl
        modelSelection = "pro"
        effortSelection = "extended"
        warnings = $warnings
    })
    exit 0
}
if ($joined -match '^tabs --json$') {
    Write-MockJson @([pscustomobject]@{ targetId = $fixture.targetId; url = $fixture.conversationUrl })
    exit 0
}
if ($joined -match '^web-ai sessions reattach ') {
    Set-Content -LiteralPath $env:MOCK_REATTACHED -Value $fixture.conversationUrl -Encoding ASCII
    Write-MockJson ([pscustomobject]@{ ok = $true; session = [pscustomobject]@{ sessionId = $fixture.sessionId; targetId = $fixture.targetId; conversationUrl = $fixture.conversationUrl } })
    exit 0
}
if ($joined -match '^web-ai sessions show ') {
    $url = if (Test-Path -LiteralPath $env:MOCK_REATTACHED) { $fixture.conversationUrl } else { $fixture.rootUrl }
    Write-MockJson ([pscustomobject]@{ session = [pscustomobject]@{ sessionId = $fixture.sessionId; targetId = $fixture.targetId; conversationUrl = $url } })
    exit 0
}
if ($joined -match '^active-tab --json$') {
    Write-MockJson ([pscustomobject]@{ targetId = $fixture.targetId; url = $fixture.conversationUrl })
    exit 0
}
if ($CliArgs.Count -gt 0 -and $CliArgs[0] -eq 'evaluate') {
    $state = Get-Content -Raw -LiteralPath $env:MOCK_STATE | ConvertFrom-Json
    Write-MockJson ([pscustomobject]@{ turnFound = $true; attachmentNames = @($state.sentNames) })
    exit 0
}

Write-Error "Unexpected mock agbrowse args: $joined"
exit 9
'@ | Set-Content -LiteralPath $mockScript -Encoding UTF8

@'
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%MOCK_SCRIPT%" %*
'@ | Set-Content -LiteralPath $mockCommand -Encoding ASCII

$originalPath = $env:PATH
$originalLocation = Get-Location
try {
    $env:PATH = "$mockDir;$originalPath"
    $env:MOCK_SCRIPT = $mockScript
    $env:MOCK_FIXTURE = $fixturePath
    $env:MOCK_STATE = $statePath
    $env:MOCK_REATTACHED = $reattachedPath
    Set-Location -LiteralPath $inputDir

    $params = @{
        Action = "send"
        NoWatch = $true
        Prompt = "Review the supplied artifacts."
        SystemPrompt = "Act as the canonical reviewer and return only the required schema."
        File = $files
        ExecutedEvidenceFile = @($files[-2], $files[-1])
        RepoRoot = $inputDir
        UrlSettleSeconds = 1
        UrlSettlePollSeconds = 1
    }
    $result = & $script @params | ConvertFrom-Json

    if (-not $result.ok -or $result.status -ne "sent_for_heartbeat_collect") {
        throw "Integrity-gated send did not succeed: $($result | ConvertTo-Json -Depth 8)"
    }
    if ($result.conversationUrl -ne $fixture.conversationUrl -or $result.conversationUrlStatus -ne "settled_and_persisted") {
        throw "Late conversation URL was not persisted: $($result.urlProbe | ConvertTo-Json -Depth 6)"
    }
    if (-not (Test-Path -LiteralPath $reattachedPath)) {
        throw "sessions reattach was not called for the late URL"
    }
    if ($result.attachmentEvidence.requestedCount -ne $result.attachmentEvidence.matchedCount -or $result.attachmentEvidence.missingNames.Count -ne 0) {
        throw "Sent-turn attachment evidence did not match: $($result.attachmentEvidence | ConvertTo-Json -Depth 6)"
    }
    if ($result.attachmentEvidence.requestedCount -gt 4) {
        throw "Provider limit was not avoided before send: $($result.attachmentEvidence.requestedCount) uploads"
    }
    if ($result.contextBundle.inputCount -ne 19 -or -not (Test-Path -LiteralPath $result.contextBundle.path)) {
        throw "Expected deterministic 19-file context bundle: $($result.contextBundle | ConvertTo-Json -Depth 6)"
    }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($result.contextBundle.path)
    try {
        $manifestEntry = $zip.GetEntry("MANIFEST.json")
        $evidenceEntry = $zip.GetEntry("EXECUTED-EVIDENCE.json")
        if ($null -eq $manifestEntry -or $null -eq $evidenceEntry) {
            throw "Bundle is missing MANIFEST.json or EXECUTED-EVIDENCE.json"
        }
        $reader = [System.IO.StreamReader]::new($manifestEntry.Open(), [System.Text.Encoding]::UTF8)
        try { $manifest = $reader.ReadToEnd() | ConvertFrom-Json } finally { $reader.Dispose() }
    } finally {
        $zip.Dispose()
    }
    if ($manifest.inputCount -ne 19 -or $manifest.files.Count -ne 19 -or [string]::IsNullOrWhiteSpace($manifest.inputSha256)) {
        throw "Bundle manifest count/hash mismatch: $($manifest | ConvertTo-Json -Depth 8)"
    }
    foreach ($item in $manifest.files) {
        if ([string]::IsNullOrWhiteSpace($item.repoRelativePath) -or [string]::IsNullOrWhiteSpace($item.sha256) -or $item.byteSize -lt 1 -or [string]::IsNullOrWhiteSpace($item.role)) {
            throw "Incomplete manifest item: $($item | ConvertTo-Json -Depth 5)"
        }
    }

    $repeat = & $script @params | ConvertFrom-Json
    if (-not $repeat.ok -or $repeat.contextBundle.sha256 -ne $result.contextBundle.sha256 -or $repeat.contextBundle.inputSha256 -ne $result.contextBundle.inputSha256) {
        throw "Context bundle is not deterministic across identical sends: first=$($result.contextBundle.sha256) repeat=$($repeat.contextBundle.sha256)"
    }

    $quotedFiles = @($files | ForEach-Object { "'" + $_.Replace("'", "''") + "'" }) -join ","
    $failClosedCommand = "`$ProgressPreference='SilentlyContinue'; & '" + $script.Replace("'", "''") + "' -Action send -NoWatch -Prompt 'fixture truncation probe' -File @(" + $quotedFiles + ") -RepoRoot '" + $inputDir.Replace("'", "''") + "' -MaxDirectFiles 22 -UrlSettleSeconds 1 -UrlSettlePollSeconds 1"
    $encodedCommand = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($failClosedCommand))
    $failClosedRaw = & powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand $encodedCommand
    $failClosedExitCode = $LASTEXITCODE
    $failClosed = ($failClosedRaw | Out-String) | ConvertFrom-Json
    if ($failClosedExitCode -eq 0 -or $failClosed.ok -or $failClosed.status -ne "provider_attachment_mismatch") {
        throw "22-to-20 truncation did not fail closed: exit=$failClosedExitCode result=$($failClosed | ConvertTo-Json -Depth 8)"
    }
    if (@($failClosed.attachmentEvidence.missingNames).Count -ne 2 -or $failClosed.attachmentEvidence.missingNames[0] -ne $fixture.missingNames[0] -or $failClosed.attachmentEvidence.missingNames[1] -ne $fixture.missingNames[1]) {
        throw "Truncation fixture missing-name evidence changed: $($failClosed.attachmentEvidence | ConvertTo-Json -Depth 6)"
    }
} finally {
    Set-Location -LiteralPath $originalLocation
    $env:PATH = $originalPath
    Remove-Item Env:MOCK_SCRIPT, Env:MOCK_FIXTURE, Env:MOCK_STATE, Env:MOCK_REATTACHED -ErrorAction SilentlyContinue
    if ($null -ne $result -and $null -ne $result.contextBundle -and (Test-Path -LiteralPath $result.contextBundle.path)) {
        Remove-Item -LiteralPath $result.contextBundle.path -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $mockDir -Recurse -Force -ErrorAction SilentlyContinue
}

[pscustomobject]@{
    status = "passed"
    lateUrlPersisted = $true
    truncationAvoided = $true
    sentTurnEvidenceMatched = $true
    truncationFailedClosed = $true
    deterministicBundleVerified = $true
} | ConvertTo-Json -Depth 3
