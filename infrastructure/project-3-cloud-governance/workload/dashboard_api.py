import json
import logging
import os
from decimal import Decimal

import boto3

LOGGER = logging.getLogger(__name__)

REGION = os.environ.get("APP_REGION", "us-east-1")
INCIDENTS_TABLE_NAME = os.environ["INCIDENTS_TABLE"]
COST_TABLE_NAME = os.environ["COST_SUMMARIES_TABLE"]
SECURITY_READ_ROLE_ARN = os.environ["SECURITY_READ_ROLE_ARN"]
FINOPS_READ_ROLE_ARN = os.environ["FINOPS_READ_ROLE_ARN"]
MAX_ITEMS = int(os.environ.get("MAX_ITEMS", "50"))
ALLOWED_ORIGINS = {
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
}

sts = boto3.client("sts", region_name=REGION)


def _assumed_dynamodb(role_arn, session_name):
    response = sts.assume_role(RoleArn=role_arn, RoleSessionName=session_name)
    creds = response["Credentials"]
    return boto3.resource(
        "dynamodb",
        region_name=REGION,
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
    )


def _json_safe(value):
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, Decimal):
        return float(value)
    return value


def _query_recent(table, index_name, record_type):
    response = table.query(
        IndexName=index_name,
        KeyConditionExpression="record_type = :record_type",
        ExpressionAttributeValues={":record_type": record_type},
        ScanIndexForward=False,
        Limit=MAX_ITEMS,
    )
    return _json_safe(response.get("Items", []))


def _response(event, status_code, body):
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
        "Referrer-Policy": "no-referrer",
    }

    origin = (event.get("headers") or {}).get("origin") or (event.get("headers") or {}).get("Origin")
    if origin in ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Vary"] = "Origin"

    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps(body),
    }


def handler(event, context):
    resource = event.get("resource", "")
    method = event.get("httpMethod", "")

    if method != "GET":
        return _response(event, 405, {"message": "Method Not Allowed"})

    try:
        if resource == "/incidents":
            dynamodb = _assumed_dynamodb(SECURITY_READ_ROLE_ARN, "dashboard-security-read")
            items = _query_recent(
                dynamodb.Table(INCIDENTS_TABLE_NAME), "by_updated_at", "incident"
            )
            return _response(event, 200, {"items": items})

        if resource == "/cost-summary":
            dynamodb = _assumed_dynamodb(FINOPS_READ_ROLE_ARN, "dashboard-finops-read")
            items = _query_recent(
                dynamodb.Table(COST_TABLE_NAME), "by_generated_at", "weekly_cost"
            )
            return _response(event, 200, {"items": items})
    except Exception:
        # Backend account/service failures must not expose role, table, or AWS error
        # details to an authenticated browser client. Preserve the stack trace only
        # in CloudWatch Logs for operators.
        LOGGER.exception("Dashboard backend dependency failed")
        return _response(event, 503, {"message": "Service Unavailable"})

    return _response(event, 404, {"message": "Not Found"})
