import os
from pymongo import MongoClient

MONGO_URL =  "mongodb://localhost:27017"

if not MONGO_URL:
    raise ValueError("MONGO_URL environment variable is not set")

client = MongoClient(MONGO_URL)
db = client["student_predictor"]

users_collection = db["users"]
predictions_collection = db["predictions"]
