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


# This part is user provided model code
# you will need to copy the next section to run the code
# COMMAND ----------
# this part is dbt logic for get ref work, do not modify

def ref(*args, **kwargs):
    refs = {"stg_customers": "metrics.dbt_drani.stg_customers", "stg_orders": "metrics.dbt_drani.stg_orders", "stg_payments": "metrics.dbt_drani.stg_payments"}
    key = '.'.join(args)
    version = kwargs.get("v") or kwargs.get("version")
    if version:
        key += f".v{version}"
    dbt_load_df_function = kwargs.get("dbt_load_df_function")
    return dbt_load_df_function(refs[key])


def source(*args, dbt_load_df_function):
    sources = {}
    key = '.'.join(args)
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
    database = "metrics"
    schema = "dbt_drani"
    identifier = "customers"
    
    def __repr__(self):
        return 'metrics.dbt_drani.customers'


class dbtObj:
    def __init__(self, load_df_function) -> None:
        self.source = lambda *args: source(*args, dbt_load_df_function=load_df_function)
        self.ref = lambda *args, **kwargs: ref(*args, **kwargs, dbt_load_df_function=load_df_function)
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

