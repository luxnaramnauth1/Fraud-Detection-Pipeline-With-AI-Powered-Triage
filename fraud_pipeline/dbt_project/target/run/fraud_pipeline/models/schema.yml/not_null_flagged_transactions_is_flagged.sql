
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select is_flagged
from "fraud_pipeline"."main"."flagged_transactions"
where is_flagged is null



  
  
      
    ) dbt_internal_test