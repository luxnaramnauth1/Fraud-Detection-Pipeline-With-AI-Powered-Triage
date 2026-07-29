-- Intermediate model: computes each customer's OWN historical transaction
-- behavior (avg amount, stddev, typical location) directly from observed
-- transactions. This is what a real fraud system would use -- comparing
-- new activity against the customer's own baseline, not a fixed threshold.

with tx as (
    select * from "fraud_pipeline"."main"."stg_transactions"
),

customer_stats as (
    select
        customer_id,
        avg(amount)                          as observed_avg_amount,
        stddev(amount)                        as observed_stddev_amount,
        count(*)                              as total_transactions,
        mode() within group (order by location) as most_common_location
    from tx
    group by customer_id
)

select * from customer_stats