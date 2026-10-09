import base64
import json
import os
import urllib.request
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

sqs = boto3.client("sqs")
ses = boto3.client("ses")
dynamodb = boto3.client("dynamodb")

MAX_MESSAGES = 10
SUGGESTION_COUNT = 3


def pick_restaurant_ids(cuisine):
    query = {
        "size": SUGGESTION_COUNT,
        "query": {
            "function_score": {
                "query": {"match": {"Cuisine": cuisine}},
                "random_score": {},
            }
        },
    }
    url = f"{os.environ['ES_ENDPOINT']}/{os.environ.get('ES_INDEX', 'restaurants')}/_search"
    token = base64.b64encode(f"{os.environ['ES_USER']}:{os.environ['ES_PASS']}".encode()).decode()
    req = urllib.request.Request(
        url,
        data=json.dumps(query).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Basic {token}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        hits = json.load(resp)["hits"]["hits"]
    return [hit["_source"]["RestaurantID"] for hit in hits]


def fetch_details(restaurant_ids):
    if not restaurant_ids:
        return []
    table = os.environ.get("TABLE_NAME", "yelp-restaurants")
    response = dynamodb.batch_get_item(
        RequestItems={table: {"Keys": [{"BusinessID": {"S": rid}} for rid in restaurant_ids]}}
    )
    items = response["Responses"].get(table, [])
    by_id = {item["BusinessID"]["S"]: item for item in items}
    return [by_id[rid] for rid in restaurant_ids if rid in by_id]


def pretty_time(value):
    try:
        return datetime.strptime(value, "%H:%M").strftime("%-I:%M %p")
    except (TypeError, ValueError):
        return value or "your chosen time"


def build_email(request, restaurants):
    cuisine = (request.get("cuisine") or "").capitalize()
    people = request.get("people") or "your"
    lines = [f"Hello! Here are my {cuisine} restaurant suggestions for {people} people, at {pretty_time(request.get('dining_time'))}:", ""]
    for number, item in enumerate(restaurants, start=1):
        name = item["Name"]["S"]
        address = item.get("Address", {}).get("S", "address unavailable")
        lines.append(f"{number}. {name}, located at {address}")
    lines += ["", "Enjoy your meal!"]
    return "\n".join(lines)


def send_email(sender, recipient, body):
    ses.send_email(
        Source=sender,
        Destination={"ToAddresses": [recipient]},
        Message={
            "Subject": {"Data": "Your dining suggestions"},
            "Body": {"Text": {"Data": body}},
        },
    )


def handle_message(message):
    request = json.loads(message["Body"])
    ids = pick_restaurant_ids(request["cuisine"])
    restaurants = fetch_details(ids)
    if restaurants:
        body = build_email(request, restaurants)
    else:
        body = f"Sorry, I couldn't find any {request['cuisine']} restaurants right now. Please try another cuisine."
    send_email(os.environ["SENDER_EMAIL"], request["email"], body)


def lambda_handler(event, context):
    queue_url = os.environ["QUEUE_URL"]
    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=MAX_MESSAGES, WaitTimeSeconds=1)
    processed = 0

    for message in response.get("Messages", []):
        try:
            handle_message(message)
        except (ValueError, KeyError) as err:
            print(f"Dropping bad message {message.get('MessageId')}: {err!r}")
        except ClientError as err:
            code = err.response["Error"]["Code"]
            print(f"AWS error for message {message.get('MessageId')}: {code}")
            if code != "MessageRejected":
                continue
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
        processed += 1

    return {"processed": processed}
