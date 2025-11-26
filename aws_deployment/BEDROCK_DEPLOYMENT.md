# AWS Lambda Deployment with Bedrock (Simplified)

## STEP 1: Update Lambda Execution Role Permissions

In AWS IAM Console:
1. Go to **Roles** → Find **LambdaSageMakerRole**
2. Go to **Permissions** tab
3. Add this inline policy:

**Policy Name:** `AllowBedrock`

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:Converse"
            ],
            "Resource": "arn:aws:bedrock:us-east-1::model/anthropic.claude-3-haiku-*"
        }
    ]
}
```

## STEP 2: Create Lambda Function

In AWS Lambda Console:
1. Click **Create function**
2. **Name:** `rag-chatbot-bedrock`
3. **Runtime:** Python 3.12
4. **Role:** Select **LambdaSageMakerRole**
5. Click **Create**

## STEP 3: Add Code

1. In Lambda editor, delete default code
2. Copy-paste the code from: `lambda_handler_bedrock.py`
3. Click **Deploy**

## STEP 4: Add Layers (Dependencies)

Lambda needs these Python packages:
- `pymongo`
- `sentence-transformers`
- `scikit-learn`
- `numpy`

**Option A (Easy):** Add as Lambda Layer
- Create ZIP with: `/python/lib/python3.12/site-packages/` containing the packages
- Upload as layer

**Option B (Simpler):** Use environment variables
- Set timeout to 300 seconds (5 minutes) for first run
- Lambda will install on first invocation

## STEP 5: Configure Lambda

1. **Timeout:** 300 seconds (5 minutes)
2. **Memory:** 3008 MB (for sentence-transformers)
3. **Ephemeral storage:** 10240 MB

## STEP 6: Test

Click **Test** in Lambda console:

```json
{
    "user_input": "What does the first video discuss?"
}
```

Expected response: JSON with `response` and `status` fields

## STEP 7: Create API Gateway Endpoint

1. Go to **API Gateway** → **Create API**
2. **Type:** REST API
3. **Name:** `rag-chatbot-api`
4. Click **Create**

### Create Resource & Method:
1. Create resource: `/chat`
2. Create method: `POST`
3. **Integration type:** Lambda Function
4. **Lambda Function:** `rag-chatbot-bedrock`
5. Deploy to stage: `prod`

**Your API Endpoint URL:**
```
https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/chat
```

## STEP 8: Update Streamlit App

In `streamlit_app_cloud.py`, replace:
```python
LAMBDA_API_ENDPOINT = "YOUR_API_ENDPOINT_URL"
```

With your actual API Gateway endpoint.

## STEP 9: Test End-to-End

Run Streamlit locally:
```bash
streamlit run streamlit_app_cloud.py
```

Ask a question → Should get response from Claude via Bedrock!

## Cost Estimate

- **Lambda:** ~$0.20 per 1M requests (negligible)
- **Bedrock Claude 3 Haiku:** ~$0.25 per 1M input tokens
- **Total:** ~$5-20/month depending on usage

## Key Differences from SageMaker

| Feature | SageMaker | Bedrock |
|---------|-----------|---------|
| Cost | $0.35/hour always | Pay per token |
| Setup | Complex ECR issues | Simple API call |
| Model | Single neural-chat | Claude, Llama, Mistral |
| Quality | Good | Excellent (Claude) |
| Time to Deploy | 1+ hours | 10 minutes |

---

**Next Steps:**
1. Add Bedrock policy to Lambda role
2. Create Lambda function with bedrock handler code
3. Deploy API Gateway
4. Test!

No more SageMaker issues! 🎉
