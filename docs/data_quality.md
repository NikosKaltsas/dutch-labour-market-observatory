# Data-Quality Checks

The unemployment staging table is checked at two layers:

1. Python validates the raw-to-CSV transformation.
2. SQL validates the data after it has been loaded into DuckDB.

## SQL checks

| Check | Pass condition | Purpose |
|---|---|---|
| `duplicate_periods` | Zero duplicate months | Enforces one observation per month |
| `invalid_values` | Zero negative counts or rates outside 0–100 | Detects impossible analytical values |
| `missing_months` | Every month between the first and last observation exists | Detects gaps in the time series |
| `unexpected_source_ids` | Every row identifies CBS table `80590ENG` | Prevents accidental source mixing |

Run the checks with:

```powershell
python -m dutch_labour_observatory.cli check-quality `
  --database data/warehouse/labour_market.duckdb `
  --sql sql/quality/unemployment_quality_checks.sql
```

Each line reports `PASS` or `FAIL` and the number of failing rows. The command exits
with code `1` if any check fails, allowing the same command to block a later CI
workflow.

Database constraints and quality queries intentionally overlap. Constraints stop
invalid values during loading; queries produce visible, reviewable evidence that
the stored dataset satisfies the contract.

## Vacancy checks

The vacancy table adds checks for:

- One observation per quarter.
- No missing quarters between the first and last observation.
- Dates that are valid calendar quarter ends.
- Non-negative vacancy counts.
- Consistency between normalized status and `is_provisional`.
- CBS source table ID `84545ENG`.

Run them by passing `sql/quality/vacancy_quality_checks.sql` to the same
`check-quality` command.

## Wage checks

The wage table checks:

- One observation per month and no gaps in the complete series.
- Valid first-of-month dates and positive wage-index values.
- Year-on-year growth within the accepted numeric range.
- Null year-on-year growth only in 2020, when the source has no 2019 baseline.
- Consistency between normalized status and `is_provisional`.
- CBS source table ID `85663ENG`.

Run them by passing `sql/quality/wage_quality_checks.sql` to `check-quality`. The
same non-zero exit behavior applies if any rule fails.

## CPI checks

The CPI table checks:

- One observation per month and no gaps from the first to the latest period.
- Valid first-of-month dates and positive CPI-index values.
- Annual inflation within the accepted numeric range.
- No missing index or inflation values in the staging window.
- Consistency between normalized status and `is_provisional`.
- CBS source table ID `86141ENG`.

Run them by passing `sql/quality/cpi_quality_checks.sql` to `check-quality`. The
database constraints also reject null or invalid CPI measures during loading.

## dbt analytical-model tests

The dbt tests
cover source and model uniqueness, required values, accepted publication statuses,
continuous monthly and quarterly coverage, complete wage-CPI alignment, valid
quarter ends, and reproduction of the calculated formulas within small rounding
tolerances.

The complete-alignment test compares the mart with every common staging period that
has a published wage-growth value. This prevents an inner join from silently
dropping otherwise valid months.

The vacancy tests additionally require every quarter to match an unemployment
observation in its final month and verify the vacancies-per-100-unemployed formula.
The calendar and monthly labour-market tests prevent gaps in the dashboard axes.

The dashboard layer adds required-field, unique-key, accepted-value, continuity,
and single-KPI-row checks. The project contains eight models and 63 data tests.
The Python suite contains 43 tests, including atomic CSV export and CLI reporting.
See [the release checklist](release_checklist.md) for dated test results and the
distinction between testing an existing warehouse and rebuilding from scratch.
