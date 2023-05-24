import os
import boto3
from snowflake.snowpark import Session
from snowflake.snowpark.types import StringType, StructType, StructField
import uuid

from crhelper import CfnResource

helper = CfnResource()


def create_session():
    connection_params = dict(
        user=os.getenv("SF_USER"),
        password=os.getenv("PASSWORD"),
        account=os.getenv("ACCOUNT"),
        role=os.getenv("ROLE"),
        warehouse=os.getenv("WAREHOUSE"),
        database=os.getenv("DATABASE"),
        schema=os.getenv("SCHEMA"),
    )
    return Session.builder.configs(connection_params).create()


@helper.delete
@helper.update
def no_op(_, __):
    pass


@helper.create
def seed_tables(event, context):
    try:
        with open("resources/customers.csv") as file:
            session = create_session()

            schema = StructType(
                [
                    StructField("customer_id", StringType()),
                    StructField("email", StringType()),
                    StructField("tokenized_email", StringType()),
                ]
            )
            data = [
                f"{line.strip()},{str(uuid.uuid4())}".split(",")[:3]
                for line in file.readlines()
            ]
            df = session.create_dataframe(data, schema)
            df.select("customer_id", "tokenized_email").with_column_renamed(
                "tokenized_email", "email"
            ).write.mode("overwrite").save_as_table("customers")

            ddb_table_data = [
                {"id": row["TOKENIZED_EMAIL"], "value": row["EMAIL"]}
                for row in df.collect()
            ]
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table("customers")

            with table.batch_writer() as writer:
                for item in ddb_table_data:
                    writer.put_item(Item=item)
            return {"status_code": 200}
    except Exception:
        return {"status_code": 400}


def handler(event, context):
    helper(event, context)
