import os
import boto3
from jinja2 import Template
import snowflake.connector
from snowflake.connector import DictCursor
from crhelper import CfnResource

helper = CfnResource()


def create_cursor():
    return snowflake.connector.connect(
        user=os.getenv("SF_USER"),
        password=os.getenv("PASSWORD"),
        account=os.getenv("ACCOUNT"),
        warehouse=os.getenv("WAREHOUSE"),
        database=os.getenv("DATABASE"),
        schema=os.getenv("SCHEMA"),
    )


def update_api(event):
    client = boto3.client("apigateway")

    f = open("resources/policy.json", "r")
    template = Template(f.read())
    policy = template.render(
        ACCOUNT_ID=event["ResourceProperties"]["AccountId"],
        SNOWFLAKE_IAM_ROLE_NAME=os.getenv("SNOWFLAKE_IAM_ROLE_NAME"),
    )
    f.close()

    client.update_rest_api(
        restApiId=event["ResourceProperties"]["ApiGwId"],
        patchOperations=[
            {
                "op": "replace",
                "path": "/policy",
                "value": str(policy),
            },
        ],
    )
    client.create_deployment(
        restApiId=event["ResourceProperties"]["ApiGwId"],
        stageName=event["ResourceProperties"]["Stage"],
    )


def update_up_snowflake_objects(event):
    f = open("resources/update_resources.sql", "r")
    template = Template(f.read())
    sqls = template.render(
        API_GW_ID=event["ResourceProperties"]["ApiGwId"],
        REGION=event["ResourceProperties"]["Region"],
        STAGE=event["ResourceProperties"]["Stage"],
    ).split(";")
    f.close()
    cursor = create_cursor().cursor(DictCursor)

    for sql in sqls:
        cursor.execute(sql)


@helper.delete
@helper.update
def no_op(_, __):
    pass


@helper.create
def update_resources(event, _):
    update_up_snowflake_objects(event)
    update_api(event)


def handler(event, context):
    helper(event, context)
