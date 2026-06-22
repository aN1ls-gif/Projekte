{{config(materialized = "view")}}

WITH payments AS (
    SELECT
    order_id,
    SUM(amount) as total_paid,
    COUNT(*) as payment_count
    FROM {{ref("stg_payments")}} -- whatever the output of stg_payments.sql is
    group by order_id
)

SELECT
o.order_id,
o.customer_id,
o.order_timestamp,
o.status,
o.total_amount,
coalesce(p.total_paid, 0) as total_paid, -- coalesce returns the first non-null value. inother words: if p.total_paid is NULL return 0
coalesce(p.payment_count, 0) as payment_count,
(o.total_amount - coalesce(p.total_paid, 0)) as outstanding_amount
-- whatever the output of stf_orders.sql is
FROM {{ref("stg_orders")}} AS o 
left join payments AS p on o.order_id = p.order_id