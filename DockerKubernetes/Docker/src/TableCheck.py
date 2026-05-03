# -*- coding: utf-8 -*-
"""
Created on Sat Apr 18 10:52:13 2026

@author: Nils
"""


import pyspark
# from pyspark.sql.functions import col, date_format
import delta

import streamlit as st





###### 1. Inwiefern macht Caching Sinn? Kann ich es effektiver Cachen?
###### 2. SessionState um Sachen zwischen Reruns zu speichern ? (mehr speed?)
###### 3. Titel mit Erklärung. 

@st.cache_resource
def StartSession():
    """
    Start the Spark Session for Data retrieval. Save the session in cache (is that even possible) to avoid reloading-time
    """
    builder = pyspark.sql.SparkSession.builder.appName("Tablecheck") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")\
    .master("local")

    spark = delta.configure_spark_with_delta_pip(builder).getOrCreate()
    df = spark.read.format("delta").load("/app/StreamData/Target/Entries").dropDuplicates(["Stock_Alias", "Date"])
    return df


df = StartSession()


st.header("The Table")
st.table(df.toPandas())

st.header("The dtypes")
Dtype = df.dtypes
st.write(Dtype)

st.header("Example Date Entry")
Date_example = df.select("Date").toPandas().iloc[0]
st.write(Date_example)
st.write(type(Date_example))



