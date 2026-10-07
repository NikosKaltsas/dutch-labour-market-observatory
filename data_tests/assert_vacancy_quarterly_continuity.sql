with counts as (
    select
        date_diff('quarter', min(quarter_end), max(quarter_end)) + 1
            as expected_quarters,
        count(*) as actual_quarters
    from {{ ref('fct_vacancies') }}
)

select *
from counts
where expected_quarters <> actual_quarters
