# IEEE Access Manuscript Analysis

Companion analysis for **Performance Trade-offs of React Native's New Architecture
on Android: A Two-Device Empirical Study**, by Antoni Michalczak and Filip Kruzel.

The `supplement/`, `tables/`, and `figures/` directories are imported unchanged
from the final manuscript source package dated 10 October 2026. This directory
contains the analysis artifact, not the manuscript PDF or its author photographs.

## Reproduce and Verify

From the repository root, using Python 3.11 in a virtual environment:

```sh
python -m pip install -r paper/ieee-access/supplement/reference/analysis/requirements-lock.txt
python paper/ieee-access/verify.py
```

The verifier runs the bundled scripts in a temporary copy. It compares all five
result CSVs at a tolerance of `1e-12`, checks the seven LaTeX table/macro files,
checks the reference-file SHA-256 manifest, and regenerates all four PDF figures.
Runtime-version fields are reported but excluded from comparisons of the
scientific verification summary. Figure PDF bytes are not compared because
rendering metadata can differ between runs. The checkout is left unchanged.

Expected results: **700 records, 70 ten-run cells, 40 comparisons, and 184756
permutation assignments**. There are 31 significant comparisons with RQ-wise
Holm adjustment, 33 with RQ-wise BH, and 30 with study-wide Holm adjustment.

To regenerate outputs directly in this directory:

```sh
python paper/ieee-access/supplement/reproduce_results.py
python paper/ieee-access/supplement/make_figures.py
```

Regression tests for the verifier:

```sh
python -m unittest discover -s paper/ieee-access/tests -v
```

## Package Layout

| Path | Contents |
| --- | --- |
| `supplement/reference/` | Frozen v1.0.4 data, archived analysis, license, and citation metadata |
| `supplement/reproduce_results.py` | Exact tests, correction families, sensitivity analyses, and LaTeX tables |
| `supplement/make_figures.py` | Four manuscript figures |
| `supplement/results/` | Numerical results, sample inventory, and verification metadata |
| `supplement/acquisition_metadata.json` | Device settings and measurement-series provenance |
| `tables/` | Six result tables and one numerical-macro file |
| `figures/` | Four vector PDF figures |

Further methodological and acquisition details are in
[`supplement/README.txt`](supplement/README.txt).

## Relationship to RNArchBench v1.0.4

The reference software and observations are archived under
[10.5281/zenodo.22087347](https://doi.org/10.5281/zenodo.22087347), at Git commit
`4e7dac59541d650a7f85cab76af8080836849bb4`.

The root `analysis/` directory reproduces the archived statistical analysis.
This supplement adds the manuscript's exact tests, RQ-wise Holm correction
across both devices, and sensitivity analyses using the same observations.
Neither the original release nor its DOI is replaced by this addition.

The local `.gitattributes` preserves the imported files byte-for-byte on Windows
and Linux so that the bundled reference checksums remain valid. Keep
`supplement/`, `tables/`, and `figures/` together when distributing the package.
