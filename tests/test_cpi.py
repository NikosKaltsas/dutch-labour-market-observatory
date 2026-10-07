from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from dutch_labour_observatory.transform import (
    DataValidationError,
    normalize_cpi_snapshots,
    write_cpi_staging_csv,
)


def make_snapshot(rows, *, table_id="86141ENG"):
    return {
        "table_id": table_id,
        "retrieved_at_utc": "2026-09-09T12:00:00+00:00",
        "rows": rows,
    }


def make_cpi_row(period, index, inflation, *, category="T001112  "):
    return {
        "ExpenditureCategories": category,
        "Periods": period,
        "CPI_1": index,
        "AnnualRateOfChangeCPI_5": inflation,
    }


class NormalizeCpiTests(unittest.TestCase):
    def test_applies_cutoff_and_maps_status(self) -> None:
        observations = make_snapshot(
            [
                make_cpi_row("2009MM12", 79.1, None),
                make_cpi_row("2020MM01", 88.2, 1.8),
                make_cpi_row("2026MM08", 104.36, 3.3),
            ]
        )
        periods = make_snapshot(
            [
                {"Key": "2020MM01", "Status": "Definitief"},
                {"Key": "2026MM08", "Status": "Voorlopig"},
            ]
        )

        rows = normalize_cpi_snapshots(observations, periods)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["period"], "2020-01-01")
        self.assertEqual(rows[0]["cpi_inflation_yoy_pct"], 1.8)
        self.assertEqual(rows[0]["status"], "final")
        self.assertTrue(rows[1]["is_provisional"])

    def test_rejects_unexpected_category(self) -> None:
        observations = make_snapshot(
            [make_cpi_row("2020MM01", 88.2, 1.8, category="CPI010000")]
        )
        periods = make_snapshot([{"Key": "2020MM01", "Status": "Definitief"}])

        with self.assertRaisesRegex(
            DataValidationError,
            "unexpected ExpenditureCategories",
        ):
            normalize_cpi_snapshots(observations, periods)

    def test_rejects_missing_metadata(self) -> None:
        observations = make_snapshot([make_cpi_row("2020MM01", 88.2, 1.8)])

        with self.assertRaisesRegex(DataValidationError, "missing period metadata"):
            normalize_cpi_snapshots(observations, make_snapshot([]))

    def test_rejects_missing_inflation_after_cutoff(self) -> None:
        observations = make_snapshot([make_cpi_row("2020MM01", 88.2, None)])
        periods = make_snapshot([{"Key": "2020MM01", "Status": "Definitief"}])

        with self.assertRaisesRegex(DataValidationError, "requires numeric field"):
            normalize_cpi_snapshots(observations, periods)

    def test_rejects_non_positive_index(self) -> None:
        observations = make_snapshot([make_cpi_row("2020MM01", 0, 1.8)])
        periods = make_snapshot([{"Key": "2020MM01", "Status": "Definitief"}])

        with self.assertRaisesRegex(DataValidationError, "non-positive index"):
            normalize_cpi_snapshots(observations, periods)

    def test_writes_cpi_csv(self) -> None:
        rows = normalize_cpi_snapshots(
            make_snapshot([make_cpi_row("2020MM01", 88.2, 1.8)]),
            make_snapshot([{"Key": "2020MM01", "Status": "Definitief"}]),
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "cpi.csv"
            write_cpi_staging_csv(output, rows)
            with output.open(encoding="utf-8", newline="") as handle:
                written = list(csv.DictReader(handle))

        self.assertEqual(written[0]["period"], "2020-01-01")
        self.assertEqual(written[0]["cpi_index_2025"], "88.2")


if __name__ == "__main__":
    unittest.main()
