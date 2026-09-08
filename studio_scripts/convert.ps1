param(
    [Parameter(Mandatory=$false)]
    [string]$InputPath = ".",
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = "converted",
    [Parameter(Mandatory=$false)]
    [switch]$ProRes = $false
)

# Ensure FFmpeg is available
$envPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$ffBin = Join-Path $envPath "env"
if ($env:PATH -notlike "*$ffBin*") {
    $env:PATH = "$ffBin;$env:PATH"
}

# Resolve input path
$resolvedPath = Resolve-Path $InputPath -ErrorAction Stop
Write-Output "Scanning: $resolvedPath"
Write-Output ""

# Find all MOV files
$files = Get-ChildItem -Path $resolvedPath -Filter "*.MOV" -File
$files += Get-ChildItem -Path $resolvedPath -Filter "*.mov" -File
$files = $files | Sort-Object Name -Unique

if ($files.Count -eq 0) {
    Write-Output "No .MOV files found in: $resolvedPath"
    exit 1
}

# Create output directory
$outDir = Join-Path $resolvedPath $OutputDir
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

Write-Output "Found $($files.Count) file(s) to convert"
Write-Output "Output: $outDir"
Write-Output ("=" * 60)

$total = $files.Count
$current = 0

foreach ($file in $files) {
    $current++
    $outName = [System.IO.Path]::GetFileNameWithoutExtension($file.Name) + ".mp4"
    $outFile = Join-Path $outDir $outName

    Write-Output "[$current/$total] Converting: $($file.Name) -> $outName"

    if ($ProRes) {
        # Apple ProRes 422 HQ — best for editing quality
        ffmpeg -y -i $file.FullName `
            -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le `
            -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" `
            -c:a pcm_s16le `
            $outFile 2>&1
    } else {
        # H.264 High Profile — great for Resolve, smaller files
        # Handles HDR -> SDR tonemapping if needed
        ffmpeg -y -i $file.FullName `
            -c:v libx264 -profile:v high -crf 18 -preset slow `
            -pix_fmt yuv420p `
            -vf "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,t=bt709:m=bt709,scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black" `
            -c:a aac -b:a 192k `
            -movflags +faststart `
            $outFile 2>&1
    }

    if ($LASTEXITCODE -eq 0) {
        # Show output file info
        $outSize = "{0:N2} MB" -f ((Get-Item $outFile).Length / 1MB)
        Write-Output "   -> Done: $outSize"
    } else {
        Write-Output "   -> FAILED (exit code: $LASTEXITCODE)"
    }
    Write-Output ""
}

Write-Output ("=" * 60)
Write-Output "All done! $total file(s) converted to: $outDir"
