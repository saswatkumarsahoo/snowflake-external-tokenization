# Snowflake Dynamic Masking using External Tokenization

## Usage
This is an example to demonstrate snowflake external tokenization
Blog Link - 
### Prerequisites

- A (trial) Snowflake Account with ACCOUNTADMIN permission
- An AWS account & AWS CLI pre-installed
- Install node.js if you have not already

### Installtaion
Install serverless module via NPM
```bash
$ npm install -g serverless
```
### Configuration
Fill your snowflake account details in the env.yml file
```yaml
SF_USER: your snowflake username
PASSWORD: your snowflake password
ACCOUNT: your snowflake account
WAREHOUSE: COMPUTE_WH
DATABASE: TOKENIZER_DEMO
SCHEMA: PUBLIC
ROLE: ACCOUNTADMIN
```

### Deployment
Deploy the application
```bash
$ serverless deploy
```

After deploying, you should see output similar to:

```bash
Deploying snowflake-dynamic-masking to stage dev (eu-west-1)

✔ Service deployed to stack snowflake-dynamic-masking-dev (236s)

endpoint: POST - https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/
functions:
  setupResources: snowflake-dynamic-masking-dev-setupResources
  updateResources: snowflake-dynamic-masking-dev-updateResources
  seeder: snowflake-dynamic-masking-dev-seeder
  detokenizer: snowflake-dynamic-masking-dev-detokenizer (8.1 kB)
```
### Test
After successful deployment, you can login to snowsight and test the external tokenizer
```sql
-- test with developer role
USE ROLE DEMO_DEVELOPER;
USE WAREHOUSE TOKENIZER_DEMO_WH; 
USE DATABASE TOKENIZER_DEMO;
SELECT * FROM TOKENIZER_DEMO.PUBLIC.CUSTOMERS;

-- test with analyst role
USE ROLE DEMO_ANALYST;
USE WAREHOUSE TOKENIZER_DEMO_WH; 
USE DATABASE TOKENIZER_DEMO;
SELECT * FROM TOKENIZER_DEMO.PUBLIC.CUSTOMERS;
```

_**Note**_
This example is only for demo purpose and not production ready. Snowflake credentials are stored in plain text in lambda's environment variables which is not considered as a security best practice. 

### Clean Up
Remove the AWS & Snowflake resources

```bash
$ serverless remove
```

