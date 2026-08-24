from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from data_utils import DeviceSpec, load_device_registry, read_csv_measurements

ROOT = Path(__file__).resolve().parents[1]

SCENARIO_FILES = {
    "s1_latency.csv",
    "s2_scroll.csv",
    "s3_js_driver.csv",
    "s3_native_driver.csv",
    "s4_scalar.csv",
    "s4_array.csv",
    "s5_startup.csv",
}

OPTIONAL_FILES = {"s4_scalar_validation.csv"}

S1_CONDITIONS = {
    (app, architecture, interval)
    for app, architecture in {
        ("Native", "Android"),
        ("RN", "Legacy"),
        ("RN", "New Architecture"),
    }
    for interval in (50.0, 100.0, 200.0, 1000.0)
}
S2_CONDITIONS = {
    ("Native", "Native", 1000.0),
    ("RN", "Legacy", 1000.0),
    ("RN", "NewArch", 1000.0),
}
S3_JS_CONDITIONS = {
    ("Native", "Native"),
    ("RN", "Legacy"),
    ("RN", "NewArch"),
}
S3_NATIVE_DRIVER_CONDITIONS = {
    ("RN", "Legacy"),
    ("RN", "NewArch"),
}
S4_TECHNOLOGIES = {"RN_Legacy", "RN_NewArch"}
S4_ARRAY_CONDITIONS = {
    (technology, payload_size)
    for technology in S4_TECHNOLOGIES
    for payload_size in (1, 10, 100, 1000, 10000)
}
S5_TECHNOLOGIES = {"Native", "RN_Legacy", "RN_NewArch"}


def add_error(errors: list[str], path: Path, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {message}")


def require_columns(
    errors: list[str], path: Path, df: pd.DataFrame, required: list[str]
) -> bool:
    missing = [column for column in required if column not in df.columns]
    if missing:
        add_error(errors, path, f"missing required columns: {', '.join(missing)}")
        return False
    return True


def validate_no_missing(
    errors: list[str], path: Path, df: pd.DataFrame, columns: list[str]
) -> None:
    missing_counts = {
        column: int(df[column].isna().sum())
        for column in columns
        if column in df.columns and int(df[column].isna().sum()) > 0
    }
    if missing_counts:
        parts = [f"{column}={count}" for column, count in missing_counts.items()]
        add_error(errors, path, f"missing values in required fields: {', '.join(parts)}")


def validate_allowed_values(
    errors: list[str],
    path: Path,
    df: pd.DataFrame,
    column: str,
    allowed: set[str],
) -> None:
    if column not in df.columns:
        return
    values = {str(value) for value in df[column].dropna().unique()}
    invalid = sorted(values - allowed)
    if invalid:
        add_error(
            errors,
            path,
            f"unexpected values in {column}: {', '.join(invalid)}",
        )


def validate_positive_numeric(
    errors: list[str], path: Path, df: pd.DataFrame, columns: list[str]
) -> None:
    for column in columns:
        if column not in df.columns:
            continue
        numeric = pd.to_numeric(df[column], errors="coerce")
        if numeric.isna().any():
            add_error(errors, path, f"{column} contains non-numeric values")
            continue
        if (numeric <= 0).any():
            add_error(errors, path, f"{column} contains non-positive values")


def validate_nonnegative_numeric(
    errors: list[str], path: Path, df: pd.DataFrame, columns: list[str]
) -> None:
    for column in columns:
        if column not in df.columns:
            continue
        numeric = pd.to_numeric(df[column], errors="coerce")
        if numeric.isna().any():
            add_error(errors, path, f"{column} contains non-numeric values")
            continue
        if (numeric < 0).any():
            add_error(errors, path, f"{column} contains negative values")


def validate_unique_rows(
    errors: list[str], path: Path, df: pd.DataFrame, keys: list[str]
) -> None:
    if not set(keys).issubset(df.columns):
        return
    duplicates = int(df.duplicated(subset=keys).sum())
    if duplicates:
        add_error(errors, path, f"found {duplicates} duplicate rows for keys {keys}")


def validate_run_groups(
    errors: list[str],
    path: Path,
    df: pd.DataFrame,
    group_columns: list[str],
    expected_runs: int,
) -> None:
    if not set(group_columns + ["Run"]).issubset(df.columns):
        return

    for keys, group in df.groupby(group_columns, dropna=False):
        runs = pd.to_numeric(group["Run"], errors="coerce")
        if runs.isna().any():
            add_error(errors, path, f"non-numeric run identifiers in group {keys}")
            continue

        ordered = sorted(int(value) for value in runs)
        expected = list(range(1, expected_runs + 1))
        if ordered != expected:
            add_error(
                errors,
                path,
                f"group {keys} has runs {ordered}, expected {expected}",
            )


def format_condition(columns: list[str], condition: tuple[object, ...]) -> str:
    return ", ".join(
        f"{column}={value!r}" for column, value in zip(columns, condition)
    )


def validate_expected_conditions(
    errors: list[str],
    path: Path,
    df: pd.DataFrame,
    columns: list[str],
    expected_conditions: set[tuple[object, ...]],
) -> None:
    if not set(columns).issubset(df.columns):
        return

    actual_conditions = set(
        df[columns].drop_duplicates().itertuples(index=False, name=None)
    )
    missing = expected_conditions - actual_conditions
    unexpected = actual_conditions - expected_conditions

    if missing:
        formatted = "; ".join(
            format_condition(columns, condition)
            for condition in sorted(missing, key=lambda item: tuple(map(str, item)))
        )
        add_error(errors, path, "missing required condition(s): " + formatted)
    if unexpected:
        formatted = "; ".join(
            format_condition(columns, condition)
            for condition in sorted(unexpected, key=lambda item: tuple(map(str, item)))
        )
        add_error(errors, path, "unexpected condition(s): " + formatted)


def validate_app_architecture_alignment(
    errors: list[str],
    path: Path,
    df: pd.DataFrame,
    expected_pairs: set[tuple[str, str]],
) -> None:
    if not {"App", "Architecture"}.issubset(df.columns):
        return
    actual_pairs = {
        (str(app), str(architecture))
        for app, architecture in df[["App", "Architecture"]].dropna().itertuples(index=False)
    }
    invalid = sorted(actual_pairs - expected_pairs)
    if invalid:
        formatted = [f"{app}/{architecture}" for app, architecture in invalid]
        add_error(
            errors,
            path,
            "unexpected App/Architecture combinations: " + ", ".join(formatted),
        )


def validate_s4_throughput(errors: list[str], path: Path, df: pd.DataFrame) -> None:
    required = ["Operations_Count", "Total_Duration_ms", "Operations_per_second"]
    if not require_columns(errors, path, df, required):
        return

    counts = pd.to_numeric(df["Operations_Count"], errors="coerce")
    durations = pd.to_numeric(df["Total_Duration_ms"], errors="coerce")
    reported = pd.to_numeric(df["Operations_per_second"], errors="coerce")
    expected = np.rint(counts / (durations / 1000.0))
    mismatches = df.loc[reported != expected]

    if not mismatches.empty:
        add_error(
            errors,
            path,
            f"{len(mismatches)} row(s) have inconsistent Operations_per_second",
        )


def validate_s1(errors: list[str], path: Path, expected_runs: int) -> None:
    df = read_csv_measurements(path)
    required = [
        "App",
        "Architecture",
        "Scenario",
        "Interval_ms",
        "Run",
        "Avg_Latency_ms",
        "P95_Latency_ms",
        "P99_Latency_ms",
        "Measured_Duration_ms",
        "CPU_Modal_percent",
        "CPU_Peak_percent",
        "RAM_Peak_MB",
    ]
    if not require_columns(errors, path, df, required):
        return

    validate_no_missing(errors, path, df, required)
    validate_allowed_values(errors, path, df, "App", {"Native", "RN"})
    validate_allowed_values(
        errors, path, df, "Architecture", {"Android", "Legacy", "New Architecture"}
    )
    validate_allowed_values(errors, path, df, "Scenario", {"Real-time updates"})
    validate_app_architecture_alignment(
        errors,
        path,
        df,
        {
            ("Native", "Android"),
            ("RN", "Legacy"),
            ("RN", "New Architecture"),
        },
    )
    validate_expected_conditions(
        errors, path, df, ["App", "Architecture", "Interval_ms"], S1_CONDITIONS
    )
    validate_positive_numeric(
        errors,
        path,
        df,
        [
            "Interval_ms",
            "Avg_Latency_ms",
            "P95_Latency_ms",
            "P99_Latency_ms",
            "Measured_Duration_ms",
            "RAM_Peak_MB",
        ],
    )
    validate_nonnegative_numeric(
        errors,
        path,
        df,
        [
            "CPU_Modal_percent",
            "CPU_Peak_percent",
            "Janky_Frames_Percent",
            "Total_Frames_Rendered",
        ],
    )
    validate_unique_rows(errors, path, df, ["Architecture", "Interval_ms", "Run"])
    validate_run_groups(errors, path, df, ["Architecture", "Interval_ms"], expected_runs)


def validate_s2(errors: list[str], path: Path, expected_runs: int) -> None:
    df = read_csv_measurements(path)
    required = [
        "App",
        "Architecture",
        "Scenario",
        "List_Size",
        "Run",
        "Status",
        "Measured_Duration_ms",
        "CPU_Modal_percent",
        "CPU_Peak_percent",
        "RAM_Peak_MB",
        "Total_Frames_Rendered",
        "Janky_Frames_Percent",
        "Frame_P99_ms",
    ]
    if not require_columns(errors, path, df, required):
        return

    validate_no_missing(errors, path, df, required)
    validate_allowed_values(errors, path, df, "App", {"Native", "RN"})
    validate_allowed_values(errors, path, df, "Architecture", {"Native", "Legacy", "NewArch"})
    validate_allowed_values(errors, path, df, "Scenario", {"Large list scroll"})
    validate_allowed_values(errors, path, df, "Status", {"Finished"})
    validate_app_architecture_alignment(
        errors,
        path,
        df,
        {
            ("Native", "Native"),
            ("RN", "Legacy"),
            ("RN", "NewArch"),
        },
    )
    validate_expected_conditions(
        errors, path, df, ["App", "Architecture", "List_Size"], S2_CONDITIONS
    )
    validate_positive_numeric(
        errors,
        path,
        df,
        [
            "List_Size",
            "Measured_Duration_ms",
            "RAM_Peak_MB",
            "Total_Frames_Rendered",
            "Frame_P99_ms",
        ],
    )
    validate_nonnegative_numeric(
        errors,
        path,
        df,
        ["CPU_Modal_percent", "CPU_Peak_percent", "Janky_Frames_Percent"],
    )
    validate_unique_rows(errors, path, df, ["Architecture", "Run"])
    validate_run_groups(errors, path, df, ["Architecture"], expected_runs)


def validate_s3(
    errors: list[str],
    path: Path,
    expected_runs: int,
    expected_conditions: set[tuple[str, str]],
) -> None:
    df = read_csv_measurements(path)
    required = [
        "App",
        "Architecture",
        "Scenario",
        "Animated_Boxes",
        "Run",
        "Status",
        "FPS modal",
        "Measured_Duration_ms",
        "CPU_Modal_percent",
        "CPU_Peak_percent",
        "RAM_Peak_MB",
        "Total_Frames_Rendered",
        "Janky_Frames_Percent",
        "Frame_P99_ms",
    ]
    if not require_columns(errors, path, df, required):
        return

    validate_no_missing(errors, path, df, required)
    validate_allowed_values(
        errors, path, df, "App", {app for app, _ in expected_conditions}
    )
    validate_allowed_values(
        errors,
        path,
        df,
        "Architecture",
        {architecture for _, architecture in expected_conditions},
    )
    validate_allowed_values(errors, path, df, "Scenario", {"Animations"})
    validate_allowed_values(errors, path, df, "Status", {"Finished"})
    validate_expected_conditions(
        errors, path, df, ["App", "Architecture"], expected_conditions
    )
    validate_positive_numeric(
        errors,
        path,
        df,
        [
            "Animated_Boxes",
            "FPS modal",
            "Measured_Duration_ms",
            "RAM_Peak_MB",
            "Total_Frames_Rendered",
            "Frame_P99_ms",
        ],
    )
    validate_nonnegative_numeric(
        errors,
        path,
        df,
        ["CPU_Modal_percent", "CPU_Peak_percent", "Janky_Frames_Percent"],
    )
    validate_unique_rows(errors, path, df, ["Architecture", "Run"])
    validate_run_groups(errors, path, df, ["Architecture"], expected_runs)


def validate_s4_scalar(
    errors: list[str], path: Path, expected_runs: int, expected_technologies: set[str]
) -> None:
    df = read_csv_measurements(path)
    required = [
        "Technology",
        "Test",
        "Run",
        "Operations_Count",
        "Total_Duration_ms",
        "Operations_per_second",
    ]
    if not require_columns(errors, path, df, required):
        return

    validate_no_missing(errors, path, df, required)
    validate_allowed_values(errors, path, df, "Technology", expected_technologies)
    validate_allowed_values(errors, path, df, "Test", {"Simple"})
    validate_expected_conditions(
        errors,
        path,
        df,
        ["Technology"],
        {(technology,) for technology in expected_technologies},
    )
    validate_positive_numeric(
        errors,
        path,
        df,
        ["Run", "Operations_Count", "Total_Duration_ms", "Operations_per_second"],
    )
    validate_unique_rows(errors, path, df, ["Technology", "Run"])
    validate_run_groups(errors, path, df, ["Technology"], expected_runs)
    validate_s4_throughput(errors, path, df)


def validate_s4_array(errors: list[str], path: Path, expected_runs: int) -> None:
    df = read_csv_measurements(path)
    required = [
        "Technology",
        "Test",
        "Payload_Size",
        "Run",
        "Operations_Count",
        "Total_Duration_ms",
        "Operations_per_second",
    ]
    if not require_columns(errors, path, df, required):
        return

    validate_no_missing(errors, path, df, required)
    validate_allowed_values(errors, path, df, "Technology", {"RN_Legacy", "RN_NewArch"})
    validate_allowed_values(errors, path, df, "Test", {"Complex"})
    validate_expected_conditions(
        errors, path, df, ["Technology", "Payload_Size"], S4_ARRAY_CONDITIONS
    )
    validate_positive_numeric(
        errors,
        path,
        df,
        [
            "Payload_Size",
            "Run",
            "Operations_Count",
            "Total_Duration_ms",
            "Operations_per_second",
        ],
    )
    validate_unique_rows(errors, path, df, ["Technology", "Payload_Size", "Run"])
    validate_run_groups(errors, path, df, ["Technology", "Payload_Size"], expected_runs)
    validate_s4_throughput(errors, path, df)


def validate_s5(errors: list[str], path: Path, expected_runs: int) -> None:
    df = read_csv_measurements(path)
    required = ["Technology", "Run", "TotalTime_ms", "WaitTime_ms"]
    if not require_columns(errors, path, df, required):
        return

    validate_no_missing(errors, path, df, required)
    validate_allowed_values(errors, path, df, "Technology", S5_TECHNOLOGIES)
    validate_expected_conditions(
        errors,
        path,
        df,
        ["Technology"],
        {(technology,) for technology in S5_TECHNOLOGIES},
    )
    validate_positive_numeric(errors, path, df, ["Run", "TotalTime_ms", "WaitTime_ms"])
    validate_unique_rows(errors, path, df, ["Technology", "Run"])
    validate_run_groups(errors, path, df, ["Technology"], expected_runs)


def validate_device(
    device: DeviceSpec, expected_runs: int, errors: list[str], validated: list[Path]
) -> None:
    canonical = {path.name for path in device.data_dir.glob("*.csv")}
    missing = sorted(SCENARIO_FILES - canonical)
    extra = sorted(canonical - SCENARIO_FILES - OPTIONAL_FILES)

    for filename in missing:
        add_error(errors, device.data_dir / filename, "missing canonical scenario file")
    for filename in extra:
        add_error(errors, device.data_dir / filename, "unexpected top-level CSV file")

    for filename in sorted(canonical & SCENARIO_FILES):
        path = device.data_dir / filename
        if filename == "s1_latency.csv":
            validate_s1(errors, path, expected_runs)
        elif filename == "s2_scroll.csv":
            validate_s2(errors, path, expected_runs)
        elif filename == "s3_js_driver.csv":
            validate_s3(
                errors,
                path,
                expected_runs,
                expected_conditions=S3_JS_CONDITIONS,
            )
        elif filename == "s3_native_driver.csv":
            validate_s3(
                errors,
                path,
                expected_runs,
                expected_conditions=S3_NATIVE_DRIVER_CONDITIONS,
            )
        elif filename == "s4_scalar.csv":
            validate_s4_scalar(errors, path, expected_runs, S4_TECHNOLOGIES)
        elif filename == "s4_array.csv":
            validate_s4_array(errors, path, expected_runs)
        elif filename == "s5_startup.csv":
            validate_s5(errors, path, expected_runs)
        validated.append(path)

    validation_path = device.data_dir / "s4_scalar_validation.csv"
    if validation_path.exists():
        validate_s4_scalar(errors, validation_path, expected_runs, {"RN_NewArch"})
        validated.append(validation_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate RNArchBench canonical measurement CSV files."
    )
    parser.add_argument(
        "--device",
        action="append",
        dest="devices",
        help="Validate only the given device folder from data/devices.csv. Repeat as needed.",
    )
    parser.add_argument(
        "--expected-runs",
        type=int,
        default=10,
        help="Expected run count per condition (default: 10).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    devices = load_device_registry()
    if args.devices:
        selected = set(args.devices)
        devices = [device for device in devices if device.folder in selected]
        missing = sorted(selected - {device.folder for device in devices})
        if missing:
            raise SystemExit("Unknown device(s) requested: " + ", ".join(missing))

    errors: list[str] = []
    validated: list[Path] = []
    for device in devices:
        validate_device(device, args.expected_runs, errors, validated)

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"Validated {len(validated)} CSV files across {len(devices)} device directories."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
