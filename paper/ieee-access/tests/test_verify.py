"""Regression tests for portable manuscript-output comparison."""

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

spec = importlib.util.spec_from_file_location("paper_verify", Path(__file__).resolve().parents[1] / "verify.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class VerificationTests(unittest.TestCase):
    def test_runtime_versions_do_not_change_scientific_summary(self):
        verify.compare_summary(
            {"canonical_records": 700, "Holm_RQ_significant": 31, "python": "3.11.4"},
            {"canonical_records": 700, "Holm_RQ_significant": 31, "python": "3.11.14"},
        )

    def test_changed_scientific_summary_is_rejected(self):
        with self.assertRaises(AssertionError):
            verify.compare_summary({"Holm_RQ_significant": 31}, {"Holm_RQ_significant": 32})

    def test_missing_scientific_field_is_rejected(self):
        with self.assertRaises(AssertionError):
            verify.compare_summary({"canonical_records": 700}, {})

    def test_windows_manifest_paths_are_portable(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps({"data\\device\\run.csv": "abc"}), encoding="utf-8")
            self.assertEqual(verify.normalized_manifest(path), {"data/device/run.csv": "abc"})

    def test_csv_tolerates_roundoff_but_rejects_changed_results(self):
        with TemporaryDirectory() as tmp:
            expected, actual = Path(tmp) / "expected.csv", Path(tmp) / "actual.csv"
            expected.write_text("metric,value\nthroughput,1.0\n", encoding="utf-8")
            actual.write_text("metric,value\nthroughput,1.0000000000001\n", encoding="utf-8")
            verify.compare_csv(expected, actual)
            actual.write_text("metric,value\nthroughput,1.01\n", encoding="utf-8")
            with self.assertRaises(AssertionError):
                verify.compare_csv(expected, actual)

    def test_missing_csv_value_is_rejected(self):
        with TemporaryDirectory() as tmp:
            expected, actual = Path(tmp) / "expected.csv", Path(tmp) / "actual.csv"
            expected.write_text("metric,value\nthroughput,1.0\n", encoding="utf-8")
            actual.write_text("metric,value\nthroughput,\n", encoding="utf-8")
            with self.assertRaises(AssertionError):
                verify.compare_csv(expected, actual)

    def test_missing_output_is_rejected(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaises(AssertionError):
                verify.require_names(Path(tmp), "*.pdf", {"study_design.pdf"})


if __name__ == "__main__":
    unittest.main()
