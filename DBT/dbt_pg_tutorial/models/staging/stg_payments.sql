{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'payments') }}
),
casted as (
    select
        id           as payment_id,
        order_id,
        lower(payment_method) as payment_method,
        amount::numeric(10,2) as amount,
        paid_at::timestamp    as paid_at
    from source
)
select * from casted