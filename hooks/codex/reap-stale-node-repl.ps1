[CmdletBinding(SupportsShouldProcess)]
param(
  [ValidateRange(0, 64)]
  [int]$MaxNodeRepl = 1
)

$ErrorActionPreference = "Stop"

$appServerPids = @(
  Get-CimInstance Win32_Process -Filter "Name='codex.exe'" |
    Where-Object { $_.CommandLine -like '* app-server*' } |
    Select-Object -ExpandProperty ProcessId
)

$nodeRepls = @(
  Get-CimInstance Win32_Process -Filter "Name='node_repl.exe'" |
    Where-Object { $_.ParentProcessId -in $appServerPids } |
    Sort-Object CreationDate -Descending
)

$targets = @($nodeRepls | Select-Object -Skip $MaxNodeRepl)
$removed = 0
foreach ($process in $targets) {
  if ($PSCmdlet.ShouldProcess(
      "node_repl.exe PID $($process.ProcessId)",
      "Stop stale Codex-owned process"
    )) {
    Stop-Process -Id $process.ProcessId -Force
    $removed++
  }
}

[pscustomobject]@{
  Found = $nodeRepls.Count
  Kept = [Math]::Min($nodeRepls.Count, $MaxNodeRepl)
  Removed = $removed
  MaxNodeRepl = $MaxNodeRepl
}
