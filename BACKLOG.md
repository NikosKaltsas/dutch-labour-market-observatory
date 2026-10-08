# Delivery Backlog

Tasks are ordered. Finish the MVP before adding regional maps, cloud platforms, or
forecasting.

## Milestone 1: source-to-raw

- [x] Select and document the current monthly unemployment table.
- [x] Select and document the current quarterly vacancy table.
- [x] Select and document the current collective-agreement wage table.
- [x] Search the English CBS StatLine catalogue for the current CPI table.
- [x] Confirm that each table is active, note its update frequency, and copy its
      identifier and URL into `config/sources.json`.
- [x] Inspect `TableInfos`, `DataProperties`, and all dimension resources.
- [x] Write down the exact filters needed for Netherlands totals and monthly or
      quarterly observations.
- [x] Download and inspect a three-row unemployment snapshot.
- [x] Download and validate the complete monthly unemployment history.
- [x] Download and inspect a three-row vacancy snapshot.
- [x] Download the complete vacancy observations and period-status metadata.
- [x] Download and inspect a three-month wage snapshot and its status metadata.
- [x] Download the complete monthly wage observations and period-status metadata.
- [x] Download a small CPI snapshot; commit only representative samples, not full
      generated datasets.
- [x] Download the complete monthly CPI observations and period-status metadata.

## Milestone 2: raw-to-staging

- [x] Normalize the unemployment source columns to stable snake_case names.
- [x] Preserve the original unemployment period key with the clean date.
- [x] Parse monthly CBS unemployment period keys and apply the 2015 cutoff.
- [x] Parse monthly and quarterly periods while retaining vacancy status metadata.
- [ ] Add annual-period support only if a later source requires it.
- [x] Load the clean unemployment staging table into DuckDB.
- [x] Load the clean vacancy staging table into DuckDB.
- [x] Normalize the wage source, preserve expected 2020 growth nulls, and retain
      source status metadata.
- [x] Load the clean wage staging table into DuckDB.
- [x] Normalize the CPI source, apply the January 2020 cutoff, and retain source
      status metadata.
- [x] Load the clean CPI staging table into DuckDB.
- [x] Add database checks for duplicate unemployment periods, missing months,
      numeric ranges, and source identifiers.
- [x] Add equivalent value, continuity, and provenance checks for vacancies.
- [x] Add equivalent value, continuity, status, null, and provenance checks for
      wages.
- [x] Add value, continuity, status, null, and provenance checks for CPI.

## Milestone 3: analytical product

- [x] Model `fct_wages_prices` and an annual wage-price summary in dbt.
- [x] Model `fct_labour_market_periodic`, `fct_vacancies`, and a small date
      dimension.
- [x] Calculate real wage growth only for aligned frequencies and periods.
- [x] Create tested headline KPI, monthly trend, quarterly tightness, and calendar
      exports for Power BI.
- [x] Specify the Power BI overview and definitions/data-quality page layouts.
- [x] Package the Power BI theme, DAX measures, build sequence, and visual
      validation targets.
- [x] Build the Power BI overview and definitions/data-quality pages.
- [x] Write three findings, three limitations, and one recommended next question.

## Milestone 4: release

- [x] Save donut interaction exclusions for both quarterly visuals.
- [ ] Complete final visual acceptance checks in `docs/release_checklist.md`.
- [x] Review and confirm the public GitHub destination before publishing.
- [x] Add screenshots of both report pages to the README.
- [ ] Record a two-minute walkthrough.
- [ ] Write the two-page labour-market briefing.
- [ ] Run the full rebuild and test suite from a clean environment.
- [ ] Tag v0.1 and add the project to the main GitHub profile README.

## Post-MVP ideas

- Sector breakdowns.
- Provincial or labour-market-region comparisons.
- Eurostat comparison with selected EU countries.
- Scheduled refresh and cloud warehouse deployment.
