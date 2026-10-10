#!/usr/bin/env python3
"""Reproduce and verify the manuscript supplement without modifying the checkout."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

import pandas as pd

ROOT = Path(__file__).resolve().parent
RUNTIME_FIELDS = {"python", "numpy", "pandas", "scipy"}
CSV_NAMES = {
    "canonical_inventory.csv", "primary_contrasts.csv",
    "s4_initial_series_contrasts.csv", "s4_remeasurement_sensitivity.csv",
    "s4_unrounded_throughput.csv",
}
TABLE_NAMES = {"numbers.tex", "sensitivity.tex", *(f"s{i}.tex" for i in range(1, 6))}
FIGURE_NAMES = {
    "study_design.pdf", "callback_delay.pdf", "array_throughput.pdf",
    "animation_boundaries.pdf",
}


def file_hashes(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def normalized_manifest(path):
    # The manuscript manifest was produced on Windows; paths are platform-neutral.
    manifest = json.loads(path.read_text(encoding="utf-8"))
    return {name.replace("\\", "/"): digest for name, digest in manifest.items()}


def compare_csv(expected, actual):
    pd.testing.assert_frame_equal(
        pd.read_csv(expected), pd.read_csv(actual),
        check_exact=False, atol=1e-12, rtol=1e-12,
    )


def compare_summary(expected, actual):
    scientific_expected = {k: v for k, v in expected.items() if k not in RUNTIME_FIELDS}
    scientific_actual = {k: v for k, v in actual.items() if k not in RUNTIME_FIELDS}
    if scientific_expected != scientific_actual:
        raise AssertionError("Scientific verification summary differs from the manuscript")


def require_names(directory, pattern, expected):
    names = {path.name for path in directory.glob(pattern)}
    if names != expected:
        raise AssertionError(f"Unexpected output set in {directory}: {names ^ expected}")


def verify(root=ROOT):
    root = Path(root).resolve()
    supplement = root / "supplement"
    expected_results = supplement / "results"
    manifest = normalized_manifest(expected_results / "reference_sha256.json")
    if file_hashes(supplement / "reference") != manifest:
        raise AssertionError("Bundled reference files do not match their SHA-256 manifest")
    require_names(expected_results, "*.csv", CSV_NAMES)
    require_names(root / "tables", "*.tex", TABLE_NAMES)
    require_names(root / "figures", "*.pdf", FIGURE_NAMES)
    before = file_hashes(root)

    with TemporaryDirectory(prefix="rnarchbench-paper-") as temporary:
        work = Path(temporary) / "paper"

        def ignore_outputs(directory, names):
            ignored = {"__pycache__"} & set(names)
            if Path(directory) == root:
                ignored |= {"tables", "figures"}
            if Path(directory) == supplement:
                ignored.add("results")
            return ignored

        # Exclude previous outputs so a missing generator output cannot pass validation.
        shutil.copytree(root, work, ignore=ignore_outputs)
        for folder in ["tables", "figures", "supplement/results"]:
            (work / folder).mkdir(parents=True, exist_ok=True)
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg")
        for script in ["reproduce_results.py", "make_figures.py"]:
            subprocess.run(
                [sys.executable, str(work / "supplement" / script)],
                cwd=work / "supplement", env=environment, check=True,
            )

        actual_results = work / "supplement/results"
        require_names(actual_results, "*.csv", CSV_NAMES)
        for name in sorted(CSV_NAMES):
            compare_csv(expected_results / name, actual_results / name)
        require_names(work / "tables", "*.tex", TABLE_NAMES)
        for name in sorted(TABLE_NAMES):
            expected = (root / "tables" / name).read_text(encoding="utf-8")
            actual = (work / "tables" / name).read_text(encoding="utf-8")
            if expected != actual:
                raise AssertionError(f"Manuscript table changed: {name}")

        expected_summary = json.loads((expected_results / "verification.json").read_text())
        actual_summary = json.loads((actual_results / "verification.json").read_text())
        compare_summary(expected_summary, actual_summary)
        if normalized_manifest(actual_results / "reference_sha256.json") != manifest:
            raise AssertionError("Regenerated reference manifest differs from the manuscript")
        if file_hashes(work / "supplement/reference") != manifest:
            raise AssertionError("Reproduction changed the temporary reference snapshot")

        require_names(work / "figures", "*.pdf", FIGURE_NAMES)
        for name in sorted(FIGURE_NAMES):
            content = (work / "figures" / name).read_bytes()
            valid_pdf = len(content) >= 1000 and content.startswith(b"%PDF-") and b"%%EOF" in content[-100:]
            if not valid_pdf:
                raise AssertionError(f"Missing or incomplete generated PDF: {name}")

    if file_hashes(root) != before:
        raise AssertionError("Verification changed the manuscript checkout")
    print("Verified 5 result CSVs, 7 LaTeX files, 4 regenerated PDFs, and reference checksums.")
    print("Manuscript outputs match; checkout unchanged.")


if __name__ == "__main__":
    verify()
