#!/usr/bin/env python
# coding: utf-8

# # This script scrapes the Stock Market Data for various companies, comodities and currencies and saves the data in individual json files. This is supposed to simulate the continously incoming data for the pyspark streaming pipeline

# In[1]:


Interests = {"Companies": ["AMZN", "NVDA", "GOOG", "BA", "BAYN.DE"], # Amazon, Nvidia, Google, Boeing, Bayer-Aktiengesellschaft
            "Currencies": ["EURUSD=X", "BTC-USD", "ETH-USD"]}


# In[7]:


# After Testing:
# 1. Implemetn a loop
# 2. Impelemtn a Dataset atll will be saved in before seperating it into individual jsons
# 3. No pop-up window
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver import ChromeOptions
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
from tqdm import tqdm
import traceback
import sys




URL = "https://finance.yahoo.com/markets/"
No_GUI = True
pxl_per_step = 3
pause = 3
Sleep = True

import pyspark
from pyspark.sql import SparkSession
import delta

builder = SparkSession.builder.appName("Stream_Scrape") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")\
    .config("spark.driver.memory", "8g")

spark = delta.configure_spark_with_delta_pip(builder).getOrCreate()


# Initialize WebDriver (e.g., Firefox or Chrome)
while True:
    try:
        #### Used to determine from what timepoint on we need new data
        Table = spark.read.format("delta").option("multiline", "false").load("/app/StreamData/Target/Entries")
        date_func_delta = lambda x: Table.where(pyspark.sql.functions.col("Stock_Alias") == x).select(pyspark.sql.functions.max("Date")).collect()[0][0]
        print("\nDelta Table loaded.")
    except:
        print("\nNo delta table exists yet. Use todays date and calculate 6 months into the past.")
    finally:
        # if no table exists (i.e completly fresh start)
        today = datetime.now()# .date()
        date_func_backup = lambda x: today + relativedelta(months=-6)
    
    options = ChromeOptions()
    if No_GUI:
        options.add_argument('--headless=new') # Do not open a browser; easier computation
        # options.add_argument("--session-timeout=30000")
    # Get the url of the remote selenium server that we have set up in the dockerfiles and docker-compose
    SELENIUM_REMOTE_URL = os.environ.get("SELENIUM_REMOTE_URL")
    driver = webdriver.Remote( 
        command_executor=SELENIUM_REMOTE_URL,
        options=options)
    IMPLICIT_WAIT_TIME = int(os.environ.get("IMPLICIT_WAIT_TIME"))
    driver.implicitly_wait(IMPLICIT_WAIT_TIME)
    RESTART_WAIT = int(os.environ.get("RESTART_WAIT"))
    # driver = webdriver.Chrome(options)
    # driver.implicitly_wait(300)
    
    try:
        ####### 1. Opens the Website
        driver.get(URL)
        if not No_GUI:
            driver.maximize_window()
        # time.sleep(sleeping)
    
        ######## 2. Deal with Overlay Windows (Consent forms, cookie forms etc)
        # When opening this yahoo website using Selenium, we are first greeted with a Consent Form. On this consent form, find and click the "Alle ablehnen" button. AFterwards, the actual website that I wanted to access will be loaded
        consent_overlay_button = driver.find_element(By.XPATH, "//button[@class = 'btn secondary reject-all']")
        consent_overlay_button.click()
        print("Entered Site")
        # time.sleep(5)
    
        ######## 3. Locate the search/ query field and enter my search query.
        # In case we switched to a different conttent before.
        driver.switch_to.default_content()
        
        try:
            with open("/app/StreamData/ScrapingCheckpoint/Savepoint.txt", "r") as f:
                AlreadyChecked = [i.replace("\n", "") for i in f.readlines()]
        except:
            AlreadyChecked = []
        
        print("Prepare Date determination")    
            
        
    
        print("Scraping Start:\n")
        for Interest in Interests:
            for BigC in Interests[Interest]:
                if BigC in AlreadyChecked:
                    continue
                print()
                print(BigC)
    
                # gain access to the search query field
                query_field = driver.find_element(By.XPATH, "//input[@id = 'ybar-sbq']")
                # enter the search string into the search query field
                query_field.send_keys(BigC)
                # time.sleep(5)
                # simulate the pressing of the Return Button to submit the query
                query_field.send_keys(Keys.RETURN)
                print("Performed Search")
                time.sleep(15)
    
    
                ######### 4. I am Interested in the data of the last 6 Months. Locate and click the "6M" Button
                Timespan_button = driver.find_element(By.XPATH, "//button[@id = 'tab-6m']")
                Timespan_button.click()
                print("Selected subwindow")
                time.sleep(5)
    
    
                ######### 5. Hover over the interactive graph. From the Center, move to the lest-most part of the window. 
                interactive_graph = driver.find_element(By.CSS_SELECTOR, "div.ciq-chart-area")
                Width = int(interactive_graph.find_element(By.XPATH, "//canvas[@role = 'img']").get_attribute("width")) 
                ActionChains(driver).move_to_element_with_offset(interactive_graph, -Width/2, 0).perform() 
                print("Reached left most part of the interactive graph")
                time.sleep(5)
    
                ######## 6. In a loop: Find the current values, save them, move one pixel to the right.
                
                try:
                    Latest_Entry_Date = date_func_delta(BigC)
                    # Case: Delta TAble Already exists but the current Stock alias has not yet any entry.
                    # the return value will be None. If that is the case, use the backup date
                    Latest_Entry_Date = date_func_backup(BigC) if Latest_Entry_Date is None else Latest_Entry_Date
                except:
                    # Delta table did not exist to begin with
                    Latest_Entry_Date = date_func_backup(BigC)
                # The DAte Value must be completly dissconected form teh spark engine or else there will be 'temp spark dir could not be removed' errors that freeze teh code
                # I achieve thies by transfroming the Datetime-format into a string and back into datetime-format
                Latest_Entry_Date = datetime.strptime(Latest_Entry_Date.strftime("%m/%d/%Y"), "%m/%d/%Y")
                tooltips = driver.find_element(By.XPATH, "//table[@class = 'hu-tooltip']")
                print("Start retrieving data from website")
                for i in tqdm(range(0, Width, pxl_per_step)):
                    
                    Result_dict = {}
                    ### DT = mm/dd/yyyy. Only interested in Data from Dates that are not already in the Delta Table
                    
                    DT = tooltips.find_element(By.XPATH, "//tr[@hu-tooltip-field = 'DT']/td[@class = 'hu-tooltip-value']").text
                    dateNotEmpty = DT != ""
                    if dateNotEmpty:
                        print("Date is not empty")
                        print(DT)
                        month, day, year = DT.split("/")
                        # if month or day is only single digit, it needs to be zero-padded for the transformation
                        # from string to datetime to work
                        if len(month) == 1:
                            month = "0" + month
                        if len(day) == 1:
                            day = "0" + day
                        DT = f"{month}/{day}/{year}"
                        DT_datetime = datetime.strptime(DT, "%m/%d/%Y")
                     
                        dateLargerThanExistingEntry = DT_datetime > Latest_Entry_Date
                        if  dateLargerThanExistingEntry:
                            print("Date is new, entry can be made")
                            Result_dict["date"] = DT
                            Result_dict["alias"] = BigC
                            Result_dict["Category"] = Interest
                            for element in ["Open", "Close", "High", "Low", "Volume"]:
                                Content = tooltips.find_element(By.XPATH, f"//tr[@hu-tooltip-field = '{element}']/td[@class = 'hu-tooltip-value']").text
                                if Content == "n/a":
                                    # Sometimes, Dates have multiple values, once with actual numbers and once with only NaNs. Therefore, I ignore the entry if it is None (as that is the default) and only enter Non-Nan Values.
                                    continue
                                else:
                                    Result_dict[element] = Content 
                            
                            with open(f"/app/StreamData/ScrapeSource/{BigC}_{DT.replace('/', '_')}.json", "w") as f:
                                json.dump(Result_dict, f)
                    
                    ActionChains(driver).move_by_offset(pxl_per_step, 0).perform()
                    # wait with next website interaction
                    time.sleep(pause)
                
                print("Update Checkpoint")
                # If one complet while-loop gets interupted and must be restart, skip the Stocks that have already
                # been read in this run-through. Saves time compared to checking the date for every single one
                with open("/app/StreamData/ScrapingCheckpoint/Savepoint.txt", "a") as f:
                    f.write(BigC + "\n")
        # One while loop successfully completed. Can reset the ckeckpoint     
        with open("/app/StreamData/ScrapingCheckpoint/Savepoint.txt", "w") as f:
            f.write("")
            
    except Exception as e:
        spark.stop()
        print(e)
        print(traceback.format_exc())
        Sleep = False
    
    finally:
        driver.quit()
        if Sleep:
            time.sleep(86400) # wait 86400 seconds == 24 hours before the next walkthrough. 
        else:
            time.sleep(RESTART_WAIT) # give me time to see the error before the script shuts down and the pod gets restarted
            sys.exit()



