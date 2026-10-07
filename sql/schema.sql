CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.unemployment_monthly (
    period DATE PRIMARY KEY,
    source_period VARCHAR NOT NULL UNIQUE,
    unemployed_thousands DOUBLE NOT NULL CHECK (unemployed_thousands >= 0),
    unemployment_rate_pct DOUBLE NOT NULL
        CHECK (unemployment_rate_pct BETWEEN 0 AND 100),
    source_table_id VARCHAR NOT NULL,
    retrieved_at_utc TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS staging.vacancies_quarterly (
    quarter_end DATE PRIMARY KEY,
    source_period VARCHAR NOT NULL UNIQUE,
    unfilled_vacancies_thousands DOUBLE NOT NULL
        CHECK (unfilled_vacancies_thousands >= 0),
    status VARCHAR NOT NULL CHECK (status IN ('final', 'provisional')),
    source_status VARCHAR NOT NULL,
    is_provisional BOOLEAN NOT NULL,
    source_table_id VARCHAR NOT NULL,
    retrieved_at_utc TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS staging.wages_monthly (
    period DATE PRIMARY KEY,
    source_period VARCHAR NOT NULL UNIQUE,
    hourly_cao_wage_index_2020 DOUBLE NOT NULL
        CHECK (hourly_cao_wage_index_2020 > 0),
    hourly_cao_wage_yoy_pct DOUBLE
        CHECK (hourly_cao_wage_yoy_pct > -100
               AND hourly_cao_wage_yoy_pct <= 100),
    status VARCHAR NOT NULL CHECK (status IN ('final', 'provisional')),
    source_status VARCHAR NOT NULL,
    is_provisional BOOLEAN NOT NULL,
    source_table_id VARCHAR NOT NULL,
    retrieved_at_utc TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS staging.cpi_monthly (
    period DATE PRIMARY KEY,
    source_period VARCHAR NOT NULL UNIQUE,
    cpi_index_2025 DOUBLE NOT NULL CHECK (cpi_index_2025 > 0),
    cpi_inflation_yoy_pct DOUBLE NOT NULL
        CHECK (cpi_inflation_yoy_pct > -100
               AND cpi_inflation_yoy_pct <= 100),
    status VARCHAR NOT NULL CHECK (status IN ('final', 'provisional')),
    source_status VARCHAR NOT NULL,
    is_provisional BOOLEAN NOT NULL,
    source_table_id VARCHAR NOT NULL,
    retrieved_at_utc TIMESTAMPTZ NOT NULL
);
