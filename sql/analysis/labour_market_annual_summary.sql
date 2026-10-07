SELECT
    calendar_year,
    count(*) AS months_observed,
    round(avg(unemployed_thousands), 1) AS avg_unemployed_thousands,
    round(avg(unemployment_rate_pct), 2) AS avg_unemployment_rate_pct,
    round(avg(cpi_inflation_yoy_pct), 2) AS avg_inflation_yoy_pct,
    round(avg(hourly_cao_wage_yoy_pct), 2) AS avg_nominal_wage_growth_pct,
    round(avg(real_wage_growth_pct), 2) AS avg_real_wage_growth_pct,
    bool_or(is_provisional) AS includes_provisional_data
FROM analytics.fct_labour_market_periodic
GROUP BY calendar_year
ORDER BY calendar_year;
