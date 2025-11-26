from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", None)  # Set in .env file or environment variables
DATABASE_NAME = "video_grading"
COLLECTION_NAME = "videos"

client = MongoClient(MONGO_URI)
collection = client[DATABASE_NAME][COLLECTION_NAME]

docs = collection.find({}, {"_id": 0, "video_name": 1})
print("All video_name values in MongoDB:")
for doc in docs:
    print(f"  - {doc.get('video_name')}")
