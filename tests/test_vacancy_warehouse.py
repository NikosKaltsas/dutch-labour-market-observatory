from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from dutch_labour_observatory.warehouse import (
    load_vacancies_csv,
    run_quality_checks,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
QUALITY_QUERY = PROJECT_ROOT / "sql" / "quality" / "vacancy_quality_checks.sql"


class VacancyWarehouseTests(unittest.TestCase):
    def test_load_is_idempotent_and_quality_checks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "vacancies.csv"
            database_path = root / "test.duckdb"
            self._write_csv(csv_path)

            first = load_vacancies_csv(
                database_path=database_path,
                csv_path=csv_path,
                schema_path=SCHEMA_PATH,
            )
            second = load_vacancies_csv(
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
        self.assertEqual(first.first_period, "2015-03-31")
        self.assertEqual(first.last_period, "2015-06-30")
        self.assertTrue(all(result.passed for result in results))

    def test_quality_checks_find_gap_and_wrong_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "vacancies.csv"
            database_path = root / "test.duckdb"
            self._write_csv(
                csv_path,
                second_quarter_end="2015-09-30",
                second_source_period="2015KW03",
                source_table_id="WRONG",
            )
            load_vacancies_csv(
                database_path=database_path,
                csv_path=csv_path,
                schema_path=SCHEMA_PATH,
            )
            results = run_quality_checks(
                database_path=database_path,
                sql_path=QUALITY_QUERY,
            )

        failures = {result.check_name: result.failed_rows for result in results}
        self.assertEqual(failures["missing_quarters"], 1)
        self.assertEqual(failures["unexpected_source_ids"], 2)

    @staticmethod
    def _write_csv(
        path: Path,
        *,
        second_quarter_end: str = "2015-06-30",
        second_source_period: str = "2015KW02",
        source_table_id: str = "84545ENG",
    ) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "quarter_end",
                    "source_period",
                    "unfilled_vacancies_thousands",
                    "status",
                    "source_status",
                    "is_provisional",
                    "source_table_id",
                    "retrieved_at_utc",
                ]
            )
            writer.writerow(
                [
                    "2015-03-31",
                    "2015KW01",
                    130.0,
                    "final",
                    "Definitief",
                    False,
                    source_table_id,
                    "2026-09-09T12:00:00+00:00",
                ]
            )
            writer.writerow(
                [
                    second_quarter_end,
                    second_source_period,
                    140.0,
                    "final",
                    "Definitief",
                    False,
                    source_table_id,
                    "2026-09-09T12:00:00+00:00",
                ]
            )


if __name__ == "__main__":
    unittest.main()
