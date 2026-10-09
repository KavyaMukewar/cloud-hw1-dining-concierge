# Dining Concierge Chatbot (Cloud Computing and Big Data, Fall 2026, HW1)

Serverless dining concierge: a chat page on S3 talks to API Gateway and Lambda, which hands off to an Amazon Lex bot. Restaurant suggestions are emailed to the user.

Region for everything: `us-east-1`.

## Repo layout

| Folder | Contents |
|--------|----------|
| `frontend/` | Chat web app (from the course starter), hosted on S3 |
| `lambda-functions/` | One folder per Lambda (`LF0`, later `LF1`, `LF2`) |
| `other-scripts/` | API spec (`swagger.yaml`), Yelp scrape script, OpenSearch loader |

## Architecture

```
S3 website -> API Gateway -> LF0 -> Lex -> LF1 -> SQS (Q1)
                                                   |
                                  EventBridge (1 min) -> LF2 -> OpenSearch + DynamoDB -> SES email
Yelp API -> DynamoDB (yelp-restaurants) + OpenSearch (restaurants index)
```

## Status

| Part | What | Status |
|------|------|--------|
| 1 | Frontend on S3 | Done |
| 2 | API Gateway + LF0 (boilerplate reply) | Done |
| 3 | Lex bot, LF1, SQS | Pending |
| 4 | LF0 calls Lex | Pending |
| 5 | Yelp scrape to DynamoDB | Done |
| 6 | OpenSearch index | Pending |
| 7 | LF2 queue worker + SES | Pending |

## Setup log

### Part 1: Frontend on S3
1. Created a general purpose S3 bucket (public access block turned off).
2. Enabled static website hosting with `chat.html` as the index document.
3. Added a bucket policy allowing public `s3:GetObject` on all objects.
4. Uploaded `frontend/chat.html` and `frontend/assets/`.

### Part 2: API and LF0
1. Created Lambda `LF0` (Python 3.12) returning the canned reply "I'm still under development. Please come back later." in the Lambda proxy response format. Code: `lambda-functions/LF0/lambda_function.py`.
2. Imported `other-scripts/swagger.yaml` into API Gateway as a Regional REST API ("AI Customer Service API").
3. Set the `POST /chatbot` integration to LF0 with Lambda proxy integration enabled.
4. Enabled CORS on `/chatbot` (adds `OPTIONS`).
5. Deployed to a stage named `dev`.
6. Pointed `frontend/assets/js/sdk/apigClient.js` (`invokeUrl`) at the deployed stage, then re-uploaded that file to S3.

### Part 5: Yelp scrape to DynamoDB
1. Created DynamoDB table `yelp-restaurants` (partition key `BusinessID`, on-demand capacity).
2. Created a Yelp app and API key (Base plan). The key is read from the `YELP_API_KEY` environment variable, never stored in the repo.
3. Ran `other-scripts/scrape_yelp.py` in AWS CloudShell. It searched Manhattan for 7 cuisines (chinese, italian, japanese, mexican, indian, thai, korean), skipped duplicate business IDs, and stored 1,325 unique restaurants with BusinessID, Name, Address, Coordinates, NumberOfReviews, Rating, ZipCode, Cuisine and insertedAtTimestamp.
4. The script also wrote `restaurants.json` (RestaurantID + Cuisine) for loading into OpenSearch.

## Secrets

No keys or credentials are stored in this repo. The scrape script reads the Yelp API key from an environment variable.
