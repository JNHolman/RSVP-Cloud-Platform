"""Serialize work on one incident and resume notification from a durable checkpoint."""

import json
import time
import uuid


def process(client, table, key, signature, observed, retention_days, investigate, publish):
    # Both functions have a 45-second invocation limit. A dead worker's lease
    # expires before the normal second async retry.
    now = int(time.time())
    owner = {"S": uuid.uuid4().hex}
    record = {"TableName": table, "Key": key}
    old = client.update_item(
        **record,
        ConditionExpression="attribute_not_exists(lease_until) OR lease_until < :now",
        UpdateExpression="SET lease_until = :until, lease_owner = :owner, expires_at = :ttl",
        ExpressionAttributeValues={
            ":now": {"N": str(now)}, ":until": {"N": str(now + 50)},
            ":owner": owner, ":ttl": {"N": str(now + retention_days * 86400)},
        },
        ReturnValues="ALL_OLD",
    ).get("Attributes", {})

    def update(expression, **values):
        client.update_item(
            **record, UpdateExpression=expression,
            ConditionExpression="lease_owner = :owner",
            ExpressionAttributeValues={":owner": owner, **{":" + k: v for k, v in values.items()}},
        )

    def deliver(notification):
        publish(**notification)
        # Standard SNS cannot atomically acknowledge this DynamoDB write.
        update("REMOVE pending_notification")

    if "pending_notification" in old:
        deliver(json.loads(old["pending_notification"]["S"]))
    previous_time = float(old.get("event_time", {"N": "0"})["N"])
    if old.get("signature", {}).get("S") == signature or observed < previous_time:
        result = json.loads(old["result_json"]["S"])
    else:
        result, notification = investigate()
        expression = "SET signature = :sig, result_json = :result, event_time = :stamp"
        values = dict(sig={"S": signature}, result={"S": json.dumps(result)}, stamp={"N": str(observed)})
        if notification:
            expression += ", pending_notification = :notification"
            values["notification"] = {"S": json.dumps(notification)}
        update(expression, **values)
        if notification:
            deliver(notification)
    update("SET event_time = :stamp REMOVE lease_until, lease_owner",
           stamp={"N": str(max(previous_time, observed))})
    return result
