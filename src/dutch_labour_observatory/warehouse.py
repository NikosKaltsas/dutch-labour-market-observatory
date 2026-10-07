"""DuckDB loading and query helpers."""

from __future__ import annotations

import csv
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LoadResult:
    row_count: int
    first_period: str
    last_period: str


@dataclass(frozen=True)
class QualityCheckResult:
    check_name: str
    failed_rows: int

    @property
    def passed(self) -> bool:
        return self.failed_rows == 0


@dataclass(frozen=True)
class ExportResult:
    row_count: int
    column_count: int


def load_unemployment_csv(
    *,
    database_path: Path,
    csv_path: Path,
    schema_path: Path,
) -> LoadResult:
    """Replace the unemployment staging table from a validated CSV."""

    _require_file(csv_path, "staging CSV")
    _require_file(schema_path, "schema SQL")
    database_path.parent.mkdir(parents=True, exist_ok=True)
    duckdb = _import_duckdb()

    with duckdb.connect(str(database_path)) as connection:
        connection.execute(schema_path.read_text(encoding="utf-8"))
        connection.execute("BEGIN TRANSACTION")
        try:
            connection.execute("DELETE FROM staging.unemployment_monthly")
            connection.execute(
                """
                INSERT INTO staging.unemployment_monthly
                SELECT
                    period,
                    source_period,
                    unemployed_thousands,
                    unemployment_rate_pct,
                    source_table_id,
                    retrieved_at_utc
                FROM read_csv(
                    ?,
                    header = true,
                    columns = {
                        'period': 'DATE',
                        'source_period': 'VARCHAR',
                        'unemployed_thousands': 'DOUBLE',
                        'unemployment_rate_pct': 'DOUBLE',
                        'source_table_id': 'VARCHAR',
                        'retrieved_at_utc': 'TIMESTAMPTZ'
                    }
                )
                """,
                [str(csv_path.resolve())],
            )
            row_count, first_period, last_period = connection.execute(
                """
                SELECT count(*), min(period), max(period)
                FROM staging.unemployment_monthly
                """
            ).fetchone()
            if row_count == 0:
                raise ValueError("warehouse load produced an empty staging table")
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise

    return LoadResult(
        row_count=row_count,
        first_period=first_period.isoformat(),
        last_period=last_period.isoformat(),
    )


def load_vacancies_csv(
    *,
    database_path: Path,
    csv_path: Path,
    schema_path: Path,
) -> LoadResult:
    """Replace the quarterly vacancy staging table from a validated CSV."""

    _require_file(csv_path, "vacancy staging CSV")
    _require_file(schema_path, "schema SQL")
    database_path.parent.mkdir(parents=True, exist_ok=True)
    duckdb = _import_duckdb()

    with duckdb.connect(str(database_path)) as connection:
        connection.execute(schema_path.read_text(encoding="utf-8"))
        connection.execute("BEGIN TRANSACTION")
        try:
            connection.execute("DELETE FROM staging.vacancies_quarterly")
            connection.execute(
                """
                INSERT INTO staging.vacancies_quarterly
                SELECT
                    quarter_end,
                    source_period,
                    unfilled_vacancies_thousands,
                    status,
                    source_status,
                    is_provisional,
                    source_table_id,
                    retrieved_at_utc
                FROM read_csv(
                    ?,
                    header = true,
                    columns = {
                        'quarter_end': 'DATE',
                        'source_period': 'VARCHAR',
                        'unfilled_vacancies_thousands': 'DOUBLE',
                        'status': 'VARCHAR',
                        'source_status': 'VARCHAR',
                        'is_provisional': 'BOOLEAN',
                        'source_table_id': 'VARCHAR',
                        'retrieved_at_utc': 'TIMESTAMPTZ'
                    }
                )
                """,
                [str(csv_path.resolve())],
            )
            row_count, first_period, last_period = connection.execute(
                """
                SELECT count(*), min(quarter_end), max(quarter_end)
                FROM staging.vacancies_quarterly
                """
            ).fetchone()
            if row_count == 0:
                raise ValueError("warehouse load produced an empty vacancy table")
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise

    return LoadResult(
        row_count=row_count,
        first_period=first_period.isoformat(),
        last_period=last_period.isoformat(),
    )


def load_wages_csv(
    *,
    database_path: Path,
    csv_path: Path,
    schema_path: Path,
) -> LoadResult:
    """Replace the monthly wage staging table from a validated CSV."""

    _require_file(csv_path, "wage staging CSV")
    _require_file(schema_path, "schema SQL")
    database_path.parent.mkdir(parents=True, exist_ok=True)
    duckdb = _import_duckdb()

    with duckdb.connect(str(database_path)) as connection:
        connection.execute(schema_path.read_text(encoding="utf-8"))
        connection.execute("BEGIN TRANSACTION")
        try:
            connection.execute("DELETE FROM staging.wages_monthly")
            connection.execute(
                """
                INSERT INTO staging.wages_monthly
                SELECT
                    period,
                    source_period,
                    hourly_cao_wage_index_2020,
                    hourly_cao_wage_yoy_pct,
                    status,
                    source_status,
                    is_provisional,
                    source_table_id,
                    retrieved_at_utc
                FROM read_csv(
                    ?,
                    header = true,
                    columns = {
                        'period': 'DATE',
                        'source_period': 'VARCHAR',
                        'hourly_cao_wage_index_2020': 'DOUBLE',
                        'hourly_cao_wage_yoy_pct': 'DOUBLE',
                        'status': 'VARCHAR',
                        'source_status': 'VARCHAR',
                        'is_provisional': 'BOOLEAN',
                        'source_table_id': 'VARCHAR',
                        'retrieved_at_utc': 'TIMESTAMPTZ'
                    }
                )
                """,
                [str(csv_path.resolve())],
            )
            row_count, first_period, last_period = connection.execute(
                """
                SELECT count(*), min(period), max(period)
                FROM staging.wages_monthly
                """
            ).fetchone()
            if row_count == 0:
                raise ValueError("warehouse load produced an empty wage table")
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise

    return LoadResult(
        row_count=row_count,
        first_period=first_period.isoformat(),
        last_period=last_period.isoformat(),
    )


def load_cpi_csv(
    *,
    database_path: Path,
    csv_path: Path,
    schema_path: Path,
) -> LoadResult:
    """Replace the monthly CPI staging table from a validated CSV."""

    _require_file(csv_path, "CPI staging CSV")
    _require_file(schema_path, "schema SQL")
    database_path.parent.mkdir(parents=True, exist_ok=True)
    duckdb = _import_duckdb()

    with duckdb.connect(str(database_path)) as connection:
        connection.execute(schema_path.read_text(encoding="utf-8"))
        connection.execute("BEGIN TRANSACTION")
        try:
            connection.execute("DELETE FROM staging.cpi_monthly")
            connection.execute(
                """
                INSERT INTO staging.cpi_monthly
                SELECT
                    period,
                    source_period,
                    cpi_index_2025,
                    cpi_inflation_yoy_pct,
                    status,
                    source_status,
                    is_provisional,
                    source_table_id,
                    retrieved_at_utc
                FROM read_csv(
                    ?,
                    header = true,
                    columns = {
                        'period': 'DATE',
                        'source_period': 'VARCHAR',
                        'cpi_index_2025': 'DOUBLE',
                        'cpi_inflation_yoy_pct': 'DOUBLE',
                        'status': 'VARCHAR',
                        'source_status': 'VARCHAR',
                        'is_provisional': 'BOOLEAN',
                        'source_table_id': 'VARCHAR',
                        'retrieved_at_utc': 'TIMESTAMPTZ'
                    }
                )
                """,
                [str(csv_path.resolve())],
            )
            row_count, first_period, last_period = connection.execute(
                """
                SELECT count(*), min(period), max(period)
                FROM staging.cpi_monthly
                """
            ).fetchone()
            if row_count == 0:
                raise ValueError("warehouse load produced an empty CPI table")
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise

    return LoadResult(
        row_count=row_count,
        first_period=first_period.isoformat(),
        last_period=last_period.isoformat(),
    )


def run_sql_file(
    *,
    database_path: Path,
    sql_path: Path,
) -> tuple[list[str], list[tuple[Any, ...]]]:
    """Execute a read-only project query and return its result."""

    _require_file(database_path, "DuckDB database")
    _require_file(sql_path, "SQL query")
    duckdb = _import_duckdb()

    with duckdb.connect(str(database_path), read_only=True) as connection:
        cursor = connection.execute(sql_path.read_text(encoding="utf-8"))
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
    return columns, rows


def run_quality_checks(
    *,
    database_path: Path,
    sql_path: Path,
) -> list[QualityCheckResult]:
    """Run SQL checks that return ``check_name`` and ``failed_rows``."""

    columns, rows = run_sql_file(
        database_path=database_path,
        sql_path=sql_path,
    )
    if columns != ["check_name", "failed_rows"]:
        raise ValueError(
            "quality SQL must return exactly: check_name, failed_rows"
        )

    results: list[QualityCheckResult] = []
    seen_names: set[str] = set()
    for check_name, failed_rows in rows:
        if not isinstance(check_name, str) or not check_name:
            raise ValueError("quality check names must be non-empty text")
        if check_name in seen_names:
            raise ValueError(f"duplicate quality check name: {check_name}")
        if not isinstance(failed_rows, int) or failed_rows < 0:
            raise ValueError(
                f"quality check {check_name!r} returned an invalid failure count"
            )
        seen_names.add(check_name)
        results.append(QualityCheckResult(check_name, failed_rows))

    if not results:
        raise ValueError("quality SQL returned no checks")
    return results


def export_sql_to_csv(
    *,
    database_path: Path,
    sql_path: Path,
    output_path: Path,
) -> ExportResult:
    """Run a read-only SQL file and atomically export its result to CSV."""

    columns, rows = run_sql_file(
        database_path=database_path,
        sql_path=sql_path,
    )
    if not columns:
        raise ValueError("export query returned no columns")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=output_path.parent,
        delete=False,
        suffix=".tmp",
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)
        temporary_path = Path(handle.name)

    temporary_path.replace(output_path)
    return ExportResult(row_count=len(rows), column_count=len(columns))


def _require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")


def _import_duckdb():
    try:
        import duckdb
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "DuckDB is not installed. Install the pipeline dependencies with "
            "python -m pip install -e '.[pipeline]'."
        ) from error
    return duckdb
