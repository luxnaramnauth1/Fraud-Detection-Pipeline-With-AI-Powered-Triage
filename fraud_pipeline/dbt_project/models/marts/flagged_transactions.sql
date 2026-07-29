-- Final mart: applies rule-based fraud-flagging logic by combining
-- transaction data with customer behavioral baselines and velocity checks.
--
-- Three independent rules, each mirroring a real-world fraud signal:
--   1. HIGH_AMOUNT     -- transaction is far above the customer's own average
--   2. UNUSUAL_LOCATION -- transaction location differs from the customer's typical location
--   3. RAPID_REPEAT    -- multiple transactions in a very short window
--
-- A transaction is flagged if it trips ANY rule. flag_count shows how many
-- rules it tripped, which is useful for risk-prioritizing the review queue.

with tx as (
    select * from {{ ref('stg_transactions') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

stats as (
    select * from {{ ref('int_customer_transaction_stats') }}
),

velocity as (
    select * from {{ ref('int_transaction_velocity') }}
),

joined as (
    select
        tx.transaction_id,
        tx.customer_id,
        tx.transaction_ts,
        tx.amount,
        tx.merchant_category,
        tx.location,
        customers.home_city,
        stats.observed_avg_amount,
        stats.observed_stddev_amount,
        velocity.is_rapid_repeat,
        tx.is_simulated_fraud  -- kept only for evaluation, see docs
    from tx
    left join customers  on tx.customer_id = customers.customer_id
    left join stats       on tx.customer_id = stats.customer_id
    left join velocity    on tx.transaction_id = velocity.transaction_id
),

flagged as (
    select
        *,
        (amount > observed_avg_amount + 3 * coalesce(observed_stddev_amount, 0))
            as flag_high_amount,

        (location != home_city)
            as flag_unusual_location,

        coalesce(is_rapid_repeat, false)
            as flag_rapid_repeat
    from joined
)

select
    transaction_id,
    customer_id,
    transaction_ts,
    amount,
    merchant_category,
    location,
    home_city,
    flag_high_amount,
    flag_unusual_location,
    flag_rapid_repeat,
    (
        cast(flag_high_amount as int) +
        cast(flag_unusual_location as int) +
        cast(flag_rapid_repeat as int)
    ) as flag_count,
    (flag_high_amount or flag_unusual_location or flag_rapid_repeat) as is_flagged,
    is_simulated_fraud
from flagged
order by flag_count desc, transaction_ts desc
