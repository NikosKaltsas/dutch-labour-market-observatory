WITH duplicate_quarters AS (
    SELECT coalesce(sum(duplicate_count - 1), 0)::BIGINT AS failed_rows
    FROM (
        SELECT count(*) AS duplicate_count
        FROM staging.vacancies_quarterly
        GROUP BY quarter_end
        HAVING count(*) > 1
    )
),
invalid_values AS (
    SELECT count(*)::BIGINT AS failed_rows
    FROM staging.vacancies_quarterly
    WHERE unfilled_vacancies_thousands < 0
),
invalid_status AS (
    SELECT count(*)::BIGINT AS failed_rows
    FROM staging.vacancies_quarterly
    WHERE status NOT IN ('final', 'provisional')
       OR is_provisional <> (status = 'provisional')
),
unexpected_source_ids AS (
    SELECT count(*)::BIGINT AS failed_rows
    FROM staging.vacancies_quarterly
    WHERE source_table_id <> '84545ENG'
),
invalid_quarter_ends AS (
    SELECT count(*)::BIGINT AS failed_rows
    FROM staging.vacancies_quarterly
    WHERE month(quarter_end) NOT IN (3, 6, 9, 12)
       OR quarter_end <> last_day(quarter_end)
),
quarter_counts AS (
    SELECT
        date_diff('quarter', min(quarter_end), max(quarter_end)) + 1
            AS expected_quarters,
        count(DISTINCT quarter_end) AS actual_quarters
    FROM staging.vacancies_quarterly
),
missing_quarters AS (
    SELECT greatest(expected_quarters - actual_quarters, 0)::BIGINT AS failed_rows
    FROM quarter_counts
)
SELECT 'duplicate_quarters' AS check_name, failed_rows FROM duplicate_quarters
UNION ALL
SELECT 'invalid_quarter_ends', failed_rows FROM invalid_quarter_ends
UNION ALL
SELECT 'invalid_status', failed_rows FROM invalid_status
UNION ALL
SELECT 'invalid_values', failed_rows FROM invalid_values
UNION ALL
SELECT 'missing_quarters', failed_rows FROM missing_quarters
UNION ALL
SELECT 'unexpected_source_ids', failed_rows FROM unexpected_source_ids
ORDER BY check_name;
