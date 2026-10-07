select period
from {{ ref('fct_wages_prices') }}
where abs(
    real_wage_growth_pct
    - (
        (
            (1 + hourly_cao_wage_yoy_pct / 100.0)
            / (1 + cpi_inflation_yoy_pct / 100.0)
            - 1
        ) * 100
    )
) > 0.0001
