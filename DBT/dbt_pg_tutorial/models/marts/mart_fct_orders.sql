{{ config(materialized='table') }}

select
    i.order_id,
    i.customer_id,
    i.order_timestamp,
    i.status,
    i.total_amount,
    i.total_paid,
    i.payment_count,
    i.outstanding_amount,
    case
        when i.outstanding_amount = 0 and i.total_amount > 0 then true
        else false
    end as is_fully_paid
from {{ ref('int_order_payments') }} AS i