with expected as (
    select wages.period
    from {{ source('staging', 'wages_monthly') }} as wages
    inner join {{ source('staging', 'cpi_monthly') }} as prices using (period)
    where wages.hourly_cao_wage_yoy_pct is not null
),

actual as (
    select period
    from {{ ref('fct_wages_prices') }}
)

select coalesce(expected.period, actual.period) as period
from expected
full outer join actual using (period)
where expected.period is null or actual.period is null
