import os
from pymongo import MongoClient

MONGO_URL =  os.getenv("MONGO_URL")

client = MongoClient(MONGO_URL)

db = client["marks_app"]


users_collection = db["users"] 
predictions_collection = db["predictions"]
