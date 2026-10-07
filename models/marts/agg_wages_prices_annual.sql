select
    year(period) as calendar_year,
    count(*) as months_observed,
    round(avg(hourly_cao_wage_yoy_pct), 2) as avg_nominal_wage_growth_pct,
    round(avg(cpi_inflation_yoy_pct), 2) as avg_inflation_yoy_pct,
    round(avg(real_wage_growth_pct), 2) as avg_real_wage_growth_pct,
    count(*) filter (where real_wage_growth_pct > 0)
        as months_with_positive_real_wage_growth,
    bool_or(is_provisional) as includes_provisional_data
from {{ ref('fct_wages_prices') }}
group by calendar_year
order by calendar_year
