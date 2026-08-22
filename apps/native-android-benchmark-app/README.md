# Native Android Benchmark App

This project contains the native Android baseline implementation used in the comparative study of:

- React Native Legacy Architecture,
- React Native New Architecture,
- native Android.

The application is part of the replication package for:

**Performance Trade-offs of React Native's New Architecture: A Multi-Device Empirical Comparison with Legacy React Native and Native Android**

Research data, analysis scripts, and generated figures are stored at the repository root outside this application directory.

## Scenarios

The application contains native Android implementations corresponding to the benchmark scenarios used for cross-technology comparison:

1. periodic real-time UI updates,
2. large-list scrolling,
3. UI animations,
4. communication-style workload implemented fully on Android.

Application cold start is measured externally using Android tooling and therefore does not require a dedicated benchmark screen.

## Project Structure

```text
app/src/main/java/   Android activities and benchmark logic
app/src/main/res/    layouts, drawables, and other resources
gradle/              Gradle wrapper and version catalog
```

## Requirements

- Android SDK,
- JDK compatible with the Android Gradle Plugin.

Using the JDK bundled with a current Android Studio installation is recommended.

## Release Build

The measurements reported in the study were collected from release builds.

From this directory:

```powershell
.\gradlew.bat assembleRelease
```

The generated APK is written to:

```text
app/build/outputs/apk/release/
```

The release-build procedure was verified from a clean repository worktree on Windows.

The public repository does not include a private release signing key. Consequently, a locally generated release artifact may be named:

```text
app-release-unsigned.apk
```

Signing is not required to inspect or compile the benchmark source code, but installation of an unsigned APK requires the usual local Android signing/build workflow.

## Development Build

For development-only use, the debug variant can be built or installed with:

```powershell
.\gradlew.bat assembleDebug
.\gradlew.bat installDebug
```

These debug commands are not the measurement workflow used for the reported benchmark results.

## Measurement Data

Canonical measurement datasets are stored at the repository root under:

```text
data/moto-g72/
data/pixel-4a/
```

See the root `data/README.md` for details about canonical datasets, validation runs, and retained raw/superseded measurements.

## Analysis

Statistical analysis and figure-generation scripts are stored at the repository root under:

```text
analysis/
```

Generated publication figures are stored under:

```text
figures/
```
