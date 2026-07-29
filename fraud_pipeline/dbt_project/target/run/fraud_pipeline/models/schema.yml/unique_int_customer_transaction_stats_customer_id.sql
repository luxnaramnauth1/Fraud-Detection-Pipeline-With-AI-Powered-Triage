
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    customer_id as unique_field,
    count(*) as n_records

from "fraud_pipeline"."main"."int_customer_transaction_stats"
where customer_id is not null
group by customer_id
having count(*) > 1



  
  
      
    ) dbt_internal_test