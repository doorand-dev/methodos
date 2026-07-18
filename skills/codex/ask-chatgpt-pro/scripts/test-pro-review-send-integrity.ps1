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
$files = foreach ($name in $names) { $path = Join-Path $inputDir $name; Set-Content -LiteralPath $path -Value "fixture content" -Encoding UTF8; $path }
$secret = Join-Path $inputDir ".env.local"; Set-Content -LiteralPath $secret -Value "TOKEN=bad" -Encoding ASCII

$mockScript = Join-Path $mockDir "mock-agbrowse.ps1"
@'
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$CliArgs)
$fixture = Get-Content -Raw -LiteralPath $env:MOCK_FIXTURE | ConvertFrom-Json
function Write-MockJson($value) { $value | ConvertTo-Json -Depth 12 -Compress }
$joined = $CliArgs -join " "
if ($joined -match '^web-ai send ') {
    $paths = @(); for ($i = 0; $i -lt $CliArgs.Count; $i++) { if ($CliArgs[$i] -eq '--file') { $paths += $CliArgs[$i + 1] } }
    $sent = @($paths | ForEach-Object { Split-Path -Leaf $_ })
    [pscustomobject]@{ sentNames = $sent } | ConvertTo-Json | Set-Content -LiteralPath $env:MOCK_STATE -Encoding UTF8
    Write-MockJson ([pscustomobject]@{ sessionId = $fixture.sessionId; targetId = $fixture.targetId; url = $fixture.rootUrl }); exit 0
}
if ($joined -match '^tabs --json$') { Write-MockJson @([pscustomobject]@{ targetId = $fixture.targetId; url = $fixture.conversationUrl }); exit 0 }
if ($joined -match '^web-ai sessions reattach ') { Set-Content -LiteralPath $env:MOCK_REATTACHED -Value $fixture.conversationUrl; Write-MockJson ([pscustomobject]@{ ok = $true }); exit 0 }
if ($joined -match '^web-ai sessions show ') { Write-MockJson ([pscustomobject]@{ session = [pscustomobject]@{ sessionId = $fixture.sessionId; targetId = $fixture.targetId; conversationUrl = $fixture.rootUrl } }); exit 0 }
if ($CliArgs.Count -gt 0 -and $CliArgs[0] -eq 'evaluate') { $state = Get-Content -Raw -LiteralPath $env:MOCK_STATE | ConvertFrom-Json; Write-MockJson ([pscustomobject]@{ turnFound = $true; attachmentNames = @($state.sentNames) }); exit 0 }
Write-Error "Unexpected mock args: $joined"; exit 9
'@ | Set-Content -LiteralPath $mockScript -Encoding UTF8
@'
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%MOCK_SCRIPT%" %*
'@ | Set-Content -LiteralPath (Join-Path $mockDir "agbrowse.cmd") -Encoding ASCII

$originalPath = $env:PATH; $originalLocation = Get-Location
try {
    $env:PATH = "$mockDir;$originalPath"; $env:MOCK_SCRIPT = $mockScript; $env:MOCK_FIXTURE = $fixturePath; $env:MOCK_STATE = $statePath; $env:MOCK_REATTACHED = $reattachedPath
    Set-Location -LiteralPath $inputDir
    $result = & $script -Action send -NoWatch -ApproveExternalUpload -Prompt "Review supplied files" -File $files -RepoRoot $inputDir -UrlSettleSeconds 1 -UrlSettlePollSeconds 1 | ConvertFrom-Json
    if (-not $result.ok -or $result.status -ne "sent") { throw "Safe send failed" }
    if ($result.conversationUrl -ne $fixture.conversationUrl -or -not (Test-Path $reattachedPath)) { throw "Late URL was not captured and reattached" }
    if ($result.attachmentEvidence.missingNames.Count -ne 0 -or $result.attachmentEvidence.requestedCount -ne $result.attachmentEvidence.matchedCount) { throw "Attachment name/count check failed" }
    if ($null -eq $result.contextBundle -or $result.contextBundle.inputCount -ne 18) { throw "Expected temporary context bundle" }
    if ($result.contextBundle.path -match "[0-9a-f]{16,}") { throw "Bundle name unexpectedly contains a content digest" }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($result.contextBundle.path)
    try { $entry = $zip.GetEntry("MANIFEST.json"); if ($null -eq $entry) { throw "Manifest missing" }; $reader = [System.IO.StreamReader]::new($entry.Open()); try { $manifest = $reader.ReadToEnd() | ConvertFrom-Json } finally { $reader.Dispose() } } finally { $zip.Dispose() }
    if ($manifest.inputCount -ne 18 -or $manifest.files.Count -ne 18) { throw "Manifest count mismatch" }

    $approvalRaw = & $script -Action send -NoWatch -Prompt "approval" -File $files[0] -RepoRoot $inputDir 2>&1
    if ($LASTEXITCODE -ne 2 -or (($approvalRaw | Out-String) -notmatch "approval_required")) { throw "External upload approval was not required" }

    $secretFailed = $false
    try { & $script -Action send -NoWatch -ApproveExternalUpload -Prompt "secret" -File $secret -RepoRoot $inputDir | Out-Null } catch { $secretFailed = $true }
    if (-not $secretFailed) { throw "Sensitive path was not rejected" }
} finally {
    Set-Location -LiteralPath $originalLocation; $env:PATH = $originalPath
    Remove-Item Env:MOCK_SCRIPT, Env:MOCK_FIXTURE, Env:MOCK_STATE, Env:MOCK_REATTACHED -ErrorAction SilentlyContinue
    if ($null -ne $result -and $null -ne $result.contextBundle -and (Test-Path $result.contextBundle.path)) { Remove-Item -LiteralPath $result.contextBundle.path -Force -ErrorAction SilentlyContinue }
    Remove-Item -LiteralPath $mockDir -Recurse -Force -ErrorAction SilentlyContinue
}
[pscustomobject]@{ status = "passed"; secretRejected = $true; attachmentNamesAndCountChecked = $true; lateUrlReattached = $true; bundleManifestWithoutDigest = $true } | ConvertTo-Json -Depth 3
