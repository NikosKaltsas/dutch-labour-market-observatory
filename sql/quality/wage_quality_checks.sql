WITH duplicate_periods AS (
    SELECT coalesce(sum(duplicate_count - 1), 0)::BIGINT AS failed_rows
    FROM (
        SELECT count(*) AS duplicate_count
        FROM staging.wages_monthly
        GROUP BY period
        HAVING count(*) > 1
    )
),
invalid_values AS (
    SELECT count(*)::BIGINT AS failed_rows
    FROM staging.wages_monthly
    WHERE hourly_cao_wage_index_2020 <= 0
       OR hourly_cao_wage_yoy_pct <= -100
       OR hourly_cao_wage_yoy_pct > 100
),
unexpected_null_growth AS (
    SELECT count(*)::BIGINT AS failed_rows
    FROM staging.wages_monthly
    WHERE hourly_cao_wage_yoy_pct IS NULL
      AND year(period) <> 2020
),
invalid_status AS (
    SELECT count(*)::BIGINT AS failed_rows
    FROM staging.wages_monthly
    WHERE status NOT IN ('final', 'provisional')
       OR is_provisional <> (status = 'provisional')
),
unexpected_source_ids AS (
    SELECT count(*)::BIGINT AS failed_rows
    FROM staging.wages_monthly
    WHERE source_table_id <> '85663ENG'
),
invalid_month_starts AS (
    SELECT count(*)::BIGINT AS failed_rows
    FROM staging.wages_monthly
    WHERE day(period) <> 1
),
date_bounds AS (
    SELECT min(period) AS first_period, max(period) AS last_period
    FROM staging.wages_monthly
),
expected_months AS (
    SELECT generated_period::DATE AS period
    FROM date_bounds,
         generate_series(
             first_period,
             last_period,
             INTERVAL 1 MONTH
         ) AS expected(generated_period)
),
missing_months AS (
    SELECT count(*)::BIGINT AS failed_rows
    FROM expected_months
    LEFT JOIN staging.wages_monthly USING (period)
    WHERE staging.wages_monthly.period IS NULL
)
SELECT 'duplicate_periods' AS check_name, failed_rows FROM duplicate_periods
UNION ALL
SELECT 'invalid_month_starts', failed_rows FROM invalid_month_starts
UNION ALL
SELECT 'invalid_status', failed_rows FROM invalid_status
UNION ALL
SELECT 'invalid_values', failed_rows FROM invalid_values
UNION ALL
SELECT 'missing_months', failed_rows FROM missing_months
UNION ALL
SELECT 'unexpected_null_growth', failed_rows FROM unexpected_null_growth
UNION ALL
SELECT 'unexpected_source_ids', failed_rows FROM unexpected_source_ids
ORDER BY check_name;
