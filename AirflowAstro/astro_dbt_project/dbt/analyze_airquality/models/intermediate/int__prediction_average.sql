WITH source AS (
    SELECT 
    "date",
    "hour",
    "pm10",
    "pm2_5",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone"
    FROM {{ref("stg_hourly")}}
), -- SELECT ALL non-aqi columns from the stagging layer
moving_average_ranked AS (
    SELECT
    "date",
    "hour",
    AVG("pm10") OVER (PARTITION BY "date" ORDER BY "hour" ASC ROWS BETWEEN 12 PRECEDING AND CURRENT ROW) AS "AVG_pm10",
    AVG("pm2_5") OVER (PARTITION BY "date" ORDER BY "hour" ASC ROWS BETWEEN 12 PRECEDING AND CURRENT ROW) AS "AVG_pm2_5",
    AVG("nitrogen_dioxide") OVER (PARTITION BY "date" ORDER BY "hour" ASC ROWS BETWEEN 12 PRECEDING AND CURRENT ROW) AS "AVG_nitrogen_dioxide",
    AVG("sulphur_dioxide") OVER (PARTITION BY "date" ORDER BY "hour" ASC ROWS BETWEEN 12 PRECEDING AND CURRENT ROW) AS "AVG_sulphur_dioxide",
    AVG("ozone") OVER (PARTITION BY "date" ORDER BY "hour" ASC ROWS BETWEEN 12 PRECEDING AND CURRENT ROW) AS "AVG_ozone",
    ROW_NUMBER() OVER (PARTITION BY "date" ORDER BY "hour" ASC) AS "row_number" 
    FROM source
) -- Calculate the Moving Average for the columns, seperated by day with a 12 sample window
SELECT * FROM moving_average_ranked
WHERE "row_number" = 12 OR "row_number" = 24 -- select only the first and the last moving average (from 00:00 - 12:00 and from 12:00-23:00)