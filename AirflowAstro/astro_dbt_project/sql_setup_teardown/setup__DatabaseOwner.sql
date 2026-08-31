CREATE ROLE astrodbtuser WITH LOGIN PASSWORD 'dbt_password';

CREATE DATABASE airflow_pipeline OWNER astrodbtuser;
GRANT ALL PRIVILEGES ON DATABASE airflow_pipeline TO astrodbtuser;

