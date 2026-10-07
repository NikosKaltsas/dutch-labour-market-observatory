# Source Audit

This log records why each dataset was selected before any observations are added to
the pipeline.

## Source 1: monthly unemployment

**Decision:** Use CBS StatLine table `80590ENG`, *Monthly labour participation and
unemployment*.

**Checked:** 9 September 2026.

**Why this table:**

- It is an active English-language CBS table updated monthly.
- It contains both the unemployed count and the unemployment rate.
- It publishes seasonally adjusted monthly measures suitable for comparisons over
  time.
- Its `Sex` and `Age` dimensions allow an explicit Netherlands-total, age 15–74
  filter rather than relying on an undocumented default.

**MVP selection:**

| Role | CBS key | Selected value |
|---|---|---|
| Sex dimension | `Sex` | `T001038` — Total sex |
| Age dimension | `Age` | `52052   ` — 15 to 74 years; three trailing spaces are significant |
| Period dimension | `Periods` | Monthly keys from `2015MM01` onward |
| Unemployed count | `SeasonallyAdjusted_6` | Thousands of people |
| Unemployment rate | `SeasonallyAdjusted_8` | Percent of labour force |

**Decision:** Use seasonally adjusted values on the main dashboard.

**Reason:** Seasonal adjustment makes adjacent months more comparable by removing
regular within-year patterns. We will not mix these values with unadjusted figures.

**Decision:** Use the CBS-published unemployment rate.

**Reason:** The published counts are rounded to thousands. Recalculating a rate from
those rounded values can differ slightly from the official rate calculated with
more precise source data.

**Known limitations:**

- The table covers people living in the Netherlands aged 15–74 and excludes the
  institutionalized population.
- The unemployment definition requires no paid work, recent job search, and direct
  availability.
- Revisions can occur, so each extraction must preserve its retrieval timestamp and
  source status.

## First extraction check

The project CLI retrieved three observations for January through March 2015 and
wrote them to `data/raw/unemployment_2015_q1.json`.

| Period | Seasonally adjusted unemployed | Published unemployment rate |
|---|---:|---:|
| 2015 January | 760 thousand | 8.3% |
| 2015 February | 747 thousand | 8.1% |
| 2015 March | 745 thousand | 8.1% |

The first API filter returned zero rows because the age key was written as `52052`.
CBS stores this dimension as the fixed-width string `52052   `, including three
trailing spaces. The source configuration now preserves the exact value. This is a
useful schema-contract test to add before the full extraction.

**Not done at this checkpoint:** The sample observations have not been cleaned,
renamed, loaded into a database, or used to calculate new metrics.

## Full monthly extraction

The raw extraction keeps every monthly observation available in the selected table:

- 283 observations.
- January 2003 through July 2026.
- 283 unique period keys matching `YYYYMMmm`.
- No missing unemployment counts or rates.

An attempted `Periods ge '2015MM01'` source filter was not applied by the CBS API,
even though the monthly-period filter was applied. Rather than create a long list of
individual periods or pretend the range filter worked, the raw snapshot preserves
the complete monthly history. The staging layer will apply and test the portfolio's
January 2015 analysis cutoff.

Raw file: `data/raw/unemployment_monthly_full_history.json`.

## Source 2: quarterly unfilled vacancies

**Decision:** Use CBS StatLine table `84545ENG`, *Vacancies; flowfigures,
seasonally adjusted*.

**Checked:** 9 September 2026.

**Why this table:**

- It is an active English-language CBS table updated quarterly.
- It directly provides the national seasonally adjusted number of unfilled
  vacancies.
- It avoids adding an economic-activity classification before the national MVP is
  complete.
- It provides the numerator needed for a later “vacancies per 100 unemployed”
  indicator.

**MVP selection:**

| Role | CBS key | Selected value |
|---|---|---|
| Period dimension | `Periods` | Quarterly keys from `2015KW01` onward |
| Unfilled vacancies | `VacanciesSeasonallyAdjustedUnfilled_1` | Thousands of vacancies |
| Period status | `Periods.Status` | Retain final/provisional metadata |

The unfilled-vacancy measure is a stock at the end of each quarter. It is not the
number of vacancies created during the quarter.

**Small extraction check:**

| Period | Seasonally adjusted unfilled vacancies |
|---|---:|
| 2025 Q1 | 394.2 thousand |
| 2025 Q2 | 388.7 thousand |
| 2025 Q3 | 385.4 thousand |

The sample was written to `data/raw/vacancies_2025_q1_q3.json`. The 2026 periods
were marked provisional in the separate CBS `Periods` resource when the table was
checked. That metadata will be ingested alongside the complete observation series
before staging.

**Frequency decision:** Keep quarterly vacancies separate from monthly unemployment
in staging. Any combined indicator must state how the monthly unemployment values
are aligned to quarter-end or quarterly-average vacancy data.

## Source 3: monthly negotiated wages

**Decision:** Use CBS StatLine table `85663ENG`, *Cao wages, contractual wage costs
and working hours; index (2020=100)*.

**Checked:** 9 September 2026.

**Why this table:**

- It is the active replacement for the discontinued 2010-base table.
- It is updated monthly and provides both an index and a CBS-published year-on-year
  change.
- It provides current and first-published versions, making the revision choice
  explicit.
- It has national total and all-economic-activities dimension values suitable for
  the MVP.

**MVP selection:**

| Role | CBS key | Selected value |
|---|---|---|
| CAO sector | `CaoSector` | `T001020` — Total CAO sector |
| Economic activity | `SectorBranchesSIC2008` | `T001081` — All activities |
| Version | `Version` | `A045600   ` — Current figures; trailing spaces significant |
| Wage index | `HourlyCaoWagesInclSpecialPayments_4` | Hourly CAO wages including special payments, 2020=100 |
| Wage growth | `HourlyCaoWagesInclSpecialPayments_11` | Published year-on-year change, percent |

**Measure decision:** Use hourly CAO wages including special payments. Hourly values
account for changes in contractual working hours, while including binding special
payments gives a broader contractual compensation measure. Conditional bonuses and
individual wage increases are not included.

**Revision decision:** Use current figures. They are the best currently available
estimates and may revise as additional collective agreements are completed. The raw
snapshot timestamp and period status make those revisions auditable. First-published
figures are deferred unless the project later studies revisions themselves.

**Time-window decision:** This table's monthly 2020-base series starts in 2020. Do
not splice it to the discontinued 2010-base table in the MVP. Unemployment and
vacancy charts can begin in 2015, while wage and real-wage charts will begin in 2020.

**Small extraction check:**

| Period | Wage index | Year-on-year growth | Status |
|---|---:|---:|---|
| 2025 December | 126.7 | 4.6% | Final |
| 2026 January | 128.7 | 4.3% | Provisional |
| 2026 February | 129.0 | 4.5% | Provisional |

The observation sample is stored in `data/raw/wages_2025_dec_2026_feb.json`; its
period metadata is stored in `data/raw/wage_periods_sample_metadata.json`.

## Source 4: monthly consumer prices

**Decision:** Use CBS StatLine table `86141ENG`, *Consumer prices; CPI 2025=100,
index and rates of change*.

**Checked:** 9 September 2026.

**Why this table:**

- It is the current active English-language national CPI table, updated monthly.
- It contains the regular monthly all-items CPI and the CBS-published annual rate
  of change used as the Dutch inflation rate.
- CBS rebased the index from 2015=100 to 2025=100 in 2026 and supplies a rebased
  history back to December 2009.
- It retains final/provisional status through the separate `Periods` resource.

The twelve-month-average table `86143ENG` was not selected because it smooths each
observation over twelve months. The HICP table was also not selected: HICP is best
for EU comparisons, while this MVP asks about purchasing power in the Dutch
domestic labour market.

**MVP selection:**

| Role | CBS key | Selected value |
|---|---|---|
| Expenditure category | `ExpenditureCategories` | `T001112  ` — `000000 All items`; two trailing spaces are significant |
| Period dimension | `Periods` | Monthly keys from `2020MM01` onward |
| Price index | `CPI_1` | CPI, 2025=100 |
| Inflation | `AnnualRateOfChangeCPI_5` | Published annual rate of change, percent |
| Period status | `Periods.Status` | Retain final/provisional metadata |

**Measure decision:** Use the CBS-published annual CPI change rather than deriving
it from rounded index values. Keep the index as a useful reference and for
validation. Stage the series from January 2020 so it aligns with the wage source;
the complete available monthly history will remain in the raw snapshot.

**Small extraction check:**

| Period | CPI index | Annual inflation | Status |
|---|---:|---:|---|
| 2025 December | 100.73 | 2.9% | Final |
| 2026 January | 99.99 | 2.4% | Final |
| 2026 February | 101.02 | 2.4% | Final |

The observation sample is stored in `data/raw/cpi_2025_dec_2026_feb.json`. The
latest period in the metadata, August 2026, was provisional when checked.

## Full CPI extraction

The all-items monthly extraction contains 201 observations from December 2009
through August 2026, with no missing index values. The first twelve observations
have no published annual rate because no prior-year comparison exists. Staging
applies the January 2020 cutoff, producing 80 continuous observations with complete
index and inflation measures. August 2026 is the only provisional staging period.

Raw observations are stored in `data/raw/cpi_monthly_full_history.json`, period
metadata in `data/raw/cpi_periods_metadata.json`, and normalized output in
`data/processed/cpi_monthly_2020_onward.csv`.
