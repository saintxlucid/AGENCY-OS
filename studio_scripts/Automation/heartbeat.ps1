# heartbeat.ps1 — Contextual daemon pulse + light maintenance sweep
# Scheduled: every ~30 min. Updates HEARTBEAT.md and runs light checks.
param(
    [double]$DiskWarnGB = 5
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent (Split-Path -Parent $here)
$hb = Join-Path $root "HEARTBEAT.md"
$now = Get-Date -Format "yyyy-MM-dd HH:mm"

# --- Light maintenance sweep ---

# 1) Ensure today's temporal log exists
& (Join-Path $here "daily-log.ps1") | Out-Null

# 2) Disk-space check on the Playground drive
$driveLetter = $root.Substring(0, 1)
$freeGB = [Math]::Round((Get-PSDrive -Name $driveLetter -ErrorAction SilentlyContinue).Free / 1GB, 2)

# 3) Stale output leftovers?
$leftovers = @()
foreach ($d in @("converted", "prores")) {
    $p = Join-Path $root $d
    if (Test-Path -LiteralPath $p) { $leftovers += $d }
}
foreach ($t in Get-ChildItem -Path $root -Directory -Filter "_Trash_*" -ErrorAction SilentlyContinue) {
    $leftovers += $t.Name
}

# --- Derive pulse state from findings ---
$drift = "None detected"
$pending = "None"
$state = "Coherent"

if ($freeGB -ne $null -and $freeGB -lt $DiskWarnGB) {
    $drift = "LOW DISK: ${freeGB} GB free on ${driveLetter}:"
    $state = "Alert"
}
if ($leftovers.Count -gt 0) {
    $pending = "Stale outputs to clear: " + ($leftovers -join ", ")
}

# --- Rewrite HEARTBEAT.md (UTF-8 safe) ---
if (Test-Path -LiteralPath $hb) {
    $enc = New-Object System.Text.UTF8Encoding($false)
    $c = [System.IO.File]::ReadAllText($hb, [System.Text.Encoding]::UTF8)
    $c = $c -replace '(?m)^\*\*Last[^-]*\*\*.*$', "**Last Beat:** $now"
    $c = $c -replace '(?m)^- \*\*State\*\*:.*$', "- **State:** $state"
    $c = $c -replace '(?m)^- \*\*Drift\*\*:.*$', "- **Drift:** $drift"
    $c = $c -replace '(?m)^- \*\*Pending Actions\*\*:.*$', "- **Pending Actions:** $pending"
    [System.IO.File]::WriteAllText($hb, $c, $enc)
}

# --- Report (visible in task history / when run manually) ---
Write-Output "HEARTBEAT $now | State=$State | Drift=$drift | Pending=$pending | Free=${freeGB} GB"