# Prospective Acquisition Guide

This guide describes a **prospective replication workflow** for RNArchBench. It is not a reconstruction of the complete historical orchestration used for the frozen Moto G72 and Pixel 4a datasets; the limits of historical acquisition reproducibility are documented in `REPLICATION_NOTES.md`.

## 1. Prepare and record the environment

Use a physical Android device and keep each device as a separate replication context.

From the repository root, capture the software/toolchain and, when connected, the Android build properties:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\capture_environment.ps1 -OutputPath environment_snapshot.txt
```

Record at minimum:

- repository revision/tag;
- device manufacturer/model;
- Android version and build fingerprint;
- display refresh-rate setting used during the run;
- Node, Java, Gradle, Android SDK/ADB, and Python versions;
- whether the RN build is Legacy or New Architecture.

When you are ready to add a new canonical device directory, also add one row to:

```text
data/devices.csv
```

### Windows path-length note

React Native New Architecture code generation can exceed the Windows Ninja/CMake path limit when the repository is stored under a long path. If this occurs, build from a short ASCII-only path such as:

```text
C:\r
C:\RNArchBench
```

The same source revision should be used; only the working-tree location changes.

## 2. Build release variants

The frozen study used release build types. Do not substitute the normal React Native debug workflow for measurement runs.

### React Native New Architecture

```powershell
python .\scripts\configure_rn_architecture.py new
cd .\apps\react-native-benchmark-app
npm ci
cd android
.\gradlew.bat clean
.\gradlew.bat app:assembleRelease
```

### React Native Legacy Architecture

Return to the repository root, then:

```powershell
python .\scripts\configure_rn_architecture.py legacy
cd .\apps\react-native-benchmark-app\android
.\gradlew.bat clean
.\gradlew.bat app:assembleRelease
```

### Native Android

```powershell
cd .\apps\native-android-benchmark-app
.\gradlew.bat clean
.\gradlew.bat assembleRelease
```

The public release build types use the Android debug signing configuration solely to make locally generated replication APKs installable without publishing a private production signing key.

## 3. Preserve and hash the APKs

Because Legacy and New Architecture builds use the same RN output filename, copy each APK to a labeled artifact directory before cleaning/building the other architecture. For example:

```powershell
mkdir release-artifacts
copy .\apps\react-native-benchmark-app\android\app\build\outputs\apk\release\app-release.apk .\release-artifacts\rn-new-release.apk
# rebuild Legacy, then:
copy .\apps\react-native-benchmark-app\android\app\build\outputs\apk\release\app-release.apk .\release-artifacts\rn-legacy-release.apk
# build native, then:
copy .\apps\native-android-benchmark-app\app\build\outputs\apk\release\app-release.apk .\release-artifacts\native-release.apk
```

Hash the retained artifacts:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\hash_release_apks.ps1 -ArtifactDirectory .\release-artifacts
```

## 4. General run discipline

For an extension intended to be comparable with the frozen dataset:

- use the same app revision for all architectures on a device;
- keep OS/display/power settings fixed within a device context;
- use release builds;
- reset the application to a known state before a run;
- use a fixed number of repetitions (the frozen canonical configurations contain 10 runs each);
- assign explicit run identifiers rather than treating Legacy/New runs as paired observations;
- retain app-level outputs and lower-level raw tooling output rather than only transcribing summary values;
- do not pool different physical devices into one sample unless the new study explicitly models device effects.

## 5. Scenario-specific workflow

### S1 — periodic UI updates

The React Native screen supports update intervals of 50, 100, 200, and 1,000 ms. The current implementation uses a 10 s warm-up followed by a 60 s measurement window.

The S1 timing construct is **update-to-next-frame-callback delay**. In React Native, the timestamp is taken immediately before the state-update computation is scheduled; in the native baseline, the new data values are computed before the timestamp and the timestamp precedes adapter notification. Therefore S1 should not be described as a native paint marker or direct end-to-end frame latency, and RN-vs-Native absolute comparisons include a small instrumentation-boundary asymmetry.

For prospective work, preserve individual callback-delay samples if the acquisition instrumentation is extended. The historical package does not retain every individual S1 sample.

### S2 — large-list scrolling

The current RN implementation scrolls a 1,000-item list for 60 s using the built-in automatic-scroll scenario.

For graphics-layer measurements, reset Android graphics statistics immediately before each run and retain the complete post-run output, for example:

```powershell
adb shell dumpsys gfxinfo <package> reset
# run S2 in the application
adb shell dumpsys gfxinfo <package> > s2_runXX_gfxinfo.txt
```

RN package:

```text
com.rnbenchmarkapp
```

Native package:

```text
com.example.nativebenchmarkapp
```

If CPU or memory measurements are collected, preserve the raw source used to derive the reported modal/peak values and use the same procedure for every architecture on that device. The original complete CPU/RAM orchestration script was not retained.

### S3 — animations

The current RN screen provides runtime selection of:

- `JS-driven` (`useNativeDriver: false`),
- `Native-driven` (`useNativeDriver: true`).

Each run lasts 60 s. Use the same graphics-statistics procedure as S2 and keep the two driver configurations as separate conditions.

The screen's one-second JS callback-rate display is useful diagnostically, but the frozen repository does not contain the complete historical one-second sample series. Treat the retained `FPS modal` field as descriptive rather than a primary inferential endpoint. The primary reproducible S3 inferential endpoints in the analysis script are rendered-frame rate, modern jank percentage, and frame P99.

### S4 — JavaScript-native communication

S4 has no native-only counterpart because it specifically evaluates the JS-native boundary.

Current operation counts:

- scalar: 100,000 sequential asynchronous round trips;
- array: 10,000 sequential asynchronous round trips.

Array payload sizes are 1, 10, 100, 1,000, and 10,000 numeric elements. The current app prepares the selected array outside the timed round-trip loop.

Run every architecture × payload condition with the chosen fixed repetition count and preserve operation count and total duration. Throughput can be recomputed as:

```text
Operations_per_second = round(Operations_Count / (Total_Duration_ms / 1000))
```

### S5 — cold start

Cold start is collected externally. A prospective Android ActivityManager workflow is:

```powershell
adb shell am force-stop com.rnbenchmarkapp
adb shell am start -W -n com.rnbenchmarkapp/.MainActivity
```

or for the native app:

```powershell
adb shell am force-stop com.example.nativebenchmarkapp
adb shell am start -W -n com.example.nativebenchmarkapp/.MainActivity
```

Retain the complete command output for every run and extract `TotalTime` (and `WaitTime` if required by the analysis table). Ensure the app is force-stopped before every repetition.

## 6. Data retention

Do not overwrite the frozen reference directories when adding a new device. Create a new device directory and retain:

- canonical per-run tables used by the analysis;
- raw/superseded series needed to explain canonical selection;
- environment snapshot;
- APK SHA-256 manifest;
- raw `gfxinfo`/ActivityManager/tooling output when collected;
- notes on any deviations from this guide.

After adding the new canonical CSV files, run the validator from the repository root:

```powershell
python .\analysis\validate_data.py --device <device-folder>
```

If a redundant derived field is corrected from retained primary quantities, preserve the original raw record and document the normalization explicitly.
