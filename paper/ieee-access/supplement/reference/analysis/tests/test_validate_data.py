from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis"))

from data_utils import read_csv_measurements  # noqa: E402
from validate_data import validate_s4_array  # noqa: E402


class ValidateDataTests(unittest.TestCase):
    def test_s4_array_canonical_grid_passes(self) -> None:
        errors: list[str] = []
        validate_s4_array(errors, ROOT / "data" / "moto-g72" / "s4_array.csv", 10)
        self.assertEqual(errors, [])

    def test_s4_array_rejects_missing_payload_condition(self) -> None:
        source = ROOT / "data" / "moto-g72" / "s4_array.csv"
        df = read_csv_measurements(source)
        incomplete = df[df["Payload_Size"] != 10000]

        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "s4_array.csv"
            incomplete.to_csv(path, sep=";", index=False)
            errors: list[str] = []
            validate_s4_array(errors, path, 10)

        self.assertTrue(
            any(
                "missing required condition(s)" in error
                and "Payload_Size=10000" in error
                for error in errors
            ),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
