#!/usr/bin/env python
# coding: utf-8

# # This script scrapes the Stock Market Data for various companies, comodities and currencies and saves the data in individual json files. This is supposed to simulate the continously incoming data for the pyspark streaming pipeline

# In[1]:


Interests = {"Companies": ["AMZN", "NVDA", "GOOG", "BA", "BAYN.DE"], # Amazon, Nvidia, Google, Boeing, Bayer-Aktiengesellschaft
            "Currencies": ["EURUSD=X", "GBPEUR=X", "EURHUF=X", "BTC-USD", "ETH-USD"],
            "Commodities": ["GC=F", "HG=F", "SI=F", "CL=F", "NG=F"]}


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
from tqdm import tqdm
import json

URL = "https://finance.yahoo.com/markets/"
No_GUI = True
pxl_per_step = 3
pause = 3


# Initialize WebDriver (e.g., Firefox or Chrome)

options = ChromeOptions()
if No_GUI:
    options.add_argument('--headless=new') # Do not open a browser; easier computation
driver = webdriver.Chrome(options)

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
    time.sleep(5)

    ######## 3. Locate the search/ query field and enter my search query.
    # In case we switched to a different conttent before.
    driver.switch_to.default_content()
    try:
        with open("StreamData/ScrapingCheckpoint/Savepoint.json", "r") as f:
            Result_dict = json.load(f)

        with open("StreamData/SrapingCheckpoint/Savepoint.txt", "r") as f:
            AlreadyChecked = [i.replace("\n", "") for i in f.readlines()]

        print("Continue from previous scraping")
    except:
        Result_dict = {}
        AlreadyChecked = []
        print("Starting a new scrape")

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
            time.sleep(5)
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

            tooltips = driver.find_element(By.XPATH, "//table[@class = 'hu-tooltip']")
            print("Start retrieving data from website")
            for i in tqdm(range(0, Width, pxl_per_step)):
                DT = tooltips.find_element(By.XPATH, "//tr[@hu-tooltip-field = 'DT']/td[@class = 'hu-tooltip-value']").text
                if DT != "":
                    Result_dict.setdefault(DT, {})
                    Result_dict[DT].setdefault(BigC, {"Open": "n/a", "Close": "n/a", "High": "n/a", "Low": "n/a", "Volume": "n/a"})
                    for element in Result_dict[DT][BigC]:
                        Content = tooltips.find_element(By.XPATH, f"//tr[@hu-tooltip-field = '{element}']/td[@class = 'hu-tooltip-value']").text
                        if Content == "n/a":
                            # Sometimes, Dates have multiple values, once with actual numbers and once with only NaNs. Therefore, I ignore the entry if it is None (as that is the default) and only enter Non-Nan Values.
                            continue
                        Result_dict[DT][BigC][element] = Content 
                ActionChains(driver).move_by_offset(pxl_per_step, 0).perform()
                time.sleep(pause)

            with open("StreamData/ScrapingCheckpoint/Savepoint.json", "w") as f:
                json.dump(Result_dict, f)

            with open("StreamData/ScrapingCheckpoint/Savepoint.txt", "a") as f:
                f.write(BigC + "\n")

finally:
    driver.quit()


# In[8]:


import pandas as pd
import json

Interests = {"Companies": ["AMZN", "NVDA", "GOOG", "BA", "BAYN.DE"], # Amazon, Nvidia, Google, Boeing, Bayer-Aktiengesellschaft
            "Currencies": ["EURUSD=X", "GBPEUR=X", "EURHUF=X", "BTC-USD", "ETH-USD"],
            "Commodities": ["GC=F", "HG=F", "SI=F", "CL=F", "NG=F"]}
reverse = {Item: Interest for Interest in Interests for Item in Interests[Interest]}

with open("StreamData/ScrapingCheckpoint/Savepoint.json", "r") as f:
    DF = pd.DataFrame.from_dict(json.load(f))

# DF = pd.DataFrame.from_dict(Result_dict)
# Not all Storck Markets have the same dates. This causes some to have a simple NA entry after turning the nested dict into a DataFrame of Dicts.
# Fill all NA with the default empty Dict: {"Open": "n/a", "Close": "n/a", "High": "n/a", "Low": "n/a", "Volume": "n/a"}
DF = DF.mask(DF.isna(), {"Open": "n/a", "Close": "n/a", "High": "n/a", "Low": "n/a", "Volume": "n/a"})
DF.to_csv("Temp_Save.csv")
# DF = pd.read_csv("Temp_Save.csv", index_col = 0)
DF.reset_index(names = "Stock_Alias", inplace = True)
DF.head()
for count, col in enumerate(list(DF.columns)[1:]):
    Subset = DF.loc[:, ("Stock_Alias", col)]
    Entries = Subset.shape[0]
    Subset = Subset.to_dict()
    Section = dict(Date = col)
    As_List = []
    for i in range(Entries):
        Nested_dict = dict()
        Nested_dict["Stock_Alias"] = Subset["Stock_Alias"][i]
        Nested_dict["Data"] = Subset[col][i]
        Nested_dict["Category"] = reverse[Subset["Stock_Alias"][i]]
        As_List.append(Nested_dict)
    Section["Entries"] = As_List

    with open(f"StreamData/ExampleData/SampleData_{count}.json", "w") as f:
        json.dump(Section, f)


# In[ ]:




