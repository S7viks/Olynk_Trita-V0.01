-- F-GRAPH-SHELL: dbt target schemas (T-P0-020, T-P0-021)

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS quarantine;

GRANT USAGE ON SCHEMA staging TO authenticated;
GRANT USAGE ON SCHEMA gold TO authenticated;
GRANT USAGE ON SCHEMA quarantine TO authenticated;
