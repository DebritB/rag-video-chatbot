# Security & Secrets Management

## Overview

This project handles sensitive information carefully:
- **API Endpoints** → Safe to share (public interfaces)
- **Database URIs** → Stored in AWS Secrets Manager + env vars
- **AWS Credentials** → Via IAM roles (never exposed in code)
- **Environment Variables** → .env file excluded via .gitignore

## What NOT to Commit

❌ **NEVER commit these to GitHub:**
```
.env (contains LAMBDA_API_ENDPOINT for cloud)
aws_deployment/.env (contains MONGO_URI for local testing)
.aws/credentials
AWS API keys / secret keys
MongoDB connection strings in code
Anthropic API keys
```

✅ **DO commit these:**
```
.env.example (template, no secrets)
aws_deployment/.env.example (template, no secrets)
.gitignore (tells Git what to exclude)
Code files (with secrets read from env vars)
```

## Environment Variables

### For Local Testing (`.env`)
```bash
# aws_deployment/.env (local only, NOT committed)
LAMBDA_API_ENDPOINT=https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/chat
```

### For Streamlit Cloud Deployment
1. **Do NOT** put secrets in `.env` on cloud
2. **Do** use Streamlit Secrets:
   - App dashboard → Settings → Secrets
   - Add:
     ```toml
     LAMBDA_API_ENDPOINT = "https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/chat"
     ```

### For Lambda Function
- MongoDB URI: Stored in **AWS Secrets Manager** (secret name: `MONGO_URI`)
- AWS credentials: Via **Lambda execution role** (IAM)
- Region: Set in Lambda environment variable `AWS_REGION=us-east-1`

## AWS Secrets Manager (For Lambda)

### Creating a Secret
```bash
# Create secret for MongoDB URI
aws secretsmanager create-secret \
  --name MONGO_URI \
  --secret-string "mongodb+srv://user:pass@cluster.mongodb.net/?appName=ClusterDB" \
  --region us-east-1
```

### Retrieving a Secret (Lambda code)
```python
import boto3
client = boto3.client('secretsmanager', region_name='us-east-1')
response = client.get_secret_value(SecretId="MONGO_URI")
mongo_uri = response["SecretString"]
```

This is already done in `lambda_handler_bedrock.py`.

## GitHub Secrets (For CI/CD, if needed)

If you add GitHub Actions workflows that deploy Lambda:

1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Add:
   - `AWS_ACCESS_KEY_ID` (only if needed for CI/CD)
   - `AWS_SECRET_ACCESS_KEY` (only if needed for CI/CD)

**Recommendation:** Use AWS IAM roles instead (safer, no keys exposed).

## Verifying Secrets Are NOT in Code

Before committing, check:

```bash
# Ensure no passwords in committed files
git diff --cached | grep -i password

# Ensure no AWS keys
git diff --cached | grep AKIA

# Ensure no MongoDB URIs in Python code
git diff --cached | grep "mongodb+srv://"
```

## API Endpoint (Safe to Share)

The Lambda API Gateway URL like:
```
https://hxvtgx7m24.execute-api.us-east-1.amazonaws.com/prod/chat
```

is **perfectly safe** to share because:
- ✅ It's the public interface (meant to be called)
- ✅ Protected by AWS IAM (caller must have permissions)
- ✅ No credentials in URL itself
- ✅ Rate limiting via API Gateway throttling
- ✅ CloudWatch logs all activity

## Incident Response

If you accidentally commit a secret:

```bash
# Option 1: Remove from history (if not pushed to origin yet)
git rm --cached .env
echo ".env" >> .gitignore
git commit --amend -m "Remove .env"
git push

# Option 2: Use BFG Repo Cleaner (if already pushed)
# https://rtyley.github.io/bfg-repo-cleaner/

# Option 3: Regenerate credentials
# - Change MongoDB password in Atlas
# - Rotate AWS keys
# - Update Secrets Manager
# - Redeploy Lambda
```

## Best Practices

✅ Do:
- Use `.env.example` as template for developers
- Store long-term secrets in AWS Secrets Manager
- Use environment variables in code
- Rotate credentials periodically
- Use narrow IAM roles (least privilege)
- Enable CloudTrail for audit logs

❌ Don't:
- Hardcode secrets in Python files
- Commit .env files
- Share AWS credentials via email/Slack
- Use root AWS account for Lambda
- Leave old credentials in git history
- Test with production credentials

## Troubleshooting

### "ModuleNotFoundError: No module named 'dotenv'"
- Install: `pip install python-dotenv`
- Or remove if not using `.env` (Streamlit Secrets doesn't need it)

### "SecretId MONGO_URI not found"
- Verify secret name in Secrets Manager is exactly `MONGO_URI`
- Verify Lambda role has `secretsmanager:GetSecretValue` permission

### "Unauthorized: User is not authorized to perform: bedrock:Converse"
- Verify Lambda role has Bedrock permissions
- IAM → Roles → Lambda role → Attached policies

## References

- [AWS Secrets Manager docs](https://docs.aws.amazon.com/secretsmanager/)
- [Streamlit Secrets docs](https://docs.streamlit.io/deploy/streamlit-cloud/deploy-your-app#secrets-management)
- [OWASP: Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
