import snowflake.snowpark.functions as F

def model(dbt, session):

    stg_customers_df = dbt.ref('stg_customers')
    stg_orders_df = dbt.ref('stg_orders')
    stg_payments_df = dbt.ref('stg_payments')

    customer_orders_df = (
        stg_orders_df
        .group_by("customer_id")
        .agg(
            F.min(F.col("order_date")).alias('first_order'),
            F.max(F.col("order_date")).alias('most_recent_order'),
            F.count(F.col("order_id")).alias('number_of_orders')
        )
    )

    customer_payments_df = (
        stg_payments_df
        .join(stg_orders_df, stg_payments_df.order_id == stg_orders_df.order_id, "left")
        .group_by(stg_orders_df.customer_id)
        .agg(
            F.sum(F.col("amount")).alias('total_amount')
        )
    )

    final_df = (
        stg_customers_df
        .join(customer_orders_df, stg_customers_df.customer_id == customer_orders_df.customer_id, "left")
        .join(customer_payments_df, stg_customers_df.customer_id == customer_payments_df.customer_id, "left")
        .select(stg_customers_df.customer_id.alias("customer_id"),
                stg_customers_df.first_name.alias("first_name"),
                stg_customers_df.last_name.alias("last_name"),
                customer_orders_df.first_order.alias("first_order"),
                customer_orders_df.most_recent_order.alias("most_recent_order"),
                customer_orders_df.number_of_orders.alias("number_of_orders"),
                customer_payments_df.total_amount.alias("customer_lifetime_value")
        )
    )

    return final_df