# Decision Log

## ADR-001: ship a national MVP before regional expansion

**Status:** accepted

**Decision:** The first release uses Netherlands-total indicators from 2015 onward.
Sector and regional detail are deferred.

**Why:** National time series are sufficient to demonstrate ingestion, modelling,
testing, visualization, and economic communication. Mixing several geographic and
sector classifications in the first milestone would delay a complete product.

## ADR-002: keep CBS raw responses immutable

**Status:** accepted

**Decision:** Each ingestion writes a timestamped or explicitly named JSON snapshot
that includes retrieval metadata. Transformations never overwrite source files.

**Why:** CBS tables can be revised or redesigned. Raw snapshots make later changes
auditable and support reproducible debugging.

## ADR-003: exact real-growth formula

**Status:** accepted

**Decision:** Calculate real wage growth from the ratio of nominal and price growth
factors. The dashboard may also explain the intuitive nominal-minus-inflation
approximation.

**Why:** The ratio is mathematically exact for growth rates and is still easy to
communicate.

## ADR-004: preserve full monthly history in raw storage

**Status:** accepted

**Decision:** Keep all available monthly unemployment observations in the raw
snapshot. Apply the January 2015 portfolio cutoff in the staging layer.

**Why:** The CBS API applied the monthly-period predicate but did not apply a range
comparison to the coded `Periods` dimension. Keeping the complete response is
simple, auditable, and faithful to the source. The smaller analysis window belongs
in a tested transformation rather than an unreliable extraction predicate.

## ADR-005: retain source keys beside clean staging fields

**Status:** accepted

**Decision:** Convert the CBS period key to an ISO date for analysis, but retain the
original `source_period` in the staging output. Carry the table ID and raw retrieval
timestamp into every row.

**Why:** Clean names make analysis understandable, while source identifiers make
every value traceable back to the exact extraction. The raw snapshot remains
unchanged.

## ADR-006: use a transactional full refresh for the first staging table

**Status:** accepted

**Decision:** Load the unemployment CSV into an explicitly typed DuckDB table inside
a transaction. Each successful run replaces all rows in the staging table.

**Why:** The dataset is small, so a full refresh is simpler and safer than premature
incremental logic. The transaction prevents a failed load from leaving a partially
updated table, while primary and check constraints enforce the core contract.

## ADR-007: make warehouse quality checks executable

**Status:** accepted

**Decision:** Store data-quality rules in SQL and expose them through a command that
returns exit code `1` when any rule reports failures.

**Why:** The SQL is directly reviewable by analysts and can later run unchanged in
continuous integration. Reporting failure counts makes problems diagnosable, while
the non-zero exit code prevents a failing dataset from silently continuing through
the pipeline.

## ADR-008: use national quarterly vacancy flows before sector detail

**Status:** accepted

**Decision:** Use CBS table `84545ENG` and its seasonally adjusted unfilled-vacancy
measure for the MVP. Keep it at quarterly frequency and retain the CBS period
status from the separate `Periods` metadata resource.

**Why:** The project first needs a defensible national tightness indicator. This
table supplies the relevant vacancy stock without introducing sector aggregation
issues. Monthly unemployment and quarterly vacancies will remain separate until an
explicit frequency-alignment rule is chosen.

## ADR-009: represent vacancy observations by quarter-end

**Status:** accepted

**Decision:** Convert CBS quarterly keys to the final calendar date of each quarter.
Retain both the original Dutch status and a normalized English status with a Boolean
provisional flag.

**Why:** Unfilled vacancies are measured as a stock at quarter-end, so a quarter-end
date is more truthful than an arbitrary quarter-start date. Keeping both status
representations supports English analysis without losing source fidelity.

## ADR-010: use current hourly CAO wages including special payments

**Status:** accepted

**Decision:** Use the index and published year-on-year change for hourly CAO wages
including special payments from CBS table `85663ENG`. Select current figures for the
total CAO sector and all economic activities. Begin the monthly wage series in 2020.

**Why:** The measure accounts for contractual working-time changes and includes
binding special payments. Current figures provide the best available estimate, and
source status makes revisions visible. Avoiding a splice to the discontinued
2010-base series keeps the MVP method transparent and reproducible.

## ADR-011: preserve valid baseline-year wage-growth nulls

**Status:** accepted

**Decision:** Keep the CBS-published year-on-year wage field null for January
through December 2020. Require a non-null growth value for every later month. Keep
the source index values for 2020 rather than calculating an unsupported comparison.

**Why:** The selected 2020-base table begins in 2020 and therefore has no 2019
observations from which it could publish a prior-year change. Treating these twelve
nulls as expected preserves source fidelity, while a targeted SQL check prevents
later missing values from being accepted silently.

## ADR-012: use the current national all-items CPI series

**Status:** accepted

**Decision:** Use the all-items CPI and its CBS-published annual rate of change from
table `86141ENG`, based on 2025=100. Keep the full available history in raw storage
and apply a January 2020 cutoff in staging to align prices with wages.

**Why:** The national CPI directly represents household consumer prices in the
Netherlands and is the appropriate deflator for the MVP's domestic purchasing-power
question. The current table already provides rebased history, so no manual splice
to the discontinued 2015-base table is needed. The twelve-month-average CPI would
over-smooth monthly inflation, while HICP is more appropriate for international
comparison.

## ADR-013: align wage and CPI months before calculating real growth

**Status:** accepted

**Decision:** Inner join the monthly wage and CPI staging tables on their exact
observation date and exclude months without a CBS-published wage-growth rate.
Calculate exact real wage growth as
`((1 + nominal/100) / (1 + inflation/100) - 1) * 100`. Retain nominal minus
inflation only as an explicitly labelled approximation.

**Why:** Both selected rates are year-on-year monthly measures, so exact date
alignment is defensible. Excluding the 2020 wage baseline avoids inventing missing
growth and makes January 2021 the first analytical observation. Keeping the exact
and approximate results together makes the distinction visible and testable.

## ADR-014: use final-month unemployment for quarterly tightness

**Status:** accepted

**Decision:** Calculate vacancies per 100 unemployed by pairing each quarter-end
vacancy observation with the seasonally adjusted unemployment observation from the
quarter's final month. Name the metric a tightness indicator and do not present it
as the official vacancy rate.

**Why:** The vacancy source is an end-of-quarter stock, making final-month
unemployment the clearest available temporal match. Both measures are expressed in
thousands, so their units cancel in the ratio. The populations are not identical,
and the project does not yet contain occupied jobs, so calling this a vacancy rate
would overstate what the calculation represents.

## ADR-015: preserve separate reporting dates on headline cards

**Status:** accepted

**Decision:** Build the headline KPI dataset with separate unemployment, vacancy,
and wage-price reporting dates. Do not assign a single shared date to the latest
values. Keep the one-row KPI table disconnected from historical date filters.

**Why:** Monthly unemployment, quarterly vacancies, wages, and CPI are published on
different schedules. A shared “latest period” label would imply temporal alignment
that does not exist. Explicit card subtitles make freshness visible, while the
historical datasets remain filterable through the shared calendar.

## ADR-016: keep report logic reproducible outside the PBIX binary

**Status:** accepted

**Decision:** Version the Power BI theme, DAX measures, model relationships, page
copy, and acceptance checks as text files. Treat the `.pbix` as a generated desktop
artifact built from the four tested CSV exports.

**Why:** A binary report alone is difficult to review in Git and can hide metric or
formatting changes. Keeping the implementation contract in text makes the report
auditable, lets another analyst reproduce it, and separates tested data logic from
manual visual layout work.
