{{config(materialized = "view")}}

-- sqlite does not have a dedicated date/time format. However, it can handle date or time-strings if they are formated in a specific manner.
-- YYYY-MM-DD
-- HH:MM
-- YYYY-MM-DDTHH:MM

WITH source AS (
    SELECT * FROM {{source("rawdata", "current")}}
),
updated AS (
    SELECT 
    TO_DATE(SPLIT_PART(time_string, 'T', 1), 'YYYY-MM-DD') as "date",
    CAST(SPLIT_PART(time_string, 'T', 2) as time) as "hour",
    CAST("european_aqi" AS NUMERIC) AS "overall_aqi",
    CAST("pm10" AS NUMERIC),
    CAST("pm2_5" AS NUMERIC),
    CAST("nitrogen_dioxide" AS NUMERIC),
    CAST("sulphur_dioxide" AS NUMERIC),
    CAST("ozone" AS NUMERIC),
    CAST("european_aqi_pm2_5" AS NUMERIC) AS "pm2_5_aqi",
    CAST("european_aqi_pm10" AS NUMERIC) AS "pm10_aqi",
    CAST("european_aqi_nitrogen_dioxide" AS NUMERIC) AS "nitrogen_dioxide_aqi",
    CAST("european_aqi_ozone" AS NUMERIC) AS "ozone_aqi",
    CAST("european_aqi_sulphur_dioxide" AS NUMERIc) as "sulphur_dioxide_aqi"
    FROM source
)
SELECT * FROM updated