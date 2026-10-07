"""Pure, testable calculations used by the analytical layer."""

from __future__ import annotations

from collections.abc import Sequence


def year_over_year_change(current: float, prior_year: float) -> float:
    """Return percentage change from the same period one year earlier."""

    if prior_year == 0:
        raise ValueError("prior_year must be non-zero")
    return (current / prior_year - 1) * 100


def real_wage_growth(nominal_wage_growth_pct: float, inflation_pct: float) -> float:
    """Return the exact change in real wages, in percentage points.

    This uses the ratio of gross growth factors. Subtracting inflation from nominal
    growth is a close approximation, but the ratio is more accurate.
    """

    if inflation_pct <= -100:
        raise ValueError("inflation_pct must be greater than -100")
    return ((1 + nominal_wage_growth_pct / 100) / (1 + inflation_pct / 100) - 1) * 100


def vacancy_rate(open_vacancies: float, filled_jobs: float) -> float:
    """Return vacancies as a percentage of occupied jobs plus vacancies."""

    if open_vacancies < 0 or filled_jobs < 0:
        raise ValueError("job counts must be non-negative")
    denominator = open_vacancies + filled_jobs
    if denominator == 0:
        raise ValueError("at least one job or vacancy is required")
    return open_vacancies / denominator * 100


def ensure_same_length(*series: Sequence[object]) -> None:
    """Raise when aligned source series contain different observation counts."""

    if len({len(values) for values in series}) > 1:
        raise ValueError("aligned series must contain the same number of observations")
