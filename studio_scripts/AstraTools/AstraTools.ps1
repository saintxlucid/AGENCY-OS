# =============================================================================
# AstraTools.ps1 — General-Purpose Playground Toolkit (LIBRARY)
# Dot-source this file to load all functions:
#   . .\Scripts\AstraTools\AstraTools.ps1
# Nothing executes on import — it only defines functions.
# Non-destructive by default: destructive actions require explicit -Commit.
# =============================================================================

# -----------------------------------------------------------------------------
# FILE & WORKSPACE UTILITIES
# -----------------------------------------------------------------------------

<#
.SYNOPSIS
Report disk usage of a folder tree, summarized by immediate child, sorted desc.
#>
function Get-FolderUsage {
    [CmdletBinding()]
    param(
        [string]$Path = ".",
        [int]$Top = 10
    )
    $root = (Resolve-Path $Path -ErrorAction Stop).Path
    $rows = Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $bytes = (Get-ChildItem -LiteralPath $_.FullName -Recurse -File -Force -ErrorAction SilentlyContinue |
            Measure-Object -Property Length -Sum).Sum
        [PSCustomObject]@{ Folder = $_.Name; SizeMB = [Math]::Round($bytes / 1MB, 2) }
    }
    $rows | Sort-Object SizeMB -Descending | Select-Object -First $Top |
        Format-Table -AutoSize
}

<#
.SYNOPSIS
    Find duplicate files by content hash within a directory tree.
    Non-destructive: only reports. Use -Commit to move duplicates to a Trash dir.
.Parameter Path
    Root directory to scan.
.Parameter MinMBDuplicateThreshold
    Skip files smaller than X MB (default 0 = all).
#>
function Find-DuplicateFiles {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [double]$MinSizeMB = 0,
        [switch]$Commit
    )
    $root = (Resolve-Path $Path -ErrorAction Stop).Path
    $minBytes = $MinSizeMB * 1MB

    $files = Get-ChildItem -LiteralPath $root -Recurse -File -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Length -ge $minBytes }

    if (-not $files) { Write-Output "No files found matching the filter."; return }

    Write-Output "Hashing $($files.Count) file(s) for duplicates..."

    # Fast pipe: hash full content, group by hash, flag groups > 1.
    $hashGroups = $files | ForEach-Object {
        [PSCustomObject]@{
            File   = $_
            Hash   = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        }
    } | Group-Object Hash | Where-Object { $_.Count -gt 1 }

    $duplicates = foreach ($g in $hashGroups) {
        $canonical = $g.Group | Select-Object -First 1
        foreach ($dup in ($g.Group | Select-Object -Skip 1)) {
            [PSCustomObject]@{
                SizeMB    = [Math]::Round($dup.File.Length / 1MB, 2)
                Keep      = $canonical.File.FullName
                Duplicate = $dup.File.FullName
            }
        }
    }

    if (-not $duplicates) {
        Write-Output "No duplicates found."
        return
    }
    $duplicates | Format-Table -AutoSize
    Write-Output ("Found $($duplicates.Count) duplicate candidate(s) (keep + remove pairs).")

    if ($Commit) {
        $trash = Join-Path $root "_Trash_Duplicates"
        New-Item -ItemType Directory -Path $trash -Force | Out-Null
        foreach ($d in $duplicates) {
            $dst = Join-Path $trash ([System.IO.Path]::GetFileName($d.Duplicate))
            Move-Item -LiteralPath $d.Duplicate -Destination $dst -Force
            Write-Output "Moved -> $dst"
        }
    } else {
        Write-Output "Dry run. Re-run with -Commit to move duplicates to _Trash_Duplicates."
    }
}

<#
.SYNOPSIS
    Count files grouped by extension. Reports without modifying.
.Parameter Path
    Directory to scan.
#>
function Get-ExtensionBreakdown {
    [CmdletBinding()]
    param([string]$Path = ".")
    $root = (Resolve-Path $Path -ErrorAction Stop).Path
    Get-ChildItem -LiteralPath $root -Recurse -File -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension } |
        Group-Object Extension |
        Sort-Object Count -Descending |
        ForEach-Object {
            [PSCustomObject]@{
                Extension = $_.Name
                Count     = $_.Count
                SizeMB    = [Math]::Round((($_.Group | Measure-Object Length -Sum).Sum) / 1MB, 2)
            }
        } | Format-Table -AutoSize
}

<#
.SYNOPSIS
    Batch rename files by a simple find/replace on the filename.
    Non-destructive by default; -Commit applies changes.
.Parameter Path
    Directory containing the files.
.Parameter Find
    Text to find in the filename.
.Parameter Replace
    Replacement text (default "" = remove).
#>
function Rename-Batch {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Find,
        [string]$Replace = "",
        [switch]$Commit
    )
    $root = (Resolve-Path $Path -ErrorAction Stop).Path
    $files = Get-ChildItem -LiteralPath $root -File -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "*$Find*" }

    if (-not $files) { Write-Output "No matching files."; return }

    foreach ($f in $files) {
        $newName = $f.Name.Replace($Find, $Replace)
        if ($newName -eq $f.Name) { continue }
        $newPath = Join-Path $root $newName
        if ($Commit) {
            if (Test-Path -LiteralPath $newPath) {
                Write-Warning "Skip (exists): $newName"
                continue
            }
            Rename-Item -LiteralPath $f.FullName -NewName $newName
            Write-Output "Renamed: $($f.Name)  ->  $newName"
        } else {
            Write-Output "Would rename: $($f.Name)  ->  $newName"
        }
    }
    if (-not $Commit) { Write-Output "Dry-run. Re-run with -Commit to execute." }
}

<#
.SYNOPSIS
    Move items to the Windows Recycle Bin safely. Never permanent.
.Parameter.Path
    Items to trash (files or directories).
#>
function Invoke-SafeTrash {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
        [string[]]$Path
    )
    begin { Add-Type -AssemblyName Microsoft.VisualBasic -ErrorAction SilentlyContinue | Out-Null }
    process {
        foreach ($p in $Path) {
            if (-not (Test-Path -LiteralPath $p)) {
                Write-Warning "Not found (skip): $p"
                continue
            }
            if ((Get-Item -LiteralPath $p).PSIsContainer) {
                [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory(
                    $p, 'OnlyErrorDialogs', 'SendToRecycleBin') | Out-Null
            } else {
                [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile(
                    $p, 'OnlyErrorDialogs', 'SendToRecycleBin') | Out-Null
            }
            Write-Output "Trashed: $p"
        }
    }
}

# Backup a directory's contents into a dated archive copied to a target tree.
function Invoke-SafeBackup {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Destination
    )
    $src = (Resolve-Path $Path -ErrorAction Stop).Path
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $dest = Join-Path $Destination ("{0}_{1}" -f (Split-Path $src -Leaf), $stamp)
    New-Item -ItemType Directory -Path $dest -Force | Out-Null
    Copy-Item -Path $src -Destination $dest -Recurse -Force
    Write-Output "Backup complete -> $dest"
}

# ------------------------------------------------------------------ DEV & AUTOMATION HELPERS
# ------------------------------------------------------------------

<#
.SYNOPSIS
    Scaffold a new project folder from a simple template.
    Creates .gitignore, a README.md stub and a language-specific entry file.
.Parameter Name
    Project name.
.Parameter Lang
    Template: ps1 | py | js | generic.
#>
function New-ProjectScaffold {
    [CmdletBinding()]
    param(
        [string]$Name,
        [ValidateSet("ps1", "python", "js", "generic")]
        [string]$Template = "generic",
        [string]$Path = "."
    )
    $root = (Resolve-Path $Path -ErrorAction Stop).Path
    if (-not $Name) { Write-Error "Provide -Name"; return }
    $dir = Join-Path $root $Name
    if (Test-Path -LiteralPath $dir) { Write-Warning "Exists: $dir"; return }
    New-Item -ItemType Directory -Path $dir | Out-Null

    # .gitignore
    Set-Content -LiteralPath (Join-Path $dir ".gitignore") -Value @(
        "# personal ignore rules"
        "*.log"
        ".DS_Store"
        "Thumbs.db"
        "node_modules/"
        ".env"
    )

    # README stub
    Set-Content -LiteralPath (Join-Path $dir "README.md") -Value ""

switch ($Template) {
        "ps1"     { Set-Content -LiteralPath (Join-Path $dir "$Name.ps1") -Value "Write-Output 'ready'" }
        "python"  { Set-Content -LiteralPath (Join-Path $dir "$Name.py")   -Value "def main():
    print('ready')

if __name__ == '__main__':
    main()" }
        "js"      { Set-Content -LiteralPath (Join-Path $dir "$Name.js")   -Value "console.log('ready');" }
        default   { Set-Content -LiteralPath (Join-Path $dir "$Name.txt")   -Value "Project scaffold" }
    }
    Write-Output "Scaffolded: $dir"
}

<#
.SYNOPSIS
    Inspect the current environment: path entries, versions, and the OS.
#>
function Show-Environment {
    $cols = Get-ChildItem Env: | Sort-Object Name
    [PSCustomObject]@{
        Machine = $env:COMPUTERNAME
        OS      = [System.Environment]::OSVersion.VersionString
        PS      = $PSVersionTable.PSVersion.ToString()
    } | Format-List
    Write-Output ("PATH entries ({0}):" -f $env:PATH.Split(';').Count)
    $env:PATH.Split(';') | Where-Object { $_ } | ForEach-Object { Write-Output "  $_" }
}