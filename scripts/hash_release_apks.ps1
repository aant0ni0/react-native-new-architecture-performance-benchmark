param(
    [string]$OutputPath = "APK_SHA256SUMS.txt",
    [string]$ArtifactDirectory = ""
)

if ($ArtifactDirectory) {
    if (-not (Test-Path -LiteralPath $ArtifactDirectory -PathType Container)) {
        Write-Error "Artifact directory not found: $ArtifactDirectory"
        exit 1
    }

    $files = Get-ChildItem -LiteralPath $ArtifactDirectory -Filter *.apk -File |
        Sort-Object Name
} else {
    $patterns = @(
        ".\apps\react-native-benchmark-app\android\app\build\outputs\apk\release\*.apk",
        ".\apps\native-android-benchmark-app\app\build\outputs\apk\release\*.apk"
    )

    $files = foreach ($pattern in $patterns) {
        Get-ChildItem $pattern -File -ErrorAction SilentlyContinue
    }
    $files = $files | Sort-Object FullName
}

if (-not $files) {
    if ($ArtifactDirectory) {
        Write-Error "No APK files found in artifact directory: $ArtifactDirectory"
    } else {
        Write-Error "No release APK files found. Build the current release artifacts first."
    }
    exit 1
}

$lines = foreach ($file in $files) {
    $hash = (Get-FileHash $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $relative = Resolve-Path -Relative $file.FullName
    "$hash  $relative"
}

$lines | Set-Content $OutputPath -Encoding ascii
$lines
Write-Host "Saved checksums to: $OutputPath"
