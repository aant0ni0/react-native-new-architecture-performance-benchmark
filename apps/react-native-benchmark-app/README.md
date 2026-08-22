# React Native Benchmark App

This project contains the React Native implementation of the benchmark scenarios used in the comparative study of:

- React Native Legacy Architecture,
- React Native New Architecture,
- native Android.

The application is part of the replication package for:

**Performance Trade-offs of React Native's New Architecture: A Multi-Device Empirical Comparison with Legacy React Native and Native Android**

Research data, analysis scripts, and generated figures are stored at the repository root outside this application directory.

## Scenarios

The application contains four interactive benchmark scenarios:

1. periodic real-time UI updates,
2. large-list scrolling,
3. UI animations,
4. JavaScript-native communication.

Application cold start is measured externally using Android tooling and therefore does not require a dedicated benchmark screen.

## Project Structure

```text
android/     Android host app and native benchmark modules
ios/         iOS host app
modules/     JavaScript wrappers around native communication modules
screens/     Benchmark scenario screens
specs/       TurboModule specs used by React Native codegen
```

## Requirements

- Node.js,
- npm,
- Android SDK,
- JDK compatible with the Android Gradle Plugin.

The Android benchmark is the configuration used in the reported study.

## Architecture Switching

The React Native Legacy Architecture and New Architecture configurations must be kept consistent in both:

- `android/gradle.properties`,
- `modules/CommunicationModule.ts`.

Use:

- `newArchEnabled=false` with `IS_LEGACY = true`,
- `newArchEnabled=true` with `IS_LEGACY = false`.

This ensures that the Android host configuration and the JavaScript-side communication-module selection correspond to the same architecture.

## Release Build

The measurements reported in the study were collected from release builds rather than the default React Native debug workflow.

From this directory:

```powershell
npm ci
cd android
.\gradlew.bat app:assembleRelease
```

The generated APK is written to:

```text
android/app/build/outputs/apk/release/
```

The release-build procedure was verified from a clean repository worktree on Windows.

For an installed release variant, Gradle also exposes:

```powershell
.\gradlew.bat app:installRelease
```

provided that an Android device or emulator is connected and the build is installable in the local environment.

## Development Workflow

For interactive development, Metro and the standard React Native tooling can still be used:

```powershell
npm start
npm run android
```

These commands are intended for development and are not the measurement workflow used for the reported benchmark results.

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
