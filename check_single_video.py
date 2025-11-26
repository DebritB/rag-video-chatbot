from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", None)  # Set in .env file or environment variables
DATABASE_NAME = "video_grading"
COLLECTION_NAME = "videos"
VIDEO_NAME = "14517926_video7-1.mp4"

client = MongoClient(MONGO_URI)
collection = client[DATABASE_NAME][COLLECTION_NAME]

doc = collection.find_one({"video_name": VIDEO_NAME})
if doc:
    print("FOUND:", doc.get("video_name"))
    print("Has transcript:", "transcript" in doc)
    print("Has embedding:", "embedding" in doc)
else:
    print("NOT FOUND")
