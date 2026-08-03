param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("send", "collect", "watch-accelerate")]
    [string]$Action,

    [string]$Prompt,
    [string]$SystemPrompt,
    [string[]]$File,
    [string[]]$DirectFile,
    [string[]]$ExecutedEvidenceFile,
    [string]$RepoRoot = (Get-Location).Path,
    [int]$MaxDirectFiles = 3,
    [string]$SessionId,
    [string]$ContextFromFiles,
    [string[]]$ContextExclude,
    [ValidateSet("upload", "inline")]
    [string]$ContextTransport = "upload",
    [switch]$ReuseTab,
    [switch]$NoWatch,
    [switch]$Force,
    [int]$MinAgeMinutes = 10,
    [int]$MinAnswerChars = 1500,
    [int]$ResumeTimeoutSeconds = 180,
    [int]$StabilitySeconds = 30,
    [int]$UrlSettleSeconds = 30,
    [int]$UrlSettlePollSeconds = 2,
    [string]$AutomationId,
    [int]$WakeDelaySeconds = 30,
    [string]$WatchLog,
    [string]$AccelerateLog,
    [switch]$CloseTabOnComplete
)

$ErrorActionPreference = "Stop"
$script:Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = $script:Utf8NoBom
[Console]::OutputEncoding = $script:Utf8NoBom

function Write-Json($value) {
    $value | ConvertTo-Json -Depth 12
}

function Add-DecodedTextProperty($object, [string]$encodedName, [string]$propertyName) {
    if ($null -eq $object -or -not ($object.PSObject.Properties.Name -contains $encodedName)) {
        return
    }
    $encoded = [string]$object.$encodedName
    if ([string]::IsNullOrWhiteSpace($encoded)) {
        return
    }
    $decoded = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($encoded))
    if ($object.PSObject.Properties.Name -contains $propertyName) {
        $object.$propertyName = $decoded
    } else {
        $object | Add-Member -NotePropertyName $propertyName -NotePropertyValue $decoded
    }
}

function Convert-AgbrowseJsonWithNode($text, $stage) {
    $inputPath = Join-Path $env:TEMP ("agbrowse-json-" + [guid]::NewGuid().ToString("N") + ".json")
    $scriptPath = Join-Path $env:TEMP ("agbrowse-json-normalize-" + [guid]::NewGuid().ToString("N") + ".mjs")
    [System.IO.File]::WriteAllText($inputPath, [string]$text, $script:Utf8NoBom)
    [System.IO.File]::WriteAllText($scriptPath, @"
import fs from "node:fs";

const input = fs.readFileSync(process.argv[2], "utf8");

function extractJson(text) {
  const trimmed = String(text || "").trim();
  try {
    JSON.parse(trimmed);
    return trimmed;
  } catch {}

  const start = trimmed.indexOf("{");
  if (start < 0) throw new Error("no JSON object start");
  let depth = 0;
  let inString = false;
  let escaped = false;
  for (let i = start; i < trimmed.length; i += 1) {
    const ch = trimmed[i];
    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (ch === "\\") {
        escaped = true;
      } else if (ch === "\"") {
        inString = false;
      }
      continue;
    }
    if (ch === "\"") {
      inString = true;
    } else if (ch === "{") {
      depth += 1;
    } else if (ch === "}") {
      depth -= 1;
      if (depth === 0) return trimmed.slice(start, i + 1);
    }
  }
  throw new Error("no complete JSON object");
}

function b64(value) {
  return typeof value === "string" ? Buffer.from(value, "utf8").toString("base64") : null;
}

const obj = JSON.parse(extractJson(input));
const session = obj && typeof obj.session === "object" && obj.session !== null ? obj.session : null;
const answerText =
  typeof obj.answerText === "string" ? obj.answerText :
  typeof obj.text === "string" ? obj.text :
  obj.answerArtifact && typeof obj.answerArtifact.markdown === "string" ? obj.answerArtifact.markdown :
  null;

const out = {
  ok: obj.ok ?? null,
  action: obj.action ?? null,
  status: obj.status ?? null,
  vendor: obj.vendor ?? null,
  url: obj.url ?? null,
  sessionId: obj.sessionId ?? session?.sessionId ?? null,
  targetId: obj.targetId ?? session?.targetId ?? session?.tabId ?? null,
  tabId: obj.tabId ?? session?.tabId ?? null,
  conversationUrl: obj.conversationUrl ?? session?.conversationUrl ?? obj.url ?? null,
  completedAt: obj.completedAt ?? session?.completedAt ?? null,
  responseStableMs: obj.responseStableMs ?? null,
  warnings: Array.isArray(obj.warnings) ? obj.warnings : [],
  answerTextB64: b64(answerText),
  answerB64: b64(obj.answer),
  session: session ? {
    sessionId: session.sessionId ?? null,
    vendor: session.vendor ?? null,
    status: session.status ?? null,
    completedAt: session.completedAt ?? null,
    targetId: session.targetId ?? session.tabId ?? null,
    tabId: session.tabId ?? null,
    conversationUrl: session.conversationUrl ?? session.originalUrl ?? null,
    originalUrl: session.originalUrl ?? null,
    warnings: Array.isArray(session.warnings) ? session.warnings : [],
    lastResponseCharCount: session.lastResponseCharCount ?? null,
    answerB64: b64(session.answer),
  } : null,
};

process.stdout.write(JSON.stringify(out));
"@, $script:Utf8NoBom)

    try {
        $raw = & node $scriptPath $inputPath 2>&1
        $exitCode = $LASTEXITCODE
        $normalizedText = ($raw | Out-String).Trim()
        if ($exitCode -ne 0) {
            throw "$stage node JSON fallback failed: $normalizedText"
        }
        $object = $normalizedText | ConvertFrom-Json
        Add-DecodedTextProperty $object "answerTextB64" "answerText"
        Add-DecodedTextProperty $object "answerB64" "answer"
        if ($null -ne $object.session) {
            Add-DecodedTextProperty $object.session "answerB64" "answer"
        }
        return $object
    } finally {
        Remove-Item -LiteralPath $inputPath, $scriptPath -ErrorAction SilentlyContinue
    }
}

function Convert-AgbrowseJson($rawText, $stage) {
    $text = [string]$rawText
    try {
        return $text | ConvertFrom-Json
    } catch {
        try {
            return Convert-AgbrowseJsonWithNode $text $stage
        } catch {
            $nodeError = $_
        }
        $jsonStarts = @($text.IndexOf("{"), $text.IndexOf("["))
        $starts = @($jsonStarts | Where-Object { $_ -ge 0 })
        $start = -1
        if ($starts.Count -gt 0) {
            $start = ($starts | Measure-Object -Minimum).Minimum
        }
        $end = [Math]::Max($text.LastIndexOf("}"), $text.LastIndexOf("]"))
        if ($start -ge 0 -and $end -ge $start) {
            return $text.Substring($start, $end - $start + 1) | ConvertFrom-Json
        }
        throw "$stage returned no parseable JSON. Node fallback: $nodeError"
    }
}

function Invoke-AgbrowseNative($arguments) {
    $previousErrorActionPreference = $ErrorActionPreference
    $nativePref = Get-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue
    try {
        $ErrorActionPreference = "Continue"
        [Console]::OutputEncoding = $script:Utf8NoBom
        $OutputEncoding = $script:Utf8NoBom
        if ($null -ne $nativePref) {
            Set-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -Value $false
        }
        $raw = & agbrowse @arguments 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
        if ($null -ne $nativePref) {
            Set-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -Value $nativePref.Value
        }
    }

    $stdoutParts = @()
    $stderrParts = @()
    $raw | ForEach-Object {
        if ($_ -is [System.Management.Automation.ErrorRecord]) {
            $stderrParts += $_.ToString()
        } else {
            $stdoutParts += [string]$_
        }
    }

    $stdout = ($stdoutParts -join "`n").Trim()
    $stderr = ($stderrParts -join "`n").Trim()
    $textParts = @()
    if (-not [string]::IsNullOrWhiteSpace($stdout)) {
        $textParts += $stdout
    }
    if (-not [string]::IsNullOrWhiteSpace($stderr)) {
        $textParts += $stderr
    }

    return [pscustomobject]@{
        exitCode = $exitCode
        stdout = $stdout
        stderr = $stderr
        text = ($textParts -join "`n").Trim()
    }
}

function Invoke-AgbrowseJson($arguments, $stage) {
    $native = Invoke-AgbrowseNative $arguments
    if ($native.exitCode -ne 0) {
        $parsed = $null
        try {
            $jsonText = $native.stdout
            if ([string]::IsNullOrWhiteSpace($jsonText)) {
                $jsonText = $native.text
            }
            $parsed = Convert-AgbrowseJson $jsonText $stage
        } catch {
            $parsed = $null
        }
        $headLength = [Math]::Min(1200, $native.text.Length)
        Write-Json ([pscustomobject]@{
            ok = $false
            action = $Action
            stage = $stage
            status = "provider_blocker"
            exitCode = $native.exitCode
            outputHead = $native.text.Substring(0, $headLength)
            provider = $parsed
            next = "Stop new sends. Recover any existing sessionId before retrying."
        })
        exit 2
    }
    $jsonText = $native.stdout
    if ([string]::IsNullOrWhiteSpace($jsonText)) {
        $jsonText = $native.text
    }
    return Convert-AgbrowseJson $jsonText $stage
}

function Try-AgbrowseJson($arguments, $stage) {
    $native = Invoke-AgbrowseNative $arguments
    if ($native.exitCode -ne 0) {
        return [pscustomobject]@{
            ok = $false
            stage = $stage
            exitCode = $native.exitCode
            outputHead = $native.text.Substring(0, [Math]::Min(1200, $native.text.Length))
            value = $null
        }
    }
    try {
        $jsonText = $native.stdout
        if ([string]::IsNullOrWhiteSpace($jsonText)) {
            $jsonText = $native.text
        }
        return [pscustomobject]@{
            ok = $true
            stage = $stage
            exitCode = 0
            outputHead = $null
            value = Convert-AgbrowseJson $jsonText $stage
        }
    } catch {
        return [pscustomobject]@{
            ok = $false
            stage = $stage
            exitCode = 0
            outputHead = [string]$_
            value = $null
        }
    }
}

function Get-ObjectProperty($object, [string[]]$names) {
    if ($null -eq $object) {
        return $null
    }
    foreach ($name in $names) {
        if ($object.PSObject.Properties.Name -contains $name) {
            $value = [string]$object.$name
            if (-not [string]::IsNullOrWhiteSpace($value)) {
                return $value
            }
        }
    }
    return $null
}

function Get-SessionAnswer($sessionObject) {
    if ($null -eq $sessionObject) {
        return ""
    }
    if ($sessionObject.PSObject.Properties.Name -contains "answerText") {
        return [string]$sessionObject.answerText
    }
    if ($sessionObject.PSObject.Properties.Name -contains "session") {
        $session = $sessionObject.session
        if ($null -ne $session -and $session.PSObject.Properties.Name -contains "answer") {
            return [string]$session.answer
        }
    }
    return ""
}

function Get-TextSha256([string]$text) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
        $hash = $sha.ComputeHash($bytes)
        return -join ($hash | ForEach-Object { $_.ToString("x2") })
    } finally {
        $sha.Dispose()
    }
}

function Get-FileSha256([string]$path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
}

function Get-NormalizedFullPath([string]$path) {
    return [System.IO.Path]::GetFullPath($path)
}

function Test-SensitiveBundlePath([string]$relativePath) {
    $normalized = $relativePath.Replace("\", "/")
    $segments = @($normalized.Split("/", [System.StringSplitOptions]::RemoveEmptyEntries))
    foreach ($segment in $segments) {
        if ($segment -ieq "secrets" -or $segment -ieq ".env" -or $segment -ilike ".env.*") {
            return $true
        }
    }
    return $false
}

function Get-RepoRelativePath([string]$path, [string]$root) {
    $fullPath = Get-NormalizedFullPath $path
    $fullRoot = (Get-NormalizedFullPath $root).TrimEnd("\", "/") + [System.IO.Path]::DirectorySeparatorChar
    if (-not $fullPath.StartsWith($fullRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Bundle input must be under -RepoRoot. input=$fullPath repoRoot=$root"
    }
    return $fullPath.Substring($fullRoot.Length).Replace("\", "/")
}

function Get-UniqueExistingFiles($paths) {
    $seen = @{}
    $resolved = @()
    foreach ($path in @($paths)) {
        if ([string]::IsNullOrWhiteSpace([string]$path)) {
            continue
        }
        $fullPath = Get-NormalizedFullPath ([string]$path)
        if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
            throw "Missing attachment input: $fullPath"
        }
        if (-not $seen.ContainsKey($fullPath)) {
            $seen[$fullPath] = $true
            $resolved += $fullPath
        }
    }
    return @($resolved)
}

function New-DeterministicContextBundle($paths, $executedEvidencePaths, [string]$root) {
    $inputs = @(Get-UniqueExistingFiles $paths)
    if ($inputs.Count -eq 0) {
        return $null
    }
    $evidenceSet = @{}
    foreach ($path in @(Get-UniqueExistingFiles $executedEvidencePaths)) {
        $evidenceSet[$path] = $true
    }
    foreach ($path in $evidenceSet.Keys) {
        if ($inputs -notcontains $path) {
            throw "Executed evidence must be included in the context bundle inputs: $path"
        }
    }

    $manifestFiles = @()
    foreach ($path in $inputs) {
        $relativePath = Get-RepoRelativePath $path $root
        if (Test-SensitiveBundlePath $relativePath) {
            throw "Sensitive input is rejected from context bundles: $relativePath"
        }
        $item = Get-Item -LiteralPath $path
        $manifestFiles += [pscustomobject]@{
            repoRelativePath = $relativePath
            sha256 = Get-FileSha256 $path
            byteSize = [int64]$item.Length
            role = $(if ($evidenceSet.ContainsKey($path)) { "executed-evidence" } else { "context" })
            sourcePath = $path
        }
    }
    $manifestFiles = @($manifestFiles | Sort-Object repoRelativePath)
    $inputLedger = ($manifestFiles | ForEach-Object { $_.repoRelativePath + "`0" + $_.sha256 + "`0" + $_.byteSize + "`0" + $_.role }) -join "`n"
    $inputSha256 = Get-TextSha256 $inputLedger
    $publicFiles = @($manifestFiles | ForEach-Object {
        [pscustomobject]@{
            repoRelativePath = $_.repoRelativePath
            sha256 = $_.sha256
            byteSize = $_.byteSize
            role = $_.role
        }
    })
    $manifest = [pscustomobject]@{
        schemaVersion = 1
        inputCount = $publicFiles.Count
        inputSha256 = $inputSha256
        files = $publicFiles
    }
    $evidenceFiles = @($publicFiles | Where-Object { $_.role -eq "executed-evidence" })
    $evidencePacket = [pscustomobject]@{
        schemaVersion = 1
        inputCount = $evidenceFiles.Count
        inputSha256 = Get-TextSha256 (($evidenceFiles | ForEach-Object { $_.repoRelativePath + "`0" + $_.sha256 + "`0" + $_.byteSize }) -join "`n")
        files = $evidenceFiles
    }

    Add-Type -AssemblyName System.IO.Compression
    $bundlePath = Join-Path $env:TEMP ("ask-chatgpt-pro-context-" + $inputSha256.Substring(0, 16) + ".zip")
    $stream = [System.IO.File]::Open($bundlePath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    try {
        $archive = [System.IO.Compression.ZipArchive]::new($stream, [System.IO.Compression.ZipArchiveMode]::Create, $true, $script:Utf8NoBom)
        try {
            $fixedTimestamp = [DateTimeOffset]::new(2000, 1, 1, 0, 0, 0, [TimeSpan]::Zero)
            foreach ($entryData in @(
                [pscustomobject]@{ name = "MANIFEST.json"; text = ($manifest | ConvertTo-Json -Depth 12) },
                [pscustomobject]@{ name = "EXECUTED-EVIDENCE.json"; text = ($evidencePacket | ConvertTo-Json -Depth 12) }
            )) {
                $entry = $archive.CreateEntry($entryData.name, [System.IO.Compression.CompressionLevel]::Optimal)
                $entry.LastWriteTime = $fixedTimestamp
                $writer = [System.IO.StreamWriter]::new($entry.Open(), $script:Utf8NoBom)
                try { $writer.Write($entryData.text) } finally { $writer.Dispose() }
            }
            foreach ($file in $manifestFiles) {
                $entry = $archive.CreateEntry(("files/" + $file.repoRelativePath), [System.IO.Compression.CompressionLevel]::Optimal)
                $entry.LastWriteTime = $fixedTimestamp
                $input = [System.IO.File]::OpenRead($file.sourcePath)
                $output = $entry.Open()
                try { $input.CopyTo($output) } finally { $output.Dispose(); $input.Dispose() }
            }
        } finally {
            $archive.Dispose()
        }
    } finally {
        $stream.Dispose()
    }

    return [pscustomobject]@{
        path = $bundlePath
        sha256 = Get-FileSha256 $bundlePath
        byteSize = (Get-Item -LiteralPath $bundlePath).Length
        inputCount = $publicFiles.Count
        inputSha256 = $inputSha256
        evidenceCount = $evidenceFiles.Count
        manifest = $manifest
    }
}

function Resolve-AttachmentRoute($files, $directFiles, $executedEvidenceFiles, [string]$root, [int]$maxDirectFiles) {
    if ($maxDirectFiles -lt 1) {
        throw "-MaxDirectFiles must be at least 1."
    }
    $allFiles = @(Get-UniqueExistingFiles $files)
    $explicitDirect = @(Get-UniqueExistingFiles $directFiles)
    foreach ($path in $explicitDirect) {
        if (-not ($allFiles -contains $path)) {
            $allFiles = @($path) + $allFiles
        }
    }

    if ($explicitDirect.Count -gt $maxDirectFiles) {
        throw "Direct attachment count $($explicitDirect.Count) exceeds -MaxDirectFiles $maxDirectFiles."
    }
    $direct = if ($explicitDirect.Count -gt 0) {
        @($explicitDirect)
    } elseif ($allFiles.Count -le $maxDirectFiles) {
        @($allFiles)
    } else {
        @($allFiles | Select-Object -First $maxDirectFiles)
    }
    $bundleInputs = @($allFiles | Where-Object { $direct -notcontains $_ })
    $bundle = New-DeterministicContextBundle $bundleInputs $executedEvidenceFiles $root
    $uploadPaths = @($direct)
    if ($null -ne $bundle) {
        $uploadPaths += $bundle.path
    }
    $duplicateNames = @($uploadPaths | Group-Object { Split-Path -Leaf $_ } | Where-Object { $_.Count -gt 1 } | ForEach-Object { $_.Name })
    if ($duplicateNames.Count -gt 0) {
        throw "Upload basenames must be unique for sent-turn evidence: $($duplicateNames -join ', ')"
    }
    return [pscustomobject]@{
        directFiles = $direct
        bundleInputs = $bundleInputs
        contextBundle = $bundle
        uploadPaths = $uploadPaths
    }
}

function Get-SessionData($sessionObject) {
    if ($null -eq $sessionObject) {
        return $null
    }
    if ($sessionObject.PSObject.Properties.Name -contains "session") {
        return $sessionObject.session
    }
    return $sessionObject
}

function Get-TargetId($sessionObject) {
    $session = Get-SessionData $sessionObject
    $targetId = Get-ObjectProperty $session @("targetId", "tabId")
    if ([string]::IsNullOrWhiteSpace($targetId)) {
        $targetId = Get-ObjectProperty $sessionObject @("targetId", "tabId")
    }
    return $targetId
}

function Test-ChatGptConversationUrl([string]$url) {
    if ([string]::IsNullOrWhiteSpace($url)) {
        return $false
    }
    return $url -match "^https://chatgpt\.com/c/[0-9a-fA-F-]+"
}

function Get-ConversationUrl($sessionObject) {
    $fallback = $null
    $session = Get-SessionData $sessionObject
    foreach ($candidate in @($sessionObject, $session)) {
        if ($null -eq $candidate) {
            continue
        }
        foreach ($name in @("conversationUrl", "url", "originalUrl")) {
            if ($candidate.PSObject.Properties.Name -contains $name) {
                $value = [string]$candidate.$name
                if ([string]::IsNullOrWhiteSpace($value)) {
                    continue
                }
                if (Test-ChatGptConversationUrl $value) {
                    return $value
                }
                if ([string]::IsNullOrWhiteSpace($fallback)) {
                    $fallback = $value
                }
            }
        }
    }
    return $fallback
}

function Find-TargetConversationUrl($targetId) {
    if ([string]::IsNullOrWhiteSpace($targetId)) {
        return $null
    }
    $tabsResult = Try-AgbrowseJson @("tabs", "--json") "tabs"
    if (-not $tabsResult.ok) {
        return $null
    }
    foreach ($tab in @($tabsResult.value)) {
        $id = Get-ObjectProperty $tab @("targetId", "tabId", "id")
        if ($id -ne $targetId) {
            continue
        }
        $url = Get-ObjectProperty $tab @("url", "currentUrl", "href")
        if (Test-ChatGptConversationUrl $url) {
            return $url
        }
    }
    return $null
}

function Save-LateConversationUrl($sessionId, $targetId, [string]$conversationUrl) {
    $reattach = Try-AgbrowseJson @("web-ai", "sessions", "reattach", $sessionId, "--json") "sessions.reattach.url-settle"
    if (-not $reattach.ok) {
        return [pscustomobject]@{
            ok = $false
            status = "found_not_persisted"
            conversationUrl = $conversationUrl
            error = $reattach.outputHead
        }
    }
    $show = Try-AgbrowseJson @("web-ai", "sessions", "show", $sessionId, "--json") "sessions.show.url-persist"
    $storedUrl = $(if ($show.ok) { Get-ConversationUrl $show.value } else { $null })
    $storedTargetId = $(if ($show.ok) { Get-TargetId $show.value } else { $null })
    $persisted = ($storedUrl -eq $conversationUrl -and ([string]::IsNullOrWhiteSpace($targetId) -or $storedTargetId -eq $targetId))
    return [pscustomobject]@{
        ok = $persisted
        status = $(if ($persisted) { "settled_and_persisted" } else { "found_not_persisted" })
        conversationUrl = $conversationUrl
        storedUrl = $storedUrl
        targetId = $targetId
        storedTargetId = $storedTargetId
        error = $(if ($show.ok) { $null } else { $show.outputHead })
    }
}

function Test-SentTurnAttachments($targetId, $uploadPaths) {
    $expectedNames = @($uploadPaths | ForEach-Object { Split-Path -Leaf $_ })
    if ($expectedNames.Count -eq 0) {
        return [pscustomobject]@{
            ok = $true
            status = "no_attachments"
            requestedCount = 0
            matchedCount = 0
            expectedNames = @()
            matchedNames = @()
            missingNames = @()
        }
    }

    $active = Try-AgbrowseJson @("active-tab", "--json") "active-tab.attachment-evidence"
    $originalTargetId = $(if ($active.ok) { Get-ObjectProperty $active.value @("targetId", "tabId", "id") } else { $null })
    $switched = $false
    try {
        if (-not [string]::IsNullOrWhiteSpace($targetId) -and $originalTargetId -ne $targetId) {
            $switch = Try-AgbrowseJson @("tab-switch", $targetId, "--json") "tab-switch.attachment-evidence"
            if (-not $switch.ok) {
                return [pscustomobject]@{
                    ok = $false
                    status = "target_unavailable"
                    requestedCount = $expectedNames.Count
                    matchedCount = 0
                    expectedNames = $expectedNames
                    matchedNames = @()
                    missingNames = $expectedNames
                    error = $switch.outputHead
                }
            }
            $switched = $true
        }

        $expectedJson = $expectedNames | ConvertTo-Json -Compress
        $expression = @"
(() => {
  const expected = $expectedJson;
  const turns = Array.from(document.querySelectorAll('[data-turn="user"], [data-message-author-role="user"]'));
  const turn = turns.at(-1);
  if (!turn) return { turnFound: false, attachmentNames: [] };
  const nodes = Array.from(turn.querySelectorAll('[data-testid*="attachment" i], [data-testid*="file" i], [aria-label*="attachment" i], [aria-label*="file" i], .group\\/file-tile, [role="group"]'));
  const haystack = nodes.flatMap(node => [node.innerText || node.textContent || '', node.getAttribute?.('aria-label') || '', node.getAttribute?.('title') || '', node.getAttribute?.('data-testid') || '']).join('\n').toLowerCase();
  return { turnFound: true, attachmentNames: expected.filter(name => haystack.includes(String(name).toLowerCase())) };
})()
"@
        $probe = $null
        for ($attempt = 1; $attempt -le 3; $attempt++) {
            $native = Invoke-AgbrowseNative @("evaluate", $expression)
            if ($native.exitCode -eq 0) {
                try { $probe = Convert-AgbrowseJson $native.stdout "evaluate.attachment-evidence" } catch { $probe = $null }
            }
            if ($null -ne $probe -and $probe.turnFound) {
                break
            }
            if ($attempt -lt 3) {
                Start-Sleep -Seconds 1
            }
        }
        if ($null -eq $probe -or -not $probe.turnFound) {
            return [pscustomobject]@{
                ok = $false
                status = "sent_turn_unavailable"
                requestedCount = $expectedNames.Count
                matchedCount = 0
                expectedNames = $expectedNames
                matchedNames = @()
                missingNames = $expectedNames
            }
        }
        $matched = @($expectedNames | Where-Object { @($probe.attachmentNames) -contains $_ })
        $missing = @($expectedNames | Where-Object { $matched -notcontains $_ })
        return [pscustomobject]@{
            ok = ($missing.Count -eq 0 -and $matched.Count -eq $expectedNames.Count)
            status = $(if ($missing.Count -eq 0) { "matched" } else { "mismatch" })
            requestedCount = $expectedNames.Count
            matchedCount = $matched.Count
            expectedNames = $expectedNames
            matchedNames = $matched
            missingNames = $missing
        }
    } finally {
        if ($switched -and -not [string]::IsNullOrWhiteSpace($originalTargetId)) {
            [void](Try-AgbrowseJson @("tab-switch", $originalTargetId, "--json") "tab-switch.attachment-evidence.restore")
        }
    }
}

function Wait-SettledConversationUrl($sessionId, $sendObject, $settleSeconds, $pollSeconds) {
    $targetId = Get-TargetId $sendObject
    $initialUrl = Get-ConversationUrl $sendObject
    if (Test-ChatGptConversationUrl $initialUrl) {
        return [pscustomobject]@{
            ok = $true
            status = "settled"
            source = "send"
            conversationUrl = $initialUrl
            initialUrl = $initialUrl
            checkedSeconds = 0
        }
    }

    $bestUrl = $initialUrl
    $deadline = (Get-Date).AddSeconds($settleSeconds)
    $startedAt = Get-Date
    while ((Get-Date) -lt $deadline) {
        $tabUrl = Find-TargetConversationUrl $targetId
        if (Test-ChatGptConversationUrl $tabUrl) {
            $persist = Save-LateConversationUrl $sessionId $targetId $tabUrl
            return [pscustomobject]@{
                ok = $persist.ok
                status = $persist.status
                source = "tabs+sessions.reattach"
                conversationUrl = $tabUrl
                initialUrl = $initialUrl
                checkedSeconds = [Math]::Round(((Get-Date) - $startedAt).TotalSeconds, 1)
                persistence = $persist
            }
        }

        $show = Try-AgbrowseJson @("web-ai", "sessions", "show", $sessionId, "--json") "sessions.show.url-settle"
        if ($show.ok) {
            $showUrl = Get-ConversationUrl $show.value
            if (Test-ChatGptConversationUrl $showUrl) {
                return [pscustomobject]@{
                    ok = $true
                    status = "settled"
                    source = "sessions.show"
                    conversationUrl = $showUrl
                    initialUrl = $initialUrl
                    checkedSeconds = [Math]::Round(((Get-Date) - $startedAt).TotalSeconds, 1)
                }
            }
            if (-not [string]::IsNullOrWhiteSpace($showUrl)) {
                $bestUrl = $showUrl
            }
        }

        Start-Sleep -Seconds $pollSeconds
    }

    return [pscustomobject]@{
        ok = $false
        status = "root_or_unavailable"
        source = "timeout"
        conversationUrl = $bestUrl
        initialUrl = $initialUrl
        checkedSeconds = $settleSeconds
        next = "Keep sessionId as the durable handle. If collection later cannot reattach, recover the /c/ URL from the open tab or browser history before resending."
    }
}

function Start-BackgroundWatch($sessionId, $watchLog) {
    $watchCommand = "agbrowse web-ai watch --session $sessionId --json --navigate *> `"$watchLog`""
    $lastError = $null
    for ($attempt = 1; $attempt -le 2; $attempt++) {
        try {
            $watcher = Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoProfile", "-Command", $watchCommand -PassThru
            return [pscustomobject]@{
                watcher = $watcher
                command = $watchCommand
            }
        } catch {
            $lastError = $_
            Start-Sleep -Seconds 1
        }
    }
    throw "watcher start failed after retry: $lastError"
}

function Get-DefaultWatchLog($sessionId) {
    return (Join-Path $env:TEMP ("agbrowse-chatgpt-" + $sessionId + "-watch.jsonl"))
}

function Get-DefaultAccelerateLog($sessionId) {
    return (Join-Path $env:TEMP ("agbrowse-chatgpt-" + $sessionId + "-heartbeat-accelerate.log"))
}

function Get-DefaultAcceleratedResult($sessionId) {
    return (Join-Path $env:TEMP ("agbrowse-chatgpt-" + $sessionId + "-accelerated-final.json"))
}

function Start-AcceleratingWatch($sessionId, $automationId, $watchLog, $accelerateLog, $wakeDelaySeconds, $minAnswerChars, $stabilitySeconds, $resumeTimeoutSeconds) {
    if ([string]::IsNullOrWhiteSpace($sessionId)) {
        throw "-SessionId is required when -Action watch-accelerate."
    }
    if ([string]::IsNullOrWhiteSpace($automationId)) {
        throw "-AutomationId is required when -Action watch-accelerate."
    }
    if ([string]::IsNullOrWhiteSpace($watchLog)) {
        $watchLog = Get-DefaultWatchLog $sessionId
    }
    if ([string]::IsNullOrWhiteSpace($accelerateLog)) {
        $accelerateLog = Get-DefaultAccelerateLog $sessionId
    }
    $acceleratedResult = Get-DefaultAcceleratedResult $sessionId
    if ($minAnswerChars -lt 1) {
        $minAnswerChars = 1
    }
    if ($stabilitySeconds -lt 1) {
        $stabilitySeconds = 1
    }
    if ($resumeTimeoutSeconds -lt 1) {
        $resumeTimeoutSeconds = 180
    }
    $heartbeatRruleHelper = Join-Path $PSScriptRoot "codex-heartbeat-rrule.ps1"
    if (-not (Test-Path -LiteralPath $heartbeatRruleHelper)) {
        throw "Missing heartbeat RRULE helper: $heartbeatRruleHelper"
    }

    $configPath = Join-Path $env:TEMP ("agbrowse-chatgpt-" + $sessionId + "-heartbeat-accelerate-config.json")
    $workerPath = Join-Path $env:TEMP ("agbrowse-chatgpt-" + $sessionId + "-heartbeat-accelerate-worker.ps1")
    [pscustomobject]@{
        sessionId = $sessionId
        automationId = $automationId
        watchLog = $watchLog
        accelerateLog = $accelerateLog
        acceleratedResult = $acceleratedResult
        heartbeatRruleHelper = $heartbeatRruleHelper
        wakeDelaySeconds = $wakeDelaySeconds
        minAnswerChars = $minAnswerChars
        stabilitySeconds = $stabilitySeconds
        resumeTimeoutSeconds = $resumeTimeoutSeconds
        maxWaitSeconds = 1200
    } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $configPath -Encoding UTF8

    $workerScript = @'
param(
    [Parameter(Mandatory = $true)]
    [string]$ConfigPath
)

$ErrorActionPreference = "Stop"
$script:Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = $script:Utf8NoBom
[Console]::OutputEncoding = $script:Utf8NoBom

function Add-DecodedTextProperty($object, [string]$encodedName, [string]$propertyName) {
    if ($null -eq $object -or -not ($object.PSObject.Properties.Name -contains $encodedName)) {
        return
    }
    $encoded = [string]$object.$encodedName
    if ([string]::IsNullOrWhiteSpace($encoded)) {
        return
    }
    $decoded = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($encoded))
    if ($object.PSObject.Properties.Name -contains $propertyName) {
        $object.$propertyName = $decoded
    } else {
        $object | Add-Member -NotePropertyName $propertyName -NotePropertyValue $decoded
    }
}

function Convert-AgbrowseJsonWithNode($text, $stage) {
    $inputPath = Join-Path $env:TEMP ("agbrowse-json-" + [guid]::NewGuid().ToString("N") + ".json")
    $scriptPath = Join-Path $env:TEMP ("agbrowse-json-normalize-" + [guid]::NewGuid().ToString("N") + ".mjs")
    [System.IO.File]::WriteAllText($inputPath, [string]$text, $script:Utf8NoBom)
    [System.IO.File]::WriteAllText($scriptPath, @"
import fs from "node:fs";

const input = fs.readFileSync(process.argv[2], "utf8");

function extractJson(text) {
  const trimmed = String(text || "").trim();
  try {
    JSON.parse(trimmed);
    return trimmed;
  } catch {}

  const start = trimmed.indexOf("{");
  if (start < 0) throw new Error("no JSON object start");
  let depth = 0;
  let inString = false;
  let escaped = false;
  for (let i = start; i < trimmed.length; i += 1) {
    const ch = trimmed[i];
    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (ch === "\\") {
        escaped = true;
      } else if (ch === "\"") {
        inString = false;
      }
      continue;
    }
    if (ch === "\"") {
      inString = true;
    } else if (ch === "{") {
      depth += 1;
    } else if (ch === "}") {
      depth -= 1;
      if (depth === 0) return trimmed.slice(start, i + 1);
    }
  }
  throw new Error("no complete JSON object");
}

function b64(value) {
  return typeof value === "string" ? Buffer.from(value, "utf8").toString("base64") : null;
}

const obj = JSON.parse(extractJson(input));
const session = obj && typeof obj.session === "object" && obj.session !== null ? obj.session : null;
const answerText =
  typeof obj.answerText === "string" ? obj.answerText :
  typeof obj.text === "string" ? obj.text :
  obj.answerArtifact && typeof obj.answerArtifact.markdown === "string" ? obj.answerArtifact.markdown :
  null;

const out = {
  ok: obj.ok ?? null,
  action: obj.action ?? null,
  status: obj.status ?? null,
  vendor: obj.vendor ?? null,
  url: obj.url ?? null,
  sessionId: obj.sessionId ?? session?.sessionId ?? null,
  targetId: obj.targetId ?? session?.targetId ?? session?.tabId ?? null,
  tabId: obj.tabId ?? session?.tabId ?? null,
  conversationUrl: obj.conversationUrl ?? session?.conversationUrl ?? obj.url ?? null,
  completedAt: obj.completedAt ?? session?.completedAt ?? null,
  responseStableMs: obj.responseStableMs ?? null,
  warnings: Array.isArray(obj.warnings) ? obj.warnings : [],
  answerTextB64: b64(answerText),
  answerB64: b64(obj.answer),
  session: session ? {
    sessionId: session.sessionId ?? null,
    vendor: session.vendor ?? null,
    status: session.status ?? null,
    completedAt: session.completedAt ?? null,
    targetId: session.targetId ?? session.tabId ?? null,
    tabId: session.tabId ?? null,
    conversationUrl: session.conversationUrl ?? session.originalUrl ?? null,
    originalUrl: session.originalUrl ?? null,
    warnings: Array.isArray(session.warnings) ? session.warnings : [],
    lastResponseCharCount: session.lastResponseCharCount ?? null,
    answerB64: b64(session.answer),
  } : null,
};

process.stdout.write(JSON.stringify(out));
"@, $script:Utf8NoBom)

    try {
        $raw = & node $scriptPath $inputPath 2>&1
        $exitCode = $LASTEXITCODE
        $normalizedText = ($raw | Out-String).Trim()
        if ($exitCode -ne 0) {
            throw "$stage node JSON fallback failed: $normalizedText"
        }
        $object = $normalizedText | ConvertFrom-Json
        Add-DecodedTextProperty $object "answerTextB64" "answerText"
        Add-DecodedTextProperty $object "answerB64" "answer"
        if ($null -ne $object.session) {
            Add-DecodedTextProperty $object.session "answerB64" "answer"
        }
        return $object
    } finally {
        Remove-Item -LiteralPath $inputPath, $scriptPath -ErrorAction SilentlyContinue
    }
}

function Convert-AgbrowseJson($rawText, $stage) {
    $text = [string]$rawText
    try {
        return $text | ConvertFrom-Json
    } catch {
        try {
            return Convert-AgbrowseJsonWithNode $text $stage
        } catch {
            $nodeError = $_
        }
        $jsonStarts = @($text.IndexOf("{"), $text.IndexOf("["))
        $starts = @($jsonStarts | Where-Object { $_ -ge 0 })
        $start = -1
        if ($starts.Count -gt 0) {
            $start = ($starts | Measure-Object -Minimum).Minimum
        }
        $end = [Math]::Max($text.LastIndexOf("}"), $text.LastIndexOf("]"))
        if ($start -ge 0 -and $end -ge $start) {
            return $text.Substring($start, $end - $start + 1) | ConvertFrom-Json
        }
        throw "$stage returned no parseable JSON. Node fallback: $nodeError"
    }
}

function Get-SessionData($sessionObject) {
    if ($null -eq $sessionObject) {
        return $null
    }
    if ($sessionObject.PSObject.Properties.Name -contains "session") {
        return $sessionObject.session
    }
    return $sessionObject
}

function Get-SessionAnswer($sessionObject) {
    if ($null -eq $sessionObject) {
        return ""
    }
    if ($sessionObject.PSObject.Properties.Name -contains "answerText") {
        return [string]$sessionObject.answerText
    }
    if ($sessionObject.PSObject.Properties.Name -contains "session") {
        $session = $sessionObject.session
        if ($null -ne $session -and $session.PSObject.Properties.Name -contains "answer") {
            return [string]$session.answer
        }
    }
    return ""
}

function Get-TextSha256([string]$text) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
        $hash = $sha.ComputeHash($bytes)
        return -join ($hash | ForEach-Object { $_.ToString("x2") })
    } finally {
        $sha.Dispose()
    }
}

function Write-AccelerateLog($message) {
    Add-Content -LiteralPath $script:Config.accelerateLog -Value ((Get-Date -Format o) + " " + $message) -Encoding UTF8
}

function Write-AcceleratedResult($data) {
    $json = $data | ConvertTo-Json -Depth 12
    [System.IO.File]::WriteAllText($script:Config.acceleratedResult, $json, $script:Utf8NoBom)
}

function Invoke-AgbrowseNative($arguments) {
    $previousErrorActionPreference = $ErrorActionPreference
    $nativePref = Get-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue
    try {
        $ErrorActionPreference = "Continue"
        [Console]::OutputEncoding = $script:Utf8NoBom
        $OutputEncoding = $script:Utf8NoBom
        if ($null -ne $nativePref) {
            Set-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -Value $false
        }
        $raw = & agbrowse @arguments 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
        if ($null -ne $nativePref) {
            Set-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -Value $nativePref.Value
        }
    }

    $stdoutParts = @()
    $stderrParts = @()
    $raw | ForEach-Object {
        if ($_ -is [System.Management.Automation.ErrorRecord]) {
            $stderrParts += $_.ToString()
        } else {
            $stdoutParts += [string]$_
        }
    }

    $stdout = ($stdoutParts -join "`n").Trim()
    $stderr = ($stderrParts -join "`n").Trim()
    $textParts = @()
    if (-not [string]::IsNullOrWhiteSpace($stdout)) {
        $textParts += $stdout
    }
    if (-not [string]::IsNullOrWhiteSpace($stderr)) {
        $textParts += $stderr
    }

    return [pscustomobject]@{
        exitCode = $exitCode
        stdout = $stdout
        stderr = $stderr
        text = ($textParts -join "`n").Trim()
    }
}

function Invoke-AgbrowseJson($arguments, $stage) {
    $native = Invoke-AgbrowseNative $arguments
    if ($native.exitCode -ne 0) {
        Write-AccelerateLog ($stage + "_failed exitCode=" + $native.exitCode + " output=" + $native.text.Substring(0, [Math]::Min(1200, $native.text.Length)))
        exit $native.exitCode
    }
    $jsonText = $native.stdout
    if ([string]::IsNullOrWhiteSpace($jsonText)) {
        $jsonText = $native.text
    }
    return Convert-AgbrowseJson $jsonText $stage
}

function Set-HeartbeatSoon($automationId, [int]$wakeDelaySeconds, [string]$heartbeatRruleHelper) {
    if ([string]::IsNullOrWhiteSpace($heartbeatRruleHelper)) {
        throw "heartbeatRruleHelper missing from watcher config."
    }
    if (-not (Test-Path -LiteralPath $heartbeatRruleHelper)) {
        throw "Missing heartbeat RRULE helper: $heartbeatRruleHelper"
    }
    $raw = & powershell -NoProfile -ExecutionPolicy Bypass -File $heartbeatRruleHelper -AutomationId $automationId -DelaySeconds $wakeDelaySeconds -Apply 2>&1
    $exitCode = $LASTEXITCODE
    $text = ($raw | Out-String).Trim()
    if ($exitCode -ne 0) {
        throw "heartbeat RRULE helper failed exitCode=$exitCode output=$text"
    }
    $result = $text | ConvertFrom-Json
    return [pscustomobject]@{
        toml = $result.toml
        targetKst = $result.targetLocal
        rawDtstart = $result.rawDtstart
    }
}

$script:Config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json

try {
    Write-AccelerateLog ("watch_start sessionId=" + $script:Config.sessionId + " automationId=" + $script:Config.automationId)
    $watch = Invoke-AgbrowseNative @("web-ai", "watch", "--session", $script:Config.sessionId, "--json", "--navigate")
    Set-Content -LiteralPath $script:Config.watchLog -Value $watch.text -Encoding UTF8
    if ($watch.exitCode -ne 0) {
        Write-AccelerateLog ("watch_failed exitCode=" + $watch.exitCode + " output=" + $watch.text.Substring(0, [Math]::Min(1200, $watch.text.Length)))
        exit $watch.exitCode
    }

    $maxWaitSeconds = 1200
    if ($script:Config.PSObject.Properties.Name -contains "maxWaitSeconds") {
        $maxWaitSeconds = [int]$script:Config.maxWaitSeconds
    }
    if ($maxWaitSeconds -lt ([int]$script:Config.stabilitySeconds)) {
        $maxWaitSeconds = [int]$script:Config.stabilitySeconds
    }
    $deadline = (Get-Date).AddSeconds($maxWaitSeconds)
    $attempt = 0

    while ($true) {
        $attempt += 1
        $resume = Invoke-AgbrowseJson @("web-ai", "sessions", "resume", $script:Config.sessionId, "--allow-copy-markdown-fallback", "--timeout", ([string]$script:Config.resumeTimeoutSeconds), "--json") "sessions.resume"
        $resumeAnswer = Get-SessionAnswer $resume

        $show1 = Invoke-AgbrowseJson @("web-ai", "sessions", "show", $script:Config.sessionId, "--json") "sessions.show.stability1"
        Start-Sleep -Seconds ([int]$script:Config.stabilitySeconds)
        $show2 = Invoke-AgbrowseJson @("web-ai", "sessions", "show", $script:Config.sessionId, "--json") "sessions.show.stability2"
        $answer1 = Get-SessionAnswer $show1
        $answer2 = Get-SessionAnswer $show2

        $answer = $answer2
        $answerSource = "stability2"
        if ($resumeAnswer.Length -gt $answer.Length) {
            $answer = $resumeAnswer
            $answerSource = "resume"
        }

        $session = Get-SessionData $show2
        $status = ""
        $completedAt = $null
        if ($null -ne $session) {
            if ($session.PSObject.Properties.Name -contains "status") {
                $status = [string]$session.status
            }
            if ($session.PSObject.Properties.Name -contains "completedAt") {
                $completedAt = $session.completedAt
            }
        }

        $answer1Hash = Get-TextSha256 $answer1
        $answer2Hash = Get-TextSha256 $answer2
        $answerHash = Get-TextSha256 $answer
        $providerComplete = ($status -eq "complete" -and $null -ne $completedAt)
        $stable = ($answerHash -eq $answer1Hash -and $answerHash -eq $answer2Hash)
        $substantive = ($answer.Length -ge ([int]$script:Config.minAnswerChars))

        if ($providerComplete -and $stable -and $substantive) {
            Write-AcceleratedResult ([pscustomobject]@{
                ok = $true
                action = "watch-accelerate"
                status = "accelerated_final"
                sessionId = $script:Config.sessionId
                automationId = $script:Config.automationId
                providerStatus = $status
                completedAt = $completedAt
                stable = $stable
                answerHashStable = $stable
                substantive = $substantive
                answerLength = $answer.Length
                answerSource = $answerSource
                answerHashSha256 = $answerHash
                minAnswerChars = [int]$script:Config.minAnswerChars
                stabilitySeconds = [int]$script:Config.stabilitySeconds
                attempt = $attempt
                answerText = $answer
            })
            $result = Set-HeartbeatSoon $script:Config.automationId ([int]$script:Config.wakeDelaySeconds) ([string]$script:Config.heartbeatRruleHelper)
            Write-AccelerateLog ("accelerated attempt=" + $attempt + " status=" + $status + " completedAt=" + $completedAt + " answerLength=" + $answer.Length + " answerSource=" + $answerSource + " stable=" + $stable + " minAnswerChars=" + $script:Config.minAnswerChars + " stabilitySeconds=" + $script:Config.stabilitySeconds + " result=" + $script:Config.acceleratedResult + " target_kst=" + $result.targetKst + " raw_dtstart=" + $result.rawDtstart + " toml=" + $result.toml)
            exit 0
        }

        $reasonParts = @()
        if (-not $providerComplete) {
            $reasonParts += "provider_not_complete"
        }
        if (-not $stable) {
            $reasonParts += "text_not_stable"
        }
        if (-not $substantive) {
            $reasonParts += "too_short"
        }
        if ($reasonParts.Count -eq 0) {
            $reasonParts += "gate_not_met"
        }

        $remainingSeconds = [int][Math]::Ceiling(($deadline - (Get-Date)).TotalSeconds)
        if ($remainingSeconds -le 0) {
            Write-AccelerateLog ("not_accelerated_timeout attempt=" + $attempt + " reasons=" + ($reasonParts -join ",") + " status=" + $status + " completedAt=" + $completedAt + " providerComplete=" + $providerComplete + " stable=" + $stable + " substantive=" + $substantive + " answerLength=" + $answer.Length + " answerSource=" + $answerSource + " minAnswerChars=" + $script:Config.minAnswerChars + " stabilitySeconds=" + $script:Config.stabilitySeconds + " maxWaitSeconds=" + $maxWaitSeconds + " resumeLength=" + $resumeAnswer.Length + " show1Length=" + $answer1.Length + " show2Length=" + $answer2.Length)
            exit 0
        }

        $retrySeconds = [Math]::Min([int]$script:Config.stabilitySeconds, $remainingSeconds)
        Write-AccelerateLog ("not_ready_retry attempt=" + $attempt + " reasons=" + ($reasonParts -join ",") + " status=" + $status + " completedAt=" + $completedAt + " providerComplete=" + $providerComplete + " stable=" + $stable + " substantive=" + $substantive + " answerLength=" + $answer.Length + " answerSource=" + $answerSource + " minAnswerChars=" + $script:Config.minAnswerChars + " stabilitySeconds=" + $script:Config.stabilitySeconds + " retrySeconds=" + $retrySeconds + " remainingSeconds=" + $remainingSeconds + " resumeLength=" + $resumeAnswer.Length + " show1Length=" + $answer1.Length + " show2Length=" + $answer2.Length)
        Start-Sleep -Seconds $retrySeconds
    }
} catch {
    try {
        Write-AccelerateLog ("ERROR " + $_.Exception.Message)
    } catch {}
    exit 1
}
'@
    Set-Content -LiteralPath $workerPath -Value $workerScript -Encoding UTF8
    $process = Start-Process powershell -WindowStyle Hidden -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $workerPath, "-ConfigPath", $configPath) -PassThru
    return [pscustomobject]@{
        watcher = $process
        workerScript = $workerPath
        configPath = $configPath
        watchLog = $watchLog
        accelerateLog = $accelerateLog
        acceleratedResult = $acceleratedResult
    }
}

if ($Action -eq "watch-accelerate") {
    $watch = Start-AcceleratingWatch $SessionId $AutomationId $WatchLog $AccelerateLog $WakeDelaySeconds $MinAnswerChars $StabilitySeconds $ResumeTimeoutSeconds
    Write-Json ([pscustomobject]@{
        ok = $true
        action = "watch-accelerate"
        status = "accelerating_watch_started"
        sessionId = $SessionId
        automationId = $AutomationId
        minAnswerChars = $MinAnswerChars
        stabilitySeconds = $StabilitySeconds
        maxWaitSeconds = 1200
        resumeTimeoutSeconds = $ResumeTimeoutSeconds
        stabilityGate = "provider_complete_and_completedAt_and_min_chars_and_hash_stable"
        wakeDelaySeconds = $WakeDelaySeconds
        watchLog = $watch.watchLog
        accelerateLog = $watch.accelerateLog
        acceleratedResult = $watch.acceleratedResult
        workerScript = $watch.workerScript
        configPath = $watch.configPath
        watcherPid = $watch.watcher.Id
        watcherRunning = (-not $watch.watcher.HasExited)
        next = "Keep the official fallback heartbeat active. The watcher keeps polling until provider complete, completedAt, min chars, and stable text hash pass or the 20-minute fallback window expires. Heartbeat collect commands should include -MinAgeMinutes 0."
    })
    exit 0
}

if ($Action -eq "send") {
    if ([string]::IsNullOrWhiteSpace($Prompt)) {
        throw "-Prompt is required when -Action send."
    }

    $attachmentRoute = Resolve-AttachmentRoute $File $DirectFile $ExecutedEvidenceFile $RepoRoot $MaxDirectFiles
    $sendArgs = @(
        "web-ai", "send",
        "--vendor", "chatgpt",
        "--model", "pro",
        "--effort", "extended",
        "--prompt", $Prompt,
        "--json"
    )
    if (-not [string]::IsNullOrWhiteSpace($SystemPrompt)) {
        $sendArgs += @("--system", $SystemPrompt)
    }

    if (-not $ReuseTab) {
        $sendArgs += "--new-tab"
    }

    if ($attachmentRoute.uploadPaths.Count -gt 0) {
        foreach ($path in $attachmentRoute.uploadPaths) {
            $sendArgs += @("--file", $path)
        }
    } elseif (-not [string]::IsNullOrWhiteSpace($ContextFromFiles)) {
        $sendArgs += @("--context-from-files", $ContextFromFiles)
        foreach ($exclude in ($ContextExclude | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })) {
            $sendArgs += @("--context-exclude", $exclude)
        }
        $sendArgs += @("--context-transport", $ContextTransport)
    } else {
        $sendArgs += "--inline-only"
    }

    $send = Invoke-AgbrowseJson $sendArgs "send"

    $sid = [string]$send.sessionId
    if ([string]::IsNullOrWhiteSpace($sid)) {
        throw "agbrowse send did not return sessionId."
    }

    $sendClickUnresolved = $false
    if ($send.PSObject.Properties.Name -contains "trace") {
        foreach ($step in $send.trace) {
            if ($step.intentId -eq "send.click" -and ($step.status -eq "unresolved" -or $step.errorCode -eq "TARGET_UNRESOLVED")) {
                $sendClickUnresolved = $true
            }
        }
    }
    if ($sendClickUnresolved) {
        Write-Json ([pscustomobject]@{
            ok = $false
            action = "send"
            status = "sent_status_but_send_click_unverified"
            sessionId = $sid
            send = $send
            next = "Inspect the visible ChatGPT tab or run agbrowse web-ai sessions show $sid --json before starting a normal review watch."
        })
        exit 2
    }

    if ([string]::IsNullOrWhiteSpace($WatchLog)) {
        $WatchLog = Get-DefaultWatchLog $sid
    }
    $urlProbe = Wait-SettledConversationUrl $sid $send $UrlSettleSeconds $UrlSettlePollSeconds
    $attachmentEvidence = Test-SentTurnAttachments (Get-TargetId $send) $attachmentRoute.uploadPaths
    if (-not $attachmentEvidence.ok) {
        Write-Json ([pscustomobject]@{
            ok = $false
            action = "send"
            status = "provider_attachment_mismatch"
            providerSendStatus = "sent"
            sessionId = $sid
            targetId = Get-TargetId $send
            conversationUrl = $urlProbe.conversationUrl
            conversationUrlStatus = $urlProbe.status
            urlCapture = $urlProbe
            attachmentEvidence = $attachmentEvidence
            contextBundle = $attachmentRoute.contextBundle
            warnings = $send.warnings
            next = "Do not watch or collect this turn as a valid review. Inspect the sent turn and resend once with a smaller direct set plus one context bundle."
        })
        exit 2
    }
    if ($NoWatch) {
        Write-Json ([pscustomobject]@{
            ok = $true
            action = "send"
            status = "sent_for_heartbeat_collect"
            providerSendStatus = "sent"
            sessionId = $sid
            conversationUrl = $urlProbe.conversationUrl
            conversationUrlStatus = $urlProbe.status
            conversationUrlSource = $urlProbe.source
            urlProbe = $urlProbe
            urlCapture = $urlProbe
            url = $send.url
            targetId = Get-TargetId $send
            attachmentEvidence = $attachmentEvidence
            directFiles = $attachmentRoute.directFiles
            contextBundle = $attachmentRoute.contextBundle
            watchLog = $WatchLog
            watchCommand = "powershell -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Action watch-accelerate -SessionId $sid -AutomationId <automationId>"
            watcherPid = $null
            watcherRunning = $false
            modelSelection = $send.modelSelection
            effortSelection = $send.effortSelection
            warnings = $send.warnings
            collectCommand = ("powershell -ExecutionPolicy Bypass -File `"" + $PSCommandPath + "`" -Action collect -SessionId " + $sid + " -MinAgeMinutes 0")
            next = "Create or update a one-shot Codex heartbeat fallback, then optionally start watch-accelerate with that automationId."
        })
        exit 0
    }

    $watchLog = $WatchLog
    try {
        $watch = Start-BackgroundWatch $sid $watchLog
        $watcher = $watch.watcher
        $watchCommand = $watch.command
    } catch {
        Write-Json ([pscustomobject]@{
            ok = $false
            action = "send"
            status = "sent_but_unmonitored"
            providerSendStatus = "sent"
            sessionId = $sid
            conversationUrl = $urlProbe.conversationUrl
            conversationUrlStatus = $urlProbe.status
            conversationUrlSource = $urlProbe.source
            urlProbe = $urlProbe
            urlCapture = $urlProbe
            url = $send.url
            targetId = Get-TargetId $send
            attachmentEvidence = $attachmentEvidence
            directFiles = $attachmentRoute.directFiles
            contextBundle = $attachmentRoute.contextBundle
            watchLog = $watchLog
            watchCommand = "agbrowse web-ai watch --session $sid --json --navigate *> `"$watchLog`""
            error = [string]$_
            next = "Start the watch command manually or collect by sessionId before sending duplicates."
        })
        exit 2
    }

    Write-Json ([pscustomobject]@{
        ok = $true
        action = "send"
        status = "sent_and_watched"
        providerSendStatus = "sent"
        sessionId = $sid
        conversationUrl = $urlProbe.conversationUrl
        conversationUrlStatus = $urlProbe.status
        conversationUrlSource = $urlProbe.source
        urlProbe = $urlProbe
        urlCapture = $urlProbe
        url = $send.url
        targetId = Get-TargetId $send
        attachmentEvidence = $attachmentEvidence
        directFiles = $attachmentRoute.directFiles
        contextBundle = $attachmentRoute.contextBundle
        watchLog = $watchLog
        watchCommand = $watchCommand
        watcherPid = $watcher.Id
        watcherRunning = (-not $watcher.HasExited)
        modelSelection = $send.modelSelection
        effortSelection = $send.effortSelection
        warnings = $send.warnings
        collectCommand = ("powershell -ExecutionPolicy Bypass -File `"" + $PSCommandPath + "`" -Action collect -SessionId " + $sid)
    })
    exit 0
}

if ($Action -eq "collect") {
    if ([string]::IsNullOrWhiteSpace($SessionId)) {
        throw "-SessionId is required when -Action collect."
    }

    $showInitial = Invoke-AgbrowseJson @("web-ai", "sessions", "show", $SessionId, "--json") "sessions.show.initial"
    $sessionInitial = Get-SessionData $showInitial

    $ageMinutes = $null
    if ($null -ne $sessionInitial -and $sessionInitial.PSObject.Properties.Name -contains "createdAt") {
        $createdAt = [DateTime]::Parse([string]$sessionInitial.createdAt).ToUniversalTime()
        $ageMinutes = ([DateTime]::UtcNow - $createdAt).TotalMinutes
    }

    if (-not $Force -and $null -ne $ageMinutes -and $ageMinutes -lt $MinAgeMinutes) {
        $answer = Get-SessionAnswer $showInitial
        Write-Json ([pscustomobject]@{
            ok = $true
            action = "collect"
            status = "too_early_for_pro_review"
            sessionId = $SessionId
            ageMinutes = [Math]::Round($ageMinutes, 2)
            minAgeMinutes = $MinAgeMinutes
            answerLength = $answer.Length
            next = "Leave the watcher running and collect later. Do not send a follow-up for a short preamble."
        })
        exit 0
    }

    $resume = Invoke-AgbrowseJson @("web-ai", "sessions", "resume", $SessionId, "--allow-copy-markdown-fallback", "--timeout", $ResumeTimeoutSeconds, "--json") "sessions.resume"
    $resumeAnswer = Get-SessionAnswer $resume

    $show1 = Invoke-AgbrowseJson @("web-ai", "sessions", "show", $SessionId, "--json") "sessions.show.stability1"
    Start-Sleep -Seconds $StabilitySeconds
    $show2 = Invoke-AgbrowseJson @("web-ai", "sessions", "show", $SessionId, "--json") "sessions.show.stability2"
    $session2 = Get-SessionData $show2
    $answer1 = Get-SessionAnswer $show1
    $answer2 = Get-SessionAnswer $show2

    $answer = $answer2
    $answerSource = "stability2"
    if ($resumeAnswer.Length -gt $answer.Length) {
        $answer = $resumeAnswer
        $answerSource = "resume"
    }

    $status = ""
    $completedAt = $null
    if ($null -ne $session2) {
        if ($session2.PSObject.Properties.Name -contains "status") {
            $status = [string]$session2.status
        }
        if ($session2.PSObject.Properties.Name -contains "completedAt") {
        $completedAt = $session2.completedAt
        }
    }
    $targetId = Get-TargetId $show2
    if ([string]::IsNullOrWhiteSpace($targetId)) {
        $targetId = Get-TargetId $resume
    }

    $answer1Hash = Get-TextSha256 $answer1
    $answer2Hash = Get-TextSha256 $answer2
    $answerHash = Get-TextSha256 $answer
    $stable = ($answerHash -eq $answer1Hash -and $answerHash -eq $answer2Hash)
    $substantive = ($answer.Length -ge $MinAnswerChars)
    $complete = ($status -eq "complete" -and $null -ne $completedAt -and $stable -and $substantive)

    $resultStatus = "complete"
    if (-not $complete) {
        $resultStatus = "preamble_or_incomplete"
    }

    $tabCloseStatus = "not_requested"
    $tabClose = $null
    $tabCloseError = $null
    if ($complete -and $CloseTabOnComplete) {
        if ([string]::IsNullOrWhiteSpace($targetId)) {
            $tabCloseStatus = "no_target_id"
        } else {
            try {
                $closeRaw = & agbrowse tab-close $targetId --json 2>&1
                $closeExitCode = $LASTEXITCODE
                $closeText = ($closeRaw | Out-String).Trim()
                if ($closeExitCode -eq 0) {
                    $tabClose = Convert-AgbrowseJson $closeText "tab-close"
                    $tabCloseStatus = "closed"
                } else {
                    $tabCloseStatus = "close_failed"
                    $tabCloseError = $closeText.Substring(0, [Math]::Min(1200, $closeText.Length))
                }
            } catch {
                $tabCloseStatus = "close_failed"
                $tabCloseError = [string]$_
            }
        }
    }

    Write-Json ([pscustomobject]@{
        ok = $true
        action = "collect"
        status = $resultStatus
        sessionId = $SessionId
        targetId = $targetId
        ageMinutes = $(if ($null -eq $ageMinutes) { $null } else { [Math]::Round($ageMinutes, 2) })
        providerStatus = $status
        completedAt = $completedAt
        stable = $stable
        answerHashStable = $stable
        answerSource = $answerSource
        answerHashSha256 = $(if ($complete) { $answerHash } else { $null })
        substantive = $substantive
        answerLength = $answer.Length
        answerText = $(if ($complete) { $answer } else { $null })
        tabCloseStatus = $tabCloseStatus
        tabClose = $tabClose
        tabCloseError = $tabCloseError
        closeCommand = $(if ($complete -and -not [string]::IsNullOrWhiteSpace($targetId) -and -not $CloseTabOnComplete) { "agbrowse tab-close $targetId --json" } else { $null })
        next = $(if ($complete) { "Use answerText as ChatGPT Pro's final review. Close the tab if no follow-up is needed." } else { "Do not treat this as final. Keep the watcher/session for later collection or ask the user before forcing a follow-up." })
    })
}
