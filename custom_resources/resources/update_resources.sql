CREATE DATABASE IF NOT EXISTS TOKENIZER_DEMO;

ALTER API INTEGRATION TOKENIZER_API
SET api_allowed_prefixes=('https://{{ API_GW_ID }}.execute-api.{{ REGION }}.amazonaws.com/{{ STAGE }}/detokenize_string');

USE DATABASE TOKENIZER_DEMO;

CREATE OR REPLACE EXTERNAL FUNCTION TOKENIZER_DEMO.PUBLIC.detokenize_string(ID string)
    returns string
    api_integration = TOKENIZER_API
    as 'https://{{ API_GW_ID }}.execute-api.{{ REGION }}.amazonaws.com/{{ STAGE }}/detokenize_string'
;

CREATE OR REPLACE MASKING POLICY TOKENIZER_DEMO.PUBLIC.email_de_token as (val string) returns string ->
  CASE
    WHEN current_role() in ('DEMO_ANALYST') then TOKENIZER_DEMO.PUBLIC.detokenize_string(val)
    ELSE val
  END;

ALTER TABLE IF EXISTS TOKENIZER_DEMO.PUBLIC.CUSTOMERS MODIFY COLUMN email SET MASKING POLICY email_de_token