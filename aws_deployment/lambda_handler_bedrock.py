"""
AWS Lambda handler for RAG chatbot queries using AWS Bedrock Claude + MongoDB Vector Search.
Production-ready: 
- Uses MongoDB Atlas Vector Search (NOT client-side embeddings)
- Lightweight dependencies (pymongo only)
- Credentials from Secrets Manager
- Bedrock Claude for LLM
"""

import json
import os
import boto3
import re
from pymongo import MongoClient

# AWS clients
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
secrets_client = boto3.client('secretsmanager', region_name='us-east-1')

# Constants
BEDROCK_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
DATABASE_NAME = "video_grading"
COLLECTION_NAME = "videos"
VECTOR_INDEX_NAME = "embedding_index"

# Cache credentials to avoid repeated Secrets Manager calls
_cached_mongo_uri = None


def get_mongo_uri():
    """Get MongoDB URI from Secrets Manager (cached), with optional env override."""
    global _cached_mongo_uri

    if _cached_mongo_uri:
        return _cached_mongo_uri

    # Optional: allow override via environment variable for debugging
    env_uri = os.getenv("MONGO_URI")
    if env_uri:
        _cached_mongo_uri = env_uri.strip()
        return _cached_mongo_uri

    try:
        response = secrets_client.get_secret_value(SecretId="MONGO_URI")
        _cached_mongo_uri = response["SecretString"].strip()
        return _cached_mongo_uri
    except Exception as e:
        print(f"Error fetching from Secrets Manager: {e}")
        # Fallback for local/dev only – remove or replace in production.
        fallback = None  # MONGO_URI must be set in environment or Secrets Manager
        print("Using fallback Mongo URI (dev only).")
        _cached_mongo_uri = fallback
        return _cached_mongo_uri


def get_mongo_connection():
    """Connect to MongoDB Atlas."""
    try:
        mongo_uri = get_mongo_uri()
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=15000)
        client.admin.command('ping')
        return client
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        return None


def find_relevant_videos_vector_search(query_embedding, collection, top_k=3):
    """
    Use MongoDB Atlas Vector Search to find relevant videos.
    Assumes a vector search index named VECTOR_INDEX_NAME on field 'embedding'.
    """
    try:
        if query_embedding is None:
            # No embedding provided – fall back to simple transcript-based fetch
            results = list(
                collection.find(
                    {"transcript": {"$exists": True}},
                    {
                        "_id": 1,
                        "video_name": 1,
                        "transcript": 1,
                        "duration": 1,
                    },
                ).limit(top_k)
            )
            return results

        pipeline = [
            {
                "$vectorSearch": {
                    "index": VECTOR_INDEX_NAME,
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": max(top_k * 20, 200),
                    "limit": top_k,
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "video_name": 1,
                    "transcript": 1,
                    "duration": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]

        results = list(collection.aggregate(pipeline))
        return results

    except Exception as e:
        print(f"Error in vector search: {e}")
        # Fallback: simple find if vector search/index not configured
        try:
            results = list(
                collection.find(
                    {"transcript": {"$exists": True}},
                    {
                        "_id": 1,
                        "video_name": 1,
                        "transcript": 1,
                        "duration": 1,
                    },
                ).limit(top_k)
            )
            return results
        except Exception as e2:
            print(f"Fallback simple search failed: {e2}")
            return []


def find_video_by_name(query_text, collection):
    """Find a specific video document if the query mentions a video name in quotes.
    
    Uses simple substring matching (case-insensitive) to be more robust.
    """
    match = re.search(r'"([^"]+)"', query_text)
    if not match:
        return None

    quoted_name = match.group(1).strip()
    
    # Try exact case-insensitive match first
    doc = collection.find_one({"video_name": {"$regex": f"^{re.escape(quoted_name)}$", "$options": "i"}})
    if doc:
        return doc
    
    # If no exact match, try substring match (handles partial names)
    doc = collection.find_one({"video_name": {"$regex": re.escape(quoted_name), "$options": "i"}})
    return doc


def get_query_embedding_from_text(query_text):
    """Get embedding via Amazon Titan Text Embeddings V2 on Bedrock."""
    try:
        response = bedrock_client.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            body=json.dumps(
                {
                    "inputText": query_text,
                }
            ),
        )
        body = json.loads(response["body"].read())
        return body["embedding"]
    except Exception as e:
        print(f"Error getting Titan embedding: {e}")
        return None


def query_claude_for_response(prompt):
    """Call Claude via AWS Bedrock."""
    try:
        response = bedrock_client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            inferenceConfig={
                "maxTokens": 500,
                "temperature": 0.3,
                "topP": 0.9,
            }
        )
        response_text = response["output"]["message"]["content"][0]["text"]
        return response_text.strip()
            
    except Exception as e:
        print(f"Bedrock error: {e}")
        return f"Error querying Claude: {str(e)}"


def query_with_rag(question, context_videos):
    """Build RAG prompt and query Claude via Bedrock."""
    try:
        # Build context from videos
        context_parts = []
        for i, video in enumerate(context_videos, 1):
            transcript = video.get('transcript', '')
            duration = video.get('duration', 'Unknown')
            video_name = video.get('video_name', f'Video {i}')
            context_parts.append(f"[{video_name} - Duration: {duration}]\n{transcript}")
        
        context = "\n\n".join(context_parts)
        
        # Build prompt
        prompt = f"""You are a helpful assistant analyzing video transcripts.
Your job is to answer questions based on what's discussed in the videos.

VIDEO TRANSCRIPT(S):
{context}

USER QUESTION: {question}

INSTRUCTIONS:
- Answer directly from the transcript content
- If asked "what does this video do/cover/teach?" - provide a clear summary
- If asked a specific question - answer based on the transcript
- Use quotes from the transcript when relevant
- If information is not in the transcript, say so clearly
- Be concise and helpful

ANSWER:"""
        
        response = query_claude_for_response(prompt)
        return response
        
    except Exception as e:
        print(f"RAG query error: {e}")
        return f"Error processing query: {str(e)}"


def lambda_handler(event, context):
    """
    Lambda handler for RAG chat requests.
    
    Production architecture:
    1. Client sends user query
    2. Lambda retrieves top-k videos from MongoDB Vector Search
    3. Lambda builds RAG prompt with retrieved transcripts
    4. Lambda calls Bedrock Claude for response
    5. Returns response to client
    
    Expected event:
    {
        "user_input": "What is sentiment analysis?",
        "query_embedding": [0.1, 0.2, ...],  # Optional: pre-computed embedding
        "session_id": "user123"  # Optional
    }
    """
    try:
        # Parse request
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event
        user_input = body.get('user_input', '').strip()
        query_embedding = body.get('query_embedding')
        
        if not user_input:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'No user input provided', 'status': 'error'})
            }
        
        # Connect to MongoDB
        mongo_client = get_mongo_connection()
        if not mongo_client:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'MongoDB connection failed', 'status': 'error'})
            }
        
        try:
            collection = mongo_client[DATABASE_NAME][COLLECTION_NAME]
            
            # First, try to resolve a specific video name mentioned in quotes
            specific_video = find_video_by_name(user_input, collection)
            
            if specific_video:
                # If user only provided the video name in quotes, treat it as a summary request
                match = re.search(r'"([^"]+)"', user_input)
                summary_question = user_input
                if match and user_input.strip().replace(f'"{match.group(1)}"', '').strip() == '':
                    summary_question = "Summarize the key concepts and content from this video transcript."
                
                videos = [specific_video]
                answer = query_with_rag(summary_question, videos)
            else:
                # No specific video name – fall back to vector search
                videos = find_relevant_videos_vector_search(query_embedding, collection, top_k=3)
                if not videos:
                    return {
                        'statusCode': 200,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        },
                        'body': json.dumps({
                            'response': 'No relevant videos found for your question.',
                            'status': 'success',
                            'videos_used': []
                        })
                    }
                
                answer = query_with_rag(user_input, videos)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'response': answer,
                    'status': 'success',
                    'videos_used': [
                        {
                            'id': str(v.get('_id')),
                            'video_name': v.get('video_name'),
                            'duration': v.get('duration', 'Unknown')
                        }
                        for v in videos
                    ]
                })
            }
            
        finally:
            mongo_client.close()
        
    except Exception as e:
        print(f"Lambda error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'status': 'error'
            })
        }
