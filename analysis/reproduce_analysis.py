from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, PermutationMethod

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

PERM = PermutationMethod(n_resamples=100_000, rng=np.random.default_rng(20260822))


def read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig").dropna(how="all")

    # Some measurement CSVs use a decimal comma (e.g. 56,03).
    # pandas 3.x may load such columns as StringDtype rather than object,
    # therefore check all string-like columns instead of only dtype == object.
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_string_dtype(series.dtype) or series.dtype == object:
            cleaned = series.astype("string").str.strip().str.replace(",", ".", regex=False)
            numeric = pd.to_numeric(cleaned, errors="coerce")
            nonempty = cleaned.notna().sum()

            # Convert a column only when it is predominantly numeric.
            # Text identifiers such as RN_Legacy remain strings.
            if nonempty and numeric.notna().sum() >= max(1, int(np.ceil(0.8 * nonempty))):
                df[col] = numeric

    return df


def normalize_architecture(df: pd.DataFrame, col="Architecture") -> pd.DataFrame:
    if col in df.columns:
        df[col] = df[col].replace({
            "Legacy": "RN_Legacy",
            "RN Legacy": "RN_Legacy",
            "NewArch": "RN_NewArch",
            "New Architecture": "RN_NewArch",
            "RN New Architecture": "RN_NewArch",
            "Android": "Native",
            "Android Native": "Native",
        })
    return df


def cliffs_delta(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    gt = sum(a > b for a in x for b in y)
    lt = sum(a < b for a in x for b in y)
    return (gt - lt) / (len(x) * len(y))


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
    df = read_csv(DATA / device / filename)
    if architecture_col in df.columns:
        df = normalize_architecture(df, architecture_col)
    return df


# -----------------------------------------------------------------------------
# RQ1 / Scenario 1
# -----------------------------------------------------------------------------
s1_parts = []
for folder, label in [("moto-g72", "Moto G72 (120 Hz)"), ("pixel-4a", "Pixel 4a (60 Hz)")]:
    d = load_device("s1_latency.csv", folder)
    d["Device"] = label
    s1_parts.append(d)
s1 = pd.concat(s1_parts, ignore_index=True)

describe(
    s1,
    ["Device", "Architecture", "Interval_ms"],
    ["Avg_Latency_ms", "P95_Latency_ms", "P99_Latency_ms", "CPU_Modal_percent", "RAM_Peak_MB"],
).to_csv(OUT / "s1_descriptive.csv", index=False)

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
pd.DataFrame(
    reduction_rows,
    columns=["Device", "Interval_ms", "Legacy_mean_ms", "New_mean_ms", "New_reduction_pct"],
).to_csv(OUT / "s1_new_vs_legacy_reduction.csv", index=False)


# -----------------------------------------------------------------------------
# RQ2 / Scenario 2
# -----------------------------------------------------------------------------
s2_parts = []
for folder, label in [("moto-g72", "Moto G72 (120 Hz)"), ("pixel-4a", "Pixel 4a (60 Hz)")]:
    d = load_device("s2_scroll.csv", folder)
    d["Device"] = label
    d["Effective_FPS"] = d["Total_Frames_Rendered"].astype(float) / (d["Measured_Duration_ms"].astype(float) / 1000)
    s2_parts.append(d)
s2 = pd.concat(s2_parts, ignore_index=True)

describe(
    s2,
    ["Device", "Architecture"],
    ["Effective_FPS", "Janky_Frames_Percent", "Frame_P95_ms", "Frame_P99_ms", "CPU_Modal_percent", "RAM_Peak_MB"],
).to_csv(OUT / "s2_descriptive.csv", index=False)


# -----------------------------------------------------------------------------
# RQ3 / Scenario 3
# -----------------------------------------------------------------------------
s3sets = {}
for mode, filename in [("JS-driven", "s3_js_driver.csv"), ("Native-driven", "s3_native_driver.csv")]:
    parts = []
    for folder, label in [("moto-g72", "Moto G72 (120 Hz)"), ("pixel-4a", "Pixel 4a (60 Hz)")]:
        d = load_device(filename, folder)
        d["Device"] = label
        d["Effective_FPS"] = d["Total_Frames_Rendered"].astype(float) / (d["Measured_Duration_ms"].astype(float) / 1000)
        parts.append(d)
    merged = pd.concat(parts, ignore_index=True)
    s3sets[mode] = merged
    describe(
        merged,
        ["Device", "Architecture"],
        ["FPS modal", "Effective_FPS", "Janky_Frames_Percent", "Frame_P95_ms", "Frame_P99_ms", "CPU_Modal_percent", "RAM_Peak_MB"],
    ).to_csv(OUT / ("s3_js_descriptive.csv" if mode == "JS-driven" else "s3_native_descriptive.csv"), index=False)


# -----------------------------------------------------------------------------
# RQ4 / Scenario 4
# Canonical datasets are already disambiguated in data/<device>/.
# Pixel scalar validation is reported separately and is NOT pooled.
# -----------------------------------------------------------------------------
moto_scalar = read_csv(DATA / "moto-g72" / "s4_scalar.csv")
pixel_scalar = read_csv(DATA / "pixel-4a" / "s4_scalar.csv")
pixel_scalar_validation = read_csv(DATA / "pixel-4a" / "s4_scalar_validation.csv")

scalar_rows = []
for device, series, df in [
    ("Moto G72", "primary", moto_scalar),
    ("Pixel 4a", "primary", pixel_scalar),
    ("Pixel 4a", "independent NewArch validation", pixel_scalar_validation),
]:
    for tech in df["Technology"].dropna().unique():
        values = df[df["Technology"] == tech]["Operations_per_second"].astype(float)
        scalar_rows.append([
            device,
            series,
            tech,
            values.mean(),
            values.median(),
            values.std(ddof=1),
            100 * values.std(ddof=1) / values.mean(),
            len(values),
        ])
pd.DataFrame(
    scalar_rows,
    columns=["Device", "Series", "Architecture", "Mean_ops_s", "Median_ops_s", "SD_ops_s", "CV_pct", "n"],
).to_csv(OUT / "s4_scalar_summary.csv", index=False)

moto_array = read_csv(DATA / "moto-g72" / "s4_array.csv")
pixel_array = read_csv(DATA / "pixel-4a" / "s4_array.csv")
array_rows = []
for device, df in [("Moto G72", moto_array), ("Pixel 4a", pixel_array)]:
    for tech in ["RN_Legacy", "RN_NewArch"]:
        for payload in [1, 10, 100, 1000, 10000]:
            values = df[(df["Technology"] == tech) & (df["Payload_Size"] == payload)]["Operations_per_second"].astype(float)
            array_rows.append([
                device,
                tech,
                payload,
                values.mean(),
                values.median(),
                values.std(ddof=1),
                100 * values.std(ddof=1) / values.mean(),
                len(values),
            ])
pd.DataFrame(
    array_rows,
    columns=["Device", "Architecture", "Payload_Size", "Mean_ops_s", "Median_ops_s", "SD_ops_s", "CV_pct", "n"],
).to_csv(OUT / "s4_array_summary.csv", index=False)


# -----------------------------------------------------------------------------
# RQ5 / Scenario 5
# -----------------------------------------------------------------------------
s5_parts = []
for folder, label in [("moto-g72", "Moto G72"), ("pixel-4a", "Pixel 4a")]:
    d = read_csv(DATA / folder / "s5_startup.csv")
    d["Technology"] = d["Technology"].replace({
        "Legacy": "RN_Legacy",
        "NewArch": "RN_NewArch",
        "New Architecture": "RN_NewArch",
        "Android": "Native",
    })
    d["Device"] = label
    s5_parts.append(d)
s5 = pd.concat(s5_parts, ignore_index=True)

describe(s5, ["Device", "Technology"], ["TotalTime_ms"]).to_csv(OUT / "s5_descriptive.csv", index=False)


# -----------------------------------------------------------------------------
# Primary inferential comparisons: Legacy vs New, within each device.
# Mann-Whitney U with 100,000 permutation resamples and Cliff's delta.
# Benjamini-Hochberg correction is applied within each RQ x device family.
# -----------------------------------------------------------------------------
stats = []


def add_test(rq, device, metric, x, y):
    x = pd.to_numeric(pd.Series(x), errors="coerce").dropna().astype(float).to_numpy()
    y = pd.to_numeric(pd.Series(y), errors="coerce").dropna().astype(float).to_numpy()
    p = mannwhitneyu(x, y, alternative="two-sided", method=PERM).pvalue
    stats.append([rq, device, metric, p, cliffs_delta(x, y), len(x), len(y)])


for device in s1["Device"].unique():
    d = s1[s1["Device"] == device]
    for interval in [50, 100, 200, 1000]:
        add_test(
            "RQ1", device, f"Avg latency {interval} ms",
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
        for metric in ["FPS modal", "Effective_FPS", "Janky_Frames_Percent", "Frame_P99_ms", "CPU_Modal_percent"]:
            add_test(
                "RQ3", device, f"{mode}: {metric}",
                q[q["Architecture"] == "RN_Legacy"][metric],
                q[q["Architecture"] == "RN_NewArch"][metric],
            )

for device, d in [("Moto G72", moto_scalar), ("Pixel 4a", pixel_scalar)]:
    add_test(
        "RQ4", device, "Scalar",
        d[d["Technology"] == "RN_Legacy"]["Operations_per_second"],
        d[d["Technology"] == "RN_NewArch"]["Operations_per_second"],
    )

for device, d in [("Moto G72", moto_array), ("Pixel 4a", pixel_array)]:
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

stats = pd.DataFrame(stats, columns=["RQ", "Device", "Metric", "p", "Cliffs_delta", "n_Legacy", "n_New"])
stats["q_BH"] = np.nan
for _, idx in stats.groupby(["RQ", "Device"]).groups.items():
    stats.loc[idx, "q_BH"] = bh_adjust(stats.loc[idx, "p"].to_numpy())
stats.to_csv(OUT / "legacy_vs_new_statistics.csv", index=False)

print(f"Analysis complete. Results written to: {OUT}")
