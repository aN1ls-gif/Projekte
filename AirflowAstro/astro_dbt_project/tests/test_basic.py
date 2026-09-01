import os
import logging
from contextlib import contextmanager
import pytest
import json
import task_defs
import datetime
import pendulum
import pandas as pd



filedir = os.path.dirname(os.path.abspath(__file__))




current_datetime = pendulum.datetime(2026, 9, 1, 9, 0, 0, tz = "Europe/Paris")
logical_date = pendulum.datetime(2026, 9, 1, 2, 0, 0, tz = "Europe/Paris")
fetch_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
non_aqi_params = ["pm10", "pm2_5", "nitrogen_dioxide", "sulphur_dioxide", "ozone"]
aqi_params = ["european_aqi", "european_aqi_pm2_5", "european_aqi_pm10", "european_aqi_nitrogen_dioxide", "european_aqi_ozone", "european_aqi_sulphur_dioxide"]
parameters = non_aqi_params + aqi_params
fetch_params = {
            "latitude": 51.218931,
            "longitude": 6.471359,
            "timezone": "Europe/Berlin",
            "past_days": 0}

logger = logging.getLogger(__name__)


@contextmanager
def suppress_logging(namespace):
    """
    Contextmanager, use with "with" statement.
    For the duration of the "with" statement, the logging is disabled. Afterwards, it is re-enabled
    """
    logger = logging.getLogger(namespace)
    old_value = logger.disabled
    logger.disabled = True
    try:
        yield logger
    finally:
        logger.disabled = old_value


@pytest.mark.parametrize("mode", ["current", "hourly"])
def test_fetch(mode):
    """Test if data can be fetched from the weather api"""
    with suppress_logging(__name__):
        fetched_data = task_defs.fetch_data(logger, current_datetime, fetch_params, fetch_url, mode, logical_date = logical_date)
    assert True

@pytest.fixture(params = ["current", "hourly"])
def weather_api_response(request):
    """
    Mimic weather api request by loading pre-fetched data
    """
    with open(f"{filedir}/../Testdata/weather_api_fetch.json", "r") as f:
        weather_api_data = json.load(f)
    return dict(data = weather_api_data[request.param],
                parameter = request.param)

def test_clean(weather_api_response):
    """
    Test if data cleanup goes without error
    """
    data_dict, mode = weather_api_response["data"], weather_api_response["parameter"]
    with suppress_logging(__name__):
        cleaned_data = task_defs.clean_data(logger = logger, mode = mode, data_dict = data_dict)
    assert True

    