WITH source AS (
    SELECT 
    "date",
    "hour",
    "overall_aqi",
    "pm2_5_aqi",
    "pm10_aqi",
    "nitrogen_dioxide_aqi",
    "ozone_aqi",
    "sulphur_dioxide_aqi"
    FROM {{ref("stg_hourly")}}
), classes AS (
    SELECT 
    "date",
    "hour",
    CASE 
        WHEN "overall_aqi" >= 0 AND "overall_aqi" < 20 THEN 1
        WHEN "overall_aqi" >= 20 AND "overall_aqi" < 40 THEN 2
        WHEN "overall_aqi" >= 40 AND "overall_aqi" < 60 THEN 3
        WHEN "overall_aqi" >= 60 AND "overall_aqi" < 80 THEN 4
        WHEN "overall_aqi" >= 80 AND "overall_aqi" < 100 THEN 5
        ELSE 6
        END AS "overall_aqi_class",
    CASE
        WHEN "pm2_5_aqi" >= 0 AND "pm2_5_aqi" < 10 THEN 1
        WHEN "pm2_5_aqi" >= 10 AND "pm2_5_aqi" < 20 THEN 2
        WHEN "pm2_5_aqi" >= 20 AND "pm2_5_aqi" < 35 THEN 3
        WHEN "pm2_5_aqi" >= 25 AND "pm2_5_aqi" < 50 THEN 4
        WHEN "pm2_5_aqi" >= 50 AND "pm2_5_aqi" < 75 THEN 5
        ELSE 6
        END AS "pm2_5_aqi_class",
    CASE 
        WHEN "pm10_aqi" >= 0 AND "pm10_aqi" < 20 THEN 1
        WHEN "pm10_aqi" >= 20 AND "pm10_aqi" < 40 THEN 2
        WHEN "pm10_aqi" >= 40 AND "pm10_aqi" < 50 THEN 3
        WHEN "pm10_aqi" >= 50 AND "pm10_aqi" < 100 THEN 4
        WHEN "pm10_aqi" >= 100 AND "pm10_aqi" < 150 THEN 5
        ELSE 6
        END AS "pm10_aqi_class",
    CASE 
        WHEN "nitrogen_dioxide_aqi" >= 0 AND "nitrogen_dioxide_aqi" < 40 THEN 1
        WHEN "nitrogen_dioxide_aqi" >= 40 AND "nitrogen_dioxide_aqi" < 90 THEN 2
        WHEN "nitrogen_dioxide_aqi" >= 90 AND "nitrogen_dioxide_aqi" < 120 THEN 3
        WHEN "nitrogen_dioxide_aqi" >= 120 AND "nitrogen_dioxide_aqi" < 230 THEN 4
        WHEN "nitrogen_dioxide_aqi" >= 230 AND "nitrogen_dioxide_aqi" < 340 THEN 5
        ELSE 6
        END AS "nitrogen_dioxide_aqi_class",
    CASE 
        WHEN "ozone_aqi" >= 0 AND "ozone_aqi" < 50 THEN 1
        WHEN "ozone_aqi" >= 50 AND "ozone_aqi" < 100 THEN 2
        WHEN "ozone_aqi" >= 100 AND "ozone_aqi" < 130 THEN 3
        WHEN "ozone_aqi" >= 130 AND "ozone_aqi" < 240 THEN 4
        WHEN "ozone_aqi" >= 240 AND "ozone_aqi" < 380 THEN 5
        ELSE 6
        END AS "ozone_aqi_class",
    CASE 
        WHEN "sulphur_dioxide_aqi" >= 0 AND "sulphur_dioxide_aqi" < 100 THEN 1
        WHEN "sulphur_dioxide_aqi" >= 100 AND "sulphur_dioxide_aqi" < 200 THEN 2
        WHEN "sulphur_dioxide_aqi" >= 200 AND "sulphur_dioxide_aqi" < 350 THEN 3
        WHEN "sulphur_dioxide_aqi" >= 350 AND "sulphur_dioxide_aqi" < 500 THEN 4
        WHEN "sulphur_dioxide_aqi" >= 500 AND "sulphur_dioxide_aqi" < 750 THEN 5
        ELSE 6
        END AS "sulphur_dioxide_aqi_class"
    FROM source
), moving_average_ranked AS (
    SELECT 
    "date",
    "hour",
    AVG("overall_aqi_class") OVER (PARTITION BY "date" ORDER BY "hour" ASC ROWS BETWEEN 12 PRECEDING AND CURRENT ROW) AS "AVG_overall_aqi_class",
    AVG("pm10_aqi_class") OVER (PARTITION BY "date" ORDER BY "hour" ASC ROWS BETWEEN 12 PRECEDING AND CURRENT ROW) AS "AVG_pm10_aqi_class", 
    AVG("pm2_5_aqi_class") OVER (PARTITION BY "date" ORDER BY "hour" ASC ROWS BETWEEN 12 PRECEDING AND CURRENT ROW) AS "AVG_pm2_5_aqi_class", 
    AVG("nitrogen_dioxide_aqi_class") OVER (PARTITION BY "date" ORDER BY "hour" ASC ROWS BETWEEN 12 PRECEDING AND CURRENT ROW) AS "AVG_nitrogen_dioxide_aqi_class", 
    AVG("sulphur_dioxide_aqi_class") OVER (PARTITION BY "date" ORDER BY "hour" ASC ROWS BETWEEN 12 PRECEDING AND CURRENT ROW) AS "AVG_sulphur_dioxide_aqi_class", 
    AVG("ozone_aqi_class") OVER (PARTITION BY "date" ORDER BY "hour" ASC ROWS BETWEEN 12 PRECEDING AND CURRENT ROW) AS "AVG_ozone_aqi_class",
    ROW_NUMBER() OVER (PARTITION BY "date" ORDER BY "hour" ASC) AS "row_number" 
    FROM classes
) -- Calculate the Moving Average for the columns, seperated by day with a 12 sample window
SELECT * FROM moving_average_ranked
WHERE "row_number" = 12 OR "row_number" = 24 -- select only the first and the last moving average (from 00:00 - 12:00 and from 12:00-23:00)
