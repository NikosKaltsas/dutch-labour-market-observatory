from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from dutch_labour_observatory.transform import (
    DataValidationError,
    normalize_wage_snapshots,
    write_wage_staging_csv,
)


def make_snapshot(rows, *, table_id="85663ENG"):
    return {
        "table_id": table_id,
        "retrieved_at_utc": "2026-09-09T12:00:00+00:00",
        "rows": rows,
    }


def make_wage_row(period, index, growth, *, version="A045600   "):
    return {
        "CaoSector": "T001020",
        "SectorBranchesSIC2008": "T001081",
        "Version": version,
        "Periods": period,
        "HourlyCaoWagesInclSpecialPayments_4": index,
        "HourlyCaoWagesInclSpecialPayments_11": growth,
    }


class NormalizeWageTests(unittest.TestCase):
    def test_preserves_valid_null_growth_and_maps_status(self) -> None:
        observations = make_snapshot(
            [
                make_wage_row("2020MM01", 99.1, None),
                make_wage_row("2026MM08", 130.9, 4.0),
            ]
        )
        periods = make_snapshot(
            [
                {"Key": "2020MM01", "Status": "Definitief"},
                {"Key": "2026MM08", "Status": "Voorlopig"},
            ]
        )

        rows = normalize_wage_snapshots(observations, periods)

        self.assertEqual(rows[0]["period"], "2020-01-01")
        self.assertIsNone(rows[0]["hourly_cao_wage_yoy_pct"])
        self.assertEqual(rows[0]["status"], "final")
        self.assertEqual(rows[1]["status"], "provisional")
        self.assertTrue(rows[1]["is_provisional"])

    def test_rejects_unexpected_dimension_value(self) -> None:
        observations = make_snapshot(
            [make_wage_row("2020MM01", 99.1, None, version="A045601   ")]
        )
        periods = make_snapshot([{"Key": "2020MM01", "Status": "Definitief"}])

        with self.assertRaisesRegex(DataValidationError, "unexpected Version"):
            normalize_wage_snapshots(observations, periods)

    def test_rejects_missing_metadata(self) -> None:
        observations = make_snapshot([make_wage_row("2020MM01", 99.1, None)])

        with self.assertRaisesRegex(DataValidationError, "missing period metadata"):
            normalize_wage_snapshots(observations, make_snapshot([]))

    def test_rejects_non_positive_index(self) -> None:
        observations = make_snapshot([make_wage_row("2020MM01", 0, None)])
        periods = make_snapshot([{"Key": "2020MM01", "Status": "Definitief"}])

        with self.assertRaisesRegex(DataValidationError, "non-positive index"):
            normalize_wage_snapshots(observations, periods)

    def test_writes_wage_csv(self) -> None:
        rows = normalize_wage_snapshots(
            make_snapshot([make_wage_row("2020MM01", 99.1, None)]),
            make_snapshot([{"Key": "2020MM01", "Status": "Definitief"}]),
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "wages.csv"
            write_wage_staging_csv(output, rows)
            with output.open(encoding="utf-8", newline="") as handle:
                written = list(csv.DictReader(handle))

        self.assertEqual(written[0]["period"], "2020-01-01")
        self.assertEqual(written[0]["hourly_cao_wage_yoy_pct"], "")


if __name__ == "__main__":
    unittest.main()
