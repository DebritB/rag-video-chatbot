#!/usr/bin/env python3
"""
Store actual transcripts from transcriptions.xlsx in MongoDB with embeddings.
"""

from pymongo import MongoClient
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np

MONGO_URI = os.getenv("MONGO_URI", None)  # Set in .env file or environment variables
DATABASE_NAME = "video_grading"
COLLECTION_NAME = "videos"

print("Loading data...")
transcriptions_df = pd.read_excel("transcriptions.xlsx")

print("Connecting to MongoDB...")
client = MongoClient(MONGO_URI)
collection = client[DATABASE_NAME][COLLECTION_NAME]

print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

print(f"\nUploading {len(transcriptions_df)} videos with transcripts...\n")
uploaded = 0

for idx, trans_row in transcriptions_df.iterrows():
    video_name = trans_row['video_name']
    spoken_script = trans_row['transcript']
    duration = trans_row['duration']
    
    try:
        # Generate embedding from the actual transcript
        embedding = model.encode(spoken_script).tolist()
        
        # Insert new document with transcript and embedding
        result = collection.insert_one(
            {
                "video_name": video_name,
                "transcript": spoken_script,  # Actual spoken text
                "embedding": embedding,       # Embedding from transcript
                "duration": duration,
                "transcript_length": len(spoken_script)
            }
        )
        
        uploaded += 1
        if (idx + 1) % 50 == 0:
            print(f"  ✓ Processed {idx + 1} videos...")
    
    except Exception as e:
        print(f"  ❌ Error with {video_name}: {e}")

print(f"\n✅ Upload Complete!")
print(f"   Uploaded: {uploaded} videos")

# Verify
total = collection.count_documents({})
with_transcript = collection.count_documents({"transcript": {"$exists": True}})
with_embedding = collection.count_documents({"embedding": {"$exists": True}})

print(f"\n📊 MongoDB Verification:")
print(f"   Total videos: {total}")
print(f"   Videos with transcript: {with_transcript}")
print(f"   Videos with embedding: {with_embedding}")

# Show sample
sample = collection.find_one({"transcript": {"$exists": True}})
if sample:
    print(f"\n📹 Sample Video:")
    print(f"   Name: {sample['video_name']}")
    print(f"   Duration: {sample['duration']}")
    print(f"   Transcript length: {len(sample.get('transcript', ''))} chars")
    print(f"   Embedding dims: {len(sample.get('embedding', []))}")
    print(f"\n   First 300 chars of transcript:")
    print(f"   {sample.get('transcript', '')[:300]}...")

client.close()
print("\n✅ Done!")
