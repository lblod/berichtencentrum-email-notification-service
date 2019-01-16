# berichtencentrum-email-notification-service

## Configuration

### Environment variables

Required environment variables:

* `FROM_EMAIL_ADDRESS`: The email address added in the 'from' header of the sent mail.
* `LOKET_API_BASEURL`: Base URL of the loket API (so we can supply a working link to the message mentioned in the email)


Optional environment variables:
* `MU_APPLICATION_GRAPH`
* `MU_SPARQL_ENDPOINT`
* `MU_SPARQL_UPDATEPOINT`

* `RUN_INTERVAL`: How frequent the service to send email notifications must run (in minutes), _default: 5_
* `MAX_MESSAGE_AGE`: Max age of the messages requested to the API (in days), _default: 3_. This value could theoretically be equal to that of `RUN_INTERVAL`, but a margin is advised to take eventual application or API downtime into account (to not miss any older messages).
