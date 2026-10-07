"""Collect Manhattan restaurants from the Yelp API and store them in DynamoDB.

Usage:
    export YELP_API_KEY='...'
    python3 scrape_yelp.py

Also writes restaurants.json (RestaurantID + Cuisine) for loading into OpenSearch.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal

import boto3

CUISINES = ["chinese", "italian", "japanese", "mexican", "indian", "thai", "korean"]
PER_CUISINE = 200
PAGE_SIZE = 50
LOCATION = "Manhattan, NY"
TABLE_NAME = "yelp-restaurants"
REGION = "us-east-1"
YELP_URL = "https://api.yelp.com/v3/businesses/search"


def search_yelp(api_key, cuisine, offset):
    params = urllib.parse.urlencode({
        "term": f"{cuisine} restaurants",
        "location": LOCATION,
        "limit": PAGE_SIZE,
        "offset": offset,
    })
    req = urllib.request.Request(
        f"{YELP_URL}?{params}", headers={"Authorization": f"Bearer {api_key}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp).get("businesses", [])
    except urllib.error.HTTPError as err:
        print(f"Yelp error {err.code}: {err.read().decode()[:300]}")
        sys.exit(1)


def to_item(biz, cuisine):
    coords = biz.get("coordinates") or {}
    loc = biz.get("location") or {}
    return {
        "BusinessID": biz["id"],
        "Name": biz.get("name", ""),
        "Address": ", ".join(loc.get("display_address") or []),
        "Coordinates": {
            "latitude": Decimal(str(coords.get("latitude") or 0)),
            "longitude": Decimal(str(coords.get("longitude") or 0)),
        },
        "NumberOfReviews": int(biz.get("review_count") or 0),
        "Rating": Decimal(str(biz.get("rating") or 0)),
        "ZipCode": loc.get("zip_code") or "",
        "Cuisine": cuisine,
        "insertedAtTimestamp": datetime.now(timezone.utc).isoformat(),
    }


def main():
    api_key = os.environ.get("YELP_API_KEY")
    if not api_key:
        sys.exit("Set YELP_API_KEY first: export YELP_API_KEY='your key'")

    table = boto3.resource("dynamodb", region_name=REGION).Table(TABLE_NAME)
    seen = set()
    handoff = []

    for cuisine in CUISINES:
        added = 0
        for offset in range(0, PER_CUISINE, PAGE_SIZE):
            businesses = search_yelp(api_key, cuisine, offset)
            if not businesses:
                break
            with table.batch_writer() as batch:
                for biz in businesses:
                    if biz["id"] in seen:
                        continue
                    seen.add(biz["id"])
                    batch.put_item(Item=to_item(biz, cuisine))
                    handoff.append({"RestaurantID": biz["id"], "Cuisine": cuisine})
                    added += 1
            time.sleep(0.3)
        print(f"{cuisine}: added {added} (total unique so far: {len(seen)})")

    with open("restaurants.json", "w") as f:
        json.dump(handoff, f)
    print(f"Done. {len(seen)} unique restaurants stored in {TABLE_NAME}.")
    print("Wrote restaurants.json")


if __name__ == "__main__":
    main()
