# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 09:25:17 2026

@author: Nils
"""

import mysql.connector
import os
import traceback
import time


# This loop will keep going until I am able to connect to the mysql-server and create a table.
# Until this is done, the initContainer will not be finished
while True:
    try:
        mydb = mysql.connector.connect(
            host = os.environ.get("MYSQL_DATABASE_HOST"),
            user = os.environ.get("MYSQL_DATABASE_USER"),
            password = os.environ.get("MYSQL_DATABASE_PASSWORD"),
            port = os.environ.get("MYSQL_DATABASE_PORT"))
        print("created connection")
        table_name = os.environ.get("MYSQL_DATABASE_TABLE")
        mycursor = mydb.cursor()
        print("creaetd cursor")
        # database-creation for this user should already be taken care of by the mysql-image
        database = os.environ.get("MYSQL_DATABASE_NAME")
        mycursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        mycursor.execute(f"USE {database}")
        mycursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name}(
                entry_id INT PRIMARY KEY AUTO_INCREMENT,
                entry VARCHAR(255)
                )
            """
            )
        mydb.commit()
        time.sleep(5)
        mycursor.close()
        mydb.close()
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        time.sleep(20)
    else:
        break