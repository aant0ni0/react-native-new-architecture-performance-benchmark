from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DEVICE_REGISTRY = DATA / "devices.csv"


@dataclass(frozen=True)
class DeviceSpec:
    folder: str
    label: str
    short_label: str
    refresh_hz: int | None = None

    @property
    def data_dir(self) -> Path:
        return DATA / self.folder

    @property
    def display_label(self) -> str:
        if self.refresh_hz is None:
            return self.label
        return f"{self.label} ({self.refresh_hz} Hz)"


def read_csv_measurements(path: Path) -> pd.DataFrame:
    separator = "," if path.name == "devices.csv" else ";"
    df = pd.read_csv(path, sep=separator, encoding="utf-8-sig").dropna(how="all")

    for col in df.columns:
        series = df[col]
        if pd.api.types.is_string_dtype(series.dtype) or series.dtype == object:
            cleaned = series.astype("string").str.strip().str.replace(",", ".", regex=False)
            numeric = pd.to_numeric(cleaned, errors="coerce")
            nonempty = cleaned.notna().sum()

            if nonempty and numeric.notna().sum() >= max(1, int(np.ceil(0.8 * nonempty))):
                df[col] = numeric

    return df


def normalize_architecture(df: pd.DataFrame, col: str = "Architecture") -> pd.DataFrame:
    if col in df.columns:
        df[col] = df[col].replace(
            {
                "Legacy": "RN_Legacy",
                "RN Legacy": "RN_Legacy",
                "NewArch": "RN_NewArch",
                "New Architecture": "RN_NewArch",
                "RN New Architecture": "RN_NewArch",
                "Android": "Native",
                "Android Native": "Native",
            }
        )
    return df


def load_device_registry(path: Path = DEVICE_REGISTRY) -> list[DeviceSpec]:
    if not path.exists():
        raise FileNotFoundError(f"Device registry not found: {path}")

    specs: list[DeviceSpec] = []
    seen_folders: set[str] = set()

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"folder", "label", "short_label", "refresh_hz"}
        if reader.fieldnames is None or set(reader.fieldnames) != required:
            raise ValueError(
                "devices.csv must contain exactly these headers: "
                "folder,label,short_label,refresh_hz"
            )

        for row in reader:
            folder = (row["folder"] or "").strip()
            label = (row["label"] or "").strip()
            short_label = (row["short_label"] or "").strip()
            refresh_raw = (row["refresh_hz"] or "").strip()

            if not folder or not label or not short_label:
                raise ValueError(f"Incomplete row in {path}: {row}")
            if folder in seen_folders:
                raise ValueError(f"Duplicate device folder in {path}: {folder}")
            seen_folders.add(folder)

            refresh_hz = int(refresh_raw) if refresh_raw else None
            spec = DeviceSpec(
                folder=folder,
                label=label,
                short_label=short_label,
                refresh_hz=refresh_hz,
            )
            if not spec.data_dir.exists():
                raise FileNotFoundError(
                    f"Device directory declared in {path} does not exist: {spec.data_dir}"
                )
            specs.append(spec)

    if not specs:
        raise ValueError(f"No devices declared in {path}")

    return specs


def load_device_file(
    device: DeviceSpec,
    filename: str,
    architecture_col: str = "Architecture",
) -> pd.DataFrame:
    df = read_csv_measurements(device.data_dir / filename)
    if architecture_col in df.columns:
        df = normalize_architecture(df, architecture_col)
    return df
