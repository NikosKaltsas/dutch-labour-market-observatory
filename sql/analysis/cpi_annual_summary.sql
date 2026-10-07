SELECT
    year(period) AS calendar_year,
    count(*) AS months_observed,
    round(avg(cpi_index_2025), 2) AS avg_cpi_index_2025,
    round(avg(cpi_inflation_yoy_pct), 2) AS avg_inflation_yoy_pct,
    round(min(cpi_inflation_yoy_pct), 2) AS min_inflation_yoy_pct,
    round(max(cpi_inflation_yoy_pct), 2) AS max_inflation_yoy_pct,
    bool_or(is_provisional) AS includes_provisional_data
FROM staging.cpi_monthly
GROUP BY calendar_year
ORDER BY calendar_year;
