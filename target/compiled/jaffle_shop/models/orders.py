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


# This part is user provided model code
# you will need to copy the next section to run the code
# COMMAND ----------
# this part is dbt logic for get ref work, do not modify

def ref(*args,dbt_load_df_function):
    refs = {"stg_orders": "jaffle_shop.bruno.stg_orders", "stg_payments": "jaffle_shop.bruno.stg_payments"}
    key = ".".join(args)
    return dbt_load_df_function(refs[key])


def source(*args, dbt_load_df_function):
    sources = {}
    key = ".".join(args)
    return dbt_load_df_function(sources[key])


config_dict = {}


class config:
    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    def get(key, default=None):
        return config_dict.get(key, default)

class this:
    """dbt.this() or dbt.this.identifier"""
    database = 'jaffle_shop'
    schema = 'bruno'
    identifier = 'orders'
    def __repr__(self):
        return 'jaffle_shop.bruno.orders'


class dbtObj:
    def __init__(self, load_df_function) -> None:
        self.source = lambda *args: source(*args, dbt_load_df_function=load_df_function)
        self.ref = lambda *args: ref(*args, dbt_load_df_function=load_df_function)
        self.config = config
        self.this = this()
        self.is_incremental = False

# COMMAND ----------

# To run this in snowsight, you need to select entry point to be main
# And you may have to modify the return type to text to get the result back
# def main(session):
#     dbt = dbtObj(session.table)
#     df = model(dbt, session)
#     return df.collect()

# to run this in local notebook, you need to create a session following examples https://github.com/Snowflake-Labs/sfguide-getting-started-snowpark-python
# then you can do the following to run model
# dbt = dbtObj(session.table)
# df = model(dbt, session)

