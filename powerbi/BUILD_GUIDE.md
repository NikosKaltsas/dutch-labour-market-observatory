# Power BI Build Guide

This guide turns the tested CSV exports in `data/dashboard/` into the two-page
portfolio report. Save the finished report as
`powerbi/dutch_labour_market_observatory.pbix`.

The saved PBIX is included. To view it, open it in Power BI Desktop without
refreshing. To refresh on another machine, first generate `data/dashboard/*.csv`
using the repository README, then update the four CSV source paths in Power Query
to that machine's project folder. Do not publish local credentials or raw exports.
This guide describes the intended configuration; remaining acceptance checks are
tracked in `docs/release_checklist.md`.

## 1. Import the model

1. Open Power BI Desktop and create a blank report.
2. Use **Home > Get data > Text/CSV** to import:
   - `data/dashboard/dim_month.csv`
   - `data/dashboard/monthly_trends.csv`
   - `data/dashboard/quarterly_tightness.csv`
   - `data/dashboard/headline_kpis.csv`
3. In Power Query, assign the following types before choosing **Close & Apply**:

| Table | Columns | Type |
|---|---|---|
| `dim_month` | `month_start`, `quarter_end` | Date |
| `dim_month` | `calendar_year`, `month_number`, `calendar_quarter` | Whole number |
| `dim_month` | `is_quarter_end_month` | True/False |
| `monthly_trends` | `period` | Date |
| `monthly_trends` | `calendar_year`, `month_number`, `calendar_quarter` | Whole number |
| `monthly_trends` | all `has_*` columns, `is_provisional` | True/False |
| `monthly_trends` | metric columns ending in `_pct` or `_thousands` | Decimal number |
| `quarterly_tightness` | `quarter_end`, `quarter_month_start` | Date |
| `quarterly_tightness` | `calendar_year`, `calendar_quarter` | Whole number |
| `quarterly_tightness` | metric columns ending in `_pct`, `_change_qoq`, `_thousands`, or `vacancies_per_100_unemployed` | Decimal number |
| `quarterly_tightness` | `is_provisional` | True/False |
| `headline_kpis` | the three columns ending in `_period` | Date |
| `headline_kpis` | the two columns ending in `_is_provisional` | True/False |
| `headline_kpis` | all metric columns | Decimal number |

Use the displayed table names exactly as written above; the supplied DAX relies on
them.

## 2. Create relationships and sort rules

In **Model view**, create these active relationships:

- `dim_month[month_start]` (1) to `monthly_trends[period]` (1), with the
  bidirectional filtering required for a one-to-one relationship.
- `dim_month[month_start]` (1) to
  `quarterly_tightness[quarter_month_start]` (*), filtering from the date dimension.
- Do not relate `headline_kpis`; it must always show each source's latest value.

Then:

1. Do not mark `dim_month` as Power BI's formal date table. Its monthly grain is
   intentional, while Power BI requires a marked date column to contain every day
   without gaps. The relationships and historical slicer work without that flag.
2. Sort `dim_month[month_name]` by `dim_month[month_number]`.
3. Sort `dim_month[year_month]` by `dim_month[month_start]`.
4. Hide key, Boolean, and source-status fields that report consumers do not need.
5. Create the columns in `powerbi/calculated_columns.dax` in their indicated
   tables. Sort `Quarter Label` by `quarter_end`.

## 3. Add the theme and measures

1. Use **View > Themes > Browse for themes** and select
   `powerbi/dutch_labour_market_theme.json`.
2. Create the measures from `powerbi/measures.dax`. A convenient home table is
   `headline_kpis`, although the table holding a measure does not affect its logic.
3. Format rate measures as **Percentage**, with one decimal place on cards and up
   to two in tooltips. Format thousands and the tightness ratio with one decimal.

If Power BI uses semicolons as the DAX list separator for the current locale,
replace formula commas with semicolons when pasting a measure.

## 4. Build page 1: Labour-market overview

Set the page to 1920 × 1080 (16:9), rename it **Labour-market overview**, and use an
off-white background. The saved report uses visual-level color overrides on top
of the supplied base theme.

### Header

- Title: **Dutch Labour-Market Observatory**.
- Small context line: **Cards: latest available data • Charts: selected years**.
- Year slicer: `dim_month[Year]` (or the existing `calendar_year`), dropdown style.
  Exclude blank years. It should affect only
  the historical charts because `headline_kpis` is disconnected.
- Add a **Reset filters** bookmark with all years and no chart selections. Capture
  Data for All visuals; leave Display and Current page off. Connect a button's
  Bookmark action to it and test with Ctrl-click in Desktop editing mode.

### Headline cards

Place four cards across the top:

1. **Unemployment rate**: `Latest Unemployment Rate`; use
   `Unemployment Period Label` as the subtitle or reference label.
2. **Vacancies per 100 unemployed**: `Latest Vacancies per 100 Unemployed`; use
   `Vacancy Period Label` as the subtitle. Source-status measures remain available
   for an additional status annotation or tooltip.
3. **Real wage growth**: `Latest Real Wage Growth`; use
   `Wage-Price Period Label` as the subtitle and conditionally format the callout
   using `Latest Real Wage Color` if desired.
4. **Nominal growth vs inflation**: show `Latest Nominal Wage Growth` and
   `Latest CPI Inflation` in one multi-card visual; use `Wage-Price Period Label`
   as the shared subtitle. Both values share this reference period in the snapshot.

### Historical charts

1. **Unemployment rate — monthly**
   - X-axis: `monthly_trends[period]`, continuous, ascending, blank dates excluded.
   - Y-axis: `Unemployment Rate`.
   - Color: navy `#17324D`.
2. **Wage growth, inflation, and real wages — monthly**
   - X-axis: `monthly_trends[period]`, continuous and ascending.
   - Y-axis: `Nominal Wage Growth`, `CPI Inflation`, and `Real Wage Growth`.
   - Report colors: nominal growth teal, CPI coral, real growth amber.
   - Use distinct markers or dash styles as well as colors.
   - Keep **Show items with no data** off so Power BI does not invent a 2015–2020
     wage history.
3. **Vacancies per 100 unemployed — quarterly**
   - Visual: clustered column chart.
   - X-axis: `quarterly_tightness[Quarter Label]`, categorical, sorted by
     `quarter_end` ascending. A scrollbar may be necessary for the full history.
   - Y-axis: `Vacancies per 100 Unemployed`.
   - Color: teal `#147D78`.
   - Tooltip: `Unfilled Vacancies Thousands`, `unemployed_thousands`, `status`,
     and `Latest Tightness Direction` only if a latest-state annotation is useful.

Add a small caveat beside the quarterly chart:

> Tightness indicator, not the official vacancy rate. Quarterly vacancies are
> paired with unemployment from the quarter's final month.

### Middle-row summary visuals

- **Real-wage outcomes by month:** donut with `Real Wage Direction` as legend
  and Count (not distinct count) of `Real Wage Direction` as values. Exclude
  blank categories. Non-negative includes zero; negative is below zero. These
  are proportions of months, not growth magnitudes. Use teal and coral.
- A centered count card can use `Months with Real Wage Data`; label it
  **Months in current selection** and leave the donut-to-card filter enabled.
- **Vacancies per 100 unemployed:** gauge using `Vacancies per 100 Unemployed`,
  minimum 0, maximum 200, target 100. The value is the arithmetic mean of the
  selected quarterly ratios, not a ratio of pooled counts. Revisit the fixed
  maximum if future data exceeds it.
- Apply `Real Wage Coverage Note` to the donut subtitle and
  `Wage Inflation Coverage Note` to the wage-line-chart subtitle via field-value
  conditional formatting. Missing observations remain blank, never zero.

### Intended interactions

The Year slicer filters all historical visuals, including the donut and gauge,
but not the latest cards. With the donut selected, use **Edit interactions**:
filter the two monthly line charts and center count card; set **None** on both
the gauge and quarterly column chart. Monthly category selections must not
silently redefine the selected-quarter comparison. Both exclusions have been
verified in the saved file; final visual checks are in `docs/release_checklist.md`.

## 5. Build page 2: Definitions and data quality

Rename the page **Definitions & data quality**. Use text boxes and a compact table
or cards for the following content.

### Metric definitions

- **Unemployment rate:** seasonally adjusted unemployed labour force as a share of
  the labour force.
- **Vacancies per 100 unemployed:** unfilled vacancies divided by unemployed
  people, multiplied by 100; this is a project tightness indicator, not the
  official vacancy rate.
- **Nominal wage growth:** year-on-year change in hourly collective-agreement wages
  including special payments.
- **CPI inflation:** CBS-published year-on-year change in the national all-items
  consumer price index.
- **Exact real wage growth:**
  `((1 + nominal wage growth / 100) / (1 + CPI inflation / 100) - 1) * 100`.

### Sources and coverage

| CBS table | Measure | Coverage in current dashboard export |
|---|---|---|
| `80590ENG` | Unemployment | Jan 2015–Jul 2026 |
| `84545ENG` | Vacancies | Q1 2015–Q2 2026 |
| `85663ENG` | CAO wages | Growth available Jan 2021–Aug 2026 |
| `86141ENG` | CPI | Jan 2020–Aug 2026 |

Clarify that these coverage dates describe the loaded snapshot. Provisional
observations may be revised. Each headline card has its own date because the
sources update on different schedules.

### Validation and limitations

- Keep dated validation evidence in `docs/release_checklist.md`, rather than an
  undated test-count claim on the report page.
- The data contains national averages; it does not reveal regional or sector
  differences.
- CAO wage growth measures negotiated contractual wages, not every component of
  realised household earnings.
- Publication dates differ, so the latest unemployment, vacancy, wage, and CPI
  cards do not describe one common reference month.

Arrange the page as two columns: Metric definitions / Wages & prices, then
Sources & coverage / How to read this report. Put Limitations across the bottom.
Explain the Year slicer, latest-card behavior, missing coverage, donut category
selection, and Reset filters. Include the gauge and donut definitions above.

## 6. Validate before saving

With the year slicer cleared, verify the cards against
`data/dashboard/headline_kpis.csv`:

| Card | Expected value | Expected period/status |
|---|---:|---|
| Unemployment rate | 4.0% | Jul 2026 |
| Vacancies per 100 unemployed | 95.4 | Jun 2026, provisional |
| Exact real wage growth | 0.7% | Aug 2026, provisional |
| Nominal wage growth / CPI inflation | 4.0% / 3.3% | Aug 2026, provisional |

Finally verify that:

- The year slicer changes all historical charts, the gauge, and the donut, but
  none of the latest-value cards.
- Monthly charts do not connect across null source coverage.
- The quarterly X-axis labels are sorted by actual quarter-end dates.
- Provisional data is explained without relying only on color.
- Both pages are readable at Fit to page with no clipped text. A quarterly-chart
  scrollbar over the full history is intentional; page-level clipping is not.
- With 2022 and 2023 selected, the gauge is 122.8 and remains unchanged when
  either donut category is selected; all eight quarter bars remain unchanged.
- Reset clears both slicer and chart selections.
- The report saves as `powerbi/dutch_labour_market_observatory.pbix`.
