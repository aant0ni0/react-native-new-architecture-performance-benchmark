import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, PermutationMethod

from data_utils import load_device_file, load_device_registry, normalize_architecture, read_csv_measurements

OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)
DEVICES = load_device_registry()

PERM = PermutationMethod(n_resamples=100_000, rng=np.random.default_rng(20260822))
BOOTSTRAP_RESAMPLES = 100_000
BOOTSTRAP_BASE_SEED = 20260823


def write_csv(df: pd.DataFrame, path: Path) -> None:
    """Write generated analysis CSVs with deterministic LF line endings."""
    df.to_csv(path, index=False, lineterminator="\n")

def cliffs_delta(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    gt = sum(a > b for a in x for b in y)
    lt = sum(a < b for a in x for b in y)
    return (gt - lt) / (len(x) * len(y))



def bootstrap_median_difference_ci(x, y, key, confidence=0.95):
    """Bootstrap CI for median(x) - median(y), with a stable per-comparison seed."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) == 0 or len(y) == 0:
        return np.nan, np.nan, np.nan

    seed_material = f"{BOOTSTRAP_BASE_SEED}|{key}".encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "little")
    rng = np.random.default_rng(seed)

    x_idx = rng.integers(0, len(x), size=(BOOTSTRAP_RESAMPLES, len(x)))
    y_idx = rng.integers(0, len(y), size=(BOOTSTRAP_RESAMPLES, len(y)))
    differences = np.median(x[x_idx], axis=1) - np.median(y[y_idx], axis=1)

    alpha = 1.0 - confidence
    low, high = np.quantile(differences, [alpha / 2, 1 - alpha / 2])
    observed = np.median(x) - np.median(y)
    return observed, low, high

def bh_adjust(pvalues):
    p = np.asarray(pvalues, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    q = ranked * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    q = np.minimum(q, 1.0)
    out = np.empty_like(q)
    out[order] = q
    return out


def describe(df, groups, metrics):
    rows = []
    for keys, group in df.groupby(groups, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(groups, keys))
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors="coerce").dropna()
            row[f"{metric}_mean"] = values.mean()
            row[f"{metric}_median"] = values.median()
            row[f"{metric}_sd"] = values.std(ddof=1)
            row[f"{metric}_n"] = len(values)
        rows.append(row)
    return pd.DataFrame(rows)


def load_device(filename, device, architecture_col="Architecture"):
    return load_device_file(device, filename, architecture_col)


# -----------------------------------------------------------------------------
# RQ1 / Scenario 1
# -----------------------------------------------------------------------------
s1_parts = []
for device in DEVICES:
    d = load_device("s1_latency.csv", device)
    d["Device"] = device.display_label
    s1_parts.append(d)
s1 = pd.concat(s1_parts, ignore_index=True)

write_csv(
    describe(
        s1,
        ["Device", "Architecture", "Interval_ms"],
        ["Avg_Latency_ms", "P95_Latency_ms", "P99_Latency_ms", "CPU_Modal_percent", "RAM_Peak_MB"],
    ),
    OUT / "s1_descriptive.csv",
)

reduction_rows = []
for device in s1["Device"].unique():
    d = s1[s1["Device"] == device]
    for interval in [50, 100, 200, 1000]:
        legacy = d[(d["Architecture"] == "RN_Legacy") & (d["Interval_ms"] == interval)]["Avg_Latency_ms"].astype(float)
        new = d[(d["Architecture"] == "RN_NewArch") & (d["Interval_ms"] == interval)]["Avg_Latency_ms"].astype(float)
        reduction_rows.append([
            device,
            interval,
            legacy.mean(),
            new.mean(),
            100 * (legacy.mean() - new.mean()) / legacy.mean(),
        ])
write_csv(
    pd.DataFrame(
        reduction_rows,
        columns=["Device", "Interval_ms", "Legacy_mean_ms", "New_mean_ms", "New_reduction_pct"],
    ),
    OUT / "s1_new_vs_legacy_reduction.csv",
)


# -----------------------------------------------------------------------------
# RQ2 / Scenario 2
# -----------------------------------------------------------------------------
s2_parts = []
for device in DEVICES:
    d = load_device("s2_scroll.csv", device)
    d["Device"] = device.display_label
    d["Effective_FPS"] = d["Total_Frames_Rendered"].astype(float) / (d["Measured_Duration_ms"].astype(float) / 1000)
    s2_parts.append(d)
s2 = pd.concat(s2_parts, ignore_index=True)

write_csv(
    describe(
        s2,
        ["Device", "Architecture"],
        ["Effective_FPS", "Janky_Frames_Percent", "Frame_P95_ms", "Frame_P99_ms", "CPU_Modal_percent", "RAM_Peak_MB"],
    ),
    OUT / "s2_descriptive.csv",
)


# -----------------------------------------------------------------------------
# RQ3 / Scenario 3
# -----------------------------------------------------------------------------
s3sets = {}
for mode, filename in [("JS-driven", "s3_js_driver.csv"), ("Native-driven", "s3_native_driver.csv")]:
    parts = []
    for device in DEVICES:
        d = load_device(filename, device)
        d["Device"] = device.display_label
        d["Effective_FPS"] = d["Total_Frames_Rendered"].astype(float) / (d["Measured_Duration_ms"].astype(float) / 1000)
        parts.append(d)
    merged = pd.concat(parts, ignore_index=True)
    s3sets[mode] = merged
    write_csv(
        describe(
            merged,
            ["Device", "Architecture"],
            ["FPS modal", "Effective_FPS", "Janky_Frames_Percent", "Frame_P95_ms", "Frame_P99_ms", "CPU_Modal_percent", "RAM_Peak_MB"],
        ),
        OUT / ("s3_js_descriptive.csv" if mode == "JS-driven" else "s3_native_descriptive.csv"),
    )


# -----------------------------------------------------------------------------
# RQ4 / Scenario 4
# Canonical datasets are already disambiguated in data/<device>/.
# Independent New Architecture validation series, when present, are reported
# separately and are NOT pooled with the primary scalar experiment.
# -----------------------------------------------------------------------------
scalar_primary_by_device: dict[str, pd.DataFrame] = {}

scalar_rows = []
for device in DEVICES:
    primary = read_csv_measurements(device.data_dir / "s4_scalar.csv")
    scalar_primary_by_device[device.short_label] = primary
    for tech in primary["Technology"].dropna().unique():
        values = primary[primary["Technology"] == tech]["Operations_per_second"].astype(float)
        scalar_rows.append([
            device.short_label,
            "primary",
            tech,
            values.mean(),
            values.median(),
            values.std(ddof=1),
            100 * values.std(ddof=1) / values.mean(),
            len(values),
        ])

    validation = device.data_dir / "s4_scalar_validation.csv"
    if validation.exists():
        validation_df = read_csv_measurements(validation)
        for tech in validation_df["Technology"].dropna().unique():
            values = validation_df[validation_df["Technology"] == tech]["Operations_per_second"].astype(float)
            scalar_rows.append([
                device.short_label,
                "independent NewArch validation",
                tech,
                values.mean(),
                values.median(),
                values.std(ddof=1),
                100 * values.std(ddof=1) / values.mean(),
                len(values),
            ])
write_csv(
    pd.DataFrame(
        scalar_rows,
        columns=["Device", "Series", "Architecture", "Mean_ops_s", "Median_ops_s", "SD_ops_s", "CV_pct", "n"],
    ),
    OUT / "s4_scalar_summary.csv",
)

array_by_device: dict[str, pd.DataFrame] = {}
array_rows = []
for device in DEVICES:
    df = read_csv_measurements(device.data_dir / "s4_array.csv")
    array_by_device[device.short_label] = df
    for tech in ["RN_Legacy", "RN_NewArch"]:
        for payload in [1, 10, 100, 1000, 10000]:
            values = df[(df["Technology"] == tech) & (df["Payload_Size"] == payload)]["Operations_per_second"].astype(float)
            array_rows.append([
                device.short_label,
                tech,
                payload,
                values.mean(),
                values.median(),
                values.std(ddof=1),
                100 * values.std(ddof=1) / values.mean(),
                len(values),
            ])
write_csv(
    pd.DataFrame(
        array_rows,
        columns=["Device", "Architecture", "Payload_Size", "Mean_ops_s", "Median_ops_s", "SD_ops_s", "CV_pct", "n"],
    ),
    OUT / "s4_array_summary.csv",
)


# -----------------------------------------------------------------------------
# RQ5 / Scenario 5
# -----------------------------------------------------------------------------
s5_parts = []
for device in DEVICES:
    d = read_csv_measurements(device.data_dir / "s5_startup.csv")
    d = normalize_architecture(d, "Technology")
    d["Device"] = device.short_label
    s5_parts.append(d)
s5 = pd.concat(s5_parts, ignore_index=True)

write_csv(
    describe(s5, ["Device", "Technology"], ["TotalTime_ms"]),
    OUT / "s5_descriptive.csv",
)


# -----------------------------------------------------------------------------
# Primary inferential comparisons: Legacy vs New, within each device.
# Mann-Whitney U with 100,000 permutation resamples, Cliff's delta, and a
# deterministic 95% bootstrap CI for the Legacy-minus-New median difference.
# Benjamini-Hochberg correction is applied within each RQ x device family.
# For S3, inferential comparisons are restricted to reproducible graphics-layer
# endpoints; the one-second JS callback-rate summary and CPU/RAM are descriptive.
# -----------------------------------------------------------------------------
stats = []


def add_test(rq, device, metric, x, y):
    x = pd.to_numeric(pd.Series(x), errors="coerce").dropna().astype(float).to_numpy()
    y = pd.to_numeric(pd.Series(y), errors="coerce").dropna().astype(float).to_numpy()
    p = mannwhitneyu(x, y, alternative="two-sided", method=PERM).pvalue
    median_diff, ci_low, ci_high = bootstrap_median_difference_ci(
        x, y, key=f"{rq}|{device}|{metric}"
    )
    stats.append([
        rq, device, metric, p, cliffs_delta(x, y),
        np.median(x), np.median(y), median_diff, ci_low, ci_high,
        len(x), len(y),
    ])


for device in s1["Device"].unique():
    d = s1[s1["Device"] == device]
    for interval in [50, 100, 200, 1000]:
        add_test(
            "RQ1", device, f"Avg callback delay {interval} ms",
            d[(d["Architecture"] == "RN_Legacy") & (d["Interval_ms"] == interval)]["Avg_Latency_ms"],
            d[(d["Architecture"] == "RN_NewArch") & (d["Interval_ms"] == interval)]["Avg_Latency_ms"],
        )

for device in s2["Device"].unique():
    d = s2[s2["Device"] == device]
    for metric in ["Effective_FPS", "Janky_Frames_Percent", "Frame_P99_ms"]:
        add_test("RQ2", device, metric, d[d["Architecture"] == "RN_Legacy"][metric], d[d["Architecture"] == "RN_NewArch"][metric])

for mode, d in s3sets.items():
    for device in d["Device"].unique():
        q = d[d["Device"] == device]
        for metric in ["Effective_FPS", "Janky_Frames_Percent", "Frame_P99_ms"]:
            add_test(
                "RQ3", device, f"{mode}: {metric}",
                q[q["Architecture"] == "RN_Legacy"][metric],
                q[q["Architecture"] == "RN_NewArch"][metric],
            )

for device, d in scalar_primary_by_device.items():
    add_test(
        "RQ4", device, "Scalar",
        d[d["Technology"] == "RN_Legacy"]["Operations_per_second"],
        d[d["Technology"] == "RN_NewArch"]["Operations_per_second"],
    )

for device, d in array_by_device.items():
    for payload in [1, 10, 100, 1000, 10000]:
        add_test(
            "RQ4", device, f"Array payload {payload}",
            d[(d["Technology"] == "RN_Legacy") & (d["Payload_Size"] == payload)]["Operations_per_second"],
            d[(d["Technology"] == "RN_NewArch") & (d["Payload_Size"] == payload)]["Operations_per_second"],
        )

for device in s5["Device"].unique():
    d = s5[s5["Device"] == device]
    add_test(
        "RQ5", device, "Cold start",
        d[d["Technology"] == "RN_Legacy"]["TotalTime_ms"],
        d[d["Technology"] == "RN_NewArch"]["TotalTime_ms"],
    )

stats = pd.DataFrame(
    stats,
    columns=[
        "RQ", "Device", "Metric", "p", "Cliffs_delta",
        "Median_Legacy", "Median_New", "Median_diff_Legacy_minus_New",
        "Median_diff_CI95_low", "Median_diff_CI95_high",
        "n_Legacy", "n_New",
    ],
)
stats["q_BH"] = np.nan
for _, idx in stats.groupby(["RQ", "Device"]).groups.items():
    stats.loc[idx, "q_BH"] = bh_adjust(stats.loc[idx, "p"].to_numpy())
write_csv(stats, OUT / "legacy_vs_new_statistics.csv")

print(f"Analysis complete. Results written to: {OUT}")
