# RNArchBench — Native Android Benchmark App

This project provides the native Android baseline used by RNArchBench.

## Scenarios

The native application implements the cross-technology scenarios for which a native baseline is meaningful:

1. periodic UI updates,
2. large-list scrolling,
3. UI animations.

Cold start is measured externally with Android tooling.

Scenario 4 is intentionally absent from the native application because S4 specifically measures the JavaScript-native communication boundary in React Native.

## Requirements

- JDK 17 or later,
- Android SDK / compileSdk 36,
- Android Build Tools 36.0.0,
- Gradle 8.13 (wrapper-provided).

## Release Build

```powershell
.\gradlew.bat assembleRelease
```

Output:

```text
app/build/outputs/apk/release/
```

The current public project uses the Android debug signing configuration for the `release` build type. This makes the locally generated release APK installable for replication without distributing a private production signing key.

The benchmark measurements distributed with RNArchBench were collected from release variants.

## Development Build

```powershell
.\gradlew.bat assembleDebug
.\gradlew.bat installDebug
```

Debug builds are intended for development only and are not the measurement workflow used for the frozen datasets.

## Data and Analysis

See the repository root:

```text
data/
analysis/
figures/
REPLICATION_NOTES.md
ACQUISITION_GUIDE.md
```
