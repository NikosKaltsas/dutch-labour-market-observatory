SELECT
    year(period) AS calendar_year,
    count(*) AS months_observed,
    round(avg(unemployed_thousands), 1) AS avg_unemployed_thousands,
    round(avg(unemployment_rate_pct), 2) AS avg_unemployment_rate_pct,
    min(unemployment_rate_pct) AS min_unemployment_rate_pct,
    max(unemployment_rate_pct) AS max_unemployment_rate_pct
FROM staging.unemployment_monthly
GROUP BY calendar_year
ORDER BY calendar_year;
