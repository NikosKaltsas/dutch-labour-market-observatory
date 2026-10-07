with bounds as (
    select
        (select min(period) from {{ source('staging', 'unemployment_monthly') }})
            as first_month,
        greatest(
            (select max(period) from {{ source('staging', 'unemployment_monthly') }}),
            (select max(period) from {{ source('staging', 'wages_monthly') }}),
            (select max(period) from {{ source('staging', 'cpi_monthly') }}),
            (
                select date_trunc('month', max(quarter_end))::date
                from {{ source('staging', 'vacancies_quarterly') }}
            )
        ) as last_month
),

months as (
    select generated_month::date as month_start
    from bounds,
         generate_series(
             first_month,
             last_month,
             interval 1 month
         ) as calendar(generated_month)
)

select
    month_start,
    year(month_start) as calendar_year,
    month(month_start) as month_number,
    strftime(month_start, '%B') as month_name,
    quarter(month_start) as calendar_quarter,
    strftime(month_start, '%Y-%m') as year_month,
    month(month_start) in (3, 6, 9, 12) as is_quarter_end_month,
    last_day(
        make_date(year(month_start), quarter(month_start) * 3, 1)
    ) as quarter_end
from months
order by month_start
