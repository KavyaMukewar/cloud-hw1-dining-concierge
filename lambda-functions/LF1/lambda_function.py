import json
import os
import re

import boto3

sqs = boto3.client("sqs")

VALID_LOCATIONS = {"manhattan", "new york", "new york city", "nyc", "manhattan ny", "manhattan, ny"}
VALID_CUISINES = {"chinese", "italian", "japanese", "mexican", "indian", "thai", "korean"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def slot_value(slots, name):
    slot = (slots or {}).get(name)
    if not slot or not slot.get("value"):
        return None
    return slot["value"].get("interpretedValue") or slot["value"].get("originalValue")


def messages(text):
    return [{"contentType": "PlainText", "content": text}]


def close(intent, text):
    intent["state"] = "Fulfilled"
    return {
        "sessionState": {"dialogAction": {"type": "Close"}, "intent": intent},
        "messages": messages(text),
    }


def delegate(intent):
    return {"sessionState": {"dialogAction": {"type": "Delegate"}, "intent": intent}}


def elicit(intent, slot, text):
    intent["slots"][slot] = None
    return {
        "sessionState": {
            "dialogAction": {"type": "ElicitSlot", "slotToElicit": slot},
            "intent": intent,
        },
        "messages": messages(text),
    }


def validate(intent):
    slots = intent["slots"]

    location = slot_value(slots, "Location")
    if location and location.strip().lower() not in VALID_LOCATIONS:
        return elicit(intent, "Location", f"Sorry, I can't fulfill requests for {location}. Please enter a valid location.")

    cuisine = slot_value(slots, "Cuisine")
    if cuisine and cuisine.strip().lower() not in VALID_CUISINES:
        return elicit(intent, "Cuisine", "Sorry, I only know Chinese, Italian, Japanese, Mexican, Indian, Thai and Korean. Which one would you like?")

    people = slot_value(slots, "NumberOfPeople")
    if people is not None:
        try:
            count = int(float(people))
        except ValueError:
            count = 0
        if count < 1 or count > 20:
            return elicit(intent, "NumberOfPeople", "Please enter a party size between 1 and 20.")

    email = slot_value(slots, "Email")
    if email and not EMAIL_RE.match(email.strip()):
        return elicit(intent, "Email", "That doesn't look like a valid email address. Could you enter it again?")

    return delegate(intent)


def handle_dining(event):
    intent = event["sessionState"]["intent"]
    if event["invocationSource"] == "DialogCodeHook":
        return validate(intent)

    slots = intent["slots"]
    request = {
        "location": slot_value(slots, "Location"),
        "cuisine": slot_value(slots, "Cuisine"),
        "dining_time": slot_value(slots, "DiningTime"),
        "people": slot_value(slots, "NumberOfPeople"),
        "email": slot_value(slots, "Email"),
    }
    sqs.send_message(QueueUrl=os.environ["QUEUE_URL"], MessageBody=json.dumps(request))
    return close(intent, "You're all set. Expect my suggestions shortly! Have a good day.")


def lambda_handler(event, context):
    intent = event["sessionState"]["intent"]
    name = intent["name"]

    if name == "GreetingIntent":
        return close(intent, "Hi there, how can I help?")
    if name == "ThankYouIntent":
        return close(intent, "You're welcome!")
    if name == "DiningSuggestionsIntent":
        return handle_dining(event)
    return close(intent, "Sorry, I didn't catch that. I can help you find restaurant suggestions.")
