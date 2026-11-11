"""Serialize work on one incident and resume notification from a durable checkpoint."""

import json
import time
import uuid


def process(client, table, key, signature, observed, retention_days, investigate, publish, *, cancel_pending=False, event_order=0):
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

    previous_time = float(old.get("event_time", {"N": "0"})["N"])
    previous_order = float(old.get("event_order", {"N": "0"})["N"])
    latest = max((observed, event_order), (previous_time, previous_order))
    stale = (observed, event_order) < (previous_time, previous_order)
    if "pending_notification" in old:
        if cancel_pending and not stale:
            update("REMOVE pending_notification")
        else:
            deliver(json.loads(old["pending_notification"]["S"]))
    if old.get("signature", {}).get("S") == signature or stale:
        result = json.loads(old["result_json"]["S"])
    else:
        result, notification = investigate()
        expression = "SET signature = :sig, result_json = :result, event_time = :stamp, event_order = :seq"
        values = dict(sig={"S": signature}, result={"S": json.dumps(result)}, stamp={"N": str(observed)}, seq={"N": str(event_order)})
        if notification:
            expression += ", pending_notification = :notification"
            values["notification"] = {"S": json.dumps(notification)}
        update(expression, **values)
        if notification:
            deliver(notification)
    update("SET event_time = :stamp, event_order = :seq REMOVE lease_until, lease_owner",
           stamp={"N": str(latest[0])}, seq={"N": str(latest[1])})
    return result
