# media-ingest-watch.ps1 — Real-time FileSystemWatcher for Media\Inbox
# Runs continuously; processes files as they land (created/renamed/moved).
# Usage: . .\env.ps1; .\media-ingest-watch.ps1
# Or run via scheduled task (at logon, runs indefinitely).
#
# Features:
# - Debounces rapid writes (e.g., large file copy) via configurable window
# - Skips partial files (size stable for N seconds)
# - Uses existing media-ingest logic (routes by extension)
# - Logs to .opencode/logs/ingest-watch.tsv
# - Graceful shutdown on Ctrl+C

param(
    [string]$Inbox = (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "Media\Inbox"),
    [string]$MediaRoot = (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "Media"),
    [int]$DebounceMs = 2000,
    [int]$StableWaitMs = 3000
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$logDir = Join-Path $root ".opencode\logs"
$logFile = Join-Path $logDir "ingest-watch.tsv"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

function Write-Log {
    param($Action, $File, $Dest = "", $Detail = "")
    $ts = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fff")
    "$ts`t$Action`t$File`t$Dest`t$Detail" | Out-File -FilePath $logFile -Append -Encoding UTF8
    Write-Host "  [$ts] $Action $File $Dest"
}

$rules = @{
    ".mp4" = "Video"; ".mov" = "Video"; ".mkv" = "Video"; ".avi" = "Video"; ".webm" = "Video"
    ".mp3" = "Audio"; ".wav" = "Audio"; ".flac" = "Audio"; ".m4a" = "Audio"; ".ogg" = "Audio"
    ".jpg" = "Images"; ".jpeg" = "Images"; ".png" = "Images"; ".gif" = "Images"; ".webp" = "Images"; ".bmp" = "Images"
}

function Process-File {
    param($src)
    if (-not (Test-Path -LiteralPath $src)) { return }
    $name = Split-Path $src -Leaf
    $ext = [IO.Path]::GetExtension($name).ToLower()
    $kind = if ($rules.ContainsKey($ext)) { $rules[$ext] } else { "Other" }
    $target = Join-Path $MediaRoot $kind
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    $dest = Join-Path $target $name
    $i = 1
    while (Test-Path -LiteralPath $dest) {
        $dest = Join-Path $target ("{0}_copy{1}{2}" -f [IO.Path]::GetFileNameWithoutExtension($name), $i, $ext)
        $i++
    }
    try {
        Move-Item -LiteralPath $src -Destination $dest -Force -ErrorAction Stop
        Write-Log "MOVE" $name $kind
    } catch {
        Write-Log "ERROR" $name "" $_.Exception.Message
    }
}

function Wait-StableSize {
    param($path)
    $last = -1
    $stable = 0
    while ($true) {
        if (-not (Test-Path -LiteralPath $path)) { return $false }
        $sz = (Get-Item -LiteralPath $path).Length
        if ($sz -eq $last) { $stable += 500 }
        else { $stable = 0; $last = $sz }
        if ($stable -ge $StableWaitMs) { return $true }
        Start-Sleep -Milliseconds 500
    }
}

Write-Host "=== ASTRA Media Ingest Watcher ==="
Write-Host "Watching: $Inbox"
Write-Host "Media root: $MediaRoot"
Write-Host "Debounce: ${DebounceMs}ms, Stable wait: ${StableWaitMs}ms"
Write-Host "Log: $logFile"
Write-Host "Press Ctrl+C to stop."
Write-Host ""

if (-not (Test-Path -LiteralPath $Inbox)) {
    New-Item -ItemType Directory -Path $Inbox -Force | Out-Null
    Write-Host "Created inbox: $Inbox"
}

# Process any existing files on startup
Write-Host "Scanning existing files..."
Get-ChildItem -LiteralPath $Inbox -File -ErrorAction SilentlyContinue | ForEach-Object {
    if (Wait-StableSize $_.FullName) { Process-File $_.FullName }
}

# FileSystemWatcher
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $Inbox
$watcher.Filter = "*.*"
$watcher.IncludeSubdirectories = $false
$watcher.EnableRaisingEvents = $true
$watcher.NotifyFilter = [IO.NotifyFilters]'FileName, LastWrite, Size'

$queue = [System.Collections.Concurrent.ConcurrentQueue[string]]::new()
$timer = $null

function Drain-Queue {
    $now = [DateTime]::Now
    $batch = @()
    while ($queue.TryDequeue([ref]$null)) { }  # clear any stale
    while ($queue.TryDequeue([ref]$file)) {
        if (Test-Path -LiteralPath $file) { $batch += $file }
    }
    foreach ($f in $batch) {
        if (Wait-StableSize $f) { Process-File $f }
    }
}

$onCreated = {
    $queue.Enqueue($Event.SourceEventArgs.FullPath)
    if (-not $timer) {
        $timer = [System.Timers.Timer]::new($DebounceMs)
        $timer.AutoReset = $false
        $timer.Elapsed += { Drain-Queue; $timer = $null }
        $timer.Start()
    }
}
$onRenamed = {
    $queue.Enqueue($Event.SourceEventArgs.FullPath)
    if (-not $timer) {
        $timer = [System.Timers.Timer]::new($DebounceMs)
        $timer.AutoReset = $false
        $timer.Elapsed += { Drain-Queue; $timer = $null }
        $timer.Start()
    }
}

Register-ObjectEvent -InputObject $watcher -EventName Created -Action $onCreated | Out-Null
Register-ObjectEvent -InputObject $watcher -EventName Renamed -Action $onRenamed | Out-Null

Write-Host "Watcher active. Waiting for files..."

# Keep alive
try {
    while ($true) { Start-Sleep -Seconds 10 }
} finally {
    Write-Host "`nShutting down watcher..."
    Unregister-Event -SourceIdentifier "Created" -ErrorAction SilentlyContinue
    Unregister-Event -SourceIdentifier "Renamed" -ErrorAction SilentlyContinue
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    Write-Host "Done."
}