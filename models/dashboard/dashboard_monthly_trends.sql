select
    calendar.month_start as period,
    calendar.calendar_year,
    calendar.month_number,
    calendar.calendar_quarter,
    calendar.year_month,
    unemployment.unemployed_thousands,
    unemployment.unemployment_rate_pct,
    wages.hourly_cao_wage_yoy_pct,
    prices.cpi_inflation_yoy_pct,
    real_wages.real_wage_growth_pct,
    unemployment.period is not null as has_unemployment,
    wages.hourly_cao_wage_yoy_pct is not null as has_wage_growth,
    prices.cpi_inflation_yoy_pct is not null as has_inflation,
    real_wages.real_wage_growth_pct is not null as has_real_wage_growth,
    coalesce(wages.is_provisional, false)
        or coalesce(prices.is_provisional, false) as is_provisional
from {{ ref('dim_month') }} as calendar
left join {{ source('staging', 'unemployment_monthly') }} as unemployment
    on calendar.month_start = unemployment.period
left join {{ source('staging', 'wages_monthly') }} as wages
    on calendar.month_start = wages.period
left join {{ source('staging', 'cpi_monthly') }} as prices
    on calendar.month_start = prices.period
left join {{ ref('fct_wages_prices') }} as real_wages
    on calendar.month_start = real_wages.period
order by calendar.month_start
