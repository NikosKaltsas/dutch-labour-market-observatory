SELECT
    calendar_year,
    count(*) AS quarters_observed,
    round(avg(unfilled_vacancies_thousands), 1)
        AS avg_unfilled_vacancies_thousands,
    round(avg(unemployment_rate_pct), 2) AS avg_unemployment_rate_pct,
    round(avg(vacancies_per_100_unemployed), 2)
        AS avg_vacancies_per_100_unemployed,
    bool_or(is_provisional) AS includes_provisional_data
FROM analytics.fct_vacancies
GROUP BY calendar_year
ORDER BY calendar_year;
