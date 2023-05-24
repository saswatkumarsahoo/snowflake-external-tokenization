import os
import boto3
import json
from jinja2 import Template
import snowflake.connector
from snowflake.connector import DictCursor
from crhelper import CfnResource


helper = CfnResource()
iam = boto3.client("iam")
SNOWFLAKE_IAM_ROLE_NAME = os.getenv("SNOWFLAKE_IAM_ROLE_NAME")

trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole",
            "Condition": {"StringEquals": {"sts:ExternalId": "extid"}},
        }
    ],
}


def create_cursor():
    return snowflake.connector.connect(
        user=os.getenv("SF_USER"),
        password=os.getenv("PASSWORD"),
        account=os.getenv("ACCOUNT"),
        warehouse=os.getenv("WAREHOUSE"),
        database=os.getenv("DATABASE"),
        schema=os.getenv("SCHEMA"),
    )


def create_iam_role():
    return iam.create_role(
        RoleName=SNOWFLAKE_IAM_ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description="role for snowflake to assume during api execution",
    )["Role"]


def update_trust_policy():
    iam.update_assume_role_policy(
        RoleName=SNOWFLAKE_IAM_ROLE_NAME, PolicyDocument=json.dumps(trust_policy)
    )


def set_up_snowflake_objects(iam_role):
    f = open("resources/create_resources.sql", "r")
    template = Template(f.read())
    sqls = template.render(IAM_ROLE_ARN=iam_role["Arn"]).split(";")
    f.close()
    cursor = create_cursor().cursor(DictCursor)
    counter = 0
    iam_user, ext_id = None, None
    for sql in sqls:
        cursor.execute(sql)
        counter += 1
        if counter == len(sqls):
            for row in cursor.fetchall():
                if row.get("property") == "API_AWS_IAM_USER_ARN":
                    iam_user = row.get("property_value")
                if row.get("property") == "API_AWS_EXTERNAL_ID":
                    ext_id = row.get("property_value")
    return iam_user, ext_id


@helper.create
def create_resources(event, _):
    # create an IAM role
    iam_role = create_iam_role()
    # set up API integration in snowflake
    iam_user, ext_id = set_up_snowflake_objects(iam_role)

    trust_policy["Statement"][0]["Principal"] = {"AWS": iam_user}
    trust_policy["Statement"][0]["Condition"]["StringEquals"]["sts:ExternalId"] = ext_id

    # update the trust policy based on the API integration object
    update_trust_policy()
    return {"status_code": 200}


@helper.delete
def delete_iam_role(_, __):
    try:
        iam.delete_role(RoleName=SNOWFLAKE_IAM_ROLE_NAME)
        f = open("resources/drop_resources.sql", "r")
        template = Template(f.read())
        sqls = template.render().split(";")
        f.close()
        cursor = create_cursor().cursor(DictCursor)
        for sql in sqls:
            cursor.execute(sql)
    except Exception as e:
        print(e)


@helper.update
def no_op(_, __):
    pass


def handler(event, context):
    helper(event, context)
