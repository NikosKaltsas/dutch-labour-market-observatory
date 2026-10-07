with counts as (
    select
        date_diff('month', min(month_start), max(month_start)) + 1
            as expected_months,
        count(*) as actual_months
    from {{ ref('dim_month') }}
)

select *
from counts
where expected_months <> actual_months
