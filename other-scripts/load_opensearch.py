"""Load restaurants.json (RestaurantID + Cuisine) into the OpenSearch index "restaurants".

Usage (set these first, never commit them):
    export ES_ENDPOINT='https://search-restaurants-xxxx.us-east-1.es.amazonaws.com'
    export ES_USER='admin'
    export ES_PASS='...'
    python3 load_opensearch.py restaurants.json
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

INDEX = "restaurants"
BATCH = 500


def call(path, body, content_type="application/json"):
    token = base64.b64encode(f"{os.environ['ES_USER']}:{os.environ['ES_PASS']}".encode()).decode()
    req = urllib.request.Request(
        f"{os.environ['ES_ENDPOINT']}{path}",
        data=body,
        headers={"Content-Type": content_type, "Authorization": f"Basic {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        sys.exit(f"OpenSearch error {err.code}: {err.read().decode()[:300]}")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "restaurants.json"
    with open(path) as f:
        restaurants = json.load(f)

    for start in range(0, len(restaurants), BATCH):
        lines = []
        for r in restaurants[start:start + BATCH]:
            lines.append(json.dumps({"index": {"_index": INDEX, "_id": r["RestaurantID"]}}))
            lines.append(json.dumps({"RestaurantID": r["RestaurantID"], "Cuisine": r["Cuisine"]}))
        result = call("/_bulk", ("\n".join(lines) + "\n").encode(), "application/x-ndjson")
        if result.get("errors"):
            sys.exit("Some documents failed to index; check the OpenSearch response.")
        print(f"Indexed {min(start + BATCH, len(restaurants))} / {len(restaurants)}")
    print("Done.")


if __name__ == "__main__":
    main()
