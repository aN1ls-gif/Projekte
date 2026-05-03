#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pyspark
from pyspark.sql import SparkSession
import delta
import time

# spark.driver.memory is used to configure the HEAP Memory
builder = SparkSession.builder.appName("Stream_ETL") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")\
    .config("spark.driver.memory", "8g")\
    .master("local")

spark = delta.configure_spark_with_delta_pip(builder).getOrCreate()


# In[2]:


Interests = {"Companies": ["AMZN", "NVDA", "GOOG", "BA", "`BAYN.DE`"], # BAYN.DE casues issues in streaming, as it is read as two seperate strings
            "Currencies": ["EURUSD=X", "GBPEUR=X", "EURHUF=X", "BTC-USD", "ETH-USD"],
            "Commodities": ["GC=F", "HG=F", "SI=F", "CL=F", "NG=F"]}

Stock_Aliases = Interests["Companies"] + Interests["Currencies"] + Interests["Commodities"]


# In[3]:


from pyspark.sql.types import StructType, StructField, StringType, MapType, IntegerType, FloatType, ArrayType
from pyspark.sql.functions import col, lit, regexp_replace, when, length, concat, to_date, explode_outer, from_json, split, to_number
import datetime

InSchema = StructType([
    StructField("Date", StringType()),
    StructField("Entries", ArrayType(MapType(StringType(), StringType()))),
])

# Read in the data
Stream = spark.readStream\
    .format("json")\
    .option("multiline", True)\
    .option("maxFilesPerTrigger", 16)\
    .option("cleanSource", "archive")\
    .option("sourceArchiveDir", "StreamData/Archive")\
    .load("StreamData/Source", schema = InSchema)
# Explode the List in "Entries" and seperate the outer layer of teh nested dict
Stream = Stream.select("Date", explode_outer("Entries"))
Stream = Stream.select("Date", "col.Category", "col.Stock_Alias", "col.Data")
# Turn the String in the new "Data" column back into the innter layer of the nested dict
Stream = Stream.withColumn("Data", from_json(col("Data"), MapType(StringType(), StringType())))
Stream = Stream.select("*", "Data.Open", "Data.Close", "Data.High", "Data.Low", "Data.Volume")
Stream = Stream.drop("Data")

# 1. Make all DAte-Strings equal format. Then convert the Date-STrings to Date-Format
Stream = Stream.withColumn("Date", when(length(col("Date")) == 10, to_date(col("Date"), "MM/dd/yyyy"))\
    .when(length(col("Date")) == 8, to_date(col("Date"), "M/d/yyyy"))\
    .when((length(col("Date")) == 9) & (length(regexp_replace(col("Date"), "/.*", "")) == 1), to_date(col("Date"), "M/dd/yyyy"))\
    .otherwise(to_date(col("Date"), "MM/d/yyyy")))

# 2. "Volume" to IntegerFormat, remove the ","
# REmoving the "," leads to malformed strings. instread, try to_number.
# Stream = Stream.withColumn("Volume", when((col("Volume") == "n/a") | (col("Volume") == ""), lit(None)).otherwise(regexp_replace(col("Volume"), ",", ""))).withColumn("Volume", col("Volume").cast(IntegerType()))
# "990,999" accepts 1,000, 10,000 and 100,000

# Stream = Stream.withColumn("Volume", when((col("Volume") == "n/a") | (col("Volume") == ""), lit(None))\
#     .when(length(col("Volume")) < 5, col("Volume").cast(IntegerType()))\
#     .otherwise(to_number(col("Volume"), lit("990,990,990,990,999"))))

Stream = Stream.withColumn("Volume", when((col("Volume") == "n/a") | (col("Volume") == ""), lit(None))\
    .otherwise(to_number(col("Volume"), lit("990,990,990,990,990"))))

# 3. "Open", "Close", "High", "Low", transform n/a into NULL. REmove the ",". Transform the Strings into Floats.

# for column_name in ["Open", "Close", "High", "Low"]:
#     Stream = Stream.withColumn(column_name, when((col(column_name) == "n/a") | (col(column_name) == ""), lit(None))\
#         .when(length(col(column_name)) < 7, col(column_name).cast(FloatType()))\
#         .otherwise(to_number(col(column_name), lit("990,990,990,990,999.9999"))))\
#         .withColumn(column_name, pyspark.sql.functions.round(col(column_name), lit(2)))

for column_name in ["Open", "Close", "High", "Low"]:
    Stream = Stream.withColumn(column_name, when((col(column_name) == "n/a") | (col(column_name) == ""), lit(None))\
        .otherwise(to_number(col(column_name), lit("990,990,990,990,990.9999"))))\
        .withColumn(column_name, pyspark.sql.functions.round(col(column_name), lit(2)))

# 4. Add new Column: Time that the data went through the pipelie
Stream = Stream.withColumn("Processed", lit(datetime.datetime.now()))


# In[4]:


## Still Missing:
# 1. Archiving
# 3. Values go missing in the transformations

def myfunc(Stream, batch_id):
    # 5. Add new Column: Running Sum of Volume
    # Teh Sum funciotn only consider values form the current partition for the sum, utilizing the current row and all rows that come before that. This way, we get a cumulative sum for each Stock market
    running_sum_window = pyspark.sql.Window.partitionBy("Stock_Alias").orderBy("Date").rowsBetween(pyspark.sql.Window.unboundedPreceding, pyspark.sql.Window.currentRow)
    Stream = Stream.withColumn("Running_Volume", pyspark.sql.functions.sum(col("Volume")).over(running_sum_window))

    Stream.write.format("delta").option("path", "StreamData/Target/Entries").mode("append").save()

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

q = Stream.writeStream\
    .foreachBatch(myfunc)\
    .trigger(processingTime = "15 seconds")\
    .option("checkpointLocation", "StreamData/CheckPoint")\
    .start()

# q.awaitTermination()
stop_stream_query(q, 20000)


# In[5]:


test1 = spark.read.format("delta").load("StreamData/Target/Entries")


# In[6]:


test1.count()


# In[7]:


test1.sort("Date", ascending = False).show()


# In[8]:


test1.filter(col("Open").isNotNull()).groupBy("Stock_Alias").count().show()


# In[9]:


test1.filter(col("Volume").isNotNull()).groupBy("Stock_Alias").count().show()


# In[12]:


import requests
headers = {
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0'
}
url = "https://finance.yahoo.com/chart/GOOG#eyJsYXlvdXQiOnsiaW50ZXJ2YWwiOiJkYXkiLCJwZXJpb2RpY2l0eSI6MSwidGltZVVuaXQiOm51bGwsImNhbmRsZVdpZHRoIjoxMi40OCwiZmxpcHBlZCI6ZmFsc2UsInZvbHVtZVVuZGVybGF5Ijp0cnVlLCJhZGoiOnRydWUsImNyb3NzaGFpciI6dHJ1ZSwiY2hhcnRUeXBlIjoibW91bnRhaW4iLCJleHRlbmRlZCI6ZmFsc2UsIm1hcmtldFNlc3Npb25zIjp7fSwiYWdncmVnYXRpb25UeXBlIjoib2hsYyIsImNoYXJ0U2NhbGUiOiJsaW5lYXIiLCJzdHVkaWVzIjp7IuKAjHZvbCB1bmRy4oCMIjp7InR5cGUiOiJ2b2wgdW5kciIsImlucHV0cyI6eyJTZXJpZXMiOiJzZXJpZXMiLCJpZCI6IuKAjHZvbCB1bmRy4oCMIiwiZGlzcGxheSI6IuKAjHZvbCB1bmRy4oCMIn0sIm91dHB1dHMiOnsiVXAgVm9sdW1lIjoiIzBkYmQ2ZWVlIiwiRG93biBWb2x1bWUiOiIjZmY1NTQ3ZWUifSwicGFuZWwiOiJjaGFydCIsInBhcmFtZXRlcnMiOnsiY2hhcnROYW1lIjoiY2hhcnQiLCJlZGl0TW9kZSI6dHJ1ZSwicGFuZWxOYW1lIjoiY2hhcnQifSwiZGlzYWJsZWQiOmZhbHNlfX0sInBhbmVscyI6eyJjaGFydCI6eyJwZXJjZW50IjoxLCJkaXNwbGF5IjoiR09PRyIsImNoYXJ0TmFtZSI6ImNoYXJ0IiwiaW5kZXgiOjAsInlBeGlzIjp7Im5hbWUiOiJjaGFydCIsInBvc2l0aW9uIjpudWxsfSwieWF4aXNMSFMiOltdLCJ5YXhpc1JIUyI6WyJjaGFydCIsIuKAjHZvbCB1bmRy4oCMIl19fSwic2V0U3BhbiI6eyJtdWx0aXBsaWVyIjo2LCJiYXNlIjoibW9udGgiLCJwZXJpb2RpY2l0eSI6eyJwZXJpb2QiOjEsInRpbWVVbml0IjoiZGF5In0sInNob3dFdmVudHNRdW90ZSI6dHJ1ZSwiZm9yY2VMb2FkIjp0cnVlfSwib3V0bGllcnMiOmZhbHNlLCJhbmltYXRpb24iOnRydWUsImhlYWRzVXAiOnsic3RhdGljIjp0cnVlLCJkeW5hbWljIjpmYWxzZSwiZmxvYXRpbmciOmZhbHNlfSwibGluZVdpZHRoIjoyLCJmdWxsU2NyZWVuIjp0cnVlLCJzdHJpcGVkQmFja2dyb3VuZCI6dHJ1ZSwiY29sb3IiOiIjMDA4MWYyIiwiY3Jvc3NoYWlyU3RpY2t5IjpmYWxzZSwiZG9udFNhdmVSYW5nZVRvTGF5b3V0Ijp0cnVlLCJzeW1ib2xzIjpbeyJzeW1ib2wiOiJHT09HIiwic3ltYm9sT2JqZWN0Ijp7InN5bWJvbCI6IkdPT0ciLCJtYXJrZXQiOiJ1c19tYXJrZXQiLCJxdW90ZVR5cGUiOiJFUVVJVFkiLCJleGNoYW5nZVRpbWVab25lIjoiQW1lcmljYS9OZXdfWW9yayIsInBlcmlvZDEiOjE2OTIwNTA0MDAsInBlcmlvZDIiOjE3NzEyNTA0MDB9LCJwZXJpb2RpY2l0eSI6MSwiaW50ZXJ2YWwiOiJkYXkiLCJ0aW1lVW5pdCI6bnVsbCwic2V0U3BhbiI6bnVsbH1dLCJyZW5kZXJlcnMiOltdLCJyYW5nZSI6bnVsbH0sImV2ZW50cyI6eyJkaXZzIjp0cnVlLCJzcGxpdHMiOnRydWUsInRyYWRpbmdIb3Jpem9uIjoibm9uZSIsInNpZ0RldkV2ZW50cyI6W119LCJkcmF3aW5ncyI6bnVsbCwicHJlZmVyZW5jZXMiOnt9fQ=="
response = requests.get(url, headers)


# In[14]:


response.text


# In[ ]:




