# Analysis scripts

Run from the repository root after installing the Python dependencies:

```bash
python -m pip install -r analysis/requirements.txt
python analysis/reproduce_analysis.py
python analysis/make_figures.py
```

Outputs:

- `analysis/results/` — descriptive and inferential statistics used in the manuscript
- `figures/` — publication figures in PDF and PNG formats

The two devices are analyzed as separate replication contexts. The Pixel 4a scalar validation series is used only as an independent robustness check and is not pooled with the primary scalar experiment.

Primary Legacy-vs-New comparisons use a two-sided Mann-Whitney U statistic with 100,000 permutation resamples, Cliff's delta, and Benjamini-Hochberg adjustment within each RQ × device family.

### Decimal separators

The loader accepts both decimal points and decimal commas in measurement CSVs. This is required for some exported Pixel/Moto result files (for example `56,03`). The implementation is compatible with pandas 2.x and 3.x string dtypes.
