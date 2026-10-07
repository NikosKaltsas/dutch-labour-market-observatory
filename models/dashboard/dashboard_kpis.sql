with latest_unemployment as (
    select *
    from {{ ref('fct_labour_market_periodic') }}
    qualify row_number() over (order by period desc) = 1
),

latest_vacancies as (
    select *
    from {{ ref('fct_vacancies') }}
    qualify row_number() over (order by quarter_end desc) = 1
),

latest_wages_prices as (
    select *
    from {{ ref('fct_wages_prices') }}
    qualify row_number() over (order by period desc) = 1
)

select
    unemployment.period as unemployment_period,
    unemployment.unemployment_rate_pct,
    unemployment.unemployed_thousands,
    vacancies.quarter_end as vacancy_period,
    vacancies.unfilled_vacancies_thousands,
    vacancies.vacancies_per_100_unemployed,
    vacancies.tightness_direction_qoq,
    vacancies.status as vacancy_status,
    wages_prices.period as wage_price_period,
    wages_prices.hourly_cao_wage_yoy_pct,
    wages_prices.cpi_inflation_yoy_pct,
    wages_prices.real_wage_growth_pct,
    wages_prices.wage_status,
    wages_prices.cpi_status,
    vacancies.is_provisional as vacancy_is_provisional,
    wages_prices.is_provisional as wage_price_is_provisional
from latest_unemployment as unemployment
cross join latest_vacancies as vacancies
cross join latest_wages_prices as wages_prices
