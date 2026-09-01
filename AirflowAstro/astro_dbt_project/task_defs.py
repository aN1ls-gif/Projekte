import numpy as np
import requests
import pandas as pd

def fetch_data(logger, current_datetime, fetch_params, fetch_url, mode, **kwargs):
    """
    Fetch the values from the air quality api and clean them.
    """
    logical_date_time = kwargs["logical_date"]
    logger.debug(logical_date_time)
    timediff = (current_datetime - logical_date_time).days + np.maximum((current_datetime - logical_date_time).hours//24, 1)
    timediff = int(timediff) if timediff >= 0 else 0
    timediff = timediff if timediff <= 92 else 92
    
    logger.debug(current_datetime)
    logger.debug(f"past_days: {timediff}")

    params = fetch_params.copy()
    params["past_days"] = timediff


    response = requests.get(fetch_url, params=params)
    response.raise_for_status()
    data = response.json()
    current_data_dict = data.get(mode, {})
    return current_data_dict

def clean_data(data_dict, logger, mode):
    """
    Remove rows containing NaNs from the current values. 
    Change the dtype of all columns to string (safest against data corruption/malformation of data)
    """
    if mode == "current":
        df = pd.DataFrame.from_dict(data_dict, orient = "index").T.drop(columns = ["interval"])
    elif mode == "hourly":
        df = pd.DataFrame(data_dict)
    logger.debug(f"The columns of the df containing the {mode} values: {df.columns}")
    total_samples = df.shape[0]
    df.dropna(axis = 0, how = "all", inplace = True)
    all_na_samples = total_samples - df.shape[0]
    df.dropna(axis = 0, how = "any", inplace = True)
    some_na_samples = total_samples - all_na_samples - df.shape[0]
    rest_samples = df.shape[0]


    log_text = f"The {mode} values from the air quality api contained a total of {total_samples} values.\nAfter removing the {all_na_samples} samples containing only NaNs and the {some_na_samples} samples containing some NaNs,\nthe number of remaining samples is {rest_samples} ({rest_samples/total_samples:.2%} of the samples in the fetch)."
    logger.info(log_text)
    df = df.astype(str)

    columns = list(df.columns)
    logger.debug(columns)
    change_index = columns.index("time")
    columns[change_index] = "time_string"
    df.columns = columns
    return df