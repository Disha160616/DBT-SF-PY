import snowflake.snowpark.functions as F

def model(dbt, session):

    stg_orders = dbt.ref('stg_orders')
    stg_payments = dbt.ref('stg_payments')

    payment_methods = ['credit_card', 'coupon', 'bank_transfer', 'gift_card']

    agg_list = [F.sum(F.when(stg_payments.payment_method == payment_method, stg_payments.amount).otherwise(0)).alias(payment_method + "_amount") for payment_method in payment_methods]

    agg_list.append(F.sum(F.col("amount")).alias("total_amount"))

    order_payments = (
        stg_payments
        .group_by("order_id")
        .agg(*agg_list)
    )

    final_df = (
        stg_orders
        .join(order_payments, stg_orders.order_id == order_payments.order_id, "left")
        .select(stg_orders.order_id.alias("order_id"),
                stg_orders.customer_id.alias("customer_id"),
                stg_orders.order_date.alias("order_date"),
                stg_orders.status.alias("status"),
                *[F.col(payment_method + "_amount") for payment_method in payment_methods],
                order_payments.total_amount.alias("amount")
        )
    )

    return final_df




