CREATE TABLE rawdata.current(
    "time_string" VARCHAR(25) UNIQUE NOT NULL PRIMARY KEY,
    -- "subset" VARCHAR(8) NOT NULL,
    "pm10" VARCHAR(10),
    "pm2_5" VARCHAR(10),
    "nitrogen_dioxide" VARCHAR(10),
    "sulphur_dioxide" VARCHAR(10),
    "ozone" VARCHAR(10),
    "european_aqi" VARCHAR(10),
    "european_aqi_pm2_5" VARCHAR(10),
    "european_aqi_pm10" VARCHAR(10),
    "european_aqi_nitrogen_dioxide" VARCHAR(10),
    "european_aqi_ozone" VARCHAR(10),
    "european_aqi_sulphur_dioxide" VARCHAR(10)
);

CREATE TABLE rawdata.current_temp(
    "time_string" VARCHAR(25) UNIQUE NOT NULL PRIMARY KEY,
    -- "subset" VARCHAR(8) NOT NULL,
    "pm10" VARCHAR(10),
    "pm2_5" VARCHAR(10),
    "nitrogen_dioxide" VARCHAR(10),
    "sulphur_dioxide" VARCHAR(10),
    "ozone" VARCHAR(10),
    "european_aqi" VARCHAR(10),
    "european_aqi_pm2_5" VARCHAR(10),
    "european_aqi_pm10" VARCHAR(10),
    "european_aqi_nitrogen_dioxide" VARCHAR(10),
    "european_aqi_ozone" VARCHAR(10),
    "european_aqi_sulphur_dioxide" VARCHAR(10)
);

CREATE TABLE rawdata.hourly_temp(
    "time_string" VARCHAR(25) UNIQUE NOT NULL PRIMARY KEY,
    -- "subset" VARCHAR(8) NOT NULL,
    "pm10" VARCHAR(10),
    "pm2_5" VARCHAR(10),
    "nitrogen_dioxide" VARCHAR(10),
    "sulphur_dioxide" VARCHAR(10),
    "ozone" VARCHAR(10),
    "european_aqi" VARCHAR(10),
    "european_aqi_pm2_5" VARCHAR(10),
    "european_aqi_pm10" VARCHAR(10),
    "european_aqi_nitrogen_dioxide" VARCHAR(10),
    "european_aqi_ozone" VARCHAR(10),
    "european_aqi_sulphur_dioxide" VARCHAR(10)
);

CREATE TABLE rawdata.hourly(
    "time_string" VARCHAR(25) UNIQUE NOT NULL PRIMARY KEY,
    -- "subset" VARCHAR(8) NOT NULL,
    "pm10" VARCHAR(10),
    "pm2_5" VARCHAR(10),
    "nitrogen_dioxide" VARCHAR(10),
    "sulphur_dioxide" VARCHAR(10),
    "ozone" VARCHAR(10),
    "european_aqi" VARCHAR(10),
    "european_aqi_pm2_5" VARCHAR(10),
    "european_aqi_pm10" VARCHAR(10),
    "european_aqi_nitrogen_dioxide" VARCHAR(10),
    "european_aqi_ozone" VARCHAR(10),
    "european_aqi_sulphur_dioxide" VARCHAR(10)
);