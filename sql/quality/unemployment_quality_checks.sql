WITH duplicate_periods AS (
    SELECT coalesce(sum(duplicate_count - 1), 0)::BIGINT AS failed_rows
    FROM (
        SELECT count(*) AS duplicate_count
        FROM staging.unemployment_monthly
        GROUP BY period
        HAVING count(*) > 1
    )
),
invalid_values AS (
    SELECT count(*)::BIGINT AS failed_rows
    FROM staging.unemployment_monthly
    WHERE unemployed_thousands < 0
       OR unemployment_rate_pct NOT BETWEEN 0 AND 100
),
unexpected_source_ids AS (
    SELECT count(*)::BIGINT AS failed_rows
    FROM staging.unemployment_monthly
    WHERE source_table_id <> '80590ENG'
),
date_bounds AS (
    SELECT min(period) AS first_period, max(period) AS last_period
    FROM staging.unemployment_monthly
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
    LEFT JOIN staging.unemployment_monthly USING (period)
    WHERE staging.unemployment_monthly.period IS NULL
)
SELECT 'duplicate_periods' AS check_name, failed_rows FROM duplicate_periods
UNION ALL
SELECT 'invalid_values', failed_rows FROM invalid_values
UNION ALL
SELECT 'unexpected_source_ids', failed_rows FROM unexpected_source_ids
UNION ALL
SELECT 'missing_months', failed_rows FROM missing_months
ORDER BY check_name;
