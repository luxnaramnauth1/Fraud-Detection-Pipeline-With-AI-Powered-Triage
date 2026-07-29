
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select flag_count
from "fraud_pipeline"."main"."flagged_transactions"
where flag_count is null



  
  
      
    ) dbt_internal_test