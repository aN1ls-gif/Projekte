WITH 
observed as (
    SELECT * FROM {{ref("int__quality_average")}}
),
predicted as (
    SELECT * FROM {{ref("int__prediction_average")}}
), combined as (
    SELECT * FROM observed
    UNION
    SELECT * FROM predicted
    WHERE predicted."date" not in (SELECT observed."date" FROM observed) AND predicted."hour" not in (SELECT observed."hour" FROM observed)
)
SELECT 
"date",
"hour",
"AVG_pm10",
"AVG_pm2_5",
"AVG_nitrogen_dioxide",
"AVG_sulphur_dioxide",
"AVG_ozone"
FROM combined
ORDER BY "date", "hour"
