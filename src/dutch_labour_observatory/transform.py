"""Validation and staging transforms for CBS unemployment observations."""

from __future__ import annotations

import calendar
import csv
import re
import tempfile
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any

SOURCE_PERIOD_PATTERN = re.compile(
    r"^(?P<year>\d{4})MM(?P<month>0[1-9]|1[0-2])$"
)
OUTPUT_COLUMNS = (
    "period",
    "source_period",
    "unemployed_thousands",
    "unemployment_rate_pct",
    "source_table_id",
    "retrieved_at_utc",
)
VACANCY_OUTPUT_COLUMNS = (
    "quarter_end",
    "source_period",
    "unfilled_vacancies_thousands",
    "status",
    "source_status",
    "is_provisional",
    "source_table_id",
    "retrieved_at_utc",
)
WAGE_OUTPUT_COLUMNS = (
    "period",
    "source_period",
    "hourly_cao_wage_index_2020",
    "hourly_cao_wage_yoy_pct",
    "status",
    "source_status",
    "is_provisional",
    "source_table_id",
    "retrieved_at_utc",
)
CPI_OUTPUT_COLUMNS = (
    "period",
    "source_period",
    "cpi_index_2025",
    "cpi_inflation_yoy_pct",
    "status",
    "source_status",
    "is_provisional",
    "source_table_id",
    "retrieved_at_utc",
)
SOURCE_QUARTER_PATTERN = re.compile(
    r"^(?P<year>\d{4})KW0(?P<quarter>[1-4])$"
)
CBS_STATUS_MAP = {
    "Definitief": ("final", False),
    "Voorlopig": ("provisional", True),
}


class DataValidationError(ValueError):
    """Raised when raw source data violates the staging contract."""


def normalize_unemployment_snapshot(
    snapshot: Mapping[str, Any],
    *,
    start_period: str = "2015MM01",
) -> list[dict[str, Any]]:
    """Validate and normalize a raw CBS unemployment snapshot.

    Raw source values are never changed in place. Only monthly observations at or
    after ``start_period`` are returned.
    """

    _parse_monthly_period(start_period)
    rows = snapshot.get("rows")
    if not isinstance(rows, list):
        raise DataValidationError("snapshot must contain a list-valued 'rows'")

    table_id = _required_text(snapshot, "table_id")
    retrieved_at = _required_text(snapshot, "retrieved_at_utc")
    normalized: list[dict[str, Any]] = []
    seen_periods: set[str] = set()

    for row_number, row in enumerate(rows, start=1):
        if not isinstance(row, Mapping):
            raise DataValidationError(f"row {row_number} is not an object")

        source_period = _required_text(row, "Periods", row_number=row_number)
        period = _parse_monthly_period(source_period)
        if source_period < start_period:
            continue
        if source_period in seen_periods:
            raise DataValidationError(f"duplicate period: {source_period}")
        seen_periods.add(source_period)

        unemployed = _required_number(
            row,
            "SeasonallyAdjusted_6",
            row_number=row_number,
        )
        rate = _required_number(
            row,
            "SeasonallyAdjusted_8",
            row_number=row_number,
        )
        if unemployed < 0:
            raise DataValidationError(
                f"row {row_number} has a negative unemployed count"
            )
        if not 0 <= rate <= 100:
            raise DataValidationError(
                f"row {row_number} has an unemployment rate outside 0-100"
            )

        normalized.append(
            {
                "period": period.isoformat(),
                "source_period": source_period,
                "unemployed_thousands": unemployed,
                "unemployment_rate_pct": rate,
                "source_table_id": table_id,
                "retrieved_at_utc": retrieved_at,
            }
        )

    normalized.sort(key=lambda row: row["source_period"])
    if not normalized:
        raise DataValidationError(
            f"no monthly observations found at or after {start_period}"
        )
    return normalized


def write_staging_csv(
    output_path: Path,
    rows: Sequence[Mapping[str, Any]],
) -> None:
    """Atomically write normalized staging rows to CSV."""

    _write_csv(output_path, rows, fieldnames=OUTPUT_COLUMNS)


def normalize_vacancy_snapshots(
    observations_snapshot: Mapping[str, Any],
    periods_snapshot: Mapping[str, Any],
    *,
    start_period: str = "2015KW01",
) -> list[dict[str, Any]]:
    """Join vacancy observations to period status and normalize quarterly rows."""

    _parse_quarter_end(start_period)
    observation_rows = observations_snapshot.get("rows")
    period_rows = periods_snapshot.get("rows")
    if not isinstance(observation_rows, list):
        raise DataValidationError(
            "observations snapshot must contain a list-valued 'rows'"
        )
    if not isinstance(period_rows, list):
        raise DataValidationError(
            "periods snapshot must contain a list-valued 'rows'"
        )

    table_id = _required_text(observations_snapshot, "table_id")
    metadata_table_id = _required_text(periods_snapshot, "table_id")
    if metadata_table_id != table_id:
        raise DataValidationError("observation and period metadata table IDs differ")
    retrieved_at = _required_text(observations_snapshot, "retrieved_at_utc")
    status_by_period = _build_status_lookup(period_rows)

    normalized: list[dict[str, Any]] = []
    seen_periods: set[str] = set()
    for row_number, row in enumerate(observation_rows, start=1):
        if not isinstance(row, Mapping):
            raise DataValidationError(f"vacancy row {row_number} is not an object")
        source_period = _required_text(row, "Periods", row_number=row_number)
        quarter_end = _parse_quarter_end(source_period)
        if source_period < start_period:
            continue
        if source_period in seen_periods:
            raise DataValidationError(f"duplicate vacancy period: {source_period}")
        seen_periods.add(source_period)

        vacancies = _required_number(
            row,
            "VacanciesSeasonallyAdjustedUnfilled_1",
            row_number=row_number,
        )
        if vacancies < 0:
            raise DataValidationError(
                f"vacancy row {row_number} has a negative value"
            )
        if source_period not in status_by_period:
            raise DataValidationError(
                f"missing period metadata for vacancy period {source_period}"
            )
        source_status = status_by_period[source_period]
        if source_status not in CBS_STATUS_MAP:
            raise DataValidationError(
                f"unknown CBS vacancy status {source_status!r} for {source_period}"
            )
        status, is_provisional = CBS_STATUS_MAP[source_status]

        normalized.append(
            {
                "quarter_end": quarter_end.isoformat(),
                "source_period": source_period,
                "unfilled_vacancies_thousands": vacancies,
                "status": status,
                "source_status": source_status,
                "is_provisional": is_provisional,
                "source_table_id": table_id,
                "retrieved_at_utc": retrieved_at,
            }
        )

    normalized.sort(key=lambda row: row["source_period"])
    if not normalized:
        raise DataValidationError(
            f"no quarterly vacancy observations found at or after {start_period}"
        )
    return normalized


def write_vacancy_staging_csv(
    output_path: Path,
    rows: Sequence[Mapping[str, Any]],
) -> None:
    """Atomically write normalized vacancy rows to CSV."""

    _write_csv(output_path, rows, fieldnames=VACANCY_OUTPUT_COLUMNS)


def normalize_wage_snapshots(
    observations_snapshot: Mapping[str, Any],
    periods_snapshot: Mapping[str, Any],
    *,
    start_period: str = "2020MM01",
) -> list[dict[str, Any]]:
    """Join monthly CAO wage observations to status metadata and normalize them."""

    _parse_monthly_period(start_period)
    observation_rows = observations_snapshot.get("rows")
    period_rows = periods_snapshot.get("rows")
    if not isinstance(observation_rows, list):
        raise DataValidationError(
            "wage observations snapshot must contain a list-valued 'rows'"
        )
    if not isinstance(period_rows, list):
        raise DataValidationError(
            "wage periods snapshot must contain a list-valued 'rows'"
        )

    table_id = _required_text(observations_snapshot, "table_id")
    metadata_table_id = _required_text(periods_snapshot, "table_id")
    if metadata_table_id != table_id:
        raise DataValidationError("wage observation and metadata table IDs differ")
    retrieved_at = _required_text(observations_snapshot, "retrieved_at_utc")
    status_by_period = _build_status_lookup(period_rows)

    expected_dimensions = {
        "CaoSector": "T001020",
        "SectorBranchesSIC2008": "T001081",
        "Version": "A045600   ",
    }
    normalized: list[dict[str, Any]] = []
    seen_periods: set[str] = set()

    for row_number, row in enumerate(observation_rows, start=1):
        if not isinstance(row, Mapping):
            raise DataValidationError(f"wage row {row_number} is not an object")
        for dimension, expected_value in expected_dimensions.items():
            actual_value = _required_text(row, dimension, row_number=row_number)
            if actual_value != expected_value:
                raise DataValidationError(
                    f"wage row {row_number} has unexpected {dimension} value"
                )

        source_period = _required_text(row, "Periods", row_number=row_number)
        period = _parse_monthly_period(source_period)
        if source_period < start_period:
            continue
        if source_period in seen_periods:
            raise DataValidationError(f"duplicate wage period: {source_period}")
        seen_periods.add(source_period)

        wage_index = _required_number(
            row,
            "HourlyCaoWagesInclSpecialPayments_4",
            row_number=row_number,
        )
        wage_growth = _optional_number(
            row,
            "HourlyCaoWagesInclSpecialPayments_11",
            row_number=row_number,
        )
        if wage_index <= 0:
            raise DataValidationError(f"wage row {row_number} has a non-positive index")
        if wage_growth is not None and not -100 < wage_growth <= 100:
            raise DataValidationError(
                f"wage row {row_number} has year-on-year growth outside (-100, 100]"
            )
        if source_period not in status_by_period:
            raise DataValidationError(
                f"missing period metadata for wage period {source_period}"
            )
        source_status = status_by_period[source_period]
        if source_status not in CBS_STATUS_MAP:
            raise DataValidationError(
                f"unknown CBS wage status {source_status!r} for {source_period}"
            )
        status, is_provisional = CBS_STATUS_MAP[source_status]

        normalized.append(
            {
                "period": period.isoformat(),
                "source_period": source_period,
                "hourly_cao_wage_index_2020": wage_index,
                "hourly_cao_wage_yoy_pct": wage_growth,
                "status": status,
                "source_status": source_status,
                "is_provisional": is_provisional,
                "source_table_id": table_id,
                "retrieved_at_utc": retrieved_at,
            }
        )

    normalized.sort(key=lambda row: row["source_period"])
    if not normalized:
        raise DataValidationError(
            f"no monthly wage observations found at or after {start_period}"
        )
    return normalized


def write_wage_staging_csv(
    output_path: Path,
    rows: Sequence[Mapping[str, Any]],
) -> None:
    """Atomically write normalized wage rows to CSV."""

    _write_csv(output_path, rows, fieldnames=WAGE_OUTPUT_COLUMNS)


def normalize_cpi_snapshots(
    observations_snapshot: Mapping[str, Any],
    periods_snapshot: Mapping[str, Any],
    *,
    start_period: str = "2020MM01",
) -> list[dict[str, Any]]:
    """Join monthly all-items CPI observations to status metadata."""

    _parse_monthly_period(start_period)
    observation_rows = observations_snapshot.get("rows")
    period_rows = periods_snapshot.get("rows")
    if not isinstance(observation_rows, list):
        raise DataValidationError(
            "CPI observations snapshot must contain a list-valued 'rows'"
        )
    if not isinstance(period_rows, list):
        raise DataValidationError(
            "CPI periods snapshot must contain a list-valued 'rows'"
        )

    table_id = _required_text(observations_snapshot, "table_id")
    metadata_table_id = _required_text(periods_snapshot, "table_id")
    if metadata_table_id != table_id:
        raise DataValidationError("CPI observation and metadata table IDs differ")
    retrieved_at = _required_text(observations_snapshot, "retrieved_at_utc")
    status_by_period = _build_status_lookup(period_rows)

    normalized: list[dict[str, Any]] = []
    seen_periods: set[str] = set()
    for row_number, row in enumerate(observation_rows, start=1):
        if not isinstance(row, Mapping):
            raise DataValidationError(f"CPI row {row_number} is not an object")
        category = _required_text(
            row,
            "ExpenditureCategories",
            row_number=row_number,
        )
        if category != "T001112  ":
            raise DataValidationError(
                f"CPI row {row_number} has unexpected ExpenditureCategories value"
            )

        source_period = _required_text(row, "Periods", row_number=row_number)
        period = _parse_monthly_period(source_period)
        if source_period < start_period:
            continue
        if source_period in seen_periods:
            raise DataValidationError(f"duplicate CPI period: {source_period}")
        seen_periods.add(source_period)

        cpi_index = _required_number(row, "CPI_1", row_number=row_number)
        inflation = _required_number(
            row,
            "AnnualRateOfChangeCPI_5",
            row_number=row_number,
        )
        if cpi_index <= 0:
            raise DataValidationError(f"CPI row {row_number} has a non-positive index")
        if not -100 < inflation <= 100:
            raise DataValidationError(
                f"CPI row {row_number} has annual inflation outside (-100, 100]"
            )
        if source_period not in status_by_period:
            raise DataValidationError(
                f"missing period metadata for CPI period {source_period}"
            )
        source_status = status_by_period[source_period]
        if source_status not in CBS_STATUS_MAP:
            raise DataValidationError(
                f"unknown CBS CPI status {source_status!r} for {source_period}"
            )
        status, is_provisional = CBS_STATUS_MAP[source_status]

        normalized.append(
            {
                "period": period.isoformat(),
                "source_period": source_period,
                "cpi_index_2025": cpi_index,
                "cpi_inflation_yoy_pct": inflation,
                "status": status,
                "source_status": source_status,
                "is_provisional": is_provisional,
                "source_table_id": table_id,
                "retrieved_at_utc": retrieved_at,
            }
        )

    normalized.sort(key=lambda row: row["source_period"])
    if not normalized:
        raise DataValidationError(
            f"no monthly CPI observations found at or after {start_period}"
        )
    return normalized


def write_cpi_staging_csv(
    output_path: Path,
    rows: Sequence[Mapping[str, Any]],
) -> None:
    """Atomically write normalized CPI rows to CSV."""

    _write_csv(output_path, rows, fieldnames=CPI_OUTPUT_COLUMNS)


def _parse_monthly_period(value: str) -> date:
    match = SOURCE_PERIOD_PATTERN.fullmatch(value)
    if not match:
        raise DataValidationError(
            f"invalid monthly period {value!r}; expected YYYYMMmm"
        )
    return date(int(match.group("year")), int(match.group("month")), 1)


def _parse_quarter_end(value: str) -> date:
    match = SOURCE_QUARTER_PATTERN.fullmatch(value)
    if not match:
        raise DataValidationError(
            f"invalid quarterly period {value!r}; expected YYYYKW0q"
        )
    year = int(match.group("year"))
    quarter = int(match.group("quarter"))
    month = quarter * 3
    return date(year, month, calendar.monthrange(year, month)[1])


def _write_csv(
    output_path: Path,
    rows: Sequence[Mapping[str, Any]],
    *,
    fieldnames: Sequence[str],
) -> None:
    if not rows:
        raise DataValidationError("refusing to write an empty staging CSV")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=output_path.parent,
        delete=False,
        suffix=".tmp",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        temporary_path = Path(handle.name)

    temporary_path.replace(output_path)


def _build_status_lookup(period_rows: Sequence[Any]) -> dict[str, str]:
    status_by_period: dict[str, str] = {}
    for row_number, row in enumerate(period_rows, start=1):
        if not isinstance(row, Mapping):
            raise DataValidationError(
                f"period metadata row {row_number} is not an object"
            )
        key = _required_text(row, "Key", row_number=row_number)
        source_status = _required_text(row, "Status", row_number=row_number)
        if key in status_by_period:
            raise DataValidationError(f"duplicate period metadata key: {key}")
        status_by_period[key] = source_status
    return status_by_period


def _required_text(
    values: Mapping[str, Any],
    key: str,
    *,
    row_number: int | None = None,
) -> str:
    value = values.get(key)
    location = f"row {row_number}" if row_number is not None else "snapshot"
    if not isinstance(value, str) or not value:
        raise DataValidationError(f"{location} requires non-empty text field {key!r}")
    return value


def _required_number(
    values: Mapping[str, Any],
    key: str,
    *,
    row_number: int,
) -> float | int:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DataValidationError(f"row {row_number} requires numeric field {key!r}")
    return value


def _optional_number(
    values: Mapping[str, Any],
    key: str,
    *,
    row_number: int,
) -> float | int | None:
    value = values.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DataValidationError(
            f"row {row_number} requires numeric or null field {key!r}"
        )
    return value
