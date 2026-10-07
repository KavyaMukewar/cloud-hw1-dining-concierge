import json
from datetime import datetime, timezone


def lambda_handler(event, context):
    reply = {
        "messages": [
            {
                "type": "unstructured",
                "unstructured": {
                    "id": "1",
                    "text": "I'm still under development. Please come back later.",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }
        ]
    }
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
        },
        "body": json.dumps(reply),
    }
