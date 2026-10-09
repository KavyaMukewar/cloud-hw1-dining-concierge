import hashlib
import json
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

lex = boto3.client("lexv2-runtime")

HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "*",
}


def respond(status, body):
    return {"statusCode": status, "headers": HEADERS, "body": json.dumps(body)}


def session_id_for(event, client_id=None):
    identity = (event.get("requestContext") or {}).get("identity") or {}
    seed = client_id or f"{identity.get('sourceIp', '')}|{identity.get('userAgent', '')}"
    return hashlib.sha256(seed.encode()).hexdigest()[:32]


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
        unstructured = body["messages"][0]["unstructured"]
        text = unstructured["text"]
        client_id = unstructured.get("id")
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        return respond(400, {"code": 400, "message": "Expected messages[0].unstructured.text"})

    try:
        result = lex.recognize_text(
            botId=os.environ["BOT_ID"],
            botAliasId=os.environ["BOT_ALIAS_ID"],
            localeId=os.environ.get("LOCALE_ID", "en_US"),
            sessionId=session_id_for(event, client_id),
            text=text,
        )
    except ClientError as err:
        return respond(500, {"code": 500, "message": str(err)})

    now = datetime.now(timezone.utc).isoformat()
    replies = [
        {"type": "unstructured", "unstructured": {"id": str(i), "text": m["content"], "timestamp": now}}
        for i, m in enumerate(result.get("messages", []))
    ]
    if not replies:
        replies = [{"type": "unstructured", "unstructured": {"id": "0", "text": "Sorry, I didn't get that.", "timestamp": now}}]
    return respond(200, {"messages": replies})
