import snowflake.snowpark.functions as F

def model(dbt, session):

    stg_customers = dbt.ref('stg_customers')
    stg_orders = dbt.ref('stg_orders')
    stg_payments = dbt.ref('stg_payments')

    customer_orders = (
        stg_orders
        .group_by("customer_id")
        .agg(
            F.min(F.col("order_date")).alias('first_order'),
            F.max(F.col("order_date")).alias('most_recent_order'),
            F.count(F.col("order_id")).alias('number_of_orders')
        )
    )

    customer_payments = (
        stg_payments
        .join(stg_orders, stg_payments.order_id == stg_orders.order_id, "left")
        .group_by(stg_orders.customer_id)
        .agg(
            F.sum(F.col("amount")).alias('total_amount')
        )
    )

    final_df = (
        stg_customers
        .join(customer_orders, stg_customers.customer_id == customer_orders.customer_id, "left")
        .join(customer_payments, stg_customers.customer_id == customer_payments.customer_id, "left")
        .select(stg_customers.customer_id.alias("customer_id"),
                stg_customers.first_name.alias("first_name"),
                stg_customers.last_name.alias("last_name"),
                customer_orders.first_order.alias("first_order"),
                customer_orders.most_recent_order.alias("most_recent_order"),
                customer_orders.number_of_orders.alias("number_of_orders"),
                customer_payments.total_amount.alias("customer_lifetime_value")
        )
    )

    return final_df