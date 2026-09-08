# daily-log.ps1 — Ensure today's temporal memory log exists
# Usage: .\Scripts\Automation\daily-log.ps1 [-Session "ASTRA PRIME"]
param(
    [string]$Session = "ASTRA PRIME"
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$memDir = Split-Path -Parent (Split-Path -Parent $here) | Join-Path -ChildPath "Memory"
$stamp = Get-Date -Format "yyyy-MM-dd"
$file = Join-Path $memDir "$stamp.md"

if (-not (Test-Path $memDir)) { New-Item -ItemType Directory -Path $memDir -Force | Out-Null }

if (-not (Test-Path -LiteralPath $file)) {
    $lines = @(
        "# Temporal Log - $stamp"
        "**Session:** $Session"
        "**Initiator:** Saint Lucid (Karim Al-Sharif)"
        "**Status:** ACTIVE"
        ""
        "## Events"
        "- $(Get-Date -Format 'HH:mm') - Daily log initialized."
        ""
        "## Notes"
    )
    Set-Content -LiteralPath $file -Value $lines -Encoding UTF8
    Write-Output "Created: $file"
} else {
    Write-Output "Exists: $file"
}