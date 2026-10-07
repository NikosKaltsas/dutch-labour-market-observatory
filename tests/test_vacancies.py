from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from dutch_labour_observatory.transform import (
    DataValidationError,
    normalize_vacancy_snapshots,
    write_vacancy_staging_csv,
)


def make_snapshot(rows, *, table_id="84545ENG"):
    return {
        "table_id": table_id,
        "retrieved_at_utc": "2026-09-09T12:00:00+00:00",
        "rows": rows,
    }


class NormalizeVacancyTests(unittest.TestCase):
    def test_joins_status_maps_quarter_end_and_applies_cutoff(self) -> None:
        observations = make_snapshot(
            [
                {
                    "Periods": "2014KW04",
                    "VacanciesSeasonallyAdjustedUnfilled_1": 120.0,
                },
                {
                    "Periods": "2015KW01",
                    "VacanciesSeasonallyAdjustedUnfilled_1": 130.0,
                },
                {
                    "Periods": "2026KW02",
                    "VacanciesSeasonallyAdjustedUnfilled_1": 374.8,
                },
            ]
        )
        periods = make_snapshot(
            [
                {"Key": "2014KW04", "Status": "Definitief"},
                {"Key": "2015KW01", "Status": "Definitief"},
                {"Key": "2026KW02", "Status": "Voorlopig"},
            ]
        )

        rows = normalize_vacancy_snapshots(observations, periods)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["quarter_end"], "2015-03-31")
        self.assertEqual(rows[0]["status"], "final")
        self.assertFalse(rows[0]["is_provisional"])
        self.assertEqual(rows[1]["quarter_end"], "2026-06-30")
        self.assertEqual(rows[1]["source_status"], "Voorlopig")
        self.assertTrue(rows[1]["is_provisional"])

    def test_rejects_missing_period_metadata(self) -> None:
        observations = make_snapshot(
            [
                {
                    "Periods": "2015KW01",
                    "VacanciesSeasonallyAdjustedUnfilled_1": 130.0,
                }
            ]
        )
        with self.assertRaisesRegex(DataValidationError, "missing period metadata"):
            normalize_vacancy_snapshots(observations, make_snapshot([]))

    def test_rejects_unknown_status(self) -> None:
        observations = make_snapshot(
            [
                {
                    "Periods": "2015KW01",
                    "VacanciesSeasonallyAdjustedUnfilled_1": 130.0,
                }
            ]
        )
        periods = make_snapshot([{"Key": "2015KW01", "Status": "Unknown"}])
        with self.assertRaisesRegex(DataValidationError, "unknown CBS vacancy status"):
            normalize_vacancy_snapshots(observations, periods)

    def test_rejects_different_metadata_table(self) -> None:
        with self.assertRaisesRegex(DataValidationError, "table IDs differ"):
            normalize_vacancy_snapshots(
                make_snapshot([]),
                make_snapshot([], table_id="OTHER"),
            )

    def test_writes_vacancy_csv(self) -> None:
        rows = normalize_vacancy_snapshots(
            make_snapshot(
                [
                    {
                        "Periods": "2015KW01",
                        "VacanciesSeasonallyAdjustedUnfilled_1": 130.0,
                    }
                ]
            ),
            make_snapshot([{"Key": "2015KW01", "Status": "Definitief"}]),
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "vacancies.csv"
            write_vacancy_staging_csv(output, rows)
            with output.open(encoding="utf-8", newline="") as handle:
                written = list(csv.DictReader(handle))

        self.assertEqual(written[0]["quarter_end"], "2015-03-31")
        self.assertEqual(written[0]["is_provisional"], "False")


if __name__ == "__main__":
    unittest.main()
