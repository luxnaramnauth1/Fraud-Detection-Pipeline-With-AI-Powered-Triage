-- Staging model: light cleaning of raw customer profile data.

with source as (
    select * from raw.customers
),

cleaned as (
    select
        customer_id,
        customer_name,
        home_city,
        cast(avg_transaction_amount as decimal(12, 2)) as avg_transaction_amount,
        cast(account_open_date as date) as account_open_date
    from source
)

select * from cleaned