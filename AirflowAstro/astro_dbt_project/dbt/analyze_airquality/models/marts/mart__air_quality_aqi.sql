WITH 
observed as (
    SELECT * FROM {{ref("int__quality_danger")}}
),
predicted as (
    SELECT * FROM {{ref("int__prediction_danger")}}
), combined as (
    SELECT * FROM observed
    UNION
    SELECT * FROM predicted
    WHERE predicted."date" not in (SELECT observed."date" FROM observed) AND predicted."hour" not in (SELECT observed."hour" FROM observed) 
)
SELECT 
"date",
"hour",
("AVG_overall_aqi_class"),
"AVG_pm10_aqi_class",
"AVG_pm2_5_aqi_class",
"AVG_nitrogen_dioxide_aqi_class",
"AVG_sulphur_dioxide_aqi_class",
"AVG_ozone_aqi_class"
FROM combined
ORDER BY "date", "hour"