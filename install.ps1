# One-shot setup: makes `nex` runnable as a bare command in PowerShell on
# this machine, persisted across sessions via the PowerShell profile.
#
# Usage (run from the folder containing nex.py):
#   powershell -ExecutionPolicy Bypass -File .\install.ps1

$here = (Get-Location).Path
$nexPath = Join-Path $here "nex.py"

if (-not (Test-Path $nexPath)) {
    Write-Host "nex.py not found in $here -- run this script from the nex project folder."
    exit 1
}

if (-not (Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force | Out-Null
}

$funcLine = "function nex { python `"$nexPath`" @args }"

$existing = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
if ($existing -notmatch [regex]::Escape($nexPath)) {
    Add-Content -Path $PROFILE -Value "`n$funcLine"
    Write-Host "Added 'nex' function to your PowerShell profile: $PROFILE"
} else {
    Write-Host "'nex' function already present in your profile."
}

Write-Host "Restart PowerShell (or run '. `$PROFILE') then try:  nex --help"