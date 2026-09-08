# media-ingest.ps1 — Route files from a drop/inbox folder into Media/ by type.
# Non-destructive: never overwrites; name conflicts get a _copyN suffix.
# Usage:
#   .\Scripts\Automation\media-ingest.ps1 -Inbox .\Media\Inbox
#   .\Scripts\Automation\media-ingest.ps1 -Inbox .\Downloads -DryRun
param(
    [string]$Inbox = (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "Media\Inbox"),
    [switch]$DryRun,
    [string]$MediaRoot = (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "Media")
)

$rules = @{
    ".mp4" = "Video"; ".mov" = "Video"; ".mkv" = "Video"; ".avi" = "Video"; ".webm" = "Video"
    ".mp3" = "Audio"; ".wav" = "Audio"; ".flac" = "Audio"; ".m4a" = "Audio"; ".ogg" = "Audio"
    ".jpg" = "Images"; ".jpeg" = "Images"; ".png" = "Images"; ".gif" = "Images"; ".webp" = "Images"; ".bmp" = "Images"
}

if (-not (Test-Path -LiteralPath $Inbox)) {
    Write-Warning "Inbox does not exist: $Inbox"
    exit 1
}

Write-Output ("Ingesting: {0}  ->  {1}  (DryRun={2})" -f $Inbox, $MediaRoot, $DryRun)
Write-Output ""

$moved = 0
Get-ChildItem -LiteralPath $Inbox -File -ErrorAction SilentlyContinue | ForEach-Object {
    $ext = $_.Extension.ToLower()
    $kind = if ($rules.ContainsKey($ext)) { $rules[$ext] } else { "Other" }
    $target = Join-Path $MediaRoot $kind
    $dest = Join-Path $target $_.Name
    $i = 1
    while (Test-Path -LiteralPath $dest) {
        $dest = Join-Path $target ("{0}_copy{1}{2}" -f $_.BaseName, $i, $_.Extension)
        $i++
    }

    if ($DryRun) {
        Write-Output " [dry] $($_.Name) -> $kind"
    } else {
        New-Item -ItemType Directory -Path $target -Force | Out-Null
        Move-Item -LiteralPath $_.FullName -Destination $dest
        Write-Output " moved $($_.Name) -> $kind"
    }
    $script:moved++
}

Write-Output ""
Write-Output "Done. $moved file(s) processed."