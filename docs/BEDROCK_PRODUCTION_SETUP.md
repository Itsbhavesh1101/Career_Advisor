# AWS Bedrock Production Setup

## Current Integration

The backend already supports `LLM_PROVIDER=bedrock` through the Phase 3 provider abstraction. `BedrockConverseProvider` uses boto3 `bedrock-runtime` and the Bedrock Converse API, which keeps the app model-provider-specific code isolated from the analysis services.

References:

- Bedrock inference APIs: https://docs.aws.amazon.com/bedrock/latest/userguide/inference-api.html
- Bedrock inference prerequisites: https://docs.aws.amazon.com/bedrock/latest/userguide/inference-prereq.html
- Bedrock CLI examples: https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started-api-ex-cli.html

## Default Production Settings

```env
LLM_PROVIDER=bedrock
AWS_REGION=ap-south-1
BEDROCK_REGION=ap-south-1
BEDROCK_MODEL_ID=apac.amazon.nova-lite-v1:0
BEDROCK_TIMEOUT_SECONDS=45
```

The `apac.` inference profile prefix is required for Nova Lite accounts that do not support direct on-demand invocation of `amazon.nova-lite-v1:0`. The exact model or inference profile ID can be changed per sandbox availability, but keep it explicit in the environment so judges and operators can see that the system is not hardcoded to one provider.

## Permissions

For the current Converse API path, the runtime identity needs permission to invoke the selected model. AWS documents that Converse requires model invocation permissions; use least privilege around the selected model where possible.

Minimum action to allow:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

For production hardening, replace `"Resource": "*"` with approved model ARNs for the institution account and region.

## Credential Strategy

Local development:

- Use the AWS credential chain through AWS CLI profiles, environment variables, or SSO.
- Do not store AWS keys in `backend/.env`.

Cloud Run production options:

- Preferred: workload identity federation between Google Cloud and AWS.
- Acceptable for a controlled prototype: approved secret injection through Google Secret Manager.
- Avoid: committing AWS keys to repo files or checked-in env templates.

The backend uses the normal AWS credential chain from boto3. That means deployment should provide credentials to the runtime environment instead of changing application code.

## Sandbox Validation

Run these checks before the ceremony demo:

1. Confirm Bedrock model access is enabled in `ap-south-1` or update `BEDROCK_REGION`.
2. Confirm the sandbox account supports `BEDROCK_MODEL_ID`.
3. Run a small Bedrock Converse API prompt from the same credential context used by deployment.
4. Set backend env to `LLM_PROVIDER=bedrock`.
5. Start the backend and verify `/health`.
6. Run one profile analysis.
7. Confirm output is valid JSON where the app expects structured output.
8. Confirm provider errors are handled as controlled app errors, not raw stack traces.

## Governance

- Keep a model allowlist in deployment docs and environment values.
- Keep LLM daily limits enabled.
- Keep endpoint-specific budgets enabled.
- Log provider name, model ID, request status, and token count.
- Do not log raw student resumes, private profile details, or secrets.
- Prefer deterministic placement/admission intelligence where the system already has enough structured data.

## Failure Modes

- Model unavailable in selected region: change `BEDROCK_REGION` and model ID together after validation.
- Permission denied: check `bedrock:InvokeModel` and model access approval.
- Timeout: raise `BEDROCK_TIMEOUT_SECONDS` only after checking payload size and Cloud Run request timeout.
- Invalid JSON: keep the existing strict schema repair and validation path; do not display unvalidated LLM output.
