from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from dutch_labour_observatory.warehouse import (
    export_sql_to_csv,
    load_unemployment_csv,
    run_quality_checks,
    run_sql_file,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
SUMMARY_QUERY = (
    PROJECT_ROOT / "sql" / "analysis" / "unemployment_annual_summary.sql"
)
QUALITY_QUERY = (
    PROJECT_ROOT / "sql" / "quality" / "unemployment_quality_checks.sql"
)


class WarehouseTests(unittest.TestCase):
    def test_exports_query_result_to_csv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "unemployment.csv"
            database_path = root / "test.duckdb"
            output_path = root / "summary.csv"
            self._write_csv(csv_path)
            load_unemployment_csv(
                database_path=database_path,
                csv_path=csv_path,
                schema_path=SCHEMA_PATH,
            )

            result = export_sql_to_csv(
                database_path=database_path,
                sql_path=SUMMARY_QUERY,
                output_path=output_path,
            )
            with output_path.open(encoding="utf-8", newline="") as handle:
                exported = list(csv.DictReader(handle))

        self.assertEqual(result.row_count, 1)
        self.assertEqual(result.column_count, 6)
        self.assertEqual(exported[0]["calendar_year"], "2015")
        self.assertEqual(exported[0]["months_observed"], "2")

    def test_load_is_typed_queryable_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "unemployment.csv"
            database_path = root / "test.duckdb"
            self._write_csv(csv_path)

            first = load_unemployment_csv(
                database_path=database_path,
                csv_path=csv_path,
                schema_path=SCHEMA_PATH,
            )
            second = load_unemployment_csv(
                database_path=database_path,
                csv_path=csv_path,
                schema_path=SCHEMA_PATH,
            )
            columns, rows = run_sql_file(
                database_path=database_path,
                sql_path=SUMMARY_QUERY,
            )

        self.assertEqual(first.row_count, 2)
        self.assertEqual(second.row_count, 2)
        self.assertEqual(first.first_period, "2015-01-01")
        self.assertEqual(first.last_period, "2015-02-01")
        self.assertEqual(columns[0], "calendar_year")
        self.assertEqual(rows[0][0], 2015)
        self.assertEqual(rows[0][1], 2)

    def test_quality_checks_pass_for_complete_valid_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "unemployment.csv"
            database_path = root / "test.duckdb"
            self._write_csv(csv_path)
            load_unemployment_csv(
                database_path=database_path,
                csv_path=csv_path,
                schema_path=SCHEMA_PATH,
            )

            results = run_quality_checks(
                database_path=database_path,
                sql_path=QUALITY_QUERY,
            )

        self.assertTrue(all(result.passed for result in results))
        self.assertEqual(len(results), 4)

    def test_quality_checks_find_gap_and_wrong_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "unemployment.csv"
            database_path = root / "test.duckdb"
            self._write_csv(
                csv_path,
                second_period="2015-03-01",
                second_source_period="2015MM03",
                source_table_id="WRONG",
            )
            load_unemployment_csv(
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
        self.assertEqual(failures["duplicate_periods"], 0)
        self.assertEqual(failures["invalid_values"], 0)

    @staticmethod
    def _write_csv(
        path: Path,
        *,
        second_period: str = "2015-02-01",
        second_source_period: str = "2015MM02",
        source_table_id: str = "80590ENG",
    ) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "period",
                    "source_period",
                    "unemployed_thousands",
                    "unemployment_rate_pct",
                    "source_table_id",
                    "retrieved_at_utc",
                ]
            )
            writer.writerow(
                [
                    "2015-01-01",
                    "2015MM01",
                    760.0,
                    8.3,
                    source_table_id,
                    "2026-09-09T12:00:00+00:00",
                ]
            )
            writer.writerow(
                [
                    second_period,
                    second_source_period,
                    747.0,
                    8.1,
                    source_table_id,
                    "2026-09-09T12:00:00+00:00",
                ]
            )


if __name__ == "__main__":
    unittest.main()
