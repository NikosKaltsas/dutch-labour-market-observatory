with bounds as (
    select min(period) as first_period, max(period) as last_period
    from {{ ref('fct_wages_prices') }}
),

expected_months as (
    select generated_period::date as period
    from bounds,
         generate_series(
             first_period,
             last_period,
             interval 1 month
         ) as expected(generated_period)
)

select expected_months.period
from expected_months
left join {{ ref('fct_wages_prices') }} using (period)
where fct_wages_prices.period is null
