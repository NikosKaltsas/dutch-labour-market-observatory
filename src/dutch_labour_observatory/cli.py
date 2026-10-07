"""Command-line entry point for source ingestion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .cbs import CbsODataClient, write_snapshot
from .transform import (
    normalize_cpi_snapshots,
    normalize_unemployment_snapshot,
    normalize_vacancy_snapshots,
    normalize_wage_snapshots,
    write_cpi_staging_csv,
    write_staging_csv,
    write_vacancy_staging_csv,
    write_wage_staging_csv,
)
from .warehouse import (
    export_sql_to_csv,
    load_cpi_csv,
    load_unemployment_csv,
    load_vacancies_csv,
    load_wages_csv,
    run_quality_checks,
    run_sql_file,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch = subparsers.add_parser("fetch", help="download a CBS OData resource")
    fetch.add_argument("table_id", help="CBS StatLine table identifier")
    fetch.add_argument("--resource", default="TypedDataSet")
    fetch.add_argument("--select", nargs="*", help="column names to request")
    fetch.add_argument("--filter", dest="filter_expression", help="OData filter")
    fetch.add_argument("--output", type=Path, required=True)
    fetch.add_argument(
        "--allow-empty",
        action="store_true",
        help="write a snapshot even when the API returns no rows",
    )

    transform = subparsers.add_parser(
        "transform-unemployment",
        help="validate and normalize a raw unemployment snapshot",
    )
    transform.add_argument("--input", type=Path, required=True)
    transform.add_argument("--output", type=Path, required=True)
    transform.add_argument("--start-period", default="2015MM01")

    transform_vacancies = subparsers.add_parser(
        "transform-vacancies",
        help="validate and normalize raw vacancy observations and period metadata",
    )
    transform_vacancies.add_argument("--input", type=Path, required=True)
    transform_vacancies.add_argument(
        "--period-metadata",
        type=Path,
        required=True,
    )
    transform_vacancies.add_argument("--output", type=Path, required=True)
    transform_vacancies.add_argument("--start-period", default="2015KW01")

    transform_wages = subparsers.add_parser(
        "transform-wages",
        help="validate and normalize raw wage observations and period metadata",
    )
    transform_wages.add_argument("--input", type=Path, required=True)
    transform_wages.add_argument("--period-metadata", type=Path, required=True)
    transform_wages.add_argument("--output", type=Path, required=True)
    transform_wages.add_argument("--start-period", default="2020MM01")

    transform_cpi = subparsers.add_parser(
        "transform-cpi",
        help="validate and normalize raw CPI observations and period metadata",
    )
    transform_cpi.add_argument("--input", type=Path, required=True)
    transform_cpi.add_argument("--period-metadata", type=Path, required=True)
    transform_cpi.add_argument("--output", type=Path, required=True)
    transform_cpi.add_argument("--start-period", default="2020MM01")

    load = subparsers.add_parser(
        "load-unemployment",
        help="replace the DuckDB unemployment staging table from CSV",
    )
    load.add_argument("--input", type=Path, required=True)
    load.add_argument("--database", type=Path, required=True)
    load.add_argument("--schema", type=Path, default=Path("sql/schema.sql"))

    load_vacancies = subparsers.add_parser(
        "load-vacancies",
        help="replace the DuckDB vacancy staging table from CSV",
    )
    load_vacancies.add_argument("--input", type=Path, required=True)
    load_vacancies.add_argument("--database", type=Path, required=True)
    load_vacancies.add_argument(
        "--schema",
        type=Path,
        default=Path("sql/schema.sql"),
    )

    load_wages = subparsers.add_parser(
        "load-wages",
        help="replace the DuckDB wage staging table from CSV",
    )
    load_wages.add_argument("--input", type=Path, required=True)
    load_wages.add_argument("--database", type=Path, required=True)
    load_wages.add_argument(
        "--schema",
        type=Path,
        default=Path("sql/schema.sql"),
    )

    load_cpi = subparsers.add_parser(
        "load-cpi",
        help="replace the DuckDB CPI staging table from CSV",
    )
    load_cpi.add_argument("--input", type=Path, required=True)
    load_cpi.add_argument("--database", type=Path, required=True)
    load_cpi.add_argument(
        "--schema",
        type=Path,
        default=Path("sql/schema.sql"),
    )

    query = subparsers.add_parser("query", help="run a SQL file against DuckDB")
    query.add_argument("--database", type=Path, required=True)
    query.add_argument("--sql", type=Path, required=True)

    quality = subparsers.add_parser(
        "check-quality",
        help="run SQL data-quality checks against DuckDB",
    )
    quality.add_argument("--database", type=Path, required=True)
    quality.add_argument(
        "--sql",
        type=Path,
        default=Path("sql/quality/unemployment_quality_checks.sql"),
    )

    export = subparsers.add_parser(
        "export",
        help="export a read-only SQL query result to CSV",
    )
    export.add_argument("--database", type=Path, required=True)
    export.add_argument("--sql", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "fetch":
        rows = CbsODataClient().fetch(
            args.table_id,
            args.resource,
            select=args.select,
            filter_expression=args.filter_expression,
        )
        if not rows and not args.allow_empty:
            print(
                "No rows returned; check the table ID, dimension keys, and filter. "
                "No snapshot was written.",
                file=sys.stderr,
            )
            return 2
        write_snapshot(
            args.output,
            table_id=args.table_id,
            resource=args.resource,
            rows=rows,
        )
        print(f"Wrote {len(rows)} rows to {args.output}")
        return 0

    if args.command == "transform-unemployment":
        with args.input.open(encoding="utf-8") as handle:
            snapshot = json.load(handle)
        rows = normalize_unemployment_snapshot(
            snapshot,
            start_period=args.start_period,
        )
        write_staging_csv(args.output, rows)
        print(f"Wrote {len(rows)} normalized rows to {args.output}")
        return 0

    if args.command == "transform-vacancies":
        with args.input.open(encoding="utf-8") as handle:
            observations_snapshot = json.load(handle)
        with args.period_metadata.open(encoding="utf-8") as handle:
            periods_snapshot = json.load(handle)
        rows = normalize_vacancy_snapshots(
            observations_snapshot,
            periods_snapshot,
            start_period=args.start_period,
        )
        write_vacancy_staging_csv(args.output, rows)
        print(f"Wrote {len(rows)} normalized vacancy rows to {args.output}")
        return 0

    if args.command == "transform-wages":
        with args.input.open(encoding="utf-8") as handle:
            observations_snapshot = json.load(handle)
        with args.period_metadata.open(encoding="utf-8") as handle:
            periods_snapshot = json.load(handle)
        rows = normalize_wage_snapshots(
            observations_snapshot,
            periods_snapshot,
            start_period=args.start_period,
        )
        write_wage_staging_csv(args.output, rows)
        print(f"Wrote {len(rows)} normalized wage rows to {args.output}")
        return 0

    if args.command == "transform-cpi":
        with args.input.open(encoding="utf-8") as handle:
            observations_snapshot = json.load(handle)
        with args.period_metadata.open(encoding="utf-8") as handle:
            periods_snapshot = json.load(handle)
        rows = normalize_cpi_snapshots(
            observations_snapshot,
            periods_snapshot,
            start_period=args.start_period,
        )
        write_cpi_staging_csv(args.output, rows)
        print(f"Wrote {len(rows)} normalized CPI rows to {args.output}")
        return 0

    if args.command == "load-unemployment":
        result = load_unemployment_csv(
            database_path=args.database,
            csv_path=args.input,
            schema_path=args.schema,
        )
        print(
            f"Loaded {result.row_count} rows into {args.database} "
            f"({result.first_period} through {result.last_period})"
        )
        return 0

    if args.command == "load-vacancies":
        result = load_vacancies_csv(
            database_path=args.database,
            csv_path=args.input,
            schema_path=args.schema,
        )
        print(
            f"Loaded {result.row_count} vacancy rows into {args.database} "
            f"({result.first_period} through {result.last_period})"
        )
        return 0

    if args.command == "load-wages":
        result = load_wages_csv(
            database_path=args.database,
            csv_path=args.input,
            schema_path=args.schema,
        )
        print(
            f"Loaded {result.row_count} wage rows into {args.database} "
            f"({result.first_period} through {result.last_period})"
        )
        return 0


    if args.command == "load-cpi":
        result = load_cpi_csv(
            database_path=args.database,
            csv_path=args.input,
            schema_path=args.schema,
        )
        print(
            f"Loaded {result.row_count} CPI rows into {args.database} "
            f"({result.first_period} through {result.last_period})"
        )
        return 0

    if args.command == "query":
        columns, rows = run_sql_file(
            database_path=args.database,
            sql_path=args.sql,
        )
        print("\t".join(columns))
        for row in rows:
            print("\t".join(str(value) for value in row))
        return 0

    if args.command == "check-quality":
        results = run_quality_checks(
            database_path=args.database,
            sql_path=args.sql,
        )
        for result in results:
            status = "PASS" if result.passed else "FAIL"
            print(f"{status}\t{result.check_name}\tfailed_rows={result.failed_rows}")
        return 0 if all(result.passed for result in results) else 1

    if args.command == "export":
        result = export_sql_to_csv(
            database_path=args.database,
            sql_path=args.sql,
            output_path=args.output,
        )
        print(
            f"Exported {result.row_count} rows and {result.column_count} columns "
            f"to {args.output}"
        )
        return 0

    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
