from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from dutch_labour_observatory.warehouse import load_wages_csv, run_quality_checks

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
QUALITY_QUERY = PROJECT_ROOT / "sql" / "quality" / "wage_quality_checks.sql"


class WageWarehouseTests(unittest.TestCase):
    def test_load_is_idempotent_and_quality_checks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "wages.csv"
            database_path = root / "test.duckdb"
            self._write_csv(csv_path)

            first = load_wages_csv(
                database_path=database_path,
                csv_path=csv_path,
                schema_path=SCHEMA_PATH,
            )
            second = load_wages_csv(
                database_path=database_path,
                csv_path=csv_path,
                schema_path=SCHEMA_PATH,
            )
            results = run_quality_checks(
                database_path=database_path,
                sql_path=QUALITY_QUERY,
            )

        self.assertEqual(first.row_count, 2)
        self.assertEqual(second.row_count, 2)
        self.assertEqual(first.first_period, "2020-01-01")
        self.assertEqual(first.last_period, "2020-02-01")
        self.assertTrue(all(result.passed for result in results))

    def test_quality_checks_find_gap_wrong_source_and_late_null(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "wages.csv"
            database_path = root / "test.duckdb"
            self._write_csv(
                csv_path,
                first_period="2021-01-01",
                first_source_period="2021MM01",
                second_period="2021-03-01",
                second_source_period="2021MM03",
                source_table_id="WRONG",
            )
            load_wages_csv(
                database_path=database_path,
                csv_path=csv_path,
                schema_path=SCHEMA_PATH,
            )
            results = run_quality_checks(
                database_path=database_path,
                sql_path=QUALITY_QUERY,
            )

        failures = {result.check_name: result.failed_rows for result in results}
        self.assertEqual(failures["missing_months"], 1)
        self.assertEqual(failures["unexpected_source_ids"], 2)
        self.assertEqual(failures["unexpected_null_growth"], 2)

    @staticmethod
    def _write_csv(
        path: Path,
        *,
        first_period: str = "2020-01-01",
        first_source_period: str = "2020MM01",
        second_period: str = "2020-02-01",
        second_source_period: str = "2020MM02",
        source_table_id: str = "85663ENG",
    ) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "period",
                    "source_period",
                    "hourly_cao_wage_index_2020",
                    "hourly_cao_wage_yoy_pct",
                    "status",
                    "source_status",
                    "is_provisional",
                    "source_table_id",
                    "retrieved_at_utc",
                ]
            )
            for period, source_period, index in (
                (first_period, first_source_period, 99.1),
                (second_period, second_source_period, 99.2),
            ):
                writer.writerow(
                    [
                        period,
                        source_period,
                        index,
                        None,
                        "final",
                        "Definitief",
                        False,
                        source_table_id,
                        "2026-09-09T12:00:00+00:00",
                    ]
                )


if __name__ == "__main__":
    unittest.main()
