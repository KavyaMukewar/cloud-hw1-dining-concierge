# Cloud Computing Fall 2026 - HW 1

## Team Details
- Kavya Mukewar - krm9909
- Ananya Singh - as21114

## Dining Concierge Chatbot
Built as part of the Cloud Computing and Big Data course (Fall 2026).

## Architecture
- **Frontend:** Static website hosted on AWS S3
- **API:** AWS API Gateway with Swagger-defined endpoints
- **Chat Processing:** Lambda (LF0) forwards user messages to Amazon Lex
- **Chatbot:** Amazon Lex handles the conversation with three intents: GreetingIntent, ThankYouIntent and DiningSuggestionsIntent
- **Validation & Logic:** Lambda (LF1) serves as a Lex code hook for slot validation and pushes completed requests to SQS
- **Data Pipeline:** Yelp API → DynamoDB (full restaurant details) + OpenSearch (RestaurantID + Cuisine for search)
- **Suggestions Module:** Lambda (LF2) polls SQS every minute via EventBridge, queries OpenSearch and DynamoDB, and emails recommendations via SES

## How It Works
1. The user chats with the bot through the S3-hosted frontend.
2. API Gateway routes messages to LF0, which forwards them to Lex.
3. Lex identifies the user's intent and collects preferences (location, cuisine, dining time, number of people, email).
4. LF1 validates the inputs and pushes the request to an SQS queue.
5. LF2 (triggered every minute) picks up the request, finds matching restaurants through OpenSearch, fetches details from DynamoDB, and emails the user 3 restaurant suggestions through SES.

## Supported Inputs
- **Locations:** Manhattan, New York
- **Cuisines:** Chinese, Italian, Japanese, Mexican, Indian, Thai, Korean
- **Number of people:** 1 to 20

## Extra Credit
The bot remembers each user's last search (location, cuisine and restaurants sent) in DynamoDB table `concierge-state`. If a returning user asks for the same location and cuisine, the bot offers the same recommendations again.

## Repo Layout
- `frontend/`: chat website hosted on S3
- `lambda-functions/`: LF0, LF1 and LF2
- `other-scripts/`: API spec, Yelp scraper and OpenSearch loader

No keys or credentials are stored in this repo.
