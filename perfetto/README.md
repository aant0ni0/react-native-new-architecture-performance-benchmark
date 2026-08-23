# Perfetto Traces

This directory documents the system-level Perfetto traces collected as part of the extended benchmark evaluation.

The traces were recorded on the Motorola Moto G72 for selected scrolling and animation scenarios and are intended to support qualitative inspection of scheduling, rendering, and execution behavior.

## Trace Set

The collected trace set contains:

```text
S2_Native_scroll_motoG72.pftrace
S2_RN_Legacy_scroll_motoG72.pftrace
S2_RN_NewArch_scroll_motoG72.pftrace
S3_Native_animation_motoG72.pftrace
S3_RN_Legacy_JS_animation_motoG72.pftrace
S3_RN_NewArch_JS_animation_motoG72.pftrace
```

One locally collected Legacy scrolling trace originally contained a trailing underscore in its filename. For publication and archival purposes, it should be normalized to:

```text
S2_RN_Legacy_scroll_motoG72.pftrace
```

## Why the Trace Files Are Not Stored Directly in Git

Perfetto trace files are large binary artifacts and are not suitable for inclusion in the standard Git repository history.

The repository therefore contains trace documentation and the finalized checksum manifest `SHA256SUMS.txt`.

The binary trace files are distributed separately through the associated GitHub release/research-artifact storage.

## Scope

The Perfetto traces are supplementary diagnostic artifacts.

They are not used as additional observations in the primary statistical tests. The quantitative results reported in the study are reproduced from the canonical CSV datasets under:

```text
data/moto-g72/
data/pixel-4a/
```

The traces are used to support interpretation of selected Scenario 2 and Scenario 3 behaviors.

## Opening the Traces

Perfetto traces can be opened with the Perfetto trace viewer.

When using the archived trace package, verify file integrity against the checksum manifest supplied with the replication package before analysis.

## Provenance

Device:

```text
Motorola Moto G72
```

Scenarios represented:

- Scenario 2 — large-list scrolling,
- Scenario 3 — JavaScript-driven UI animation.

Implementations represented:

- native Android,
- React Native Legacy Architecture,
- React Native New Architecture.
