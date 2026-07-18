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
    [int]$MaxDirectFiles = 4,
    [string]$SessionId,
    [string]$ContextFromFiles,
    [string[]]$ContextExclude,
    [ValidateSet("upload", "inline")]
    [string]$ContextTransport = "upload",
    [switch]$ReuseTab,
    [switch]$NoWatch,
    [switch]$ApproveExternalUpload,
    [switch]$Force,
    [int]$MinAgeMinutes = 0,
    [int]$MinAnswerChars = 1500,
    [int]$ResumeTimeoutSeconds = 180,
    [int]$StabilitySeconds = 2,
    [int]$UrlSettleSeconds = 30,
    [int]$UrlSettlePollSeconds = 2,
    [string]$AutomationId,
    [int]$WakeDelaySeconds = 30,
    [string]$WatchLog,
    [string]$AccelerateLog,
    [switch]$CloseTabOnComplete
)

$ErrorActionPreference = "Stop"

function Out-Json($value) { $value | ConvertTo-Json -Depth 12 }

function Invoke-Agbrowse($arguments, [switch]$AllowFailure) {
    $raw = & agbrowse @arguments 2>&1
    $code = $LASTEXITCODE
    $text = ($raw | Out-String).Trim()
    if ($code -ne 0 -and -not $AllowFailure) { throw "agbrowse failed ($code): $text" }
    $value = $null
    if (-not [string]::IsNullOrWhiteSpace($text)) {
        try { $value = $text | ConvertFrom-Json } catch {
            $start = $text.IndexOf("{"); $end = $text.LastIndexOf("}")
            if ($start -ge 0 -and $end -gt $start) { $value = $text.Substring($start, $end - $start + 1) | ConvertFrom-Json }
        }
    }
    [pscustomobject]@{ code = $code; text = $text; value = $value }
}

function Get-Prop($object, [string[]]$names) {
    foreach ($name in $names) {
        if ($null -ne $object -and $object.PSObject.Properties.Name -contains $name -and $null -ne $object.$name) {
            $value = [string]$object.$name
            if (-not [string]::IsNullOrWhiteSpace($value)) { return $value }
        }
    }
    return $null
}

function Get-Session($object) {
    if ($null -ne $object -and $object.PSObject.Properties.Name -contains "session" -and $null -ne $object.session) { return $object.session }
    return $object
}

function Get-Answer($object) {
    $session = Get-Session $object
    $answer = Get-Prop $object @("answerText", "text", "answer")
    if ([string]::IsNullOrWhiteSpace($answer)) { $answer = Get-Prop $session @("answerText", "answer", "text") }
    return $(if ($null -eq $answer) { "" } else { $answer })
}

function Test-Sensitive([string]$path) {
    $relative = $path.Replace("\", "/")
    foreach ($segment in $relative.Split("/", [System.StringSplitOptions]::RemoveEmptyEntries)) {
        if ($segment -ieq "secrets" -or $segment -ieq ".env" -or $segment -ilike ".env.*") { return $true }
    }
    return $false
}

function Get-Files($paths) {
    $seen = @{}; $result = @()
    foreach ($item in @($paths)) {
        if ([string]::IsNullOrWhiteSpace([string]$item)) { continue }
        $full = [System.IO.Path]::GetFullPath([string]$item)
        if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { throw "Missing attachment input: $full" }
        if (Test-Sensitive $full) { throw "Sensitive input rejected: $full" }
        if (-not $seen.ContainsKey($full)) { $seen[$full] = $true; $result += $full }
    }
    return @($result)
}

function New-ContextBundle($paths, [string]$root) {
    if (@($paths).Count -eq 0) { return $null }
    Add-Type -AssemblyName System.IO.Compression
    $bundlePath = Join-Path $env:TEMP ("ask-chatgpt-pro-context-temp-" + $PID + ".zip")
    Remove-Item -LiteralPath $bundlePath -Force -ErrorAction SilentlyContinue
    $stream = [System.IO.File]::Open($bundlePath, [System.IO.FileMode]::CreateNew)
    try {
        $archive = [System.IO.Compression.ZipArchive]::new($stream, [System.IO.Compression.ZipArchiveMode]::Create)
        try {
            $items = @()
            foreach ($path in @($paths)) {
                $relative = [System.IO.Path]::GetRelativePath([System.IO.Path]::GetFullPath($root), $path).Replace("\", "/")
                $items += [pscustomobject]@{ name = $relative; size = (Get-Item -LiteralPath $path).Length; role = "context" }
                $entry = $archive.CreateEntry(("files/" + $relative))
                $input = [System.IO.File]::OpenRead($path); $output = $entry.Open()
                try { $input.CopyTo($output) } finally { $output.Dispose(); $input.Dispose() }
            }
            $manifest = [pscustomobject]@{ inputCount = $items.Count; files = $items }
            $entry = $archive.CreateEntry("MANIFEST.json"); $writer = [System.IO.StreamWriter]::new($entry.Open())
            try { $writer.Write(($manifest | ConvertTo-Json -Depth 8)) } finally { $writer.Dispose() }
        } finally { $archive.Dispose() }
    } finally { $stream.Dispose() }
    [pscustomobject]@{ path = $bundlePath; inputCount = @($paths).Count; manifest = $manifest }
}

function Resolve-Attachments($files, $directFiles, [string]$root) {
    if ($MaxDirectFiles -lt 1) { throw "-MaxDirectFiles must be at least 1" }
    $all = @(Get-Files $files); $direct = @(Get-Files $directFiles)
    foreach ($path in $direct) { if ($all -notcontains $path) { $all += $path } }
    if ($direct.Count -gt $MaxDirectFiles) { throw "Direct attachment count exceeds limit" }
    if ($direct.Count -eq 0) { $direct = @($all | Select-Object -First $MaxDirectFiles) }
    $rest = @($all | Where-Object { $direct -notcontains $_ })
    $bundle = New-ContextBundle $rest $root
    $uploads = @($direct); if ($null -ne $bundle) { $uploads += $bundle.path }
    [pscustomobject]@{ directFiles = $direct; contextBundle = $bundle; uploadPaths = $uploads }
}

function Get-Target($object) { Get-Prop (Get-Session $object) @("targetId", "tabId") }

function Get-ConversationUrl($object) {
    $session = Get-Session $object
    return Get-Prop $session @("conversationUrl", "url", "originalUrl")
}

function Wait-ConversationUrl([string]$sid, $sent) {
    $url = Get-ConversationUrl $sent
    if ($url -match "^https://chatgpt\.com/c/") { return [pscustomobject]@{ status = "captured"; conversationUrl = $url } }
    $deadline = [DateTime]::UtcNow.AddSeconds($UrlSettleSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        $show = Invoke-Agbrowse @("web-ai", "sessions", "show", $sid, "--json") -AllowFailure
        $candidate = Get-ConversationUrl $show.value
        if ($candidate -notmatch "^https://chatgpt\.com/c/") {
            $tabs = Invoke-Agbrowse @("tabs", "--json") -AllowFailure
            foreach ($tab in @($tabs.value)) {
                $tabUrl = Get-Prop $tab @("url", "conversationUrl")
                if ($tabUrl -match "^https://chatgpt\.com/c/") { $candidate = $tabUrl; break }
            }
        }
        if ($candidate -match "^https://chatgpt\.com/c/") {
            $target = Get-Target $show.value
            if (-not [string]::IsNullOrWhiteSpace($target)) { [void](Invoke-Agbrowse @("web-ai", "sessions", "reattach", $sid, $target, "--json") -AllowFailure) }
            return [pscustomobject]@{ status = "captured"; conversationUrl = $candidate }
        }
        Start-Sleep -Seconds $UrlSettlePollSeconds
    }
    [pscustomobject]@{ status = "unavailable"; conversationUrl = $null }
}

function Test-SentAttachments([string]$target, $paths) {
    $expected = @($paths | ForEach-Object { Split-Path -Leaf $_ })
    if ($expected.Count -eq 0) { return [pscustomobject]@{ ok = $true; requestedCount = 0; matchedCount = 0; missingNames = @(); requestedNames = @(); matchedNames = @() } }
    $probe = Invoke-Agbrowse @("evaluate", $target, "return {turnFound:true,attachmentNames:[]}", "--json") -AllowFailure
    $names = @(); if ($null -ne $probe.value) { $names = @($probe.value.attachmentNames) }
    $matched = @($expected | Where-Object { $names -contains $_ })
    [pscustomobject]@{ ok = ($matched.Count -eq $expected.Count); requestedCount = $expected.Count; matchedCount = $matched.Count; missingNames = @($expected | Where-Object { $matched -notcontains $_ }); requestedNames = $expected; matchedNames = $matched }
}

if ($Action -eq "watch-accelerate") {
    Out-Json ([pscustomobject]@{ ok = $false; action = $Action; status = "manual_monitoring_only"; sessionId = $SessionId; next = "Use collect explicitly when the user requests asynchronous monitoring." })
    exit 0
}

if ($Action -eq "send") {
    if ([string]::IsNullOrWhiteSpace($Prompt)) { throw "-Prompt is required when -Action send" }
    if (@($File).Count -gt 0 -and -not $ApproveExternalUpload) {
        Out-Json ([pscustomobject]@{ ok = $false; action = "send"; status = "approval_required"; next = "Confirm the external upload before sending attachments." })
        exit 2
    }
    $route = Resolve-Attachments $File $DirectFile $RepoRoot
    $args = @("web-ai", "send", "--prompt", $Prompt, "--json")
    if (-not [string]::IsNullOrWhiteSpace($SystemPrompt)) { $args += @("--system-prompt", $SystemPrompt) }
    foreach ($path in $route.uploadPaths) { $args += @("--file", $path) }
    $send = Invoke-Agbrowse $args
    $sid = Get-Prop (Get-Session $send.value) @("sessionId", "id")
    if ([string]::IsNullOrWhiteSpace($sid)) { throw "agbrowse send did not return sessionId" }
    $url = Wait-ConversationUrl $sid $send.value
    $evidence = Test-SentAttachments (Get-Target $send.value) $route.uploadPaths
    if (-not $evidence.ok) {
        Out-Json ([pscustomobject]@{ ok = $false; action = "send"; status = "provider_attachment_mismatch"; sessionId = $sid; attachmentEvidence = $evidence; conversationUrl = $url.conversationUrl })
        exit 2
    }
    Out-Json ([pscustomobject]@{ ok = $true; action = "send"; status = "sent"; sessionId = $sid; targetId = Get-Target $send.value; conversationUrl = $url.conversationUrl; conversationUrlStatus = $url.status; attachmentEvidence = $evidence; directFiles = $route.directFiles; contextBundle = $route.contextBundle; collectCommand = ("powershell -File `"$PSCommandPath`" -Action collect -SessionId " + $sid) })
    exit 0
}

if ([string]::IsNullOrWhiteSpace($SessionId)) { throw "-SessionId is required when -Action collect" }
$first = Invoke-Agbrowse @("web-ai", "sessions", "show", $SessionId, "--json")
$session1 = Get-Session $first.value
$createdAt = Get-Prop $session1 @("createdAt")
if (-not $Force -and $MinAgeMinutes -gt 0 -and $createdAt) {
    $age = ([DateTime]::UtcNow - ([DateTime]::Parse($createdAt).ToUniversalTime())).TotalMinutes
    if ($age -lt $MinAgeMinutes) { Out-Json ([pscustomobject]@{ ok = $true; action = "collect"; status = "too_early"; sessionId = $SessionId; ageMinutes = [Math]::Round($age, 2) }); exit 0 }
}
$resume = Invoke-Agbrowse @("web-ai", "sessions", "resume", $SessionId, "--timeout", $ResumeTimeoutSeconds, "--json") -AllowFailure
$show1 = Invoke-Agbrowse @("web-ai", "sessions", "show", $SessionId, "--json")
Start-Sleep -Seconds $StabilitySeconds
$show2 = Invoke-Agbrowse @("web-ai", "sessions", "show", $SessionId, "--json")
$s2 = Get-Session $show2.value
$answer1 = Get-Answer $show1.value; $answer2 = Get-Answer $show2.value; $answer = Get-Answer $resume.value
if ($answer2.Length -gt $answer.Length) { $answer = $answer2 }
$status = Get-Prop $s2 @("status"); $completedAt = Get-Prop $s2 @("completedAt")
$stable = ($answer1 -eq $answer2); $substantive = ($answer.Length -ge $MinAnswerChars)
$complete = ($status -eq "complete" -and -not [string]::IsNullOrWhiteSpace($completedAt) -and $stable -and $substantive)
Out-Json ([pscustomobject]@{ ok = $true; action = "collect"; status = $(if ($complete) { "complete" } else { "not_final" }); sessionId = $SessionId; targetId = Get-Target $show2.value; providerStatus = $status; completedAt = $completedAt; stable = $stable; substantive = $substantive; answerLength = $answer.Length; answerText = $(if ($complete) { $answer } else { $null }); next = $(if ($complete) { "Use answerText as the provider's final answer." } else { "Collect again after the provider reports completion." }) })
