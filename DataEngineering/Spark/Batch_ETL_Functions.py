# -*- coding: utf-8 -*-
"""
Created on Sat Jan 31 13:33:49 2026

@author: Nils
"""

import pyspark
from pyspark.sql import SparkSession
import logging
import os
import sys
import traceback


def initialize_logger(use_Mail = True, mode = "w", print_output = False):
    """
    Initialize the Logger
    If enabled and info is provided, also allow to send emails in case of an ERROR level log.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)s : %(levelname)s:%(levelno)s  %(asctime)s    %(message)s ')

    info_handler = logging.FileHandler("Logs/Covid_Pipeline/Info.logs", mode=mode)
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    

    warning_handler = logging.FileHandler("Logs/Covid_Pipeline/Warning.logs", mode=mode)
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(formatter)
    

    error_handler = logging.FileHandler("Logs/Covid_Pipeline/Error.logs", mode=mode)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    

    
    if use_Mail and "email_logger_config.py" in os.listdir():
        from email_logger_config import email_info
        error_emailer = logging.handlers.SMTPHandler(**email_info)
        error_emailer.setLevel(logging.ERROR)
        

    if not logger.handlers: # these remain even when initalizing a new logger. This if-statement alows the new logger to be created without having double handlers/outputs
        logger.addHandler(info_handler)
        logger.addHandler(warning_handler)
        logger.addHandler(error_handler)
        if print_output:
            logger.addHandler(logging.StreamHandler(sys.stdout)) # also print the messages while logging
        if use_Mail and "email_logger_config.py" in os.listdir():
            logger.addHandler(error_emailer)
    
    return logger
    

def start_session(logger, name):
    """
    Build the Spark Session
    For the Data-Lag later on in the Transformations, all rows must be loaded, requiring a larger load of Working memory. For that, 30 GB are allocated for the driver.
    """
    spark = SparkSession.builder.config("spark.driver.memory", "30g").appName(name).getOrCreate()
    logger.info("Spark Session created")
    return spark

def extract_one_dataset(spark, input_path, logger, inferSchema):
    """
    Read in a single datafile
    """
    # PERMISSIVE measn that spark is as lenient with malformed data as possible
    df = spark.read.csv(input_path, mode = "PERMISSIVE", header = True, inferSchema = inferSchema)
    logger.info(f"Successfully read {input_path}")
    return df

def extract_all_data(spark, logger, test = False):
    """
    Read in the datafiles
    Combine them into a single dataframe
    """

    base_path = "BatchData/Test/Covid/Load_Data_Start" if test else "BatchData/Raw"
    # Read in the singular files
    confirmed_infections = extract_one_dataset(spark, f"{base_path}/cases.csv", logger, inferSchema = True)
    confirmed_deaths = extract_one_dataset(spark, f"{base_path}/deaths.csv", logger, inferSchema = True)
    confirmed_recoveries = extract_one_dataset(spark, f"{base_path}/recoveries.csv", logger, inferSchema = True)

    count_infections = confirmed_infections.count()
    count_deaths = confirmed_deaths.count()
    count_recoveries = confirmed_recoveries.count()
    Same_Length = count_infections == count_deaths and count_infections == count_recoveries
    logger.info("All data succesfully read.")
    if not Same_Length:
        logger.warning("The datasets do not have the same number of entries.")

    #### unpivot the dataframes
    confirmed_infections = confirmed_infections.unpivot(ids = "Country", values = confirmed_infections.columns[1:], variableColumnName = "Date", valueColumnName = "Cases")
    confirmed_deaths = confirmed_deaths.unpivot(ids = "Country", values = confirmed_deaths.columns[1:], variableColumnName = "Date", valueColumnName = "Deaths")
    confirmed_recoveries = confirmed_recoveries.unpivot(ids = "Country", values = confirmed_recoveries.columns[1:], variableColumnName = "Date", valueColumnName = "Recoveries")
    # Combine thet files
    combined = confirmed_infections.join(confirmed_deaths, on = ["Country", "Date"]).join(confirmed_recoveries, on = ["Country", "Date"])

    combined.printSchema()
    logger.info("Successfully combined datasets")
    print(f"Number of partitions by default {combined.rdd.getNumPartitions()}")
    # print(spark.conf.get("spark.memory.fraction"))
    return combined



def transform_country(df, logger):
    """
    Make sure that all are in uppercase letters. 
    SANITY_CHECK = True means the entry passed inspection, False means it did not pass inspection
    """
    df = df.withColumn("Country", pyspark.sql.functions.upper(pyspark.sql.functions.col("Country")))
    df = df.withColumn("SANITY_CHECK", pyspark.sql.functions.col("Country").isNotNull())
 
    logger.info("Successfully transformed column: 'Country")
    return df


def transform_date(df, logger):
    """
    Make sure all dates in the 'date' column have the format 'yyyy-mm-dd'. If not, drop.
    Afterwards, transform from string-type into date-type
    """
    # Check if the overall format is correct
    df = df.withColumn("SANITY_CHECK", pyspark.sql.functions.when(pyspark.sql.functions.col("Date").rlike("\d\d\d\-\d\d-\d\d"), True & df.SANITY_CHECK).otherwise(False)) 


    # Somewhat check that the second /d/d is for the month ( not larger than 12) and that the last /d/d is for the days (not larger than 31)
# =============================================================================
#     df = df.withColumn("Date_Split", pyspark.sql.functions.split("Date", "-"))
#     df = df.withColumn("SANITY_CHECK", pyspark.sql.functions.when((pyspark.sql.functions.col("Date_Split")[1].cast('int') >= 1) & (pyspark.sql.functions.col("Date_Split")[1].cast('int') <= 12), True & df.SANITY_CHECK)
#         .when((pyspark.sql.functions.col("Date_Split")[2].cast('int') >= 1) & (pyspark.sql.functions.col("Date_Split")[2].cast('int') <= 31), True & df.SANITY_CHECK)
#         .otherwise(False))
#     df = df.drop("Date_Split")
# =============================================================================

    # Any date that cannot be transformed becomas a NULL values
    df = df.withColumn("Date", pyspark.sql.functions.to_date(pyspark.sql.functions.col("Date"), 'yyyy-MM-dd'))
    df = df.withColumn("SANITY_CHECK", pyspark.sql.functions.col("Date").isNotNull() & pyspark.sql.functions.col("SANITY_CHECK"))
    logger.info("Date column successfully transformed from string into date format")
    return df


def transform_cases_deaths(df, logger):
    """
    Make sure that the number-strings represent integers and cast them into integers
    """

# =============================================================================
#     df = df.withColumn("SANITY_CHECK", pyspark.sql.functions.when(pyspark.sql.functions.col("Case").rlike(".*\D.*"), False).otherwise(True & df.SANITY_CHECK))
#     df = df.withColumn("SANITY_CHECK", pyspark.sql.functions.when(pyspark.sql.functions.col("Deaths").rlike(".*\D.*"), False).otherwise(True) & df.SANITY_CHECK)
#     
# =============================================================================

    df = df.withColumn("Cases", pyspark.sql.functions.col("Cases").cast("int")).withColumn("Deaths", pyspark.sql.functions.col("Deaths").cast("int")).withColumn("Recoveries", pyspark.sql.functions.col("Recoveries").cast("int"))
    
    df = df.withColumn("SANITY_CHECK", pyspark.sql.functions.col("Cases").isNotNull() & pyspark.sql.functions.col("SANITY_CHECK")).withColumn("SANITY_CHECK", pyspark.sql.functions.col("Deaths").isNotNull() & pyspark.sql.functions.col("SANITY_CHECK")).withColumn("SANITY_CHECK", pyspark.sql.functions.col("Recoveries").isNotNull() & pyspark.sql.functions.col("SANITY_CHECK"))
    logger.info("Successfully transformed Case and Deaths columns.")
    return df




################################################################################################################################################################################






def new_columns(df, logger):
    """
    After cleaning/ transforming the other columns, make new ones
    """

    # Mortality Rate
    df = df.withColumn("Mortality_Rate", pyspark.sql.functions.try_divide(pyspark.sql.functions.col("Deaths"), pyspark.sql.functions.col("Cases")))
    logger.info("Successfully added Mortality_Rate.")
    
    # Recovery Rate
    df = df.withColumn("Recovery_Rate", pyspark.sql.functions.try_divide(pyspark.sql.functions.col("Recoveries"), pyspark.sql.functions.col("Cases")))
    logger.info("Successfully added Recovery_Rate.")


    # Change in Mortaltiy and Recovery Rate
    
    window = pyspark.sql.Window.partitionBy("Country").orderBy("Date")
    df = df.withColumn("Mortality_Rate_Change", pyspark.sql.functions.lag("Mortality_Rate", offset = 1).over(window)) # .orderBy(["Admin2", "Date"], ascending = [True, True])
    df = df.withColumn("Recovery_Rate_Change", pyspark.sql.functions.lag("Recovery_Rate", offset = 1).over(window))

    ##### 2. The percentage by which the mortality and recovery rate changed depending on the previous entry. (1.23 becomes +23 %, 0.23 becomes -77%)
    df = df.withColumn("Mortality_Rate_Change", pyspark.sql.functions.try_divide(pyspark.sql.functions.col("Mortality_Rate"), pyspark.sql.functions.col("Mortality_Rate_Change")))
    df = df.withColumn("Mortality_Rate_Change", pyspark.sql.functions.when(pyspark.sql.functions.col("Mortality_Rate_Change").isNotNull(), pyspark.sql.functions.col("Mortality_Rate_Change") - pyspark.sql.functions.lit(1)))
    
    df = df.withColumn("Recovery_Rate_Change", pyspark.sql.functions.try_divide(pyspark.sql.functions.col("Recovery_Rate"), pyspark.sql.functions.col("Recovery_Rate_Change")))
    df = df.withColumn("Recovery_Rate_Change", pyspark.sql.functions.when(pyspark.sql.functions.col("Recovery_Rate_Change").isNotNull(), pyspark.sql.functions.col("Recovery_Rate_Change") - pyspark.sql.functions.lit(1)))
    
    
    df = df.orderBy(["Country", "Date"], ascending = [True, True])
    logger.info("Succesfully added Mortality_Rate_Change and Recovery_ChangeRate")
    return df


###################################################################################################################################################################

def Transform(df, logger, Caching = True):
    """
    Complete Transformation Pipeline
    Add removal of duplicates and of Null-values
    """
    logger.info("Starting transformation ...")
    if Caching:
        df.cache()

    df = transform_country(df, logger)
    df = transform_date(df, logger)
    df = transform_cases_deaths(df, logger)
    
    ### duplicates
    df = df.dropDuplicates()

    ###### new columns
    df = new_columns(df, logger)

    ## SANITY_CHECK
    entries_with_errors = df.select(pyspark.sql.functions.count_if(~df.SANITY_CHECK)).collect()[0][0]
    total_entries = df.count()
    logger.info(f"{total_entries:_} entries have been processed. Of these, {entries_with_errors} failed inspection.")
    
    ## Null values
    df = df.na.drop()

    logger.info("Successfull tranformation of data")
    df.printSchema()
    if Caching:
        df.unpersist()
    return df

def load_to_csv(df, logger, outpath):
    df.write.mode("overwrite").format("csv").option("header", True).save(outpath)
    logger.info(f"Data saved to {outpath}")
    
    
def ETL_covid(logger, Session_Name, Caching = True):
    Return = True
    try:
        spark = start_session(logger, Session_Name)
    
        df = extract_all_data(spark, logger)
        df = Transform(df, logger, Caching)
        load_to_csv(df, logger, "BatchData/Cleaned/Covid")
        
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        Return = False
        spark.stop()
    else:
        logger.info("ETL successfully finished.")
        spark.stop()
    finally:
        if Return:
            return df