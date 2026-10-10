# RNArchBench

**RNArchBench** is an open benchmark and replication suite for evaluating performance trade-offs between React Native Legacy Architecture, React Native New Architecture, and native Android.

The repository contains the benchmark software and the frozen measurement artifact used in the companion empirical manuscript:

**Performance Trade-offs of React Native's New Architecture on Android: A Two-Device Empirical Study**

The analysis supplement prepared for IEEE Access is available in [`paper/ieee-access/`](paper/ieee-access/README.md). It uses the RNArchBench v1.0.4 observations and provides exact permutation tests, Holm correction within each research question across both devices, and sensitivity analyses for multiplicity and selected S4 remeasurements. The original archived analysis remains in `analysis/`; the manuscript supplement is a separate addition and is not part of the frozen v1.0.4 ZIP.

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
    validate_data.py
    requirements.txt
    requirements-lock.txt
  data/
    devices.csv
    moto-g72/
    pixel-4a/
    README.md
  figures/
  paper/
    ieee-access/
      supplement/
      tables/
      figures/
      verify.py
      README.md
  perfetto/
  scripts/
  .github/
    workflows/
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

S4 exposes runtime payload sizes of 1, 10, 100, 1,000, and 10,000 elements. Each timed run performs an untimed correctness preflight before the timer starts and validates the final response after the timer stops; the UI also provides a separate full diagnostic that validates every response without measuring throughput. A native Android S4 is intentionally not provided because the workload specifically evaluates the JavaScript-native boundary.

## Reference Devices and Data

The frozen datasets included with the replication package were collected on:

- Motorola Moto G72 - nominal 120 Hz display,
- Google Pixel 4a - nominal 60 Hz display, Android 13.

The devices are treated as separate replication contexts rather than pooled into one sample.

The reference-device registry used by the analysis and validation scripts lives at:

```text
data/devices.csv
```

Canonical datasets are located under:

```text
data/moto-g72/
data/pixel-4a/
```

See `data/README.md`, `REPLICATION_NOTES.md`, and `ACQUISITION_GUIDE.md` before reusing or extending the data.

## Requirements

React Native benchmark:

- Node.js >=20.19.4 and npm,
- JDK 17 or later,
- Android SDK / compileSdk 36,
- Android Build Tools 36.0.0,
- Android NDK 27.1.12297006,
- Gradle 8.14.3 (wrapper-provided).

Native Android benchmark:

- JDK 17 or later,
- Android SDK / compileSdk 36,
- Android Build Tools 36.0.0,
- Gradle 8.13 (wrapper-provided).

Using the JDK bundled with a current Android Studio installation is recommended.

## Configure React Native Architecture

The React Native host configuration and Scenario 4 module wrapper must agree.

From the repository root, configure both files consistently:

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

## Reproduce the Analyses

Create an isolated Python environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\analysis\requirements-lock.txt
```

### Manuscript Tables and Figures

From the repository root, verify the complete manuscript supplement:

```powershell
python paper/ieee-access/verify.py
```

This command reproduces the analysis and four figures in a temporary directory, compares the numerical results and LaTeX tables with the bundled manuscript outputs, and verifies the reference-file checksums. It leaves the checkout unchanged. The analysis covers 700 records, 70 ten-run cells, and 40 Legacy-New comparisons using all 184756 permutation assignments, RQ-wise Holm correction across both devices, and sensitivity analyses.

To regenerate outputs in `paper/ieee-access/` instead, run:

```powershell
python paper/ieee-access/supplement/reproduce_results.py
python paper/ieee-access/supplement/make_figures.py
```

See [`paper/ieee-access/README.md`](paper/ieee-access/README.md) for the package layout and verification details.

### Archived v1.0.4 Analysis

To reproduce the original release analysis, run:

```powershell
python .\analysis\validate_data.py
python .\analysis\reproduce_analysis.py
python .\analysis\make_figures.py
```

Outputs are written to:

```text
analysis/results/
figures/
```

The analysis scripts accept source CSVs that use either decimal points or decimal commas. `analysis/requirements-lock.txt` pins the complete tested analysis dependency set; `analysis/requirements.txt` retains the looser minimum-version specification.

`analysis/validate_data.py` checks the canonical CSV schema, exact experimental condition grid and run counts, required fields, and Scenario 4 throughput formula before you regenerate tables or figures.

The archived Legacy-vs-New comparisons use 100000 permutation resamples for Mann-Whitney U p-values, Cliff's delta, Benjamini-Hochberg adjustment within each RQ-by-device family, and a deterministic bootstrap 95% confidence interval for the Legacy-minus-New median difference. For S3, the inferential endpoints are restricted to reproducible graphics-layer metrics; the retained one-second callback-rate summary and CPU/RAM fields are descriptive. Use the separate manuscript commands above for the exact tests and Holm-adjusted tables reported in the article.

## Reproducibility Boundary

The canonical CSV datasets and numerical analysis are intended to be exactly reproducible from this repository when the pinned analysis environment is used. Publication figures are reproducible in content, but binary PDF/PNG bytes can vary across Matplotlib/platform versions because of rendering and file metadata.

Some historical measurement-acquisition intermediates were not retained, including complete per-second S3 callback samples and the complete historical ADB orchestration used during the original experiment. These limitations are documented explicitly in `REPLICATION_NOTES.md`. A prospective workflow for new acquisitions is provided in `ACQUISITION_GUIDE.md`.

Usability improvements added after the historical measurements, such as runtime S3/S4 selectors and architecture-configuration utilities, improve future replication but do not retroactively alter the provenance of the frozen datasets.

## Engineering Checks

The repository includes:

- `analysis/validate_data.py` for canonical-data validation,
- `paper/ieee-access/verify.py` and its regression tests for the manuscript supplement,
- Jest and TypeScript checks for the React Native benchmark app,
- `.github/workflows/reproducibility.yml` for archived-analysis, manuscript-supplement, application-build, and architecture-toggle CI.

## Perfetto Traces

Selected Moto G72 Perfetto traces are distributed as release assets rather than regular Git objects because of their size.

The expected filenames and SHA-256 checksums are listed in:

```text
perfetto/SHA256SUMS.txt
```

## Archived Release and DOI

The frozen RNArchBench v1.0.4 software and measurement artifact is preserved on Zenodo:

- Version DOI (v1.0.4): [10.5281/zenodo.22087347](https://doi.org/10.5281/zenodo.22087347)
- Concept DOI (all versions): [10.5281/zenodo.22071872](https://doi.org/10.5281/zenodo.22071872)

For reproducibility, cite the version DOI when referring to the exact artifact used in a study. The concept DOI may be used when referring to RNArchBench as an evolving software project.

This DOI identifies the frozen software and measurement artifact. The companion manuscript analysis is versioned separately in [`paper/ieee-access/`](paper/ieee-access/README.md) and preserves the reference observations.

## Citation

Citation metadata are provided in `CITATION.cff`. For RNArchBench v1.0.4, the archived version DOI is [10.5281/zenodo.22087347](https://doi.org/10.5281/zenodo.22087347).


## License

RNArchBench is distributed under the MIT License. See `LICENSE` or `Licence.txt`.
