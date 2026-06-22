{{config(materialized = "view")}}

WITH source AS (
    SELECT * FROM {{source("raw", "orders")}}
),
casted AS (
    SELECT
    id AS order_id,
    user_id AS customer_id,
    order_date::timestamp AS order_timestamp, -- type conversion to timestamp
    LOWER(status) as status,
    total_amount::numeric(10, 2) AS total_amount -- type conversion to numeric
    FROM source 
)
SELECT * FROM casted