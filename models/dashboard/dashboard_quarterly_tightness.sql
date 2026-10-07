select
    quarter_end,
    date_trunc('month', quarter_end)::date as quarter_month_start,
    calendar_year,
    calendar_quarter,
    unfilled_vacancies_thousands,
    unemployed_thousands,
    unemployment_rate_pct,
    vacancies_per_100_unemployed,
    vacancy_growth_qoq_pct,
    tightness_change_qoq,
    tightness_direction_qoq,
    status,
    is_provisional
from {{ ref('fct_vacancies') }}
order by quarter_end
