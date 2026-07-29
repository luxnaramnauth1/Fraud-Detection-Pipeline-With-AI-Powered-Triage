
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select customer_id
from "fraud_pipeline"."main"."int_customer_transaction_stats"
where customer_id is null



  
  
      
    ) dbt_internal_test