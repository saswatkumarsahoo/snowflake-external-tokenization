import os
import json
import boto3
from botocore.exceptions import ClientError
from typing import List, Dict

BATCH_SIZE = 100

dynamodb = boto3.resource("dynamodb")
table_name = os.environ.get("TABLE_NAME", "customers")
ddb_table = dynamodb.Table(table_name)


def split_array(keys: List) -> List[List]:
    """splits a list to a small chunks of list

    Args:
        keys (List): input list

    Returns:
        List[List]: list of list with max length of 100
    """
    for i in range(0, len(keys), BATCH_SIZE):
        yield keys[i : i + BATCH_SIZE]


def retrieve_data(keys: List) -> Dict[str, str]:
    """queries dynamodb table using a list of ids

    Args:
        keys (List): list of ids used for querying the table

    Returns:
        Dict[str, str]: dict with id as key & de-tokenized value as value
    """
    responses = []
    try:
        for id_list in split_array(keys):
            responses.extend(
                dynamodb.batch_get_item(RequestItems={table_name: {"Keys": id_list}})[
                    "Responses"
                ][table_name]
            )
    except ClientError:
        raise
    else:
        return {response["id"]: response["value"] for response in responses}


def lambda_handler(event, context):
    print(event)
    # 200 is the HTTP status code for "ok".
    status_code = 200

    # The return value will contain an array of arrays (one inner array per input row).
    array_of_rows_to_return = []
    # From the input parameter named "event", get the body, which contains
    # the input rows.
    event_body = event["body"]

    try:
        # Convert the input from a JSON string into a JSON object.
        payload = json.loads(event_body)
        # This is basically an array of arrays. The inner array contains the
        # row number, and a value for each parameter passed to the function.
        rows = payload["data"]

        # retrieve unmasked data from dynamodb
        detokenized_data = retrieve_data(
            [{"id": value} for value in dict(rows).values()]
        )
        print(detokenized_data)
        for row in rows:
            # Read the input row number (the output row number will be the same).
            row_number = row[0]

            # Read the first input parameter's value. For example, this can be a
            # numeric value or a string, or it can be a compound value such as
            # a JSON structure.
            # Compose the output based on the input
            output_value = detokenized_data.get(row[1], None)

            # Put the returned row number and the returned value into an array.
            row_to_return = [row_number, output_value]

            # ... and add that array to the main array.
            array_of_rows_to_return.append(row_to_return)

        json_compatible_string_to_return = json.dumps({"data": array_of_rows_to_return})

    except Exception as err:
        # 400 implies some type of error.
        status_code = 400
        # Tell caller what this function could not handle.
        json_compatible_string_to_return = event_body

    # Return the return value and HTTP status code.
    return {"statusCode": status_code, "body": json_compatible_string_to_return}
