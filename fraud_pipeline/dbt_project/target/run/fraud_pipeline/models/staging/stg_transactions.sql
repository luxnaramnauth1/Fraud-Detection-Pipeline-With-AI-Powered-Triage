
  
  create view "fraud_pipeline"."main"."stg_transactions__dbt_tmp" as (
    -- Staging model: light cleaning of raw transaction data.
-- No business logic here -- just type casting, renaming, and basic hygiene.

with source as (
    select * from raw.transactions
),

cleaned as (
    select
        transaction_id,
        customer_id,
        cast(timestamp as timestamp)   as transaction_ts,
        cast(amount as decimal(12, 2)) as amount,
        merchant_category,
        location,
        -- ground-truth label kept only for evaluating our rules later,
        -- NEVER used as an input feature to the flagging logic itself
        is_simulated_fraud
    from source
    where amount > 0  -- drop any malformed zero/negative amounts
)

select * from cleaned
  );
