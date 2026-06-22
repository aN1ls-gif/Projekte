{{config(materialized = "view")}}

-- The input is "source" by default. This source is our database. 
-- With the first select statement, I SELECT all rows and columns from the "customer" table within the "raw" schema. This first temporary view is supposed to be treated as "source" for the rest of this query
WITH source AS (
    SELECT * FROM {{source("raw", "customers")}}
),
-- Create a second temporary view for this query "renamed". We take all the columns from the "source" view and rename all but the last one. Also, the strings in the "first_name", "last_name" and "email" column are modified to not begin or end with whitespace-charaters and be all lowercase
renamed AS (
    SELECT
    id AS customer_id,
    LOWER(TRIM(first_name)) as first_name,
    LOWER(TRIM(last_name)) as last_name,
    LOWER(TRIM(email)) as email,
    created_at
    FROM source
)
-- give out everyhing from the second temporary view.
SELECT * FROM renamed