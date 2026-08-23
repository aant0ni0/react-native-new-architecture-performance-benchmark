param(
    [string]$OutputPath = ""
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
$lines = New-Object System.Collections.Generic.List[string]

function Add-Line {
    param([string]$Text = "")
    $script:lines.Add($Text)
}

function Invoke-NativeClean {
    param([scriptblock]$Command)

    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    try {
        $items = & $Command 2>&1
        $exitCode = $LASTEXITCODE

        $clean = foreach ($item in $items) {
            if ($item -is [System.Management.Automation.ErrorRecord]) {
                $item.Exception.Message
            } else {
                [string]$item
            }
        }

        [pscustomobject]@{
            ExitCode = $exitCode
            Output   = ($clean -join [Environment]::NewLine).TrimEnd()
        }
    }
    catch {
        [pscustomobject]@{
            ExitCode = 1
            Output   = $_.Exception.Message
        }
    }
    finally {
        $ErrorActionPreference = $oldPreference
    }
}

function Add-Command {
    param(
        [string]$Label,
        [scriptblock]$Command,
        [switch]$Optional
    )

    Add-Line "===== $Label ====="
    $result = Invoke-NativeClean $Command

    if ($result.Output) {
        Add-Line $result.Output
    } elseif ($result.ExitCode -ne 0) {
        Add-Line "UNAVAILABLE (exit code $($result.ExitCode))"
    } else {
        Add-Line "(no output)"
    }

    if (($result.ExitCode -ne 0) -and (-not $Optional)) {
        Add-Line "[command exited with code $($result.ExitCode)]"
    }

    Add-Line ""
    return $result
}

Add-Line "RNArchBench environment snapshot"
Add-Line "Captured: $([DateTime]::Now.ToString('o'))"
Add-Line "Repository root: $RepoRoot"
Add-Line ""

Add-Command "Git revision" { git -C $RepoRoot rev-parse HEAD } | Out-Null
Add-Command "Git branch" { git -C $RepoRoot branch --show-current } | Out-Null
Add-Command "Git status" { git -C $RepoRoot status --short } | Out-Null

Add-Command "System Python" { python --version } -Optional | Out-Null
Add-Command "System pip" { python -m pip --version } -Optional | Out-Null

$venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Add-Command "Analysis Python (.venv)" { & $venvPython --version } | Out-Null
    Add-Command "Analysis pip (.venv)" { & $venvPython -m pip --version } | Out-Null
} else {
    Add-Line "===== Analysis Python (.venv) ====="
    Add-Line "No repository-local .venv found."
    Add-Line ""
}

Add-Command "Node.js" { node --version } -Optional | Out-Null
Add-Command "npm" { npm.cmd --version } -Optional | Out-Null
Add-Command "Java runtime" { java -version } -Optional | Out-Null
Add-Command "Java compiler" { javac -version } -Optional | Out-Null

$rnGradle = Join-Path $RepoRoot "apps\react-native-benchmark-app\android\gradlew.bat"
$nativeGradle = Join-Path $RepoRoot "apps\native-android-benchmark-app\gradlew.bat"

if (Test-Path $rnGradle) {
    Add-Command "Gradle RN" { & $rnGradle -p (Split-Path $rnGradle -Parent) --version } | Out-Null
}
if (Test-Path $nativeGradle) {
    Add-Command "Gradle native" { & $nativeGradle -p (Split-Path $nativeGradle -Parent) --version } | Out-Null
}

$adbCommand = Get-Command adb -ErrorAction SilentlyContinue
if ($adbCommand) {
    Add-Command "ADB" { adb version } | Out-Null

    $deviceState = Invoke-NativeClean { adb get-state }
    if (($deviceState.ExitCode -eq 0) -and ($deviceState.Output -match "(?m)^device$")) {
        Add-Command "Android device model" {
            adb shell getprop ro.product.manufacturer
            adb shell getprop ro.product.model
        } | Out-Null
        Add-Command "Android version" { adb shell getprop ro.build.version.release } | Out-Null
        Add-Command "Android build fingerprint" { adb shell getprop ro.build.fingerprint } | Out-Null
        Add-Command "Android ABI" { adb shell getprop ro.product.cpu.abi } | Out-Null
        Add-Command "Android SDK level" { adb shell getprop ro.build.version.sdk } | Out-Null
    } else {
        Add-Line "===== Android device ====="
        Add-Line "No connected Android device/emulator detected; device-specific properties were skipped."
        if ($deviceState.Output) {
            Add-Line "ADB status: $($deviceState.Output)"
        }
        Add-Line ""
    }
} else {
    Add-Line "===== ADB ====="
    Add-Line "ADB not found in PATH; device-specific properties were skipped."
    Add-Line ""
}

$text = $lines -join [Environment]::NewLine
Write-Output $text

if ($OutputPath) {
    $full = [System.IO.Path]::GetFullPath($OutputPath)
    [System.IO.File]::WriteAllText(
        $full,
        $text,
        [System.Text.UTF8Encoding]::new($false)
    )
    Write-Host "Saved environment snapshot to: $full"
}
