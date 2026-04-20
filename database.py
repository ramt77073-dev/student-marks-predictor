import os
from pymongo import MongoClient

MONGO_URL =  os.getenv("MONGO_URL")

client = MongoClient(MONGO_URL)
db = client["student_predictor"]

users_collection = db["users"]
predictions_collection = db["predictions"]
