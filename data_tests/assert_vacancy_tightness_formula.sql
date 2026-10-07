select quarter_end
from {{ ref('fct_vacancies') }}
where abs(
    vacancies_per_100_unemployed
    - unfilled_vacancies_thousands / unemployed_thousands * 100
) > 0.01
