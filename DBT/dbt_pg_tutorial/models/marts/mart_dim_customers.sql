{{ config(materialized='table') }}

select
    c.customer_id,
    initcap(c.first_name) as first_name,
    initcap(c.last_name)  as last_name,
    c.email,
    c.created_at
from {{ ref('stg_customers') }} as c