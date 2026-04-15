import os
from pymongo import MongoClient

MONGO_URL =  os.getenv("MONGO_URL")

try:
    client = MongoClient(MONGO_URL)
    db = client['student_predictor']

    users_collection = db["users"]
    predictions_collection = db["predictions"]

    print("MongoDB connected")

except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
