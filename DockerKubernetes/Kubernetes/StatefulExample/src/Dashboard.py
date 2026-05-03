# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 10:05:45 2026

@author: Nils
"""

import streamlit as st
import pandas as pd
import numpy as np
import os



# import mysql.connector

# def Create_Connection():
#     mydb = mysql.connector.connect(
#         host = os.environ.get("MYSQL_DATABASE_HOST"),
#         user = os.environ.get("MYSQL_DATABASE_USER"),
#         password = os.environ.get("MYSQL_DATABASE_PASSWORD"))
#     database_name = os.environ.get("MYSQL_DATABASE_NAME")
#     mycursor = mydb.cursor()
#     mycursor.execute(f"USE {database_name}")
    
#     return mycursor

# def return_entries(db_cursor):
#     # Fetch all rows from the executed query
#     table_rows = db_cursor.fetchall()
    
#     # Create a DataFrame without column names
#     df = pd.DataFrame(table_rows)
#     return df
    
# def new_entry(db_cursor, text, table):
#     db_cursor.execute(f"INSERT INTO {table}(entry) VALUES ({text})")


# st.set_page_config(layout="wide") # Use the entire screen, not just the middle
# with st.spinner(text='Initializing Session ...'):
#     db_cursor = Create_Connection()
#     current_entries = return_entries(db_cursor)
#     table_name = os.environ.get("MYSQL_DATABASE_TABLE")

# st.header("The Text-Input Field")    
# text = st.text_input(label = "New Entry for the MySQL Database",
#                      value = "",
#                      max_chars = 255)
# if text:
#     new_entry(db_cursor, text)
    
# st.header("The current state of the my-sql database")
# st.table(current_entries)


import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, VARCHAR
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import sys


table_name = os.environ.get("MYSQL_DATABASE_TABLE")
Base = declarative_base()

class MyTable(Base):
    __tablename__ = table_name
    # apparently SQLalchemy automatically sets the first primary-key integer column with auto-increment
    entry_id = Column(Integer, primary_key=True) 
    entry = Column(VARCHAR(255))
    
@st.cache_resource
def Create_Connection():
    user = os.environ.get("MYSQL_DATABASE_USER")
    password = os.environ.get("MYSQL_DATABASE_PASSWORD")
    host = os.environ.get("MYSQL_DATABASE_HOST")
    database = os.environ.get("MYSQL_DATABASE_NAME")
    port = os.environ.get("MYSQL_DATABASE_PORT")
    
    engine = create_engine(
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}",
        pool_pre_ping=True
    )
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    return session, engine

def return_entries(session, table_name = table_name):
    data = session.query(MyTable).all()
    
    # Convert ORM query result to a DataFrame
    try:
        for_pandas = []
        for class_object in data:
            l = []
            for key in ["entry_id", "entry"]:
                l.append(getattr(class_object, key))
            for_pandas.append(l)
        df = pd.DataFrame(np.array(for_pandas))
        df.columns = ["ID", "Text entry"]
    except:
        df = pd.DataFrame(np.array([["", ""]]), columns = ["ID", "Text entry"])
    return df

def new_entry(text, session):
    # the entry_id should be taken care of by the autoincrement
    session.add(MyTable(entry = text))
    session.commit()




st.set_page_config(layout="wide") # Use the entire screen, not just the middle
with st.spinner(text='Initializing Session ...'):
    session, engine = Create_Connection()
try:
    st.header("The Text-Input Field")    
    text = st.text_input(label = "New Entry for the MySQL Database",
                        value = "",
                        max_chars = 255)
    if text:
        st.write(f"'{text}' will be entered into the sql table")
        new_entry(text, session)
        
    st.header("The current state of the my-sql database")
    current_entries = return_entries(session)
    st.table(current_entries)
except KeyboardInterrupt:
    session.close()
    engine.dispose()
    sys.exit()


