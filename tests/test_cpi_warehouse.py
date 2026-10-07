from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from dutch_labour_observatory.warehouse import load_cpi_csv, run_quality_checks

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
QUALITY_QUERY = PROJECT_ROOT / "sql" / "quality" / "cpi_quality_checks.sql"


class CpiWarehouseTests(unittest.TestCase):
    def test_load_is_idempotent_and_quality_checks_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "cpi.csv"
            database_path = root / "test.duckdb"
            self._write_csv(csv_path)

            first = load_cpi_csv(
                database_path=database_path,
                csv_path=csv_path,
                schema_path=SCHEMA_PATH,
            )
            second = load_cpi_csv(
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

    def test_quality_checks_find_gap_and_wrong_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "cpi.csv"
            database_path = root / "test.duckdb"
            self._write_csv(
                csv_path,
                second_period="2020-03-01",
                second_source_period="2020MM03",
                source_table_id="WRONG",
            )
            load_cpi_csv(
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

    @staticmethod
    def _write_csv(
        path: Path,
        *,
        second_period: str = "2020-02-01",
        second_source_period: str = "2020MM02",
        source_table_id: str = "86141ENG",
    ) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "period",
                    "source_period",
                    "cpi_index_2025",
                    "cpi_inflation_yoy_pct",
                    "status",
                    "source_status",
                    "is_provisional",
                    "source_table_id",
                    "retrieved_at_utc",
                ]
            )
            for period, source_period, index, inflation in (
                ("2020-01-01", "2020MM01", 88.2, 1.8),
                (second_period, second_source_period, 88.4, 1.6),
            ):
                writer.writerow(
                    [
                        period,
                        source_period,
                        index,
                        inflation,
                        "final",
                        "Definitief",
                        False,
                        source_table_id,
                        "2026-09-09T12:00:00+00:00",
                    ]
                )


if __name__ == "__main__":
    unittest.main()
