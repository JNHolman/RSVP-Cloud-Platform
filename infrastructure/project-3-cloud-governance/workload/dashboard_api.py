import os
import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("APP_REGION", "us-east-1"))

INCIDENTS_TABLE_NAME = os.environ["INCIDENTS_TABLE"]
COST_TABLE_NAME = os.environ["COST_SUMMARIES_TABLE"]

incidents_table = dynamodb.Table(INCIDENTS_TABLE_NAME)
cost_table = dynamodb.Table(COST_TABLE_NAME)


def _decimal_to_float(obj):
    if isinstance(obj, list):
        return [_decimal_to_float(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


def get_incidents():
    # Simple scan for now; later you can add filters or GSI for "latest"
    resp = incidents_table.scan()
    items = resp.get("Items", [])
    items = _decimal_to_float(items)
    # Sort newest first if you store timestamps later
    return {
        "items": items
    }


def get_cost_summary():
    # For now, just return all; later AI cost Lambda can write one per week
    resp = cost_table.scan()
    items = resp.get("Items", [])
    items = _decimal_to_float(items)
    return {
        "items": items
    }


def handler(event, context):
    route = event.get("requestContext", {}).get("http", {}).get("path", "/")
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")

    if method == "GET" and route == "/incidents":
        body = get_incidents()
        status = 200
    elif method == "GET" and route == "/cost-summary":
        body = get_cost_summary()
        status = 200
    else:
        body = {"message": "Not Found", "path": route, "method": method}
        status = 404

    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body),
    }
