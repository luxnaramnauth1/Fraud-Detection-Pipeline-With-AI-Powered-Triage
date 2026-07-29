
  
  create view "fraud_pipeline"."main"."int_transaction_velocity__dbt_tmp" as (
    -- Intermediate model: flags "velocity" anomalies -- i.e. a customer making
-- multiple transactions in a very short time window, a classic fraud signal
-- (e.g. a stolen card being used rapidly before it's blocked).

with tx as (
    select * from "fraud_pipeline"."main"."stg_transactions"
),

with_lag as (
    select
        transaction_id,
        customer_id,
        transaction_ts,
        lag(transaction_ts) over (
            partition by customer_id order by transaction_ts
        ) as prev_transaction_ts
    from tx
),

with_gap as (
    select
        *,
        date_diff('minute', prev_transaction_ts, transaction_ts) as minutes_since_last_tx
    from with_lag
)

select
    transaction_id,
    customer_id,
    transaction_ts,
    minutes_since_last_tx,
    case
        when minutes_since_last_tx is not null and minutes_since_last_tx <= 10 then true
        else false
    end as is_rapid_repeat
from with_gap
  );
