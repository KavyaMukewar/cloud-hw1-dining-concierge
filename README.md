### Dining Concierge Chatbot - HW1
Kavya Mukewar krm9909, Ananya Singh as21114

A serverless chatbot that collects dining preferences and emails restaurant suggestions.

S3 website -> API Gateway -> LF0 -> Lex -> LF1 -> SQS (Q1)
EventBridge (every minute) -> LF2 -> OpenSearch + DynamoDB -> SES email
Yelp API -> DynamoDB (yelp-restaurants) + OpenSearch (restaurants)

- frontend/: chat website hosted on S3
- lambda-functions/: LF0 (API to Lex), LF1 (Lex code hook), LF2 (queue worker and email)
- other-scripts/: API spec, Yelp scraper, OpenSearch loader

Extra credit: returning users get the option to repeat their last search (state in DynamoDB concierge-state).

No keys or credentials are stored in this repo.
