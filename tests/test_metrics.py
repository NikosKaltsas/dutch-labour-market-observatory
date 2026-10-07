from __future__ import annotations

import unittest

from dutch_labour_observatory.metrics import (
    ensure_same_length,
    real_wage_growth,
    vacancy_rate,
    year_over_year_change,
)


class MetricTests(unittest.TestCase):
    def test_year_over_year_change(self) -> None:
        self.assertAlmostEqual(year_over_year_change(108, 100), 8)

    def test_real_wage_growth_uses_growth_factors(self) -> None:
        self.assertAlmostEqual(real_wage_growth(5, 3), 1.9417475728)

    def test_vacancy_rate(self) -> None:
        self.assertAlmostEqual(vacancy_rate(5, 95), 5)

    def test_negative_job_count_is_invalid(self) -> None:
        with self.assertRaises(ValueError):
            vacancy_rate(-1, 95)

    def test_aligned_series_must_have_same_length(self) -> None:
        with self.assertRaises(ValueError):
            ensure_same_length([1, 2], [1])


if __name__ == "__main__":
    unittest.main()
