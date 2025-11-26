#!/usr/bin/env python3
"""
Clear MongoDB videos collection.
WARNING: This deletes all video data from MongoDB!
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "video_grading"
COLLECTION_NAME = "videos"

def main():
    logger.info("=" * 60)
    logger.warning("⚠️  WARNING: This will DELETE all videos from MongoDB!")
    logger.info("=" * 60)
    
    confirm = input("\nType 'DELETE ALL' to confirm deletion: ").strip()
    if confirm != "DELETE ALL":
        logger.info("❌ Deletion cancelled")
        return False
    
    try:
        logger.info("\nConnecting to MongoDB...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Get count before deletion
        count_before = collection.count_documents({})
        logger.info(f"Found {count_before} videos in MongoDB")
        
        # Delete all
        logger.info("\n🗑️  Deleting all videos...")
        result = collection.delete_many({})
        logger.info(f"✅ Deleted {result.deleted_count} documents")
        
        # Verify
        count_after = collection.count_documents({})
        logger.info(f"✅ Remaining videos: {count_after}")
        
        if count_after == 0:
            logger.info("\n" + "=" * 60)
            logger.info("✅ MongoDB cleaned!")
            logger.info("=" * 60)
            logger.info("\nNext steps:")
            logger.info("1. Upload videos with Excel: python upload_transcripts_to_mongodb.py")
            logger.info("2. Fine-tune embeddings: python fine_tuning/01_prepare_training_data.py")
            logger.info("=" * 60)
            return True
        else:
            logger.error(f"❌ Some documents remain ({count_after})")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
