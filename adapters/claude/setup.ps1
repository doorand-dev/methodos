# methodos -- Claude adapter for the distributed-gate harness
#
# Usage:
#   ./setup.ps1 -Global                # install to ~/.claude/ (skills + agents + hook)
#   ./setup.ps1 -Local <project path>  # install to <project>/.claude/ (skills + agent guides; hooks Global-only)
#   ./setup.ps1 -DryRun -Global        # preview without copying
#
# Installs (distributed gates -- NO central router):
#   Skills:
#     - using-methodos/SKILL.md  (passive umbrella meta-skill -- orientation only, NOT a router)
#     - grill-me/SKILL.md        (spec gate)
#     - plan/SKILL.md
#     - impl/SKILL.md
#     - plan-verify/SKILL.md
#     - impl-verify/SKILL.md
#     - context-novelist/SKILL.md
#   (also removes stale v1 skills/methodos/ router if present)
#   Agents (-Global only -- reviewer + novelist agents need ~/.claude/agents/):
#     - decision-reviewer.md
#     - plan-verify-reviewer.md
#     - impl-verify-reviewer.md
#     - spec-novelist.md      (narrative-dry-run #2)
#     - impl-novelist.md      (narrative-dry-run #4)
#   Hooks (-Global only):
#     - delegation-enforcer.py -> ~/.claude/hooks/ ; PreToolUse(Agent) merge (Agent model integrity)
#     - evidence_check.py      -> ~/.claude/hooks/ ; PostToolUse(Edit|Write) merge (verify-report hedging advisory)
#   Reference docs (one level above skills/):
#     - SKILL-ARTIFACTS.md
#     - narrative-dry-run.md  (narrative-dry-run lens)

param(
    [switch]$Global,
    [string]$Local,
    [switch]$DryRun
)

$adapterRoot = $PSScriptRoot
$packageRoot = (Resolve-Path (Join-Path $adapterRoot "..\..")).Path
$skillsSrc = Join-Path $packageRoot "skills"
$contractSrc = Join-Path $packageRoot "contract"
$agentsSrcDir = Join-Path $packageRoot "agents\claude"
$commonHooksSrcDir = Join-Path $packageRoot "hooks\common"
$claudeHooksSrcDir = Join-Path $packageRoot "hooks\claude"

if ($Global -and $Local) {
    Write-Error "Cannot specify both -Global and -Local"
    exit 1
}
if (-not $Global -and -not $Local) {
    Write-Error "Specify one of: -Global, -Local <project path>"
    exit 1
}

if ($Global) {
    $rootTarget = Join-Path $HOME ".claude"
} else {
    if (-not (Test-Path $Local)) {
        Write-Error "Project path not found: $Local"
        exit 1
    }
    $rootTarget = Join-Path $Local ".claude"
}

$skillsTarget = Join-Path $rootTarget "skills"
$artifactTarget = $rootTarget
$agentsTarget = Join-Path $rootTarget "agents"
$hooksTarget = Join-Path $rootTarget "hooks"
$settingsPath = Join-Path $rootTarget "settings.json"

Write-Host "Install target:" -ForegroundColor Cyan
Write-Host "  root: $rootTarget"
if ($Global) {
    Write-Host "  (Global mode: agents + hook + settings.json patch enabled)"
} else {
    Write-Host "  (Local mode: skills + artifact guide only; agents/hook are Global-only)"
}
Write-Host ""

$skills = @("grill-me", "plan", "impl", "plan-verify", "impl-verify", "context-novelist")
$copied = @()

# 1. using-methodos meta-skill (umbrella orientation -- NOT a router)
$gpSrc = Join-Path $skillsSrc "using-methodos\SKILL.md"
$gpDst = Join-Path $skillsTarget "using-methodos\SKILL.md"
Write-Host "using-methodos/SKILL.md -> $gpDst"
if (-not $DryRun) {
    New-Item -ItemType Directory -Path (Split-Path $gpDst) -Force | Out-Null
    Copy-Item $gpSrc $gpDst -Force
    $copied += "using-methodos/SKILL.md"
}

# 1b. Remove stale v1 router skill (skills/methodos/) if present.
$staleRouter = Join-Path $skillsTarget "methodos"
if (Test-Path $staleRouter) {
    Write-Host "removing stale v1 router skill -> $staleRouter" -ForegroundColor Yellow
    if (-not $DryRun) {
        Remove-Item $staleRouter -Recurse -Force
        $copied += "(removed) skills/methodos (v1 router)"
    }
}

# 2. Gate skills
foreach ($s in $skills) {
    $srcSkill = Join-Path $skillsSrc "$s\SKILL.md"
    $dstSkill = Join-Path $skillsTarget "$s\SKILL.md"
    Write-Host "$s/SKILL.md -> $dstSkill"
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path (Split-Path $dstSkill) -Force | Out-Null
        Copy-Item $srcSkill $dstSkill -Force
        $copied += "$s/SKILL.md"
    }
}

# 3. Reference docs (SKILL-ARTIFACTS.md + narrative-dry-run.md)
$refDocs = @("SKILL-ARTIFACTS.md", "narrative-dry-run.md")
foreach ($doc in $refDocs) {
    $docSrc = Join-Path $contractSrc $doc
    $docDst = Join-Path $artifactTarget $doc
    Write-Host "$doc -> $docDst"
    if (-not $DryRun) {
        New-Item -ItemType Directory -Path $artifactTarget -Force | Out-Null
        Copy-Item $docSrc $docDst -Force
        $copied += $doc
    }
}

# 4. Agents (Global-only)
if ($Global) {
    if (Test-Path $agentsSrcDir) {
        $agentFiles = Get-ChildItem -Path $agentsSrcDir -Filter "*.md"
        foreach ($a in $agentFiles) {
            $dstAgent = Join-Path $agentsTarget $a.Name
            Write-Host "agents/$($a.Name) -> $dstAgent"
            if (-not $DryRun) {
                New-Item -ItemType Directory -Path $agentsTarget -Force | Out-Null
                Copy-Item $a.FullName $dstAgent -Force
                $copied += "agents/$($a.Name)"
            }
        }
    }

    # 5. Hook scripts (delegation-enforcer = Agent model; evidence_check = verify-report hedging)
    $delegationDst = Join-Path $hooksTarget "delegation-enforcer.py"
    $evidenceDst = Join-Path $hooksTarget "evidence_check.py"
    foreach ($hf in @("delegation-enforcer.py", "evidence_check.py")) {
        if ($hf -eq "delegation-enforcer.py") {
            $hookSrc = Join-Path $claudeHooksSrcDir $hf
        } else {
            $hookSrc = Join-Path $commonHooksSrcDir $hf
        }
        $hookDst2 = Join-Path $hooksTarget $hf
        Write-Host "hooks/$hf -> $hookDst2"
        if (-not $DryRun) {
            New-Item -ItemType Directory -Path $hooksTarget -Force | Out-Null
            Copy-Item $hookSrc $hookDst2 -Force
            $copied += "hooks/$hf"
        }
    }

    # 6. settings.json patch (idempotent merge of PreToolUse Agent hook)
    Write-Host "settings.json patch -> $settingsPath"
    if (-not $DryRun) {
        $hookCommand = "py"
        $hookArgs = @("-3", $delegationDst)
        $hookEntry = [PSCustomObject]@{
            type    = "command"
            command = $hookCommand
            args    = $hookArgs
        }
        $matcherEntry = [PSCustomObject]@{
            matcher = "Agent"
            hooks   = @($hookEntry)
        }

        if (Test-Path $settingsPath) {
            try {
                $settings = Get-Content $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
            } catch {
                Write-Warning "settings.json parse failed; skipping patch. Manual review needed."
                $settings = $null
            }
        } else {
            $settings = [PSCustomObject]@{}
        }

        if ($settings -ne $null) {
            if (-not ($settings.PSObject.Properties.Name -contains "hooks")) {
                $settings | Add-Member -NotePropertyName "hooks" -NotePropertyValue ([PSCustomObject]@{})
            }
            if (-not ($settings.hooks.PSObject.Properties.Name -contains "PreToolUse")) {
                $settings.hooks | Add-Member -NotePropertyName "PreToolUse" -NotePropertyValue @()
            }

            # Idempotent check -- skip if delegation-enforcer is already registered.
            # delegation-enforcer is now the single canonical Agent-model hook
            # (hybrid inject-on-omit + block-on-omit; the old standalone
            # block_agent_no_model.py was merged into it and retired).
            $alreadyPresent = $false
            foreach ($m in $settings.hooks.PreToolUse) {
                if ($m.matcher -eq "Agent" -and $m.hooks) {
                    foreach ($h in $m.hooks) {
                        $sig = "$($h.command) $($h.args -join ' ')"
                        if ($sig -like "*delegation-enforcer.py*") {
                            $alreadyPresent = $true; break
                        }
                    }
                }
                if ($alreadyPresent) { break }
            }

            if ($alreadyPresent) {
                Write-Host "  (skip Agent hook: already registered)" -ForegroundColor DarkGray
            } else {
                $settings.hooks.PreToolUse = @($settings.hooks.PreToolUse) + @($matcherEntry)
                $json = $settings | ConvertTo-Json -Depth 16
                # UTF8 without BOM (avoid PowerShell 5.1 default UTF8-BOM)
                $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
                [System.IO.File]::WriteAllText($settingsPath, $json, $utf8NoBom)
                $copied += "settings.json (PreToolUse Agent registered)"
            }
        }
    }

    # 6b. settings.json patch (idempotent merge of PostToolUse Edit|Write -> evidence_check)
    Write-Host "settings.json patch (PostToolUse evidence_check) -> $settingsPath"
    if (-not $DryRun) {
        $ecEntry = [PSCustomObject]@{
            matcher = "Edit|Write"
            hooks   = @([PSCustomObject]@{ type = "command"; command = "py"; args = @("-3", $evidenceDst) })
        }
        try {
            $s2 = Get-Content $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
        } catch {
            Write-Warning "settings.json parse failed; skipping evidence_check patch."
            $s2 = $null
        }
        if ($s2 -ne $null) {
            if (-not ($s2.PSObject.Properties.Name -contains "hooks")) {
                $s2 | Add-Member -NotePropertyName "hooks" -NotePropertyValue ([PSCustomObject]@{})
            }
            if (-not ($s2.hooks.PSObject.Properties.Name -contains "PostToolUse")) {
                $s2.hooks | Add-Member -NotePropertyName "PostToolUse" -NotePropertyValue @()
            }
            $ecPresent = $false
            foreach ($m in $s2.hooks.PostToolUse) {
                if ($m.hooks) {
                    foreach ($h in $m.hooks) {
                        $sig = "$($h.command) $($h.args -join ' ')"
                        if ($sig -like "*evidence_check.py*") { $ecPresent = $true; break }
                    }
                }
                if ($ecPresent) { break }
            }
            if ($ecPresent) {
                Write-Host "  (skip evidence_check hook: already registered)" -ForegroundColor DarkGray
            } else {
                $s2.hooks.PostToolUse = @($s2.hooks.PostToolUse) + @($ecEntry)
                $json2 = $s2 | ConvertTo-Json -Depth 16
                $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
                [System.IO.File]::WriteAllText($settingsPath, $json2, $utf8NoBom)
                $copied += "settings.json (PostToolUse evidence_check registered)"
            }
        }
    }
}

# 7. Version stamp -- write installed commit SHA so users can detect drift from upstream
$versionFile = Join-Path $skillsTarget "using-methodos\.version"
$sha = $null
try {
    $sha = (& git -C $packageRoot rev-parse HEAD 2>$null).Trim()
} catch { $sha = $null }
if (-not $sha) { $sha = "unknown (not a git checkout)" }
$stampDate = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
$stamp = "sha: $sha`ninstalled: $stampDate`nsource: methodos"
Write-Host ".version stamp -> $versionFile"
Write-Host "  sha: $sha"
if (-not $DryRun) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($versionFile, $stamp, $utf8NoBom)
    $copied += "using-methodos/.version"
}

Write-Host ""
if ($DryRun) {
    Write-Host "DryRun -- no files copied. Rerun without -DryRun to install." -ForegroundColor Yellow
} else {
    Write-Host ("Done. Copied: " + $copied.Count + " items") -ForegroundColor Green
    Write-Host ""
    Write-Host "New Claude Code sessions will auto-detect (restart open sessions)." -ForegroundColor Cyan
    if ($Global) {
        Write-Host "Hook active for Agent tool calls -- verify with: tail -f stderr during a Task call." -ForegroundColor Cyan
    }
}
