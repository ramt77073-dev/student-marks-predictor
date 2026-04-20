import os
from pymongo import MongoClient

MONGO_URL = os.getenv("MONGO_URL")

if not MONGO_URL:
    print("WARNING: MONGO_URL environment variable not set")
    raise Exception("MONGO_URL not configured")

try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    # Test connection
    client.server_info()
    
    db = client["student_predictor"]
    users_collection = db["users"]
    predictions_collection = db["predictions"]
    
    print("✓ MongoDB connected successfully")
except Exception as e:
    print(f"✗ MongoDB connection failed: {e}")
    raise
