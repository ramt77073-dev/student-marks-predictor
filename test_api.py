from fastapi import FastAPI
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
from jose.exceptions import JWTError
from datetime import datetime, timedelta

app = FastAPI()

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    username: str
    password: str

@app.get("/")
def home():
    return {"message": "API is working"}

@app.post("/signup")
def signup(user: User):
    return {"message": f"User {user.username} registered"}

print("Basic imports work!")