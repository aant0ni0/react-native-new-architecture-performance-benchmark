# Replication Notes

This document separates what can be reproduced exactly from what is preserved only at the level of the frozen measurement outputs.

## Exact analysis reproducibility

The repository contains the canonical per-run CSV datasets used by the analysis pipeline together with the scripts that generate derived statistics and figures. With the pinned direct dependencies in `analysis/requirements-lock.txt`, the numerical CSV outputs are intended to be exactly reproducible. Figure content is reproducible, although binary PDF/PNG bytes may vary with rendering/file-metadata differences across platforms.

From the repository root:

```powershell
python -m pip install -r .\analysis\requirements-lock.txt
python .\analysis\reproduce_analysis.py
python .\analysis\make_figures.py
```

The two reference devices are analyzed as separate replication contexts.

## Historical acquisition provenance

The canonical datasets are preserved, but not every intermediate artifact from the original measurement acquisition was retained.

In particular:

- complete one-second S3 JavaScript callback samples are not available for the historical runs;
- complete individual S1 callback samples are not available for every historical run;
- the complete historical ADB/orchestration script used during every acquisition session was not retained;
- hashes of the exact historical APK files are not available.

These limitations do not prevent reproduction of the published analysis from the canonical CSVs, but they mean that historical measurement acquisition is only partially reproducible.

## Scenario 1 timing boundary

S1 measures update-to-next-frame-callback delay rather than a native paint event. The current React Native implementation timestamps immediately before scheduling the state-update computation, whereas the native baseline computes the new data values before taking its timestamp and then notifies the adapter. This creates a small instrumentation-boundary asymmetry in absolute RN-vs-Native S1 comparisons. Legacy-vs-New React Native comparisons use the same timing boundary.

This historical timing construct is preserved for continuity; prospective studies should describe it precisely rather than labeling it end-to-end rendering or paint latency.

## v1.0.2 canonical derived-field correction

An artifact audit found three `Operations_per_second` cells whose values were inconsistent with their preserved `Operations_Count` and `Total_Duration_ms`. v1.0.2 normalizes only those redundant derived cells in the canonical datasets. The raw provenance files are not rewritten. Exact affected rows and the formula are documented in `data/README.md`.

## Post-experiment usability improvements

Several repository changes improve prospective replication without changing the primary historical measurements. The only v1.0.2 canonical data edits are the three documented recomputations of redundant S4 throughput fields from unchanged counts and durations.

### Scenario 3 driver selector

The current React Native application allows `JS-driven` and `Native-driven` animation modes to be selected at runtime.

The historical S3 datasets were collected as separate fixed driver configurations before this runtime selector was added.

### Scenario 4 payload selector

The current React Native communication benchmark allows payload sizes 1, 10, 100, 1,000, and 10,000 to be selected at runtime.

This improves future replication ergonomics. The canonical datasets retain the actual measurement series used by the study.

### Native Scenario 4

A native Android Scenario 4 is intentionally not part of the current benchmark suite. Scenario 4 measures the JavaScript-native communication boundary and therefore has no direct like-for-like native-only equivalent.

## Pixel 4a validation series

The primary Pixel 4a scalar dataset and its independent New Architecture validation series are kept separate.

The validation series is a robustness check and is not automatically pooled with the primary scalar experiment.

For the Pixel 4a array benchmark, clean-build repeats for New Architecture payload sizes 1 and 10 are used in the canonical dataset. Earlier and appended series are retained under `data/pixel-4a/raw/` for provenance.

See `data/README.md` for the exact canonical-selection rules.

## Perfetto

Perfetto traces for selected Moto G72 scrolling and animation scenarios are supplementary qualitative diagnostic artifacts. They are not additional observations in the primary statistical tests.

The trace binaries are distributed as release assets. Expected SHA-256 hashes are stored in `perfetto/SHA256SUMS.txt`.

## Prospective replications

A fuller prospective acquisition workflow, including release builds, Windows path-length guidance, APK preservation, and scenario-specific collection notes, is provided in `ACQUISITION_GUIDE.md`.

For a new device:

1. record Android version and build fingerprint;
2. capture the repository revision and toolchain with `scripts/capture_environment.ps1`;
3. configure the React Native architecture with `scripts/configure_rn_architecture.py`;
4. build release variants;
5. run the desired benchmark configurations with fixed repetitions;
6. preserve per-run outputs and any lower-level raw samples generated by the acquisition workflow;
7. hash retained release APKs with `scripts/hash_release_apks.ps1`;
8. keep new-device data separate from the frozen reference datasets unless explicitly extending the study.
