# Data Dictionary

## `unemployment_monthly_2015_onward.csv`

Staging dataset produced from the raw CBS unemployment snapshot. One row represents
one calendar month for the Netherlands population aged 15–74, total sex.

| Column | Type | Unit | Description |
|---|---|---|---|
| `period` | date | — | First day of the observation month in ISO format |
| `source_period` | text | — | Original CBS period key, retained for traceability |
| `unemployed_thousands` | number | thousands of people | Seasonally adjusted unemployed labour force |
| `unemployment_rate_pct` | number | percent | CBS-published seasonally adjusted unemployment rate |
| `source_table_id` | text | — | CBS StatLine table identifier (`80590ENG`) |
| `retrieved_at_utc` | timestamp | UTC | Retrieval time inherited from the raw snapshot |

Validation rules:

- Period keys must match `YYYYMMmm` with months `01` through `12`.
- Periods must be unique.
- Unemployed counts cannot be negative.
- Unemployment rates must be between 0 and 100.
- The output cannot be empty.
- The MVP output begins at `2015MM01`.

## `staging.unemployment_monthly`

DuckDB table loaded from the staging CSV with an explicit SQL schema.

| Column | DuckDB type | Constraint |
|---|---|---|
| `period` | `DATE` | Primary key |
| `source_period` | `VARCHAR` | Required and unique |
| `unemployed_thousands` | `DOUBLE` | Required and non-negative |
| `unemployment_rate_pct` | `DOUBLE` | Required and between 0 and 100 |
| `source_table_id` | `VARCHAR` | Required |
| `retrieved_at_utc` | `TIMESTAMPTZ` | Required |

The database is generated locally at `data/warehouse/labour_market.duckdb` and is
not committed to Git.

## `vacancies_quarterly_2015_onward.csv`

Staging dataset produced by joining the raw vacancy observations to the CBS period
metadata. One row represents the national vacancy stock at the end of one quarter.

| Column | Type | Unit | Description |
|---|---|---|---|
| `quarter_end` | date | — | Last calendar day of the observation quarter |
| `source_period` | text | — | Original CBS quarterly key |
| `unfilled_vacancies_thousands` | number | thousands | Seasonally adjusted unfilled vacancies at quarter-end |
| `status` | text | — | English normalized status: `final` or `provisional` |
| `source_status` | text | — | Original CBS status label |
| `is_provisional` | Boolean | — | True when the observation is provisional |
| `source_table_id` | text | — | CBS StatLine table identifier (`84545ENG`) |
| `retrieved_at_utc` | timestamp | UTC | Observation snapshot retrieval time |

## `staging.vacancies_quarterly`

DuckDB table loaded from the vacancy staging CSV. `quarter_end` is its primary key;
the source period is also unique. Values must be non-negative, and normalized status
must be either `final` or `provisional`.

## `wages_monthly_2020_onward.csv`

Staging dataset produced by joining monthly wage observations to CBS period
metadata. One row represents hourly collective-agreement wages for the total CAO
sector and all economic activities.

| Column | Type | Unit | Description |
|---|---|---|---|
| `period` | date | — | First day of the observation month |
| `source_period` | text | — | Original CBS monthly key |
| `hourly_cao_wage_index_2020` | number | index, 2020=100 | Hourly CAO wages including special payments |
| `hourly_cao_wage_yoy_pct` | nullable number | percent | CBS-published year-on-year change; null throughout 2020 |
| `status` | text | — | English normalized status: `final` or `provisional` |
| `source_status` | text | — | Original CBS status label |
| `is_provisional` | Boolean | — | True when the observation is provisional |
| `source_table_id` | text | — | CBS StatLine table identifier (`85663ENG`) |
| `retrieved_at_utc` | timestamp | UTC | Observation snapshot retrieval time |

## `staging.wages_monthly`

DuckDB table loaded from the wage staging CSV. `period` is its primary key and
`source_period` is unique. The wage index must be positive. The year-on-year field,
when present, must be greater than -100 and no more than 100. Status must agree with
the provisional Boolean. Null growth is accepted only during 2020, when the
2020-base source has no prior-year comparison.

## `cpi_monthly_2020_onward.csv`

Staging dataset produced by joining national all-items CPI observations to CBS
period metadata. One row represents one calendar month.

| Column | Type | Unit | Description |
|---|---|---|---|
| `period` | date | — | First day of the observation month |
| `source_period` | text | — | Original CBS monthly key |
| `cpi_index_2025` | number | index, 2025=100 | National all-items consumer price index |
| `cpi_inflation_yoy_pct` | number | percent | CBS-published annual CPI rate of change |
| `status` | text | — | English normalized status: `final` or `provisional` |
| `source_status` | text | — | Original CBS status label |
| `is_provisional` | Boolean | — | True when the observation is provisional |
| `source_table_id` | text | — | CBS StatLine table identifier (`86141ENG`) |
| `retrieved_at_utc` | timestamp | UTC | Observation snapshot retrieval time |

## `staging.cpi_monthly`

DuckDB table loaded from the CPI staging CSV. `period` is its primary key and
`source_period` is unique. The index must be positive, annual inflation must be
greater than -100 and no more than 100, and neither measure may be null. Status
must agree with the provisional Boolean. The staging series begins in January 2020
to align with the wage table used for real-wage analysis.

## `analytics.fct_wages_prices`

dbt-built monthly fact table created by an inner join on the wage and CPI dates.
Only months with a published wage-growth rate are included, so the table begins in
January 2021.

| Column | Unit | Description |
|---|---|---|
| `period` | date | Common wage and CPI observation month |
| `wage_source_period` | text | Original wage-source period key |
| `cpi_source_period` | text | Original CPI-source period key |
| `hourly_cao_wage_index_2020` | index, 2020=100 | Published hourly CAO wage index |
| `hourly_cao_wage_yoy_pct` | percent | Published annual nominal wage growth |
| `cpi_index_2025` | index, 2025=100 | Published national all-items CPI |
| `cpi_inflation_yoy_pct` | percent | Published annual CPI inflation |
| `real_wage_growth_pct` | percent | Exact growth-factor calculation |
| `nominal_minus_inflation_pp` | percentage points | Intuitive approximation for comparison |
| `wage_status` | text | Normalized wage publication status |
| `cpi_status` | text | Normalized CPI publication status |
| `is_provisional` | Boolean | True if either source observation is provisional |

## `analytics.agg_wages_prices_annual`

Annual descriptive summary of the monthly fact table. It reports average nominal
wage growth, inflation, exact real wage growth, the number of positive real-growth
months, and whether the year contains provisional observations. Annual averages
describe the monthly year-on-year rates; they are not newly calculated annual-index
changes.

## `analytics.dim_month`

Continuous monthly calendar from January 2015 through the latest available monthly
source observation. It provides calendar year, month number and name, quarter,
`YYYY-MM` label, a quarter-end-month flag, and the corresponding calendar
quarter-end date.

## `analytics.fct_labour_market_periodic`

Monthly dashboard fact table anchored on the complete unemployment series. It
retains unemployment for every month from January 2015 and adds CPI and wage
measures when their sources become available. CPI begins in January 2020, published
wage growth and real wage growth begin in January 2021, and unavailable earlier
fields remain null rather than being filled.

## `analytics.fct_vacancies`

Quarterly vacancy fact table. Each vacancy quarter is aligned with unemployment in
the final month of that quarter.

| Column | Unit | Description |
|---|---|---|
| `quarter_end` | date | Calendar end of the vacancy quarter |
| `unfilled_vacancies_thousands` | thousands | Seasonally adjusted vacancy stock |
| `unemployed_thousands` | thousands | Unemployment in the quarter's final month |
| `unemployment_rate_pct` | percent | Published rate in the quarter's final month |
| `vacancies_per_100_unemployed` | ratio per 100 | Tightness indicator; not the official vacancy rate |
| `vacancy_growth_qoq_pct` | percent | Change in vacancy stock from the previous quarter |
| `tightness_change_qoq` | ratio-point change | Change in the tightness indicator |
| `tightness_direction_qoq` | text | `tighter`, `looser`, `unchanged`, or `not_available` |
| `is_provisional` | Boolean | CBS vacancy publication status flag |

## Dashboard exports

The `export` command writes four generated CSV files to `data/dashboard/`:

- `dim_month.csv`: 140 calendar rows at this checkpoint.
- `monthly_trends.csv`: 140 monthly chart rows with metric-availability flags.
- `quarterly_tightness.csv`: 46 quarterly chart rows and a
  `quarter_month_start` relationship key.
- `headline_kpis.csv`: one row containing 16 headline values, status flags, and
  three distinct reporting dates.

Generated dashboard CSV files are ignored by Git and can be recreated from the
versioned dbt models and SQL export queries.
