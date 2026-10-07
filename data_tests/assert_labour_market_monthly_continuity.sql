with counts as (
    select
        date_diff('month', min(period), max(period)) + 1 as expected_months,
        count(*) as actual_months
    from {{ ref('fct_labour_market_periodic') }}
)

select *
from counts
where expected_months <> actual_months
