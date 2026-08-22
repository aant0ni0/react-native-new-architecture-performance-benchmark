# React Native New Architecture Performance Benchmark

This repository contains the replication package for the empirical study:

**Performance Trade-offs of React Native's New Architecture: A Multi-Device Empirical Comparison with Legacy React Native and Native Android**

The artifact provides:

- the React Native benchmark application used for both Legacy and New Architecture measurements,
- a native Android baseline application,
- canonical measurement datasets collected on two physical Android devices,
- preserved validation and superseded measurements for provenance,
- reproducible statistical analysis scripts,
- publication figures generated directly from the repository data.

## Repository Structure

```text
react-native-new-architecture-performance-benchmark/
  apps/
    react-native-benchmark-app/
    native-android-benchmark-app/

  data/
    README.md
    moto-g72/
      raw/
      s1_latency.csv
      s2_scroll.csv
      s3_js_driver.csv
      s3_native_driver.csv
      s4_array.csv
      s4_scalar.csv
      s5_startup.csv

    pixel-4a/
      raw/
      s1_latency.csv
      s2_scroll.csv
      s3_js_driver.csv
      s3_native_driver.csv
      s4_array.csv
      s4_scalar.csv
      s4_scalar_validation.csv
      s5_startup.csv

  analysis/
    README.md
    reproduce_analysis.py
    make_figures.py
    requirements.txt
    results/

  figures/
  perfetto/

  LICENSE
  README.md
```

## Benchmark Scope

The benchmark suite evaluates five scenarios:

1. periodic real-time UI updates,
2. large-list scrolling,
3. UI animations,
4. JavaScript-native communication,
5. application cold start.

Scenario 3 evaluates both JavaScript-driven and native-driver animations.

Scenario 4 evaluates both scalar calls and array payloads. The array benchmark uses payload sizes of 1, 10, 100, 1,000, and 10,000 elements.

## Devices

Measurements are provided for two physical Android devices:

- Motorola Moto G72 - 120 Hz display,
- Google Pixel 4a - 60 Hz display.

The devices are treated as separate replication contexts in the statistical analysis rather than pooling their measurements into one sample.

See `data/README.md` for dataset-level details, canonical-series selection, validation measurements, and provenance information.

## Applications

### React Native benchmark application

Location:

```text
apps/react-native-benchmark-app/
```

The same application contains the implementations used for the React Native Legacy Architecture and New Architecture experiments.

Architecture selection is controlled by the Android React Native configuration and the corresponding JavaScript communication-module selection. See the application README for details.

### Native Android benchmark application

Location:

```text
apps/native-android-benchmark-app/
```

This project provides the native Android baseline used in the comparative experiments.

## Building the Benchmark Applications

The release-build procedures below were verified from a clean repository worktree on Windows.

### Requirements

For the React Native application:

- Node.js 20 or newer,
- npm,
- Android SDK,
- JDK compatible with the Android Gradle Plugin.

For the native Android application:

- Android SDK,
- JDK compatible with the Android Gradle Plugin.

Using the JDK bundled with a current Android Studio installation is recommended.

### React Native release build

```powershell
cd apps/react-native-benchmark-app
npm ci
cd android
.\gradlew.bat app:assembleRelease
```

The APK is generated under:

```text
apps/react-native-benchmark-app/android/app/build/outputs/apk/release/
```

The benchmark measurements reported in the study were collected using release builds rather than the default React Native debug workflow.

### Native Android release build

```powershell
cd apps/native-android-benchmark-app
.\gradlew.bat assembleRelease
```

The APK is generated under:

```text
apps/native-android-benchmark-app/app/build/outputs/apk/release/
```

The public repository does not contain a private release signing key, so a locally built native release APK may be unsigned.

## Measurement Data

Canonical datasets are located under:

```text
data/moto-g72/
data/pixel-4a/
```

CSV files use a semicolon (`;`) delimiter.

Some source measurements use a comma as the decimal separator. The provided analysis scripts normalize these values automatically.

Directories named `raw/` contain earlier or superseded measurement series retained for transparency and provenance. They should not be pooled automatically with the canonical datasets.

See `data/README.md` for detailed rules governing Scenario 4 validation and clean-build repetitions.

## Reproducing the Statistical Analysis

Python dependencies are listed in:

```text
analysis/requirements.txt
```

Creating an isolated virtual environment is recommended.

On Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\analysis\requirements.txt
```

Run the statistical analysis from the repository root:

```powershell
python .\analysis\reproduce_analysis.py
```

Generated tables are written to:

```text
analysis/results/
```

Generate the publication figures with:

```powershell
python .\analysis\make_figures.py
```

The resulting PDF and PNG figures are written to:

```text
figures/
```

## Reproducibility Notes

The repository separates:

- canonical measurements used in the primary analysis,
- independent validation measurements,
- superseded/raw measurements retained for provenance,
- derived statistical tables,
- generated figures.

This structure is intended to make the exact analysis input explicit and to prevent validation or historical measurements from being accidentally pooled with the primary datasets.

## License

This repository is distributed under the MIT License. See `LICENSE` for details.
