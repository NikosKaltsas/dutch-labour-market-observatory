# Metric Definitions

This is the analytical contract for the MVP. Source-specific field names and table
IDs are added only after the source audit confirms the current active CBS tables.

| Metric | Definition | Frequency | Important limitation |
|---|---|---|---|
| Unemployment rate | Unemployed labour force as a share of the labour force, using the CBS-published measure | Monthly | Population definition and seasonal adjustment must be displayed |
| Unemployed people | CBS-published count of unemployed people | Monthly | Do not mix raw and seasonally adjusted counts |
| Open vacancies | Unfilled jobs available at the end of the reporting period | Quarterly initially | Stock measure; not the same as newly created vacancies |
| Vacancy rate | `vacancies / (occupied jobs + vacancies) * 100` | Quarterly | Calculate only when sources use compatible populations and periods |
| Vacancies per 100 unemployed | `unfilled vacancies / unemployed people * 100`, using final-month unemployment for each quarter | Quarterly | Tightness indicator, not the official vacancy rate; numerator and denominator describe different populations |
| Nominal wage growth | Year-on-year change in collective-agreement hourly wages including special payments | Monthly or quarterly | Collective-agreement wages are not identical to actual average earnings |
| CPI inflation | Year-on-year percentage change in the all-items consumer price index | Monthly | National average does not describe every household's cost experience |
| Real wage growth | `((1 + nominal/100) / (1 + inflation/100) - 1) * 100` | Monthly or quarterly | Descriptive approximation; aligns index periods but not household composition |

## Alignment rules

1. Compare observations only when their period frequency and reference period match.
2. Keep provisional/revised status from the source.
3. Prefer CBS-published rates when available; independently calculated rates must be
   labelled as calculations.
4. Preserve original source units before converting values.
5. Never forward-fill missing official observations for headline KPIs.
6. Align quarterly vacancies to unemployment in the quarter's final month and
   label the resulting ratio as a tightness indicator, not a vacancy rate.

## What the MVP does not measure

- Causal effects of labour-market policy.
- Individual wage growth or disposable household income.
- Differences within sectors or regions.
- Labour shortages by occupation.
- Informal work, job quality, or hours preferences.
