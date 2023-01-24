
  
    
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


# This part is user provided model code
# you will need to copy the next section to run the code
# COMMAND ----------
# this part is dbt logic for get ref work, do not modify

def ref(*args,dbt_load_df_function):
    refs = {"stg_customers": "jaffle_shop.bruno.stg_customers", "stg_orders": "jaffle_shop.bruno.stg_orders", "stg_payments": "jaffle_shop.bruno.stg_payments"}
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
    identifier = 'customers'
    def __repr__(self):
        return 'jaffle_shop.bruno.customers'


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


def materialize(session, df, target_relation):
    # make sure pandas exists
    import importlib.util
    package_name = 'pandas'
    if importlib.util.find_spec(package_name):
        import pandas
        if isinstance(df, pandas.core.frame.DataFrame):
          # session.write_pandas does not have overwrite function
          df = session.createDataFrame(df)
    df.write.mode("overwrite").save_as_table("jaffle_shop.bruno.customers", create_temp_table=False)

def main(session):
    dbt = dbtObj(session.table)
    df = model(dbt, session)
    materialize(session, df, dbt.this)
    return "OK"

  