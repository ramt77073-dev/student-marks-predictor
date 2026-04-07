from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
from database import users_collection, predictions_collection
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = joblib.load("marks_model.joblib")

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class StudentInput(BaseModel):
    hours: float


class User(BaseModel):
    username: str
    password: str


@app.get("/")
def home():
    return {"message": "Student Marks Predictor API is running"}


@app.get("/about")
def about():
    return {"message": "This API predicts student marks based on study hours"}


@app.post("/signup")
def signup(user: User):
    try:
        username = user.username.strip()
        password = user.password.strip()

        if len(password.encode("utf-8")) > 72:
            return {"error": "Password too long. Keep it under 72 bytes."}

        existing_user = users_collection.find_one({"username": username})

        if existing_user:
            return {"error": "User already exists"}

        hashed_password = pwd_context.hash(password)

        users_collection.insert_one({
            "username": username,
            "password": hashed_password
        })

        return {"message": "User created successfully"}

    except Exception as e:
        return {"error": str(e)}
    
@app.post("/login")
def login(user: User):
    try:
        username = user.username.strip()
        password = user.password.strip()

        found_user = users_collection.find_one({"username": username})

        if not found_user:
            return {"error": "User not found"}

        if not pwd_context.verify(password, found_user["password"]):
            return {"error": "Invalid password"}

        return {"message": "Login successful"}

    except Exception as e:
        return {"error": str(e)}


@app.post("/predict")
def predict(data: StudentInput):
    hours = data.hours

    prediction = model.predict(pd.DataFrame({"hours": [hours]}))
    predicted_marks = round(float(prediction[0]), 2)

    return {
        "study_hours": hours,
        "predicted_marks": predicted_marks
    }