# -*- coding: utf-8 -*-
"""
Created on Mon Feb 16 09:36:49 2026

@author: Nils
"""
from datetime import timedelta

import pyspark
from pyspark.sql.functions import col
import delta

import streamlit as st
import altair as alt

def streamlit_theme():
    """
    Change 'streamlit' theme configuration for the displaying of altair charts
    """

    config = {
        "config": {
            "background": "#574969",
            "y": {"axis": {"ticks": True}},
            "x": {"axis": {"domain": True}}
            }
        }
    return config

alt.themes.register("streamlit", streamlit_theme)
alt.themes.enable("streamlit")


###### 1. Inwiefern macht Caching Sinn? Kann ich es effektiver Cachen?
###### 2. SessionState um Sachen zwischen Reruns zu speichern ? (mehr speed?)
###### 3. Titel mit Erklärung. 

@st.cache_resource
def StartSession():
    """
    Start the Spark Session for Data retrieval. Save the session in cache (is that even possible) to avoid reloading-time
    """
    builder = pyspark.sql.SparkSession.builder.appName("Stream_Dashboard") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")\
    .master("local")

    spark = delta.configure_spark_with_delta_pip(builder).getOrCreate()
    df = spark.read.format("delta").load("/app/StreamData/Target/Entries").dropDuplicates(["Stock_Alias", "Date"])
    return df


def Running_Volume(Amazon):
    """
    Simpel example that always uses the Amazon Stock Data
    """
    running_sum_window = pyspark.sql.Window.partitionBy("Stock_Alias").orderBy("Date").rowsBetween(pyspark.sql.Window.unboundedPreceding, pyspark.sql.Window.currentRow)
    Amazon = Amazon.withColumn("Running_Volume", pyspark.sql.functions.sum(col("Volume")).over(running_sum_window))
    Amazon = Amazon.dropna().select(["Date", "Running_Volume"]).toPandas()
    Amazon["Running_Volume"] = Amazon["Running_Volume"].astype(int)

    title = alt.TitleParams('Amazon running volume')
    chart = alt.Chart(Amazon, title = title)
    ## N = Nominal Data
    ## Q = Quantitative Data
    Output = chart.mark_bar().encode(
        alt.X("Date:T", title = "Date"),
        alt.Y("Running_Volume:Q", title = "Running Volume")).properties(height=500,width=1000)

    return Output

def Boxplots_Altair(Data):
    """
    Using Altair, make a boxplit for the volumes of the stock_aliases
    """
    data = Data.dropna().select(["Stock_Alias", "Volume"]).toPandas()
    data["Volume"] = data["Volume"].astype(int)
    
    title = alt.TitleParams('Volume Boxplots')
    chart = alt.Chart(data, title = title)
    ## N = Nominal Data
    ## Q = Quantitative Data
    Output = chart.mark_boxplot().encode(
        alt.Y("Stock_Alias:N", title = "Stocks"),
        alt.X("Volume:Q", title = "Volume")).properties(height=800,width=300)
            
    return Output

def LinePlot_Altair(Data):
    
    Output = alt.Chart(Data.toPandas()).mark_line().encode(
        alt.X(alt.repeat("column"), type = "temporal"),
        alt.Y(alt.repeat("row"), type = "quantitative"),
        color = "Stock_Alias:N"
        ).properties(
            width = 500,
            height = 200
            ).repeat(
                row = ["Open", "Close", "High", "Low"],
                column = ["Date"]
                ).interactive()
    
    return Output

######## Initialize ########
st.set_page_config(layout="wide") # Use the entire screen, not just the middle
with st.spinner(text='Initializing Session ...'):
    df = StartSession()
###########################


    ####### Filter (Which Category?) #######
    Unique_Categories = df.select(["Category"]).distinct().toPandas() # ReturnData(spark, columns = ["Category"]).distinct().toPandas()
    Category_filter = st.sidebar.selectbox(label = "Stock category", options = Unique_Categories, index = 0)
    
    
    ####### Filter (Which Stocks?) ########
    Unique_Stocks = df.filter(col("Category").isin([Category_filter])).select("Stock_Alias").distinct().toPandas()
    Stock_Alias_filter = st.sidebar.multiselect(label = "Stock(s)", options = Unique_Stocks, default = Unique_Stocks)
    # st.write(Stock_Alias_filter)
    
    ####### Filter (Start to end Date) #####
    Start_Date = df.select(pyspark.sql.functions.min(col("Date"))).collect()[0][0]
    End_Date = df.select(pyspark.sql.functions.max(col("Date"))).collect()[0][0]
    Date_Range_slider = st.sidebar.slider(label = "Choose the date range", min_value = Start_Date, max_value = End_Date, value = (Start_Date, End_Date), step = timedelta(days = 30))
    # st.write(Date_Range_slider)
    
    ####### Get the filtered Data
    Data = df.filter(col("Category").isin([Category_filter]) & col("Stock_Alias").isin(Stock_Alias_filter) & col("Date").between(*Date_Range_slider))
    Data = Data.sort("Date").withColumn("Date", pyspark.sql.functions.date_format("Date", "MMMM dd, yyyy"))



###########################################################################
#### Design the Site
st.title("End of Stream-ETL pipeline: A simple dashboard")



###### Create the Plots
col1, col2 = st.columns([2, 1], width = 1000000, gap = "xlarge", border = True) # First column is 3 times wider than second column
with col1:
    st.header("Line-Subplots")
    st.text("Using Altair Subplots")
    # st.text("Placeholder")
    st.altair_chart(LinePlot_Altair(Data), theme = "streamlit")
with col2:
    st.header("Boxplot")
    st.text("Using Altair")
    # st.text("Placeholder")
    st.altair_chart(Boxplots_Altair(Data), theme = "streamlit")



###############
Amazon = df.filter(col("Stock_Alias") == "AMZN")    
st.header("Running Volume Example using Amazon Stocks")
st.altair_chart(Running_Volume(Amazon), theme = "streamlit")


    

    
    

