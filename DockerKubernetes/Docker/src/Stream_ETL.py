#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pyspark
from pyspark.sql import SparkSession
import delta

# spark.driver.memory is used to configure the HEAP Memory
builder = SparkSession.builder.appName("Stream_ETL") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")\
    .config("spark.driver.memory", "8g")

spark = delta.configure_spark_with_delta_pip(builder).getOrCreate()


# In[2]:


Interests = {"Companies": ["AMZN", "NVDA", "GOOG", "BA", "`BAYN.DE`"], # BAYN.DE casues issues in streaming, as it is read as two seperate strings
            "Currencies": ["EURUSD=X", "GBPEUR=X", "EURHUF=X", "BTC-USD", "ETH-USD"],
            "Commodities": ["GC=F", "HG=F", "SI=F", "CL=F", "NG=F"]}

Stock_Aliases = Interests["Companies"] + Interests["Currencies"] + Interests["Commodities"]


# In[3]:


from pyspark.sql.types import StructType, StructField, StringType
from pyspark.sql.functions import col, lit, regexp_replace, when, length, to_date, to_number
import datetime

InSchema = StructType([
    StructField("date", StringType()),
    StructField("alias", StringType()),
    StructField("Category", StringType()),
    StructField("Open", StringType()),
    StructField("Close", StringType()),
    StructField("High", StringType()),
    StructField("Low", StringType()),
    StructField("Volume", StringType())
])

# Read in the data
Stream = spark.readStream\
    .format("json")\
    .option("multiline", True)\
    .option("maxFilesPerTrigger", 16)\
    .load("/app/StreamData/ScrapeSource", schema = InSchema)
    

# 0. Make the Column Names correct and reorder the columns so that the schema fill fit the output delta table
Stream = Stream.withColumnRenamed("date", "Date").withColumnRenamed("alias", "Stock_Alias")\
    .select(col("Date"), col("Category"), col("Stock_Alias"), col("Open"), col("Close"), col("High"), col("Low"), col("Volume"))

# 1. Make all Date-Strings equal format. Then convert the Date-STrings to Date-Format
# If Stringlength == 10: Date has MM/dd/yyyy format
# If Stringlength == 8: Date has M/d/yyyy format
# If Stringlength == 9, remove everything after the Month number. 
# If length of Month == 1, format is M/dd/yyyy. Else Format is MM/d/yyyy
Stream = Stream.withColumn("Date", when(length(col("Date")) == 10, to_date(col("Date"), "MM/dd/yyyy"))\
    .when(length(col("Date")) == 8, to_date(col("Date"), "M/d/yyyy"))\
    .when((length(col("Date")) == 9) & (length(regexp_replace(col("Date"), "/.*", "")) == 1), to_date(col("Date"), "M/dd/yyyy"))\
    .otherwise(to_date(col("Date"), "MM/d/yyyy")))

# 2. "Volume" to IntegerFormat, remove the ","
# REmoving the "," leads to malformed strings. instread, try to_number.

Stream = Stream.withColumn("Volume", when((col("Volume") == "n/a") | (col("Volume") == ""), lit(None))\
    .otherwise(to_number(col("Volume"), lit("990,990,990,990,990"))))

# 3. "Open", "Close", "High", "Low", transform n/a into NULL. REmove the ",". Transform the Strings into Floats.


for column_name in ["Open", "Close", "High", "Low"]:
    Stream = Stream.withColumn(column_name, when((col(column_name) == "n/a") | (col(column_name) == ""), lit(None))\
        .otherwise(to_number(col(column_name), lit("990,990,990,990,990.9999"))))\
        .withColumn(column_name, pyspark.sql.functions.round(col(column_name), lit(2)))

# 4. Add new Column: Time that the data went through the pipelie
Stream = Stream.withColumn("Processed", lit(datetime.datetime.now()))

import time
def stop_stream_query(query, wait_time):
    """Stop a running streaming query"""
    while query.isActive:
        msg = query.status['message']
        data_avail = query.status['isDataAvailable']
        trigger_active = query.status['isTriggerActive']
        if not data_avail and not trigger_active and \
          msg not in ("Initializing sources", "Initializing StreamExecution"):
            print('Stopping query...')
            query.stop()
        time.sleep(0.5)

    # Okay wait for the stop to happen
    print('Awaiting termination...')
    query.awaitTermination(wait_time)

# def myfunc(Stream, batch_id):
#     # 5. Add new Column: Running Sum of Volume
#     # Teh Sum funciotn only consider values form the current partition for the sum, utilizing the current row and all rows that come before that. This way, we get a cumulative sum for each Stock market
#     running_sum_window = pyspark.sql.Window.partitionBy("Stock_Alias").orderBy("Date").rowsBetween(pyspark.sql.Window.unboundedPreceding, pyspark.sql.Window.currentRow)
#     Stream = Stream.withColumn("Running_Volume", pyspark.sql.functions.sum(col("Volume")).over(running_sum_window))

#     Stream.write.format("delta").option("path", "/app/StreamData/Target/Entries").mode("append").save()



q = Stream.writeStream\
    .format("delta").option("path", "/app/StreamData/Target/Entries").outputMode("append")\
    .trigger(processingTime = "30 seconds")\
    .option("checkpointLocation", "/app/StreamData/DeltaCheckpoint")\
    .option('cleanSource', 'archive') \
    .option('sourceArchiveDir', "/app/StreamData/DeltaArchive") \
    .start()

q.awaitTermination()
# stop_stream_query(q, 20000)





