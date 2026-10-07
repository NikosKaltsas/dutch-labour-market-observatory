from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dutch_labour_observatory.cli import main
from dutch_labour_observatory.warehouse import ExportResult, QualityCheckResult


class CliTests(unittest.TestCase):
    @patch("dutch_labour_observatory.cli.export_sql_to_csv")
    def test_export_reports_shape(self, export_query) -> None:
        export_query.return_value = ExportResult(row_count=12, column_count=5)
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(
                [
                    "export",
                    "--database",
                    "test.duckdb",
                    "--sql",
                    "dashboard.sql",
                    "--output",
                    "dashboard.csv",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("Exported 12 rows and 5 columns", output.getvalue())

    @patch("dutch_labour_observatory.cli.CbsODataClient")
    def test_empty_result_fails_without_writing_snapshot(self, client_class) -> None:
        client_class.return_value.fetch.return_value = []

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "empty.json"
            exit_code = main(
                [
                    "fetch",
                    "80590ENG",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(exit_code, 2)
            self.assertFalse(output.exists())

    @patch("dutch_labour_observatory.cli.CbsODataClient")
    def test_allow_empty_writes_explicit_empty_snapshot(self, client_class) -> None:
        client_class.return_value.fetch.return_value = []

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "empty.json"
            exit_code = main(
                [
                    "fetch",
                    "80590ENG",
                    "--output",
                    str(output),
                    "--allow-empty",
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(output.exists())

    @patch("dutch_labour_observatory.cli.run_quality_checks")
    def test_failed_quality_check_returns_nonzero_exit_code(self, run_checks) -> None:
        run_checks.return_value = [QualityCheckResult("missing_months", 1)]
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(
                [
                    "check-quality",
                    "--database",
                    "test.duckdb",
                    "--sql",
                    "quality.sql",
                ]
            )

        self.assertEqual(exit_code, 1)
        self.assertIn("FAIL\tmissing_months\tfailed_rows=1", output.getvalue())


if __name__ == "__main__":
    unittest.main()
