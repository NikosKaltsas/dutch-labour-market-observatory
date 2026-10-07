SELECT
    year(quarter_end) AS calendar_year,
    count(*) AS quarters_observed,
    round(avg(unfilled_vacancies_thousands), 1)
        AS avg_unfilled_vacancies_thousands,
    min(unfilled_vacancies_thousands) AS min_unfilled_vacancies_thousands,
    max(unfilled_vacancies_thousands) AS max_unfilled_vacancies_thousands,
    bool_or(is_provisional) AS includes_provisional_data
FROM staging.vacancies_quarterly
GROUP BY calendar_year
ORDER BY calendar_year;
