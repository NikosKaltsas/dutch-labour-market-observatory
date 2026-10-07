select
    unemployment.period,
    calendar.calendar_year,
    calendar.month_number,
    calendar.calendar_quarter,
    unemployment.source_period as unemployment_source_period,
    unemployment.unemployed_thousands,
    unemployment.unemployment_rate_pct,
    wages.source_period as wage_source_period,
    wages.hourly_cao_wage_index_2020,
    wages.hourly_cao_wage_yoy_pct,
    prices.source_period as cpi_source_period,
    prices.cpi_index_2025,
    prices.cpi_inflation_yoy_pct,
    real_wages.real_wage_growth_pct,
    coalesce(wages.is_provisional, false)
        or coalesce(prices.is_provisional, false) as is_provisional
from {{ source('staging', 'unemployment_monthly') }} as unemployment
inner join {{ ref('dim_month') }} as calendar
    on unemployment.period = calendar.month_start
left join {{ source('staging', 'wages_monthly') }} as wages using (period)
left join {{ source('staging', 'cpi_monthly') }} as prices using (period)
left join {{ ref('fct_wages_prices') }} as real_wages using (period)
order by unemployment.period
