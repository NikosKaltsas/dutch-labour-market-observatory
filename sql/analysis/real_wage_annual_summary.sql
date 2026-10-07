SELECT
    calendar_year,
    months_observed,
    avg_nominal_wage_growth_pct,
    avg_inflation_yoy_pct,
    avg_real_wage_growth_pct,
    months_with_positive_real_wage_growth,
    includes_provisional_data
FROM analytics.agg_wages_prices_annual
ORDER BY calendar_year;
