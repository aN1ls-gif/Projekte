import os
import traceback
import requests
import logging
import datetime
import pendulum

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text

from airflow.sdk import dag, task, task_group
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator, BranchSQLOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

from cosmos import DbtTaskGroup, ProjectConfig, ProfileConfig, ExecutionConfig
from cosmos.profiles import PostgresUserPasswordProfileMapping

import task_defs



data_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
non_aqi_params = ["pm10", "pm2_5", "nitrogen_dioxide", "sulphur_dioxide", "ozone"]
aqi_params = ["european_aqi", "european_aqi_pm2_5", "european_aqi_pm10", "european_aqi_nitrogen_dioxide", "european_aqi_ozone", "european_aqi_sulphur_dioxide"]
parameters = non_aqi_params + aqi_params
data_params = {
            "latitude": 51.218931,
            "longitude": 6.471359,
            "timezone": "Europe/Berlin",
            "past_days": 0}


logger = logging.getLogger(__name__)
personal_log_handler = logging.FileHandler(filename = f"{os.environ.get('AIRFLOW__LOGGING__BASE_LOG_FOLDER')}/my_info.log", encoding = "utf-8")
personal_log_handler.setLevel(logging.DEBUG)
personal_log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(personal_log_handler)
# logger.info("Logger Setup Completed")

now = pendulum.now(tz = "Europe/Paris")
# importing the database string directly leads to an error when using airflow.
start_date = datetime.datetime(2026, 8, 25) #datetime.datetime.now() - datetime.timedelta(days = 1)
end_date = datetime.datetime(2026, 8, 31) #datetime.datetime.now() + datetime.timedelta(days = 1)



###################### Extras to allow Astronomer to handle the DBT connection and execution #################
CONNECTION_ID = "postgres_conn"
SCHEMA_NAME = "analytics"
DBT_EXECUTABLE_PATH = f"{os.environ['AIRFLOW_HOME']}/dbt_venv/bin/dbt" # this is the path inside the docker container
DBT_PROJECT_PATH = os.environ.get("DBT_HOME")


# this replaces the profile.yaml file
profile_config = ProfileConfig(
    profile_name="analyze_airquality",
    target_name="dev",
    profile_mapping=PostgresUserPasswordProfileMapping(
        conn_id = CONNECTION_ID,
        profile_args = {"schema": SCHEMA_NAME}
    )
)

execution_config = ExecutionConfig(
    dbt_executable_path=DBT_EXECUTABLE_PATH,
)




## Note: start_date/ end_date must be datetime object, not date object
@dag(
    dag_id = "AirQualityPipeline_v6.9",
    description = "An example project using airflow and dbt for data-cleaning and basic plotting",
    schedule = "@daily",
    start_date = start_date, # set the date of yesterday so that the backfill is triggered
    end_date = end_date,
    catchup = True,
    max_active_runs = 1,
    tags = ["self_written"]
    )
def AirQualityDag():
    @task_group(group_id = "handle_current_data")
    def handle_current_data():
        """
        TaskGroup to handle fetching, cleaning and saving the air quality data of the current time and date
        """
        @task(task_id = "fetch_data_current")
        def fetch_data_current(**kwargs):
            """
            Fetch the current values from the air quality api and clean them.
            """
            data_params_current = data_params.copy()
            data_params_current["current"] = parameters
            current_data_dict = task_defs.fetch_data(logger = logger, current_datetime = now, fetch_params = data_params_current, fetch_url = data_url, mode = "current", **kwargs)
            return current_data_dict


        @task(task_id = "clean_data_current")
        def clean_data_current(current_data_dict):
            """
            Remove rows containing NaNs from the current values. 
            Change the dtype of all columns to string (safest against data corruption/malformation of data)
            """
            df = task_defs.clean_data(logger = logger, data_dict = current_data_dict, mode = "current")

            pg_hook = PostgresHook(postgres_conn_id = CONNECTION_ID)

            engine = pg_hook.get_sqlalchemy_engine()#  create_engine(database_string, echo=False)
            with engine.connect() as conn:
                df.to_sql(
                    schema = "rawdata",
                    name = "current_temp",
                    con = conn,
                    if_exists = "replace",
                    index = True
                )


                # The non-key columns all contain a "ON CONFLICt REPLACE" clause to avoid operational erros from inserting duplicate time-values
                query_string = """
                                WITH temporary_data AS (
                                SELECT * FROM rawdata.current_temp
                                )
                                INSERT INTO rawdata.current (time_string, pm10, pm2_5, nitrogen_dioxide, sulphur_dioxide, ozone, european_aqi, european_aqi_pm2_5, european_aqi_pm10, european_aqi_nitrogen_dioxide, european_aqi_ozone, european_aqi_sulphur_dioxide) 
                                SELECT time_string, pm10, pm2_5, nitrogen_dioxide, sulphur_dioxide, ozone, european_aqi, european_aqi_pm2_5, european_aqi_pm10, european_aqi_nitrogen_dioxide, european_aqi_ozone, european_aqi_sulphur_dioxide FROM temporary_data
                                ON CONFLICT (time_string) DO UPDATE SET
                                pm10 = EXCLUDED.pm10,
                                pm2_5 = EXCLUDED.pm2_5,
                                nitrogen_dioxide = EXCLUDED.nitrogen_dioxide,
                                sulphur_dioxide = EXCLUDED.sulphur_dioxide,
                                ozone = EXCLUDED.ozone,
                                european_aqi = EXCLUDED.european_aqi,
                                european_aqi_pm10 = EXCLUDED.european_aqi_pm10,
                                european_aqi_pm2_5 = EXCLUDED.european_aqi_pm2_5,
                                european_aqi_nitrogen_dioxide = EXCLUDED.european_aqi_nitrogen_dioxide,
                                european_aqi_sulphur_dioxide = EXCLUDED.european_aqi_sulphur_dioxide,
                                european_aqi_ozone = EXCLUDED.european_aqi_ozone
                                ;
                                """
                conn.execute(text(query_string))
                conn.commit()

        df = fetch_data_current()
        clean_data_current(df)
        


    @task_group(group_id = "handle_hourly_pred_data")
    def handle_hourly_data():
        """
        TaskGroup to handle fetching, cleaning and saving the air quality data of the hourly prediciton
        """
        @task(task_id = "fetch_data_houly")
        def fetch_data_hourly(**kwargs):
            """
            Fetch the hourly values from the air quality api and clean them.
            """
            data_params_hourly = data_params.copy()
            data_params_hourly["hourly"] = parameters
            hourly_data_dict = task_defs.fetch_data(logger = logger, current_datetime = now, fetch_params = data_params_hourly, fetch_url = data_url, mode = "hourly", **kwargs)
            return hourly_data_dict

        

        @task(task_id = "clean_data_hourly")
        def clean_data_hourly(hourly_data_dict):
            """
            Remove rows containing NaNs from the current values. 
            Seperate the "time" column into the date and the hour.
            Change the dtype of all columns to string (safest against data corruption/malformation of data)
            """
            df = task_defs.clean_data(logger = logger, data_dict = hourly_data_dict, mode = "hourly")

            pg_hook = PostgresHook(postgres_conn_id = CONNECTION_ID)
            
            engine = pg_hook.get_sqlalchemy_engine()#  create_engine(database_string, echo=False)
            with engine.connect() as conn:
                df.to_sql(
                    schema = "rawdata",
                    name = "hourly_temp",
                    con = conn,
                    if_exists = "replace",
                    index = False
                )

                query_string = "TRUNCATE TABLE rawdata.hourly;"
                conn.execute(text(query_string))

                query_string = """
                                WITH temporary_data AS (
                                SELECT * FROM rawdata.hourly_temp
                                )
                                INSERT INTO rawdata.hourly (time_string, pm10, pm2_5, nitrogen_dioxide, sulphur_dioxide, ozone, european_aqi, european_aqi_pm2_5, european_aqi_pm10, european_aqi_nitrogen_dioxide, european_aqi_ozone, european_aqi_sulphur_dioxide) 
                                SELECT time_string, pm10, pm2_5, nitrogen_dioxide, sulphur_dioxide, ozone, european_aqi, european_aqi_pm2_5, european_aqi_pm10, european_aqi_nitrogen_dioxide, european_aqi_ozone, european_aqi_sulphur_dioxide FROM temporary_data
                                ;
                                """
                conn.execute(text(query_string))
                conn.commit()

        df = fetch_data_hourly()
        clean_data_hourly(df)



    dbt_pipeline = DbtTaskGroup(
        group_id="transform_data",
        project_config=ProjectConfig(DBT_PROJECT_PATH),
        profile_config=profile_config,
        execution_config=execution_config,
    )


    @task
    def plot_airquality(**kwargs):
        """
        Access the mart_tables from the end of the dbt pipeline
        Make Scatter+Lineplots for the values and danger levels (2 Plots in total, limit to the past 4 days)
        Create a hist/barplot of how many coutsn of each danger level there were is the timeframe. 
        """
        pg_hook = PostgresHook(postgres_conn_id = CONNECTION_ID)
        air_quality = pg_hook.get_pandas_df("""SELECT * FROM analytics.mart__air_quality;""")
        air_quality_aqi = pg_hook.get_pandas_df("""SELECT * FROM analytics.mart__air_quality_aqi;""")

        logger.debug(os.getcwd())
        # dr: DagRunProtocol = kwargs["dag_run"]
        # logical_date_time = dr.logical_date # datetime.datetime.strptime(dr.logical_date, r"%Y%m%dT%H%M&S")
        logical_date_time = kwargs["logical_date"]
        air_quality.loc[:, "time"] = [datetime.datetime.combine(d, t, logical_date_time.tzinfo) for d, t in zip(air_quality.loc[:, "date"], air_quality.loc[:, "hour"])] 
        air_quality_aqi.loc[:, "time"] = [datetime.datetime.combine(d, t, logical_date_time.tzinfo) for d, t in zip(air_quality_aqi.loc[:, "date"], air_quality_aqi.loc[:, "hour"])] 

        air_quality = air_quality.sort_values(by = ["time"])
        air_quality_aqi = air_quality_aqi.sort_values(by = ["time"])


        logger.debug("Finished Prep, start plotting")
        figsize = (14, 30)
        fig = plt.figure(figsize = figsize)
        ax = fig.add_subplot(len(aqi_params), 1, 1)
        ax.plot(air_quality_aqi.loc[:, "time"], air_quality_aqi.loc[:, "AVG_overall_aqi_class"], label = "overall european aqi")
        ax.set_title("Overall european air quality index")
        ax.set_ylabel("Index")
        logger.debug("Finsihed plot 1")

        for i in range(1, len(aqi_params)):
            ax = fig.add_subplot(len(aqi_params), 1, i+1, sharex = ax)
            lns1 = ax.plot(air_quality_aqi.loc[:, "time"], air_quality_aqi.loc[:, f"AVG_{non_aqi_params[i-1]}_aqi_class"], label = "aqi index", color = "blue")
            ax.set_title(non_aqi_params[i-1])
            ax.set_ylabel("Index")
            logger.debug(f"Finished plot {i+1}.1")

            ax2 = ax.twinx()
            lns2 = ax2.plot(air_quality.loc[:, "time"], air_quality.loc[:, f"AVG_{non_aqi_params[i-1]}"], label = "estimated concentration", color = "red")
            ax2.set_ylabel("Concentration [µg/m³]")
            logger.debug(f"Finished plot {i+1}.2")

            lns = lns1+lns2
            labs = [l.get_label() for l in lns]
            ax.legend(lns, labs, loc=0)

        fig.suptitle("Average estimates of air quality")
        plt.savefig("/usr/local/airflow/Figures/air_quality.png")
        plt.close()

        # Picutes are in the Docker container "scheduler". Retrieve them using the "cp" command


  

    
    [handle_current_data(), handle_hourly_data()] >> dbt_pipeline >> plot_airquality()


AirQualityDag()