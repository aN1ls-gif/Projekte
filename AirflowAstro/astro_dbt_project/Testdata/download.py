import json
import requests
import os

data_url = "https://air-quality-api.open-meteo.com/v1/air-quality"

non_aqi_params = ["pm10", "pm2_5", "nitrogen_dioxide", "sulphur_dioxide", "ozone"]
aqi_params = ["european_aqi", "european_aqi_pm2_5", "european_aqi_pm10", "european_aqi_nitrogen_dioxide", "european_aqi_ozone", "european_aqi_sulphur_dioxide"]
parameters = non_aqi_params + aqi_params

params = {
            "latitude": 51.218931,
            "longitude": 6.471359,
            "timezone": "Europe/Berlin",
            "past_days": 4,
            "current": parameters,
            "hourly": parameters
            }


response = requests.get(data_url, params=params)
response.raise_for_status()
data = response.json()

filedir = os.path.dirname(os.path.abspath(__file__))

with open(f"{filedir}/weather_api_fetch.json", "w") as f:
    json.dump(data, f)