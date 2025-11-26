from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", None)  # Set in .env file or environment variables
client = MongoClient(MONGO_URI)
collection = client['video_grading']['videos']

# Count videos
total = collection.count_documents({})
print(f'Total videos: {total}')

# Count videos with embeddings
with_embed = collection.count_documents({'embedding': {'$exists': True}})
print(f'Videos with embeddings: {with_embed}')

# Count videos with transcripts
with_trans = collection.count_documents({'transcript': {'$exists': True}})
print(f'Videos with transcripts: {with_trans}')

# Show first video name
first = collection.find_one({}, {'video_name': 1})
if first:
    print(f'First video name: {first.get("video_name")}')
