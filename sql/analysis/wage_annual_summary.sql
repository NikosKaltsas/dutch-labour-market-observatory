SELECT
    year(period) AS calendar_year,
    count(*) AS months_observed,
    round(avg(hourly_cao_wage_index_2020), 1) AS avg_wage_index_2020,
    round(avg(hourly_cao_wage_yoy_pct), 2) AS avg_wage_growth_yoy_pct,
    count(*) FILTER (WHERE hourly_cao_wage_yoy_pct IS NULL)
        AS months_missing_yoy_growth,
    bool_or(is_provisional) AS includes_provisional_data
FROM staging.wages_monthly
GROUP BY calendar_year
ORDER BY calendar_year;
