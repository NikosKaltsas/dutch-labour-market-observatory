from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from dutch_labour_observatory.transform import (
    DataValidationError,
    normalize_unemployment_snapshot,
    write_staging_csv,
)


def make_snapshot(rows):
    return {
        "table_id": "80590ENG",
        "retrieved_at_utc": "2026-09-09T12:00:00+00:00",
        "rows": rows,
    }


class NormalizeUnemploymentTests(unittest.TestCase):
    def test_normalizes_names_and_applies_start_period(self) -> None:
        snapshot = make_snapshot(
            [
                {
                    "Periods": "2014MM12",
                    "SeasonallyAdjusted_6": 700.0,
                    "SeasonallyAdjusted_8": 7.5,
                },
                {
                    "Periods": "2015MM01",
                    "SeasonallyAdjusted_6": 760.0,
                    "SeasonallyAdjusted_8": 8.3,
                },
            ]
        )

        rows = normalize_unemployment_snapshot(snapshot)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["period"], "2015-01-01")
        self.assertEqual(rows[0]["unemployed_thousands"], 760.0)
        self.assertEqual(rows[0]["unemployment_rate_pct"], 8.3)

    def test_rejects_duplicate_periods(self) -> None:
        row = {
            "Periods": "2015MM01",
            "SeasonallyAdjusted_6": 760.0,
            "SeasonallyAdjusted_8": 8.3,
        }
        with self.assertRaisesRegex(DataValidationError, "duplicate period"):
            normalize_unemployment_snapshot(make_snapshot([row, row]))

    def test_rejects_invalid_month(self) -> None:
        snapshot = make_snapshot(
            [
                {
                    "Periods": "2015MM13",
                    "SeasonallyAdjusted_6": 760.0,
                    "SeasonallyAdjusted_8": 8.3,
                }
            ]
        )
        with self.assertRaisesRegex(DataValidationError, "invalid monthly period"):
            normalize_unemployment_snapshot(snapshot)

    def test_rejects_rate_outside_percentage_range(self) -> None:
        snapshot = make_snapshot(
            [
                {
                    "Periods": "2015MM01",
                    "SeasonallyAdjusted_6": 760.0,
                    "SeasonallyAdjusted_8": 101.0,
                }
            ]
        )
        with self.assertRaisesRegex(DataValidationError, "outside 0-100"):
            normalize_unemployment_snapshot(snapshot)

    def test_writes_reviewable_csv(self) -> None:
        rows = normalize_unemployment_snapshot(
            make_snapshot(
                [
                    {
                        "Periods": "2015MM01",
                        "SeasonallyAdjusted_6": 760.0,
                        "SeasonallyAdjusted_8": 8.3,
                    }
                ]
            )
        )

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "staging.csv"
            write_staging_csv(output, rows)
            with output.open(encoding="utf-8", newline="") as handle:
                written = list(csv.DictReader(handle))

        self.assertEqual(written[0]["period"], "2015-01-01")
        self.assertEqual(written[0]["source_period"], "2015MM01")


if __name__ == "__main__":
    unittest.main()
