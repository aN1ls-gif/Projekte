FROM astrocrpublic.azurecr.io/runtime:3.3-2
# scheduler already runs airflow. This allows it to also run dbt with the postgres adapter
RUN python -m venv dbt_venv && source dbt_venv/bin/activate &&  pip install --no-cache-dir dbt-core dbt-postgres && deactivate
