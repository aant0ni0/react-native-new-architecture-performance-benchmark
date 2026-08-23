# RNArchBench

**RNArchBench** is an open benchmark and replication suite for evaluating performance trade-offs between React Native Legacy Architecture, React Native New Architecture, and native Android.

The repository also contains the frozen measurement and analysis artifact used in the empirical study:

**Performance Trade-offs of React Native's New Architecture: A Multi-Device Empirical Comparison with Legacy React Native and Native Android**

RNArchBench provides:

- a React Native benchmark application supporting Legacy and New Architecture builds,
- a native Android baseline for the cross-technology UI scenarios,
- five benchmark scenarios, including JS-native communication for React Native,
- canonical datasets for Motorola Moto G72 and Google Pixel 4a,
- retained validation and superseded datasets for provenance,
- reproducible Python analysis and figure-generation scripts,
- supplementary Perfetto trace metadata and checksums,
- utilities for architecture configuration and environment capture.

## Repository Structure

```text
react-native-new-architecture-performance-benchmark/
  apps/
    react-native-benchmark-app/
    native-android-benchmark-app/
  analysis/
    results/
    reproduce_analysis.py
    make_figures.py
    requirements.txt
    requirements-lock.txt
  data/
    moto-g72/
    pixel-4a/
    README.md
  figures/
  perfetto/
  scripts/
  ACQUISITION_GUIDE.md
  REPLICATION_NOTES.md
  CITATION.cff
  LICENSE
  Licence.txt
  README.md
```

## Benchmark Scenarios

| Scenario | React Native | Native Android | Purpose |
|---|---:|---:|---|
| S1 Periodic UI updates | Yes | Yes | Update-to-next-frame-callback delay |
| S2 Large-list scrolling | Yes | Yes | Rendering smoothness, jank, CPU and memory |
| S3 UI animations | Yes | Yes | JS-driven and native-driven animation behavior |
| S4 JS-native communication | Yes | No | Scalar and array round-trip throughput |
| S5 Cold start | External Android tooling | External Android tooling | Application startup latency |

S3 exposes a runtime selector for JS-driven versus native-driven animation execution.

S4 exposes runtime payload sizes of 1, 10, 100, 1,000, and 10,000 elements. A native Android S4 is intentionally not provided because the workload specifically evaluates the JavaScript-native boundary.

## Reference Devices and Data

The frozen datasets included with the replication package were collected on:

- Motorola Moto G72 - 120 Hz display,
- Google Pixel 4a - 60 Hz display, Android 13.

The devices are treated as separate replication contexts rather than pooled into one sample.

Canonical datasets are located under:

```text
data/moto-g72/
data/pixel-4a/
```

See `data/README.md`, `REPLICATION_NOTES.md`, and `ACQUISITION_GUIDE.md` before reusing or extending the data.

## Requirements

React Native benchmark:

- Node.js 20 or newer,
- npm,
- Android SDK,
- a JDK compatible with the Android Gradle Plugin.

Native Android benchmark:

- Android SDK,
- a JDK compatible with the Android Gradle Plugin.

Using the JDK bundled with a current Android Studio installation is recommended.

## Configure React Native Architecture

The React Native host configuration and Scenario 4 module wrapper must agree.

From the repository root, configure both files atomically:

```powershell
python .\scripts\configure_rn_architecture.py legacy
```

or:

```powershell
python .\scripts\configure_rn_architecture.py new
```

Verify the current configuration without changing it:

```powershell
python .\scripts\configure_rn_architecture.py check
```

Changing architecture requires rebuilding the application.

## Build the React Native Benchmark

```powershell
cd apps/react-native-benchmark-app
npm ci
cd android
.\gradlew.bat app:assembleRelease
```

APK output:

```text
apps/react-native-benchmark-app/android/app/build/outputs/apk/release/
```

The reported benchmark measurements were collected from release variants, not from the standard React Native debug workflow.

The public React Native `release` build type uses the Android debug signing configuration solely so that a locally generated replication APK can be installed without distributing a private production signing key. The build type itself remains `release`.

### Windows path-length note

React Native New Architecture code generation may exceed the Windows Ninja/CMake 260-character path limit when the repository lives under a long path. If this occurs, build the same revision from a short ASCII-only path such as `C:\r` or `C:\RNArchBench`.

## Build the Native Android Benchmark

```powershell
cd apps/native-android-benchmark-app
.\gradlew.bat assembleRelease
```

APK output:

```text
apps/native-android-benchmark-app/app/build/outputs/apk/release/
```

The current public project signs its local release variant with the Android debug signing configuration so that the artifact can be installed for replication without distributing a private production key. It remains a release build type.

## Capture a Replication Environment

With a device connected through ADB, run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\capture_environment.ps1
```

To save the snapshot:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\capture_environment.ps1 -OutputPath environment_snapshot.txt
```

The script records the Git revision, host tool versions, and Android device/build properties available through ADB.

## Reproduce the Statistical Analysis

Create an isolated Python environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\analysis\requirements-lock.txt
```

Run:

```powershell
python .\analysis\reproduce_analysis.py
python .\analysis\make_figures.py
```

Outputs are written to:

```text
analysis/results/
figures/
```

The analysis scripts accept source CSVs that use either decimal points or decimal commas. `analysis/requirements-lock.txt` pins the direct analysis dependencies to a known-good v1.0.2 audit environment; `analysis/requirements.txt` retains the looser minimum-version specification.

Primary Legacy-vs-New comparisons report permutation-based Mann-Whitney U p-values, Cliff's delta, Benjamini-Hochberg-adjusted q-values, and a deterministic bootstrap 95% confidence interval for the Legacy-minus-New median difference. For S3, the inferential endpoints are restricted to reproducible graphics-layer metrics; the retained one-second callback-rate summary and CPU/RAM fields are descriptive.

## Reproducibility Boundary

The canonical CSV datasets and numerical analysis are intended to be exactly reproducible from this repository when the pinned analysis environment is used. Publication figures are reproducible in content, but binary PDF/PNG bytes can vary across Matplotlib/platform versions because of rendering and file metadata.

Some historical measurement-acquisition intermediates were not retained, including complete per-second S3 callback samples and the complete historical ADB orchestration used during the original experiment. These limitations are documented explicitly in `REPLICATION_NOTES.md`. A prospective workflow for new acquisitions is provided in `ACQUISITION_GUIDE.md`.

Usability improvements added after the historical measurements, such as runtime S3/S4 selectors and architecture-configuration utilities, improve future replication but do not retroactively alter the provenance of the frozen datasets.

## Perfetto Traces

Selected Moto G72 Perfetto traces are distributed as release assets rather than regular Git objects because of their size.

The expected filenames and SHA-256 checksums are listed in:

```text
perfetto/SHA256SUMS.txt
```

## Archived Release and DOI

The exact RNArchBench v1.0.2 artifact prepared for archival and the SoftwareX submission is preserved on Zenodo:

- Version DOI (v1.0.2): [10.5281/zenodo.22071873](https://doi.org/10.5281/zenodo.22071873)
- Concept DOI (all versions): [10.5281/zenodo.22071872](https://doi.org/10.5281/zenodo.22071872)

For reproducibility, cite the version DOI when referring to the exact artifact used in a study. The concept DOI may be used when referring to RNArchBench as an evolving software project.

## Citation

Citation metadata are provided in `CITATION.cff`. For RNArchBench v1.0.2, the archived version DOI is [10.5281/zenodo.22071873](https://doi.org/10.5281/zenodo.22071873).


## License

RNArchBench is distributed under the MIT License. See `LICENSE` or `Licence.txt`.
