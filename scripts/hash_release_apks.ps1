param(
    [string]$OutputPath = "APK_SHA256SUMS.txt"
)

$patterns = @(
    ".\apps\react-native-benchmark-app\android\app\build\outputs\apk\release\*.apk",
    ".\apps\native-android-benchmark-app\app\build\outputs\apk\release\*.apk"
)

$files = foreach ($pattern in $patterns) {
    Get-ChildItem $pattern -File -ErrorAction SilentlyContinue
}

if (-not $files) {
    Write-Error "No release APK files found. Build the release variants first."
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
