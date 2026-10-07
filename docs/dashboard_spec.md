# Dashboard Specification

## Purpose

Answer two questions without mixing source frequencies:

1. Is the Dutch labour market becoming tighter or looser?
2. Is contractual wage growth staying ahead of consumer-price inflation?

The Power BI report uses generated CSV files from `data/dashboard/`. Each headline
card displays its own reporting period because CBS updates the sources on different
schedules.

## Data model

| File | Grain | Role |
|---|---|---|
| `dim_month.csv` | One row per month | Shared date filtering and display fields |
| `monthly_trends.csv` | One row per month | Unemployment, wages, inflation, and real wages |
| `quarterly_tightness.csv` | One row per quarter | Vacancies and labour-market tightness |
| `headline_kpis.csv` | One row | Latest values and their separate source dates |

Create these relationships in Power BI:

- `dim_month[month_start]` to `monthly_trends[period]`, one-to-one.
- `dim_month[month_start]` to `quarterly_tightness[quarter_month_start]`,
  one-to-many from the date dimension.
- Leave `headline_kpis` disconnected because it always represents the latest
  available observation for each source.

Keep `dim_month` at its intentional monthly grain; do not mark it as Power BI's
formal date table because that designation requires a gapless daily date column.
Sort `month_name` by `month_number` and `year_month` by `month_start`.

## Page 1: Labour-market overview

Saved canvas: 1920 × 1080 (16:9). Keep the page readable at Fit to page.

```text
+-----------------------------------------------------------------------+
| Dutch Labour-Market Observatory                 Reset filters | Year  |
+----------------+----------------+----------------+--------------------+
| Unemployment   | Vacancies per | Real wage     | Nominal vs         |
| 4.0% · Jul 26  | 100 unemployed| +0.68% · Aug26| inflation · Aug 26 |
+----------------+----------------+----------------+--------------------+
| Real-wage outcome donut | Quarterly average gauge | Quarterly columns |
+-------------------------+-------------------------+-------------------+
| Unemployment — monthly          | Wages and inflation — monthly       |
+--------------------------------+--------------------------------------+
```

Report visuals:

- Four KPI cards using `headline_kpis`, each with its own period subtitle.
- Line chart: `monthly_trends[period]` and the `Unemployment Rate` measure.
- Three-line chart: nominal wage growth, CPI inflation, and real wage growth.
- Clustered columns: `quarterly_tightness[Quarter Label]`, sorted by `quarter_end`,
  and the `Vacancies per 100 Unemployed` measure. Full history may require a
  chart scrollbar.
- Donut: counts of months with real-wage growth, classified as Non-negative
  (including zero) or Negative. Missing data is excluded, not classified as zero.
- Gauge: arithmetic mean of selected quarterly ratios, with minimum 0, maximum
  200, and reference 100. This is not a ratio of pooled counts.
- Year slicer from `dim_month[Year]` (or `calendar_year`) for historical visuals.
- Reset filters bookmark and button restore All and clear chart selections.

Intended donut interactions filter the monthly line charts and center count card,
but not the gauge or quarterly columns. See final visual acceptance checks in
[release_checklist.md](release_checklist.md). Latest KPI cards remain unaffected.
Dynamic subtitles explain CPI coverage from January 2020 and wage-growth coverage
from January 2021. The donut center label is **Months in current selection**.

Use percentage formatting with one decimal on cards and two decimals in tooltips.
Use thousands with no more than one decimal. Do not connect monthly points across
null periods before a measure's source coverage begins.

## Page 2: Definitions and data quality

Include:

- Metric definitions and the exact real-wage formula.
- A warning that vacancies per 100 unemployed is a tightness indicator, not the
  official vacancy rate.
- Source table IDs: `80590ENG`, `84545ENG`, `85663ENG`, and `86141ENG`.
- Source coverage and final/provisional status definitions.
- Dated validation evidence is kept in `release_checklist.md`, not an undated
  count on the report page.
- Limitations: national averages, CAO wages are not all earnings, and source
  publication dates differ.

Use two columns of panels (Metric definitions / Wages & prices, then Sources &
coverage / How to read this report) and a full-width Limitations panel below.
Include gauge and donut definitions, filter behavior, and coverage caveats.

## Visual system

- Background: off-white (saved overview uses `#F3F4F6`).
- Primary text and unemployment: navy `#17324D`.
- Nominal wage growth and vacancy visuals: teal.
- Inflation and negative donut category: coral.
- Real wage growth line: amber; non-negative donut category: teal.
- The supplied theme is a base; visual-level overrides in the report take
  precedence. Keep a text explanation of provisional data.

Avoid red/green as the only distinction: use line labels and different dash styles
as well. Titles should state the metric and frequency explicitly.

## Desktop implementation package

The files needed to assemble this specification in Power BI Desktop are versioned
under `powerbi/`:

- `dutch_labour_market_theme.json` applies the report palette and base typography.
- `measures.dax` contains the card, trend, status, and conditional-color measures.
- `calculated_columns.dax` documents Year, real-wage direction, and quarter labels.
- `BUILD_GUIDE.md` defines import types, model relationships, exact visual fields,
  page copy, and acceptance checks.

The binary `powerbi/dutch_labour_market_observatory.pbix` is included as the saved
desktop artifact. Companion DAX and documentation are not automatically
synchronized with its semantic model. See the release checklist for outstanding
visual acceptance checks and clean screenshots.
