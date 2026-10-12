$ErrorActionPreference = 'Stop'
$statePath = Join-Path $PSScriptRoot '.runtime-server.json'
if (-not (Test-Path -LiteralPath $statePath)) { Write-Output 'No saved server.'; exit }
$serverState = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
$serverProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($serverState.pid)"
$expectedLaunch = Join-Path $PSScriptRoot 'launch.py'
if ($serverProcess -and $serverProcess.CommandLine.Contains($expectedLaunch)) {
    Stop-Process -Id $serverState.pid
    Write-Output 'Open Genjutsu stopped.'
} elseif ($serverProcess) {
    throw 'Saved process ID belongs to another process; it was left running.'
}
Remove-Item -LiteralPath $statePath -Force
