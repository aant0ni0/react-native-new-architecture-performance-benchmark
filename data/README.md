# Measurement Data

This directory contains the per-run measurement data used in the empirical study:

**Performance Trade-offs of React Native's New Architecture: A Multi-Device Empirical Comparison with Legacy React Native and Native Android**

Measurements were collected on two physical Android devices:

- `moto-g72/` — Motorola Moto G72, 120 Hz display
- `pixel-4a/` — Google Pixel 4a, 60 Hz display

Each device directory contains the canonical datasets used for the statistical analysis reported in the paper.

## Benchmark scenarios

### Scenario 1 — Periodic UI updates
` s1_latency.csv `

Frame-scheduling latency for periodic UI updates at multiple update intervals.

### Scenario 2 — Large-list scrolling
` s2_scroll.csv `

Rendering performance during programmatic scrolling of a 1,000-item list, including frame count, deadline-based jank metrics, frame-time percentiles, CPU usage, and memory usage.

### Scenario 3 — UI animations
` s3_js_driver.csv `  
` s3_native_driver.csv `

Animation measurements for JavaScript-driven (`useNativeDriver: false`) and native-driven (`useNativeDriver: true`) configurations.

### Scenario 4 — JavaScript–Native communication
` s4_scalar.csv `  
` s4_array.csv `

Throughput of sequential asynchronous JavaScript–Native calls.

The array benchmark evaluates payload sizes of 1, 10, 100, 1,000, and 10,000 numeric elements.

### Scenario 5 — Cold start
` s5_startup.csv `

Application cold-start measurements obtained with Android ActivityManager `TotalTime`.

## Pixel 4a Scenario 4 validation

The unusually low New Architecture throughput observed for scalar calls on the Pixel 4a was independently repeated.

The canonical primary dataset is:

`pixel-4a/s4_scalar.csv`

The independent confirmation series is:

`pixel-4a/s4_scalar_validation.csv`

The validation series reproduced the same order of magnitude and is used as a robustness check rather than pooled with the primary experiment.

For the array benchmark, the initial Pixel 4a New Architecture measurements for payload sizes 1 and 10 showed unusually high variability. These two configurations were repeated after fresh application builds.

The canonical:

`pixel-4a/s4_array.csv`

contains:

- the original Legacy measurements for all payload sizes;
- the clean-build New Architecture repetitions for payload sizes 1 and 10;
- the original New Architecture measurements for payload sizes 100, 1,000, and 10,000.

Each architecture × payload combination contains exactly 10 runs.

## Raw and superseded measurements

Subdirectories named `raw/` retain earlier measurement series for transparency and provenance.

These files are **not used directly in the primary statistical analysis** unless explicitly stated above.

For Motorola Moto G72, the original Scenario 4 scalar dataset contained two anomalous New Architecture records that were subsequently re-measured. The corrected canonical series is:

`moto-g72/s4_scalar.csv`

The earlier series is retained as:

`moto-g72/raw/s4_scalar_initial.csv`

For Pixel 4a, the original and appended Scenario 4 files are retained in:

`pixel-4a/raw/`

This allows the complete measurement history to be inspected while keeping the datasets used in the paper unambiguous.

## Statistical analysis

The scripts used to reproduce descriptive statistics, inferential tests, and publication figures are provided in the repository's `analysis/` directory.

The analysis treats the two devices as separate replication contexts rather than pooling their observations into a single sample.

## Notes

All benchmark applications were executed as release builds during the reported experiments.

The repository preserves the original per-run observations; no raw measurement rows from the canonical datasets should be manually edited.
