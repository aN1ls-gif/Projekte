# -*- coding: utf-8 -*-
"""
Created on Mon Feb 16 09:36:49 2026

@author: Nils
"""

# import pandas as pd
from datetime import timedelta


from plotly.subplots import make_subplots
import plotly.graph_objects as go
# import plotly.express as px

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
    df = spark.read.format("delta").load("StreamData/Target/Entries")
    return df


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


def LinePlot_Plotly(Data):
    """
    Make use of PySparks Native Plotting to create lineplots of Open, Close, High, Low and Volume
    PySpark makes use of Plotly
    If the Datapoints exceed 1000, pyspark will pick 1000 evenly-spaced samples from the dataset for an overall overview of how the data developed 
    
    """
    Open = Data.plot(kind = "line", x = "Date", y = "Open", color = "Stock_Alias")
    Close = Data.plot(kind = "line", x = "Date", y = "Close", color = "Stock_Alias")
    High = Data.plot(kind = "line", x = "Date", y = "High", color = "Stock_Alias")
    Low = Data.plot(kind = "line", x = "Date", y = "Low", color = "Stock_Alias")
    # Volume = df.plot(kind = "line", x = "Date", y = "Volume", color = "Stock_Alias")
    
    size = 800
    colors = ["blue", "green", "yellow", "grey", "purple"]
    # These settings in combination with graph_objects allows for hoverinfo that shows all subplots at once for a single x.
    layout = dict(
        hoversubplots="axis",
        title=dict(text="Stock Price Changes"),
        hovermode="x unified",
        grid=dict(rows=4, columns=1),
        width = size,
        height = size,
        template = "seaborn"
    )
    
    fig = make_subplots(rows = 4, cols=1, subplot_titles=("Open", "Close", "High", "Low"), shared_xaxes = True)
    
    
    for i in range(len(Open.data)):
        fig.add_trace(go.Scatter(x = Open.data[i]["x"], y = Open.data[i]["y"], name = Open.data[i]["name"], showlegend = False, line = dict(color = colors[i]), xaxis = "x", yaxis = "y1", legendgroup = "Open", legendgrouptitle_text = "Open"))
        fig.add_trace(go.Scatter(x = Close.data[i]["x"], y = Close.data[i]["y"], name = Close.data[i]["name"], showlegend = False, line = dict(color = colors[i]), xaxis = "x", yaxis = "y2", legendgroup = "Close", legendgrouptitle_text = "Close"))
        fig.add_trace(go.Scatter(x = High.data[i]["x"], y = High.data[i]["y"], name = High.data[i]["name"], showlegend = False, line = dict(color = colors[i]), xaxis = "x", yaxis = "y3", legendgroup = "High", legendgrouptitle_text = "High"))
        fig.add_trace(go.Scatter(x = Low.data[i]["x"], y = Low.data[i]["y"], name = Low.data[i]["name"], showlegend = False, line = dict(color = colors[i]), xaxis = "x", yaxis = "y4", legendgroup = "Low", legendgrouptitle_text = "Low"))
        # fig.add_trace(go.Scatter(x = Volume.data[i]["x"], y = Volume.data[i]["y"], name = Volume.data[i]["name"], showlegend = False, line = dict(color = colors[i]), xaxis = "x", yaxis = "y5", legendgroup = "Volume", legendgrouptitle_text = "Low"))
    
        # This add a legend that has NO GroupTitles and is therefore usable for all subplots
        # At the same time, nothing from this will be displayed in the Hoverinfo
        fig.add_trace(go.Scatter(x = [Open.data[i]["x"][0]], y = [Open.data[i]["y"][0]], name = Open.data[i]["name"], line = dict(color = colors[i]), xaxis = "x", yaxis = "y1", hoverinfo = None, showlegend = True, mode = "lines", legendgroup = "Stocks", legendgrouptitle_text = "Stocks"))
    fig.update_layout(layout)
    
    
    return fig

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
    st.text("Using PySpark's Native Plotting (accessing Plotly)")
    # st.text("Placeholder")
    st.plotly_chart(LinePlot_Plotly(Data), theme = "streamlit")
with col2:
    st.header("Boxplot")
    st.text("Using Altair")
    # st.text("Placeholder")
    st.altair_chart(Boxplots_Altair(Data), theme = "streamlit")
    

st.table(df.select("*").toPandas())

    
    

