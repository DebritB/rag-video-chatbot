# Deployment Guide - AWS Lambda + Streamlit Cloud

## Step 1: Lambda Code Deployment

### Option A: Via AWS Console (Quick)
1. Open **AWS Lambda** console
2. Find your function (e.g., `rag-bedrock-handler`)
3. Copy contents of `lambda_handler_bedrock.py`
4. Paste into inline editor in Lambda console
5. Click **Deploy**

### Option B: Via AWS CLI (Recommended)
```bash
# From aws_deployment directory
# Ensure layer is attached (step 2 first)

zip -r lambda_function.zip lambda_handler_bedrock.py
aws lambda update-function-code \
  --function-name rag-bedrock-handler \
  --zip-file fileb://lambda_function.zip \
  --region us-east-1
```

## Step 2: Layer Attachment (One-time Setup)

Lambda needs `pymongo` layer. If not already attached:

1. In Lambda console → Layers (or Code → Designer tab)
2. Click "Add layer"
3. Select the layer you created earlier (name like `pymongo-layer-py311`)
4. Click "Add"

## Step 3: Environment Variables

In Lambda console → Configuration → Environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `MONGO_URI` | *(leave blank)* | Reads from Secrets Manager by default |

MongoDB URI should be in **AWS Secrets Manager** under secret name `MONGO_URI`.

## Step 4: IAM Permissions

Verify Lambda role has:
- ✅ `secretsmanager:GetSecretValue` (for Mongo URI)
- ✅ `bedrock:Converse` (for Claude)
- ✅ `bedrock:InvokeModel` (for embeddings)
- ✅ CloudWatch Logs (auto-included)

Check in IAM → Roles → `LambdaBedrockRole-v2` (or your role name)

## Step 5: Test Lambda

In Lambda console → **Test**:

```json
{
  "user_input": "What is sentiment analysis?"
}
```

Expected response:
```json
{
  "statusCode": 200,
  "body": "{\"status\":\"success\",\"response\":\"...\",\"videos_used\":[...]}"
}
```

## Step 6: Verify API Gateway

1. Go to **API Gateway** console
2. Find your API (e.g., `rag-api`)
3. Click **Stages** → **prod**
4. Copy **Invoke URL** (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com/prod`)
5. Test with curl:
   ```bash
   curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/prod/chat \
     -H "Content-Type: application/json" \
     -d '{"user_input":"test question"}'
   ```

## Step 7: Update Streamlit Secrets

### Local Testing (.env)
```bash
# In aws_deployment/.env
LAMBDA_API_ENDPOINT=https://abc123.execute-api.us-east-1.amazonaws.com/prod/chat
```

### Streamlit Cloud
1. Go to your Streamlit app dashboard
2. Click **⋮** (menu) → **Settings**
3. Go to **Secrets** tab
4. Add:
   ```toml
   LAMBDA_API_ENDPOINT = "https://abc123.execute-api.us-east-1.amazonaws.com/prod/chat"
   ```
5. Save

## Step 8: Deploy Streamlit (if using Streamlit Cloud)

1. Push code to GitHub:
   ```bash
   git add .
   git commit -m "Update Lambda code and config"
   git push
   ```

2. Streamlit Cloud auto-deploys when it detects changes

3. Monitor deployment in Streamlit Cloud dashboard

## Troubleshooting

### Lambda Test Returns Error

**Error: "Secrets Manager error"**
- ✅ Verify IAM role has `secretsmanager:GetSecretValue`
- ✅ Verify secret name is exactly `MONGO_URI` in Secrets Manager
- ✅ Verify Lambda role can access that secret

**Error: "MongoDB connection error"**
- ✅ Test Mongo URI locally first
- ✅ Ensure Lambda has internet access (not in private subnet without NAT)
- ✅ Check MongoDB Atlas Network Access allowlist

**Error: "Bedrock error / Access Denied"**
- ✅ Verify IAM role has `bedrock:Converse` and `bedrock:InvokeModel`
- ✅ Verify region is `us-east-1` (Bedrock not available in all regions)
- ✅ Check Anthropic use-case approval (Bedrock → Model catalog)

### Streamlit Shows "No response generated"

- ✅ Check `LAMBDA_API_ENDPOINT` is correct in Streamlit Secrets
- ✅ Open browser DevTools (F12) → Network tab → check API request status
- ✅ If 403: API Gateway endpoint is wrong
- ✅ If 500: Lambda error; check CloudWatch logs

## Monitoring

### CloudWatch Logs
1. Go to **CloudWatch** → **Logs** → **Log groups**
2. Find `/aws/lambda/rag-bedrock-handler` (or your function name)
3. Watch for errors in real-time as you test

### Lambda Metrics
1. In Lambda console → **Monitor** tab
2. Check:
   - Duration (should be < 10s for fast answers)
   - Error rate (should be 0%)
   - Memory used (should be < 256MB)

## Rollback Plan

If deployment fails:

1. **Revert Lambda code** to last working version:
   - AWS Console → Function code → revisions (if versioning enabled)
   - Or re-upload last known-good ZIP

2. **Revert API Gateway**:
   - API Gateway → Stages → rollback deployment

3. **Check logs** for root cause, fix, and re-deploy

## Cost Optimization

- **Lambda**: ~$0.20 per 1M invocations (very cheap)
- **Bedrock**: Pay per token; use temperature 0.3 for consistent answers (fewer retries)
- **MongoDB**: Use free tier for testing, scale up as needed

## Next Steps

- Monitor usage patterns over first week
- Set up CloudWatch alarms for error rate > 1%
- Plan capacity for production load
- Consider implementing request caching for repeated questions
