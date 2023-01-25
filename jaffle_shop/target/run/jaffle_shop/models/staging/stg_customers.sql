
  create or replace  view jaffle_shop.bruno.stg_customers
  
   as (
    with source as (
    select * from jaffle_shop.bruno.raw_customers

),

renamed as (

    select
        id as customer_id,
        first_name,
        last_name

    from source

)

select * from renamed
  );
