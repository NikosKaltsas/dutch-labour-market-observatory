with wages as (
    select
        period,
        source_period as wage_source_period,
        hourly_cao_wage_index_2020,
        hourly_cao_wage_yoy_pct,
        status as wage_status,
        is_provisional as wage_is_provisional,
        retrieved_at_utc as wage_retrieved_at_utc
    from {{ source('staging', 'wages_monthly') }}
    where hourly_cao_wage_yoy_pct is not null
),

prices as (
    select
        period,
        source_period as cpi_source_period,
        cpi_index_2025,
        cpi_inflation_yoy_pct,
        status as cpi_status,
        is_provisional as cpi_is_provisional,
        retrieved_at_utc as cpi_retrieved_at_utc
    from {{ source('staging', 'cpi_monthly') }}
)

select
    wages.period,
    wages.wage_source_period,
    prices.cpi_source_period,
    wages.hourly_cao_wage_index_2020,
    wages.hourly_cao_wage_yoy_pct,
    prices.cpi_index_2025,
    prices.cpi_inflation_yoy_pct,
    round(
        (
            (1 + wages.hourly_cao_wage_yoy_pct / 100.0)
            / (1 + prices.cpi_inflation_yoy_pct / 100.0)
            - 1
        ) * 100,
        4
    ) as real_wage_growth_pct,
    round(
        wages.hourly_cao_wage_yoy_pct - prices.cpi_inflation_yoy_pct,
        4
    ) as nominal_minus_inflation_pp,
    wages.wage_status,
    prices.cpi_status,
    wages.wage_is_provisional or prices.cpi_is_provisional as is_provisional,
    wages.wage_retrieved_at_utc,
    prices.cpi_retrieved_at_utc
from wages
inner join prices using (period)
order by wages.period
