# Unit tests for Webhook

In development mode, you can unit-test the webhook as a standalone Node application. To test, run the webhook in test mode:

```
npm install
npm test
```

This will run the webhook in test mode running a http server on `localhost:8002`. You can then load the PostmanCollection and PostmanEnvironment in this folder and execute the tests.


