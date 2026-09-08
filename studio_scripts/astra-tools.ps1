# =============================================================================
# astra-tools.ps1 — General-Purpose Playground Toolkit (LAUNCHER)
# Usage:
#   .\Scripts\astra-tools.ps1                  -> interactive menu
#   .\Scripts\astra-tools.ps1 <command> <args> -> direct dispatch (positional)
# Commands: usage | dup | exts | rename | trash | backup | scaffold | env
# Positional args pass through in order (e.g. scaffold <Name> <Template> <Path>).
# All commands are non-destructive unless the underlying function is given
# an explicit -Commit / destructive switch.
# =============================================================================

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("menu", "usage", "dup", "exts", "rename", "trash", "backup", "scaffold", "env")]
    [string]$Command = "menu",
    [Parameter(ValueFromRemainingArguments = $true)]
    [object[]]$ToolArgs
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $here "AstraTools\AstraTools.ps1")

function Invoke-LauncherMenu {
    Write-Output @'

  ┌──────────────────────────────────────────┐
  │   A S T R A  Playground Toolkit            │
  └──────────────────────────────────────────┘

   File & Workspace
    1) usage      Folder disk usage report
    2) dup        Find duplicate files (dry-run)
    3) exts       File counts by extension
    4) rename     Batch rename (find/replace)
    5) trash      Send items to Recycle Bin

   Dev & Automation
    6) backup     Copy a folder to a dated backup
    7) scaffold   New project scaffold
    8) env        Inspect environment / PATH

   [q]  Quit
'@
    Write-Output ""
    $prompt = "  Select: "
    $choice = Read-Host $prompt
    switch ($choice) {
        "1" { $p = Read-Host "Scan path [.]"; Get-FolderUsage -Path $p; break }
        "2" { $p = Read-Host "Scan path [.]"; Find-DuplicateFiles -Path $p; break }
        "3" { $p = Read-Host "Scan path [.]"; Get-ExtensionBreakdown -Path $p; break }
        "4" {
            $p = Read-Host "Directory"
            $f = Read-Host "Find text"
            $r = Read-Host "Replace with"
            $y = Read-Host "Commit? (y/N)"
            if ($y -eq 'y') { Rename-Batch -Path $p -Find $f -Replace $r -Commit } else { Rename-Batch -Path $p -Find $f -Replace $r }
            break
        }
        "5" {
            $p = Read-Host "Items to trash (comma-separated)"
            Invoke-SafeTrash -Path ($p -split ',')
            break
        }
        "6" {
            $src = Read-Host "Source folder"
            $dst = Read-Host "Destination folder"
            Invoke-SafeBackup -Path $src -Destination $dst
            break
        }
        "7" {
            $n = Read-Host "Project name"
            New-ProjectScaffold -Name $n
            break
        }
        "8" { Show-Environment; break }
        default { Write-Output "bye." }
    }
}

if ($Command -eq "menu") {
    Invoke-LauncherMenu
    return
}

# Direct dispatch — positional passthrough
switch ($Command) {
    "usage"    { Get-FolderUsage @ToolArgs }
    "dup"      { Find-DuplicateFiles @ToolArgs }
    "exts"     { Get-ExtensionBreakdown @ToolArgs }
    "rename"   { Rename-Batch @ToolArgs }
    "trash"    { Invoke-SafeTrash @ToolArgs }
    "backup"   { Invoke-SafeBackup @ToolArgs }
    "scaffold" { New-ProjectScaffold @ToolArgs }
    "env"      { Show-Environment }
}