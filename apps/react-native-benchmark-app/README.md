# RNArchBench — React Native Benchmark App

This application implements the React Native portion of RNArchBench for Legacy and New Architecture builds.

## Scenarios

1. periodic UI updates,
2. large-list scrolling,
3. UI animations,
4. JavaScript-native communication.

Cold start is measured externally with Android tooling.

### Scenario 3

The animation screen provides a runtime selector for:

- `JS-driven` (`useNativeDriver: false`),
- `Native-driven` (`useNativeDriver: true`).

The driver cannot be changed while a benchmark run is active.

### Scenario 4

The communication screen evaluates:

- scalar asynchronous calls,
- array/sum calls with payload sizes 1, 10, 100, 1,000, and 10,000.

The payload is selected at runtime and prepared outside the timed round-trip loop.

## Architecture Switching

Legacy/New Architecture changes require a rebuild. Do not edit the two configuration points independently.

From the **repository root**, use:

```powershell
python .\scripts\configure_rn_architecture.py legacy
```

or:

```powershell
python .\scripts\configure_rn_architecture.py new
```

Check consistency with:

```powershell
python .\scripts\configure_rn_architecture.py check
```

The helper keeps these values aligned:

- `android/gradle.properties`: `newArchEnabled`,
- `modules/CommunicationModule.ts`: `IS_LEGACY`.

## Requirements

- Node.js 20 or newer,
- npm,
- Android SDK,
- JDK compatible with the Android Gradle Plugin.

## Release Build

```powershell
npm ci
cd android
.\gradlew.bat app:assembleRelease
```

Output:

```text
android/app/build/outputs/apk/release/
```

The historical measurements distributed with RNArchBench were collected from release builds.

## Development

For interactive development:

```powershell
npm start
npm run android
```

These commands are not the measurement workflow used for the frozen benchmark datasets.

## Data and Analysis

Canonical data, provenance notes, analysis scripts, and figures live at the repository root:

```text
data/
analysis/
figures/
REPLICATION_NOTES.md
```
