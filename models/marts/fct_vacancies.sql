with aligned as (
    select
        vacancies.quarter_end,
        year(vacancies.quarter_end) as calendar_year,
        quarter(vacancies.quarter_end) as calendar_quarter,
        vacancies.source_period as vacancy_source_period,
        vacancies.unfilled_vacancies_thousands,
        unemployment.period as unemployment_period,
        unemployment.source_period as unemployment_source_period,
        unemployment.unemployed_thousands,
        unemployment.unemployment_rate_pct,
        round(
            vacancies.unfilled_vacancies_thousands
            / unemployment.unemployed_thousands * 100,
            2
        ) as vacancies_per_100_unemployed,
        vacancies.status,
        vacancies.source_status,
        vacancies.is_provisional,
        vacancies.retrieved_at_utc as vacancy_retrieved_at_utc,
        unemployment.retrieved_at_utc as unemployment_retrieved_at_utc
    from {{ source('staging', 'vacancies_quarterly') }} as vacancies
    left join {{ source('staging', 'unemployment_monthly') }} as unemployment
        on unemployment.period
            = date_trunc('month', vacancies.quarter_end)::date
),

with_previous as (
    select
        *,
        lag(unfilled_vacancies_thousands) over (order by quarter_end)
            as previous_quarter_vacancies,
        lag(vacancies_per_100_unemployed) over (order by quarter_end)
            as previous_quarter_tightness
    from aligned
)

select
    * exclude (previous_quarter_vacancies, previous_quarter_tightness),
    round(
        (
            unfilled_vacancies_thousands / previous_quarter_vacancies - 1
        ) * 100,
        2
    ) as vacancy_growth_qoq_pct,
    round(
        vacancies_per_100_unemployed - previous_quarter_tightness,
        2
    ) as tightness_change_qoq,
    case
        when previous_quarter_tightness is null then 'not_available'
        when vacancies_per_100_unemployed > previous_quarter_tightness
            then 'tighter'
        when vacancies_per_100_unemployed < previous_quarter_tightness
            then 'looser'
        else 'unchanged'
    end as tightness_direction_qoq
from with_previous
order by quarter_end
